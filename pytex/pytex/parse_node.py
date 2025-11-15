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

# Placeholder for symbols data
try:
    from .symbols_data import NON_ATOMS
except ImportError:
    NON_ATOMS = set()

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
    type: str  # "array"
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
    type: str  # "cdlabel"
    side: str
    label: AnyParseNode


class CdlabelparentParseNode(BaseParseNode):
    type: str  # "cdlabelparent"
    fragment: AnyParseNode


class ColorParseNode(BaseParseNode):
    type: str  # "color"
    color: str
    body: List[AnyParseNode]


class ColorTokenParseNode(BaseParseNode):
    type: str  # "color-token"
    color: str


class OpParseNode(BaseParseNode):
    type: str  # "op"
    limits: bool
    alwaysHandleSupSub: Optional[bool]
    suppressBaseShift: Optional[bool]
    parentIsSupSub: bool
    symbol: bool
    name: Optional[str]
    body: Optional[List[AnyParseNode]]


class OrdgroupParseNode(BaseParseNode):
    type: str  # "ordgroup"
    body: List[AnyParseNode]
    semisimple: Optional[bool]


class RawParseNode(BaseParseNode):
    type: str  # "raw"
    string: str


class SizeParseNode(BaseParseNode):
    type: str  # "size"
    value: Measurement
    isBlank: bool


class StylingParseNode(BaseParseNode):
    type: str  # "styling"
    style: StyleStr
    body: List[AnyParseNode]


class SupsubParseNode(BaseParseNode):
    type: str  # "supsub"
    base: Optional[AnyParseNode]
    sup: Optional[AnyParseNode]
    sub: Optional[AnyParseNode]


class TagParseNode(BaseParseNode):
    type: str  # "tag"
    body: List[AnyParseNode]
    tag: List[AnyParseNode]


class TextParseNode(BaseParseNode):
    type: str  # "text"
    body: List[AnyParseNode]
    font: Optional[str]


class UrlParseNode(BaseParseNode):
    type: str  # "url"
    url: str


class VerbParseNode(BaseParseNode):
    type: str  # "verb"
    body: str
    star: bool


# Symbol group nodes
class AtomParseNode(BaseParseNode):
    type: str  # "atom"
    family: Atom
    text: str


class MathordParseNode(BaseParseNode):
    type: str  # "mathord"
    text: str


class SpacingParseNode(BaseParseNode):
    type: str  # "spacing"
    text: str


class TextordParseNode(BaseParseNode):
    type: str  # "textord"
    text: str


class AccentTokenParseNode(BaseParseNode):
    type: str  # "accent-token"
    text: str


class OpTokenParseNode(BaseParseNode):
    type: str  # "op-token"
    text: str


# Function/command nodes
class AccentParseNode(BaseParseNode):
    type: str  # "accent"
    label: str
    isStretchy: Optional[bool]
    isShifty: Optional[bool]
    base: AnyParseNode


class AccentUnderParseNode(BaseParseNode):
    type: str  # "accentUnder"
    label: str
    isStretchy: Optional[bool]
    isShifty: Optional[bool]
    base: AnyParseNode


class CrParseNode(BaseParseNode):
    type: str  # "cr"
    newLine: bool
    size: Optional[Measurement]


class DelimsizingParseNode(BaseParseNode):
    type: str  # "delimsizing"
    size: int  # 1, 2, 3, or 4
    mclass: str  # "mopen" | "mclose" | "mrel" | "mord"
    delim: str


class EncloseParseNode(BaseParseNode):
    type: str  # "enclose"
    label: str
    backgroundColor: Optional[str]
    borderColor: Optional[str]
    body: AnyParseNode


class EnvironmentParseNode(BaseParseNode):
    type: str  # "environment"
    name: str
    nameGroup: AnyParseNode


class FontParseNode(BaseParseNode):
    type: str  # "font"
    font: str
    body: AnyParseNode


class GenfracParseNode(BaseParseNode):
    type: str  # "genfrac"
    continued: bool
    numer: AnyParseNode
    denom: AnyParseNode
    hasBarLine: bool
    leftDelim: Optional[str]
    rightDelim: Optional[str]
    size: Union[StyleStr, str]  # StyleStr | "auto"
    barSize: Optional[Measurement]


