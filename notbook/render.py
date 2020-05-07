import re
from pathlib import Path
from typing import List, Dict, Generator
from jinja2 import Environment, PackageLoader

from .models import PrintBlock, TextBlock, CodeBlock, Section, PrintStatement, PlotBlock
from .render_tools import render_markdown, highlight_code

THIS_DIR = Path(__file__).parent.resolve()


def render(sections: List[Section]) -> Dict[Path, str]:
    env = Environment(loader=PackageLoader('notbook'), autoescape=True)
    env.globals.update(
        highlight=highlight_code,
    )
    env.filters.update(
        is_simple=is_simple
    )
    template = env.get_template('main.jinja')
    return {
        Path('index.html'): template.render(
            sections=render_sections(sections),
            bokeh_plot=any(isinstance(s.block, PlotBlock) and s.block.format == 'bokeh' for s in sections)
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
