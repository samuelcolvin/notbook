import shutil
from pathlib import Path

from .exec import exec_file
from .render import render, render_exception
from .render_tools import ExecException

__all__ = 'build', 'prepare'


def build(exec_file_path: Path, output_dir: Path, *, reload: bool = False, dev: bool = False) -> None:
    if not reload and not dev:
        prepare(output_dir)
    try:
        sections = exec_file(exec_file_path)
    except ExecException as exc:
        if reload:
            content = render_exception(exc, reload=reload, dev=dev)
        else:
            raise
    else:
        content = render(sections, reload=reload, dev=dev)
    (output_dir / 'index.html').write_text(content)


def prepare(output_dir: Path) -> None:
    if output_dir.exists():
        assert output_dir.is_dir(), output_dir
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