class HboxParseNode(BaseParseNode):
    type: str  # "hbox"
    body: List[AnyParseNode]


class HorizBraceParseNode(BaseParseNode):
    type: str  # "horizBrace"
    label: str
    isOver: bool
    base: AnyParseNode


class HrefParseNode(BaseParseNode):
    type: str  # "href"
    href: str
    body: List[AnyParseNode]


class HtmlParseNode(BaseParseNode):
    type: str  # "html"
    attributes: Dict[str, str]
    body: List[AnyParseNode]


class HtmlmathmlParseNode(BaseParseNode):
    type: str  # "htmlmathml"
    html: List[AnyParseNode]
    mathml: List[AnyParseNode]


class IncludegraphicsParseNode(BaseParseNode):
    type: str  # "includegraphics"
    alt: str
    width: Measurement
    height: Measurement
    totalheight: Measurement
    src: str


class InfixParseNode(BaseParseNode):
    type: str  # "infix"
    replaceWith: str
    size: Optional[Measurement]
    token: Optional[Token]


class InternalParseNode(BaseParseNode):
    type: str  # "internal"


class KernParseNode(BaseParseNode):
    type: str  # "kern"
    dimension: Measurement


class LapParseNode(BaseParseNode):
    type: str  # "lap"
    alignment: str
    body: AnyParseNode


class LeftrightParseNode(BaseParseNode):
    type: str  # "leftright"
    body: List[AnyParseNode]
    left: str
    right: str
    rightColor: Optional[str]


class LeftrightRightParseNode(BaseParseNode):
    type: str  # "leftright-right"
    delim: str
    color: Optional[str]


class MathchoiceParseNode(BaseParseNode):
    type: str  # "mathchoice"
    display: List[AnyParseNode]
    text: List[AnyParseNode]
    script: List[AnyParseNode]
    scriptscript: List[AnyParseNode]


class MiddleParseNode(BaseParseNode):
    type: str  # "middle"
    delim: str


class MclassParseNode(BaseParseNode):
    type: str  # "mclass"
    mclass: str
    body: List[AnyParseNode]
    isCharacterBox: bool


class OperatornameParseNode(BaseParseNode):
    type: str  # "operatorname"
    body: List[AnyParseNode]
    alwaysHandleSupSub: bool
    limits: bool
    parentIsSupSub: bool


class OverlineParseNode(BaseParseNode):
    type: str  # "overline"
    body: AnyParseNode


class PhantomParseNode(BaseParseNode):
    type: str  # "phantom"
    body: List[AnyParseNode]


class HphantomParseNode(BaseParseNode):
    type: str  # "hphantom"
    body: AnyParseNode


class VphantomParseNode(BaseParseNode):
    type: str  # "vphantom"
    body: AnyParseNode


class PmbParseNode(BaseParseNode):
    type: str  # "pmb"
    mclass: str
    body: List[AnyParseNode]


class RaiseboxParseNode(BaseParseNode):
    type: str  # "raisebox"
    dy: Measurement
    body: AnyParseNode


class RuleParseNode(BaseParseNode):
    type: str  # "rule"
    shift: Optional[Measurement]
    width: Measurement
    height: Measurement


class SizingParseNode(BaseParseNode):
    type: str  # "sizing"
    size: int
    body: List[AnyParseNode]


class SmashParseNode(BaseParseNode):
    type: str  # "smash"
    body: AnyParseNode
    smashHeight: bool
    smashDepth: bool


class SqrtParseNode(BaseParseNode):
    type: str  # "sqrt"
    body: AnyParseNode
    index: Optional[AnyParseNode]


class UnderlineParseNode(BaseParseNode):
    type: str  # "underline"
    body: AnyParseNode


class VcenterParseNode(BaseParseNode):
    type: str  # "vcenter"
    body: AnyParseNode


class XArrowParseNode(BaseParseNode):
    type: str  # "xArrow"
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
    "SymbolParseNode",
    "UnsupportedCmdParseNode",
    "assert_node_type",
    "assert_symbol_node_type",
    "check_symbol_node_type",
    # All the node types are exported implicitly through the type system
]
