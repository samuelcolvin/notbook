import inspect
import json
import os
import re
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Literal, Union, Tuple
from unittest.mock import patch

from devtools import PrettyFormat

__all__ = ('exec_file',)

MAX_LINE_LENGTH = 120
LONG_LINE = 50
pformat = PrettyFormat(simple_cutoff=LONG_LINE)


def exec_file(file: Path):
    os.environ['NOTBOOK'] = '1'
    # sys.path.append(str(EXAMPLES_DIR))

    file_text = file.read_text('utf-8')

    code = compile(file.read_text(), file.name, 'exec')

    mp = MockPrint(file)
    with patch('builtins.print') as mock_print:
        mock_print.side_effect = mp
        try:
            exec(code)
        except Exception:
            raise
            # tb = traceback.format_exception(*sys.exc_info())

    lines = file_text.split('\n')

    for p in reversed(mp.statements):
        indent = 0
        for back in range(1, 100):
            m = re.search(r'^( *)print\(', lines[p.line_no - back])
            if m:
                indent = len(m.group(1))
                break
        lines.insert(p.line_no, p)

    sections = MakeSections(lines).sections
    debug(simplify(sections))


def simplify(obj):
    from dataclasses import is_dataclass, asdict
    if isinstance(obj, list):
        return [simplify(v) for v in obj]
    elif is_dataclass(obj):
        return {
            'type': obj.__class__.__name__,
            'values': {k: simplify(v) for k, v in asdict(obj).items()}
        }
    else:
        return obj


@dataclass
class PrintArg:
    content: str
    format: Literal['py', 'json', 'str']


@dataclass
class PrintStatement:
    args: List[PrintArg]
    line_no: int


@dataclass
class PrintBlock:
    statements: List[PrintStatement]


@dataclass
class TextBlock:
    content: str
    format: Literal['md', 'html']


@dataclass
class CodeBlock:
    lines: List[Union[str, PrintBlock]]
    format: Literal['py'] = 'py'


@dataclass
class Section:
    blocks: Union[PrintBlock, TextBlock, CodeBlock]
    title: Optional[str] = None
    caption: Optional[str] = None


class MakeSections:
    def __init__(self, lines: List[str]):
        self.iter = iter(lines)
        self.sections: List[Section] = []
        self.current_name: Optional[str] = None
        self.current_code: Optional[CodeBlock] = None
        try:
            while True:
                line = next(self.iter)
                if isinstance(line, str):
                    if self.section_divide(line):
                        continue
                    if self.triple_quote(line):
                        continue

                    if self.current_code:
                        self.current_code.lines.append(line)
                else:
                    self.print_statement(line)
        except StopIteration:
            pass
        self.maybe_add_current_code()

    def section_divide(self, line: str) -> bool:
        start = re.match(r' *# *{ *section *(.*)', line)
        if start:
            self.maybe_add_current_code()
            self.current_code = CodeBlock([])
            self.current_name = start.group(1) or None
            return True
        elif re.match(r' *# *\}', line):
            self.maybe_add_current_code()
            return True
        else:
            return False

    def triple_quote(self, first_line: str) -> bool:
        start = re.match(' *("""|\'\'\')(.*)', first_line)
        if not start:
            return False
        quotes, start_line = start.groups()
        renderer = None
        m_renderer = re.match(r'(md|html)\w*(.*)', start_line)
        if m_renderer:
            renderer, start_line = m_renderer.groups()
            if start_line:
                lines = [start_line]
            else:
                lines = []
        else:
            lines = [first_line]
        while True:
            line = next(self.iter)
            end = re.match(f'(.*){quotes}', line)
            if end:
                if renderer:
                    lines.append(end.group(1))
                else:
                    lines.append(line)
                break
            lines.append(line)

        if renderer:
            self.maybe_add_current_code()
            self.sections.append(Section(TextBlock('\n'.join(lines), renderer)))
        elif self.current_code:
            self.current_code.lines.extend(lines)
        else:
            # no render and not in a code block, do nothing
            pass
        return True

    def print_statement(self, line: PrintStatement):
        assert isinstance(line, PrintStatement), line
        if self.current_code:
            if self.current_code.lines and isinstance(self.current_code.lines[-1], PrintBlock):
                self.current_code.lines[-1].statements.append(line)
            else:
                self.current_code.lines.append(PrintBlock([line]))
        else:
            self.sections.append(Section(PrintBlock([line])))

    def maybe_add_current_code(self):
        if self.current_code:
            self.sections.append(Section(self.current_code, self.current_name))
            self.current_code = None
            self.current_name = None


class MockPrint:
    def __init__(self, file: Path):
        self.file = file
        self.statements: List[PrintStatement] = []

    def __call__(self, *args, file=None, flush=None):
        frame = inspect.currentframe().f_back.f_back.f_back
        if sys.version_info >= (3, 8):
            frame = frame.f_back
        if not self.file.samefile(frame.f_code.co_filename):
            raise RuntimeError('in another file, todo')

        args = [parse_print_value(arg) for arg in args]
        self.statements.append(PrintStatement(args, frame.f_lineno))


def parse_print_value(value: Any) -> PrintArg:
    """
    process objects passed to print and try to make them pretty
    """
    # attempt to build a pretty equivalent of the print output
    if isinstance(value, (dict, list, tuple, set)):
        return PrintArg(pformat(value), 'py')
    elif (
        isinstance(value, str) and len(value) > 10 and
        any(re.fullmatch(r, value, flags=re.DOTALL) for r in [r'{".+}', r'\[.+\]'])
    ):
        try:
            obj = json.loads(value)
        except ValueError:
            # not JSON, not a problem
            pass
        else:
            return PrintArg(json.dumps(obj, indent=2), 'json')

    return PrintArg(str(value), 'str')
