import re
from pathlib import Path
from typing import List, Dict, Generator
from jinja2 import Environment, select_autoescape, PackageLoader

from .models import PrintArg, PrintStatement, PrintBlock, TextBlock, CodeBlock, Section
from .render_tools import render_markdown, highlight_code

THIS_DIR = Path(__file__).parent.resolve()


def render(sections: List[Section]) -> Dict[Path, str]:
    env = Environment(loader=PackageLoader('notbook'), autoescape=select_autoescape(['html', 'xml']))
    template = env.get_template('main.jinja')
    return {
        Path('index.html'): template.render(
            sections=render_sections(sections),
        )
    }


def render_sections(sections: List[Section]) -> Generator[Dict[str, str], None, None]:
    for section in sections:
        b = section.block
        chunks = []
        if section.title:
            chunks.append(f'<h1>{section.title}</h1>')
        if isinstance(b, TextBlock):
            if b.format == 'html':
                chunks.append(b.content)
            else:
                chunks.append(render_markdown(b.content))
        elif isinstance(b, CodeBlock):
            code = []
            for line in b.lines:
                if isinstance(line, str):
                    code.append(line)
                else:
                    assert isinstance(line, PrintBlock), line
                    if code:
                        chunks.append(highlight_code(b.format, '\n'.join(code)))
                        code = []
                    chunks.append(render_print(line))

            if code:
                chunks.append(highlight_code(b.format, '\n'.join(code)))
        else:
            assert isinstance(b, PrintBlock), b
            chunks.append(render_print(b))
        yield dict(
            name=re.sub(r'(?<!^)(?=[A-Z])', '-', b.__class__.__name__).lower(),
            chunks=chunks
        )


def render_print(p: PrintBlock) -> str:
    html = '\n'.join(map(render_print_statement, p.statements))
    return f'<div class="print-block">{html}</div>'


def render_print_statement(s: PrintStatement):
    # TODO indent
    return f'<code>{" ".join(map(render_print_arg, s.args))}</code>'


def render_print_arg(a: PrintArg) -> str:
    return highlight_code(a.format, a.content)
