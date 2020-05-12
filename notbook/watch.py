import asyncio
from multiprocessing.context import Process
from pathlib import Path
from time import time

from aiohttp import web
from aiohttp.web_exceptions import HTTPMovedPermanently, HTTPNotFound
from aiohttp.web_fileresponse import FileResponse
from aiohttp.web_response import Response
from watchgod import PythonWatcher, awatch

from .main import build, prepare

__all__ = ('watch',)
WS = 'websockets'


async def static(request):
    request_path = request.match_info['path'].lstrip('/')
    directory: Path = request.app['output_dir'].resolve()
    if request_path == '':
        filepath = directory / 'index.html'
    else:
        try:
            filepath = (directory / request_path).resolve()
            filepath.relative_to(directory)
        except Exception as exc:
            # perm error or other kind!
            raise HTTPNotFound() from exc
    for _ in range(20):
        if filepath.exists():
            break
        await asyncio.sleep(0.1)

    if filepath.is_file():
        return FileResponse(filepath)
    else:
        raise HTTPNotFound()


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


def build_in_subprocess(exec_file_path: Path, output_dir: Path, dev: bool):
    process = Process(target=build, args=(exec_file_path, output_dir), kwargs=dict(reload=True, dev=dev))
    process.start()
    process.join()


async def rebuild(app: web.Application):
    exec_file_path: Path = app['exec_file_path']
    output_dir: Path = app['output_dir']
    dev: bool = app['dev']
    watcher = awatch(exec_file_path, watcher_cls=PythonWatcher)
    async for _ in watcher:
        print(f're-running {exec_file_path}...')
        start = time()
        await watcher.run_in_executor(build_in_subprocess, exec_file_path, output_dir, dev)
        for ws in app[WS]:
            await ws.send_str('reload')
        c = len(app[WS])
        print(f'run completed in {time() - start:0.3f}s, {c} browser{"" if c == 1 else "s"} updated')


async def startup(app):
    asyncio.get_event_loop().create_task(rebuild(app))


def watch(exec_file_path: Path, output_dir: Path, dev: bool = False):
    if not dev:
        prepare(output_dir)
    print(f'running {exec_file_path}...')
    build_in_subprocess(exec_file_path, output_dir, dev)

    app = web.Application()
    app.on_startup.append(startup)
    app.update(
        exec_file_path=exec_file_path, output_dir=output_dir, build=build, dev=dev, websockets=set(),
    )
    app.add_routes(
        [
            web.get('/.reload/up/', server_up),
            web.get('/.reload/ws/', reload_websocket),
            web.get('/index.html', moved),
            web.get('/{path:.*}', static),
        ]
    )

    port = 8000
    print(f'watching {exec_file_path}, serving output at http://localhost:{port}')

    web.run_app(app, port=port, print=lambda s: None)
