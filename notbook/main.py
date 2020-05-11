import shutil
from pathlib import Path

from .exec import exec_file
from .render import render

__all__ = 'build', 'prepare'


def build(exec_file_path: Path, output_dir: Path) -> None:
    sections = exec_file(exec_file_path)
    for path, content in render(sections).items():
        (output_dir / path).write_text(content)


def prepare(output_dir: Path) -> None:
    if output_dir.exists():
        assert output_dir.is_dir(), output_dir
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)


