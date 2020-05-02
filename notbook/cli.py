from pathlib import Path

import typer

from .main import build

cli = typer.Typer()


@cli.command()
def main(file: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=True, readable=True)):
    build(file, Path('site'))


if __name__ == '__main__':
    cli()
