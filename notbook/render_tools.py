import re
import traceback
from typing import Literal

from markupsafe import Markup
from misaka import HtmlRenderer, Markdown, escape_html
from pygments import highlight as pyg_highlight
from pygments.formatters import HtmlFormatter, Terminal256Formatter
from pygments.lexers import Python3TracebackLexer, get_lexer_by_name
from pygments.util import ClassNotFound

__all__ = 'render_markdown', 'code_block', 'highlight_code', 'slugify', 'ExecException'

MD_EXTENSIONS = 'fenced-code', 'strikethrough', 'no-intra-emphasis', 'tables'
DL_REGEX = re.compile('<li>(.*?)::(.*?)</li>', re.S)
LI_REGEX = re.compile('<li>(.*?)</li>', re.S)
tb_lexer = Python3TracebackLexer()
shell_formatter = Terminal256Formatter(style='vim')
html_formatter = HtmlFormatter(nowrap=True)


class CustomHtmlRenderer(HtmlRenderer):
    @staticmethod
    def blockcode(text, lang) -> str:
        if lang.lower() in {'math', 'maths', 'eq', 'equation'}:
            return f'<p class="equation d-none">{escape_html(text)}</p>'
        else:
            return code_block(lang, text)

    @staticmethod
    def list(content, is_ordered, is_block):
        if not is_ordered and len(DL_REGEX.findall(content)) == len(LI_REGEX.findall(content)):
            return '<dl>\n' + DL_REGEX.sub(r'  <dt>\1</dt><dd>\2</dd>', content) + '</dl>'
        elif is_ordered:
            return f'<ol>\n{content}</ol>'
        else:
            return f'<ul>\n{content}</ul>'

    @staticmethod
    def header(content, level):
        return f'<h{level} id="{level}-{slugify(content, path_like=False)}">{content}</h{level}>\n'

    @staticmethod
    def triple_emphasis(content):
        return f'<u>{content}</u>'


md_to_html = Markdown(CustomHtmlRenderer(), extensions=MD_EXTENSIONS)


def render_markdown(md: str) -> str:
    return md_to_html(md)


def code_block(lang: str, code: str) -> str:
    return f'<div><pre class="code-block">{highlight_code(lang, code)}</pre></div>'


def highlight_code(format: str, code: str) -> Markup:
    try:
        lexer = get_lexer_by_name(format, stripall=True)
    except ClassNotFound:
        lexer = None

    if lexer:
        h = pyg_highlight(code, lexer=lexer, formatter=html_formatter).strip('\n')
        return Markup(f'<span class="highlight">{h}</span>')
    else:
        return Markup(f'<span class="raw">{escape_html(code)}</span>')


RE_URI_NOT_ALLOWED = re.compile(r'[^a-zA-Z0-9_\-/.]')
RE_HTML_SYMBOL = re.compile(r'&(?:#\d{2,}|[a-z0-9]{2,});')
RE_TITLE_NOT_ALLOWED = re.compile(r'[^a-z0-9_\-]')
RE_REPEAT_DASH = re.compile(r'-{2,}')


def slugify(v, *, path_like=True):
    v = v.replace(' ', '-').lower()
    if path_like:
        v = RE_URI_NOT_ALLOWED.sub('', v)
    else:
        v = RE_HTML_SYMBOL.sub('', v)
        v = RE_TITLE_NOT_ALLOWED.sub('', v)
    return RE_REPEAT_DASH.sub('-', v).strip('_-')


class ExecException(Exception):
    def __init__(self, exc_info):
        self.exc_info = exc_info

    def format(self, format: Literal['html', 'shell']) -> str:
        stack = traceback.format_exception(*self.exc_info)
        # remove the fist element in the trace which refers to this file
        # (element 0 is the standard "Traceback (most recent call last):" message, hence removing element 1)
        stack.pop(1)
        tb = ''.join(stack)
        if format == 'html':
            h = pyg_highlight(tb, lexer=tb_lexer, formatter=html_formatter).rstrip('\n')
            return Markup(f'<span class="highlight">{h}</span>')
        else:
            return pyg_highlight(tb, lexer=tb_lexer, formatter=shell_formatter).rstrip('\n')
