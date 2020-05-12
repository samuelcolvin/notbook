import os
from pathlib import Path
from time import time

import typer

from . import main
from .render_tools import ExecException
from .version import VERSION
from .watch import watch as _watch

cli = typer.Typer()
file_default = typer.Argument(..., exists=True, file_okay=True, dir_okay=True, readable=True)
dev_mode = 'NOTBOOK_DEV' in os.environ


@cli.command()
def build(
    file: Path = file_default,
    output_dir: Path = typer.Argument(Path('site'), file_okay=False, dir_okay=True, readable=True),
):
    print(f'executing {file} and saving output to {output_dir}...')
    start = time()
    try:
        main.build(file, output_dir, dev=dev_mode)
    except ExecException as exc:
        print(exc.format('shell'))
        print(f'build failed after {time() - start:0.3f}s')
        raise typer.Exit(1)
    else:
        print(f'build completed in {time() - start:0.3f}s')


@cli.command()
def watch(
    file: Path = file_default,
    output_dir: Path = typer.Argument(Path('.live'), file_okay=False, dir_okay=True, readable=True),
):
    _watch(file, output_dir, dev=dev_mode)


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
