import re

from misaka import HtmlRenderer, Markdown, escape_html
from pygments import highlight as pyg_highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

__all__ = 'render_markdown', 'highlight_code', 'slugify'

MD_EXTENSIONS = 'fenced-code', 'strikethrough', 'no-intra-emphasis', 'tables'
DL_REGEX = re.compile('<li>(.*?)::(.*?)</li>', re.S)
LI_REGEX = re.compile('<li>(.*?)</li>', re.S)


class CustomHtmlRenderer(HtmlRenderer):
    @staticmethod
    def blockcode(text, lang):
        return highlight_code(lang, text)

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


def highlight_code(lang: str, code: str) -> str:
    try:
        lexer = get_lexer_by_name(lang, stripall=True)
    except ClassNotFound:
        lexer = None

    code = code.strip('\n')
    debug(code)
    if lexer:
        formatter = HtmlFormatter(cssclass='highlight')
        return pyg_highlight(code, lexer, formatter)
    else:
        return f'<div class="raw"><pre>{escape_html(code)}</pre></div>'


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
