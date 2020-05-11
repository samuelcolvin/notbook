from pathlib import Path
from time import time

import typer

from . import main
from .version import VERSION
from .watch import watch as _watch

cli = typer.Typer()
file_default = typer.Argument(..., exists=True, file_okay=True, dir_okay=True, readable=True)


@cli.command()
def build(
    file: Path = file_default,
    output_dir: Path = typer.Argument(Path('site'), file_okay=False, dir_okay=True, readable=True),
):
    print(f'executing {file} and saving output to {output_dir}...')
    start = time()
    main.prepare(output_dir)
    main.build(file, output_dir)
    print(f'build completed in {time() - start:0.3f}s')


@cli.command()
def watch(
    file: Path = file_default,
    output_dir: Path = typer.Argument(Path('.live'), file_okay=False, dir_okay=True, readable=True),
):
    _watch(file, output_dir)


def version_callback(value: bool):
    if value:
        print(f'notbook: v{VERSION}')
        raise typer.Exit()


@cli.callback(help=f'notbook command line interface v{VERSION}')
def callback(
    version: bool = typer.Option(
        None, '--version', callback=version_callback, is_eager=True, help='Show the version and exit.'
    ),
) -> None:
    pass


if __name__ == '__main__':
    cli()
