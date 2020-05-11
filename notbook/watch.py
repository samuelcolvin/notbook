import asyncio
from multiprocessing.context import Process
from pathlib import Path
from time import time

from aiohttp import web
from aiohttp.web_exceptions import HTTPMovedPermanently
from aiohttp.web_fileresponse import FileResponse
from aiohttp.web_response import Response
from watchgod import awatch, PythonWatcher

from .main import prepare, build

__all__ = ('watch',)
WS = 'websockets'


async def index(request):
    path = request.app['output_dir'] / 'index.html'
    for _ in range(20):
        if path.exists():
            break
        await asyncio.sleep(100)
    return FileResponse(path)


async def server_up(request):
    return Response(body=b'server up\n', content_type='text/plain')


async def reload_websocket(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    request.app[WS].add(ws)
    async for _ in ws:
        pass

    request.app[WS].remove(ws)
    return ws


async def moved(request):
    raise HTTPMovedPermanently('/')


def build_in_subprocess(exec_file_path: Path, output_dir: Path):
    process = Process(target=build, args=(exec_file_path, output_dir))
    process.start()
    process.join()


async def rebuild(app: web.Application):
    exec_file_path: Path = app['exec_file_path']
    output_dir: Path = app['output_dir']
    watcher = awatch(exec_file_path, watcher_cls=PythonWatcher)
    async for _ in watcher:
        print(f're-running {exec_file_path}...')
        start = time()
        await watcher.run_in_executor(build_in_subprocess, exec_file_path, output_dir)
        for ws in app[WS]:
            await ws.send_str('reload')
        c = len(app[WS])
        print(f'run completed in {time() - start:0.3f}s, {c} browser{"" if c == 1 else "s"} updated')


async def startup(app):
    asyncio.get_event_loop().create_task(rebuild(app))


def watch(exec_file_path: Path, output_dir: Path):
    prepare(output_dir)
    print(f'running {exec_file_path}...')
    build_in_subprocess(exec_file_path, output_dir)

    app = web.Application()
    app.on_startup.append(startup)
    app.update(
        exec_file_path=exec_file_path,
        output_dir=output_dir,
        build=build,
        websockets=set(),
    )
    app.add_routes([
        web.get('/', index),
        web.get('/.devtools/up/', server_up),
        web.get('/.devtools/reload-ws/', reload_websocket),
        web.get('/index.html', moved),
    ])

    port = 8000
    print(f'watching {exec_file_path}, serving output at http://localhost:{port}')

    web.run_app(app, port=port, print=lambda s: None)
