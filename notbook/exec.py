import inspect
import json
import os
import re
import sys
from io import BufferedWriter
from operator import attrgetter
from pathlib import Path
from typing import Any, List, Optional, Union

from devtools import PrettyFormat

from . import context
from .models import CodeBlock, PlotBlock, PrintArg, PrintBlock, PrintStatement, Section, TextBlock
from .render_tools import ExecException

__all__ = ('exec_file',)

MAX_LINE_LENGTH = 120
LONG_LINE = 50
pformat = PrettyFormat(simple_cutoff=LONG_LINE)


def exec_file(file: Path) -> List[Section]:
    file_text = file.read_text('utf-8')

    context.activate()
    os.environ['NOTBOOK'] = '1'
    mp = MockPrint(file)
    exec_globals = dict(print=mp)
    code = compile(file_text, str(file), 'exec')
    try:
        exec(code, exec_globals)
    except Exception:
        raise ExecException(sys.exc_info())

    lines: List[Union[str, PrintStatement, PlotBlock]] = file_text.split('\n')

    extra = sorted(mp.statements + context.get(), key=attrgetter('line_no'), reverse=True)

    for p in extra:
        if isinstance(p, PrintStatement):
            for back in range(1, 100):
                m = re.search(r'^( *)print\(', lines[p.line_no - back])
                if m:
                    p.indent = len(m.group(1))
                    break
            lines.insert(p.line_no, p)
        else:
            assert isinstance(p, PlotBlock), p
            lines.insert(p.line_no, p)

    return MakeSections(lines).sections


def simplify(obj):
    from dataclasses import is_dataclass, fields

    if is_dataclass(obj):
        return {'*type': obj.__class__.__name__, **{f.name: simplify(getattr(obj, f.name)) for f in fields(obj)}}
    elif isinstance(obj, list):
        return [simplify(v) for v in obj]
    else:
        return obj


class MakeSections:
    def __init__(self, lines: List[Union[str, PrintStatement, PlotBlock]]):
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
                elif isinstance(line, PrintStatement):
                    self.print_statement(line)
                else:
                    self.plot_block(line)
        except StopIteration:
            pass
        self.maybe_add_current_code()

    def section_divide(self, line: str) -> bool:
        start = re.match(r' *# *{ *(.*)', line)
        if start:
            self.maybe_add_current_code()
            self.current_code = CodeBlock([])
            self.current_name = start.group(1) or None
            return True
        end = re.match(r' *# *} *(.*)', line)
        if end:
            self.maybe_add_current_code(end.group(1) or None)
            return True

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
            was_in_section = bool(self.current_code)
            self.maybe_add_current_code()
            self.sections.append(Section(TextBlock('\n'.join(lines), renderer)))
            if was_in_section:
                self.current_code = CodeBlock([])
        elif self.current_code:
            self.current_code.lines.extend(lines)
        else:
            # no render and not in a code block, do nothing
            pass
        return True

    def print_statement(self, print_statement: PrintStatement):
        if self.current_code:
            if self.current_code.lines and isinstance(self.current_code.lines[-1], PrintBlock):
                self.current_code.lines[-1].statements.append(print_statement)
            else:
                self.current_code.lines.append(PrintBlock([print_statement]))
        else:
            if self.sections and isinstance(self.sections[-1].block, PrintBlock):
                self.sections[-1].block.statements.append(print_statement)
            else:
                self.sections.append(Section(PrintBlock([print_statement])))

    def plot_block(self, plot: PlotBlock):
        assert isinstance(plot, PlotBlock), plot
        if self.current_code:
            raise NotImplementedError('TODO')
        else:
            self.sections.append(Section(plot))

    def maybe_add_current_code(self, caption: str = None):
        if self.current_code:
            self.sections.append(Section(self.current_code, self.current_name, caption))
            self.current_code = None
            self.current_name = None


default = object()


class MockPrint:
    def __init__(self, file: Path):
        self.file = file
        self.statements: List[PrintStatement] = []

    def __call__(self, *args, file: Optional[BufferedWriter] = default, flush=None):
        if file is not default:
            print(*args, file=file, flush=flush)
            return
        frame = inspect.currentframe()
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
    if not isinstance(value, (str, int, float)):
        return PrintArg(pformat(value), 'py')
    elif (
        isinstance(value, str)
        and len(value) > 10
        and any(re.fullmatch(r, value, flags=re.DOTALL) for r in [r'{".+}', r'\[.+\]'])
    ):
        try:
            obj = json.loads(value)
        except ValueError:
            # not JSON, not a problem
            pass
        else:
            return PrintArg(json.dumps(obj, indent=2), 'json')

    return PrintArg(str(value), 'str')
