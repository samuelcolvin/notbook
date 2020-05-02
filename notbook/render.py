import re
from html import escape
from typing import List, Optional
from misaka import HtmlRenderer, Markdown, escape_html
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

from .models import PrintArg, PrintStatement, PrintBlock, TextBlock, CodeBlock, Section

md_renderer = HtmlRenderer()  # todo better, see harrier
MD_EXTENSIONS = 'fenced-code', 'strikethrough', 'no-intra-emphasis', 'tables'
md = Markdown(md_renderer, extensions=MD_EXTENSIONS)


def render(sections: List[Section]) -> str:
    html_sections = []
    for section in sections:
        b = section.block
        html = []
        if section.title:
            html.append(f'<h1>{section.title}</h1>')
        if isinstance(b, TextBlock):
            if b.format == 'html':
                html.append(b.content)
            else:
                html.append(md(b.content))
        elif isinstance(b, CodeBlock):
            code = []
            for line in b.lines:
                if isinstance(line, str):
                    code.append(line)
                else:
                    assert isinstance(line, PrintBlock), line
                    if code:
                        html.append(render_code(b.format, '\n'.join(code)))
                        code = []
                    html.append(render_print(line))

            if code:
                html.append(render_code(b.format, '\n'.join(code)))
        else:
            assert isinstance(b, PrintBlock), b
            html.append(render_print(b))
        css_cls_name = re.sub(r'(?<!^)(?=[A-Z])', '-', b.__class__.__name__).lower()
        html_sections.append('<div class="{}">{}</div>'.format(css_cls_name, '\n'.join(html)))

    return '\n'.join(f'<section>{s}</section>' for s in html_sections)


def render_print(p: PrintBlock) -> str:
    html = '\n'.join(map(render_print_statement, p.statements))
    return f'<div class="print-block">{html}</div>'


def render_print_statement(s: PrintStatement):
    # TODO indent
    return f'<code>{" ".join(map(render_print_arg, s.args))}</code>'


def render_print_arg(a: PrintArg) -> str:
    return render_code(a.format, a.content)


def render_code(lang: str, code: str) -> str:
    try:
        lexer = get_lexer_by_name(lang, stripall=True)
    except ClassNotFound:
        lexer = None

    if lexer:
        formatter = HtmlFormatter(cssclass='hi')
        return f'<div class="code-highlighted">{highlight(code, lexer, formatter)}</div>'
    else:
        return f'<code class="code-raw">{code}</code>'
