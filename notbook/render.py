import re
from pathlib import Path
from typing import Dict, Generator, List

from jinja2 import Environment, PackageLoader

from .models import CodeBlock, PlotBlock, PrintBlock, PrintStatement, Section, TextBlock
from .render_tools import ExecException, highlight_code, render_markdown

THIS_DIR = Path(__file__).parent.resolve()
__all__ = 'render', 'render_exception'

assets_gist = (
    'https://gistcdn.githack.com/samuelcolvin/647671890d647695930ff74f1ca5bfc2/raw/'
    '9bdb8ecebe25293cad8332cbb2a79d844cdfd9a3'
)
github_icon_url = f'{assets_gist}/github.png'
css_url = f'{assets_gist}/notbook.css'
reload_js_url = f'{assets_gist}/reload.js'


def render(sections: List[Section], *, reload: bool = False, dev: bool = False) -> str:
    template = get_env(reload, dev).get_template('main.jinja')
    return template.render(
        sections=render_sections(sections),
        bokeh_plot=any(isinstance(s.block, PlotBlock) and s.block.format == 'bokeh' for s in sections),
    )


def render_exception(exc: ExecException, *, reload: bool = False, dev: bool = False) -> str:
    template = get_env(reload, dev).get_template('error.jinja')
    return template.render(exception=exc.format('html'))


def get_env(reload: bool, dev: bool) -> Environment:
    env = Environment(loader=PackageLoader('notbook'), autoescape=True)
    env.globals.update(
        highlight=highlight_code,
        title='Notbook',
        description='An experiment in displaying python scripts.',
        css_url='/assets/main.css' if dev else css_url,
        github_icon_url=github_icon_url,
        repo='samuelcolvin/notbook',
    )
    if reload:
        env.globals['reload_js_url'] = '/assets/reload.js' if dev else reload_js_url
    env.filters.update(is_simple=is_simple)
    return env


def render_sections(sections: List[Section]) -> Generator[Dict[str, str], None, None]:
    for section in sections:
        b = section.block
        d = dict(
            name=re.sub(r'(?<!^)(?=[A-Z])', '-', b.__class__.__name__.replace('Block', 'Section')).lower(),
            title=section.title,
            caption=section.caption,
        )
        if isinstance(b, TextBlock):
            d['html'] = b.content if b.format == 'html' else render_markdown(b.content)
        elif isinstance(b, CodeBlock):
            d['code'] = render_code(b)
        elif isinstance(b, PrintBlock):
            d['print_statements'] = b.statements
        else:
            assert isinstance(b, PlotBlock), b
            d['plot'] = b.html
        yield d


def render_code(c: CodeBlock):
    code = []
    for line in c.lines:
        if isinstance(line, str):
            code.append(line)
        else:
            assert isinstance(line, PrintBlock), line
            if code:
                yield {'format': 'py', 'content': '\n'.join(code)}
                code = []
            yield line.statements
    if code:
        yield {'format': 'py', 'content': '\n'.join(code)}


def is_simple(p: PrintStatement) -> bool:
    return all(a.format == 'str' for a in p.args)
