from dataclasses import dataclass
from typing import Literal, List, Union, Optional


@dataclass
class PrintArg:
    content: str
    format: Literal['py', 'json', 'str']


@dataclass
class PrintStatement:
    args: List[PrintArg]
    line_no: int
    indent: int = 0


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
    block: Union[TextBlock, CodeBlock, PrintBlock]
    title: Optional[str] = None
    caption: Optional[str] = None
