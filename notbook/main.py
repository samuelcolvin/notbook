from pathlib import Path

from .exec import exec_file
from .render import render

__all__ = ('build',)


def build(file: Path, output: Path) -> None:
    sections = exec_file(file)
    html = render(sections)
    output.write_text(html)
