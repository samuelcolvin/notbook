import re
from pathlib import Path
from typing import Dict, Generator, List

from jinja2 import Environment, PackageLoader

from .models import CodeBlock, PlotBlock, PrintBlock, PrintStatement, Section, TextBlock
from .render_tools import highlight_code, render_markdown

THIS_DIR = Path(__file__).parent.resolve()

css_url = (
    'https://gistcdn.githack.com/samuelcolvin/647671890d647695930ff74f1ca5bfc2/raw/'
    '3143aa748b26483e44be32c93da4e08c23292583/notbook.css'
)
reload_js_url = 'https://rawcdn.githack.com/samuelcolvin/foxglove/fbc87301a2470263e3ba45e56c7089f286a84a4e/reload.js'


def render(sections: List[Section]) -> Dict[Path, str]:
    env = Environment(loader=PackageLoader('notbook'), autoescape=True)
    env.globals.update(highlight=highlight_code, css_url=css_url, reload_js_url=reload_js_url)
    env.filters.update(is_simple=is_simple)
    template = env.get_template('main.jinja')
    return {
        Path('index.html'): template.render(
            sections=render_sections(sections),
            bokeh_plot=any(isinstance(s.block, PlotBlock) and s.block.format == 'bokeh' for s in sections),
            title='Notbook',
        )
    }


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
