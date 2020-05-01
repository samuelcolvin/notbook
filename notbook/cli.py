from pathlib import Path

import typer

from .main import exec_file

cli = typer.Typer()


@cli.command()
def main(file: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=True, readable=True)):
    code = exec_file(file)
    print(code)


if __name__ == '__main__':
    cli()
