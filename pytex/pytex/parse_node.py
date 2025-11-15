"""Python port of KaTeX's parseNode.js - AST node type definitions."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from typing_extensions import TypedDict

from .source_location import SourceLocation
from .token import Token
from .types import Mode, StyleStr
from .units import Measurement

# Forward references for recursive types
AnyParseNode = Union[
    'ArrayParseNode',
    'CdlabelParseNode',
    'CdlabelparentParseNode',
    'ColorParseNode',
    'ColorTokenParseNode',
    'OpParseNode',
    'OrdgroupParseNode',
    'RawParseNode',
    'SizeParseNode',
    'StylingParseNode',
    'SupsubParseNode',
    'TagParseNode',
    'TextParseNode',
    'UrlParseNode',
    'VerbParseNode',
    'AtomParseNode',
    'MathordParseNode',
    'SpacingParseNode',
    'TextordParseNode',
    'AccentTokenParseNode',
    'OpTokenParseNode',
    'AccentParseNode',
    'AccentUnderParseNode',
    'CrParseNode',
    'DelimsizingParseNode',
    'EncloseParseNode',
    'EnvironmentParseNode',
    'FontParseNode',
    'GenfracParseNode',
    'HboxParseNode',
    'HorizBraceParseNode',
    'HrefParseNode',
    'HtmlParseNode',
    'HtmlmathmlParseNode',
    'IncludegraphicsParseNode',
    'InfixParseNode',
    'InternalParseNode',
    'KernParseNode',
    'LapParseNode',
    'LeftrightParseNode',
    'LeftrightRightParseNode',
    'MathchoiceParseNode',
    'MiddleParseNode',
    'MclassParseNode',
    'OperatornameParseNode',
    'OverlineParseNode',
    'PhantomParseNode',
    'HphantomParseNode',
    'VphantomParseNode',
    'PmbParseNode',
    'RaiseboxParseNode',
    'RuleParseNode',
    'SizingParseNode',
    'SmashParseNode',
    'SqrtParseNode',
    'UnderlineParseNode',
    'VcenterParseNode',
    'XArrowParseNode',
]

# Compatibility alias matching KaTeX's ParseNode name
ParseNode = AnyParseNode

# Placeholder for symbols data
try:
    from .symbols_data import NON_ATOMS
except ImportError:
    NON_ATOMS = {}

# Placeholder for environment types
AlignSpec = Any
ColSeparationType = Any
Atom = str


# Base parse node structure
class BaseParseNode(TypedDict):
    type: str
    mode: Mode
    loc: Optional[SourceLocation]


# Complex node types
class ArrayParseNode(BaseParseNode):

    colSeparationType: Optional[ColSeparationType]
    hskipBeforeAndAfter: Optional[bool]
    addJot: Optional[bool]
    cols: Optional[List[AlignSpec]]
    arraystretch: float
    body: List[List[AnyParseNode]]  # 2D array
    rowGaps: List[Optional[Measurement]]
    hLinesBeforeRow: List[List[bool]]
    tags: Optional[List[Union[bool, List[AnyParseNode]]]]
    leqno: Optional[bool]
    isCD: Optional[bool]


class CdlabelParseNode(BaseParseNode):

    side: str
    label: AnyParseNode


class CdlabelparentParseNode(BaseParseNode):

    fragment: AnyParseNode


class ColorParseNode(BaseParseNode):

    color: str
    body: List[AnyParseNode]


class ColorTokenParseNode(BaseParseNode):

    color: str


class OpParseNode(BaseParseNode):

    limits: bool
    alwaysHandleSupSub: Optional[bool]
    suppressBaseShift: Optional[bool]
    parentIsSupSub: bool
    symbol: bool
    name: Optional[str]
    body: Optional[List[AnyParseNode]]


class OrdgroupParseNode(BaseParseNode):

    body: List[AnyParseNode]
    semisimple: Optional[bool]


class RawParseNode(BaseParseNode):

    string: str


class SizeParseNode(BaseParseNode):

    value: Measurement
    isBlank: bool


class StylingParseNode(BaseParseNode):

    style: StyleStr
    body: List[AnyParseNode]


class SupsubParseNode(BaseParseNode):

    base: Optional[AnyParseNode]
    sup: Optional[AnyParseNode]
    sub: Optional[AnyParseNode]


class TagParseNode(BaseParseNode):

    body: List[AnyParseNode]
    tag: List[AnyParseNode]


class TextParseNode(BaseParseNode):

    body: List[AnyParseNode]
    font: Optional[str]


class UrlParseNode(BaseParseNode):

    url: str


class VerbParseNode(BaseParseNode):

    body: str
    star: bool


# Specialized nodes -------------------------------------------------


class AtomParseNode(BaseParseNode):

    family: Atom
    text: str


class MathordParseNode(BaseParseNode):

    text: str


class SpacingParseNode(BaseParseNode):

    text: str


class TextordParseNode(BaseParseNode):

    text: str


class AccentTokenParseNode(BaseParseNode):

    text: str


class OpTokenParseNode(BaseParseNode):

    text: str


# Function/command nodes
class AccentParseNode(BaseParseNode):

    label: str
    isStretchy: Optional[bool]
    isShifty: Optional[bool]
    base: AnyParseNode


class AccentUnderParseNode(BaseParseNode):

    label: str
    isStretchy: Optional[bool]
    isShifty: Optional[bool]
    base: AnyParseNode


class CrParseNode(BaseParseNode):

    newLine: bool
    size: Optional[Measurement]


class DelimsizingParseNode(BaseParseNode):

    size: int  # 1, 2, 3, or 4
    mclass: str  # "mopen" | "mclose" | "mrel" | "mord"
    delim: str


class EncloseParseNode(BaseParseNode):

    label: str
    backgroundColor: Optional[str]
    borderColor: Optional[str]
    body: AnyParseNode


class EnvironmentParseNode(BaseParseNode):

    name: str
    nameGroup: AnyParseNode


class FontParseNode(BaseParseNode):

    font: str
    body: List[AnyParseNode]


class GenfracParseNode(BaseParseNode):

    continued: bool
    numer: AnyParseNode
    denom: AnyParseNode
    hasBarLine: bool
    leftDelim: Optional[str]
    rightDelim: Optional[str]
    size: str
    barSize: Optional[Dict[str, Any]]


class HboxParseNode(BaseParseNode):

    body: List[AnyParseNode]


class HorizBraceParseNode(BaseParseNode):

    label: str
    isOver: bool
    base: AnyParseNode


class HrefParseNode(BaseParseNode):

    href: str
    body: List[AnyParseNode]


class HtmlParseNode(BaseParseNode):

    attributes: Dict[str, str]
    body: List[AnyParseNode]


class HtmlmathmlParseNode(BaseParseNode):

    html: List[AnyParseNode]
    mathml: List[AnyParseNode]


class IncludegraphicsParseNode(BaseParseNode):

    alt: str
    width: Measurement
    height: Measurement
    totalheight: Measurement
    src: str


class InfixParseNode(BaseParseNode):

    replaceWith: str
    size: Optional[Measurement]
    token: Optional[Token]


class InternalParseNode(BaseParseNode):
    pass



class KernParseNode(BaseParseNode):

    dimension: Measurement


class LapParseNode(BaseParseNode):

    alignment: str
    body: AnyParseNode


class LeftrightParseNode(BaseParseNode):

    body: List[AnyParseNode]
    left: str
    right: str
    rightColor: Optional[str]


class LeftrightRightParseNode(BaseParseNode):

    delim: str
    color: Optional[str]


class MathchoiceParseNode(BaseParseNode):

    display: List[AnyParseNode]
    text: List[AnyParseNode]
    script: List[AnyParseNode]
    scriptscript: List[AnyParseNode]


class MiddleParseNode(BaseParseNode):

    delim: str


class MclassParseNode(BaseParseNode):

    mclass: str
    body: List[AnyParseNode]
    isCharacterBox: bool


class OperatornameParseNode(BaseParseNode):

    body: List[AnyParseNode]
    alwaysHandleSupSub: bool
    limits: bool
    parentIsSupSub: bool


class OverlineParseNode(BaseParseNode):

    body: AnyParseNode


class PhantomParseNode(BaseParseNode):

    body: List[AnyParseNode]


class HphantomParseNode(BaseParseNode):

    body: AnyParseNode


class VphantomParseNode(BaseParseNode):

    body: AnyParseNode


class PmbParseNode(BaseParseNode):

    mclass: str
    body: List[AnyParseNode]


class RaiseboxParseNode(BaseParseNode):

    dy: Measurement
    body: AnyParseNode


class RuleParseNode(BaseParseNode):

    shift: Optional[Measurement]
    width: Measurement
    height: Measurement


class SizingParseNode(BaseParseNode):

    size: int
    body: List[AnyParseNode]


class SmashParseNode(BaseParseNode):

    body: AnyParseNode
    smashHeight: bool
    smashDepth: bool


class SqrtParseNode(BaseParseNode):

    body: AnyParseNode
    index: Optional[AnyParseNode]


class UnderlineParseNode(BaseParseNode):

    body: AnyParseNode


class VcenterParseNode(BaseParseNode):

    body: AnyParseNode


class XArrowParseNode(BaseParseNode):

    label: str
    body: AnyParseNode
    below: Optional[AnyParseNode]


# Type unions
SymbolParseNode = Union[
    AtomParseNode,
    AccentTokenParseNode,
    MathordParseNode,
    OpTokenParseNode,
    SpacingParseNode,
    TextordParseNode,
]

UnsupportedCmdParseNode = ColorParseNode


def assert_node_type(node: Optional[AnyParseNode], expected_type: str) -> AnyParseNode:
    """Assert that a node is of the expected type."""
    if not node or node["type"] != expected_type:
        node_type = node["type"] if node else "None"
        raise ValueError(f"Expected node of type {expected_type}, but got node of type {node_type}")
    return node


def assert_symbol_node_type(node: Optional[AnyParseNode]) -> Optional[SymbolParseNode]:
    """Assert that a node is a symbol node type."""
    if not node:
        return None

    if node["type"] == "atom" or node["type"] in NON_ATOMS:
        return node  # type: ignore

    raise ValueError(f"Expected node of symbol group type, but got node of type {node['type']}")


def check_symbol_node_type(node: Optional[AnyParseNode]) -> Optional[SymbolParseNode]:
    """Check if a node is a symbol node type, returning None if not."""
    if not node:
        return None

    if node["type"] == "atom" or node["type"] in NON_ATOMS:
        return node  # type: ignore

    return None


__all__ = [
    "AnyParseNode",
    "ParseNode",
    "PmbParseNode",
    "SymbolParseNode",
    "UnsupportedCmdParseNode",
    "assert_node_type",
    "assert_symbol_node_type",
    "check_symbol_node_type",
    # All the node types are exported implicitly through the type system
]
