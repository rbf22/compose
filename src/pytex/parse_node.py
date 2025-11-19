"""Python port of KaTeX's parseNode.js - AST node type definitions."""

from __future__ import annotations

from typing import Any, Union

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
    from .symbols_data_generated import NON_ATOMS
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
    loc: SourceLocation | None


# Complex node types
class ArrayParseNode(BaseParseNode):

    colSeparationType: ColSeparationType | None
    hskipBeforeAndAfter: bool | None
    addJot: bool | None
    cols: list[AlignSpec] | None
    arraystretch: float
    body: list[list[AnyParseNode]]  # 2D array
    rowGaps: list[Measurement | None]
    hLinesBeforeRow: list[list[bool]]
    tags: list[bool | list[AnyParseNode]] | None
    leqno: bool | None
    isCD: bool | None


class CdlabelParseNode(BaseParseNode):

    side: str
    label: AnyParseNode


class CdlabelparentParseNode(BaseParseNode):

    fragment: AnyParseNode


class ColorParseNode(BaseParseNode):

    color: str
    body: list[AnyParseNode]


class ColorTokenParseNode(BaseParseNode):

    color: str


class OpParseNode(BaseParseNode):

    limits: bool
    alwaysHandleSupSub: bool | None
    suppressBaseShift: bool | None
    parentIsSupSub: bool
    symbol: bool
    name: str | None
    body: list[AnyParseNode] | None


class OrdgroupParseNode(BaseParseNode):

    body: list[AnyParseNode]
    semisimple: bool | None


class RawParseNode(BaseParseNode):

    string: str


class SizeParseNode(BaseParseNode):

    value: Measurement
    isBlank: bool


class StylingParseNode(BaseParseNode):

    style: StyleStr
    body: list[AnyParseNode]


class SupsubParseNode(BaseParseNode):

    base: AnyParseNode | None
    sup: AnyParseNode | None
    sub: AnyParseNode | None


class TagParseNode(BaseParseNode):

    body: list[AnyParseNode]
    tag: list[AnyParseNode]


class TextParseNode(BaseParseNode):

    body: list[AnyParseNode]
    font: str | None


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
    isStretchy: bool | None
    isShifty: bool | None
    base: AnyParseNode


class AccentUnderParseNode(BaseParseNode):

    label: str
    isStretchy: bool | None
    isShifty: bool | None
    base: AnyParseNode


class CrParseNode(BaseParseNode):

    newLine: bool
    size: Measurement | None


class DelimsizingParseNode(BaseParseNode):

    size: int  # 1, 2, 3, or 4
    mclass: str  # "mopen" | "mclose" | "mrel" | "mord"
    delim: str


class EncloseParseNode(BaseParseNode):

    label: str
    backgroundColor: str | None
    borderColor: str | None
    body: AnyParseNode


class EnvironmentParseNode(BaseParseNode):

    name: str
    nameGroup: AnyParseNode


class FontParseNode(BaseParseNode):

    font: str
    body: list[AnyParseNode]


class GenfracParseNode(BaseParseNode):

    continued: bool
    numer: AnyParseNode
    denom: AnyParseNode
    hasBarLine: bool
    leftDelim: str | None
    rightDelim: str | None
    size: str
    barSize: dict[str, Any] | None


class HboxParseNode(BaseParseNode):

    body: list[AnyParseNode]


class HorizBraceParseNode(BaseParseNode):

    label: str
    isOver: bool
    base: AnyParseNode


class HrefParseNode(BaseParseNode):

    href: str
    body: list[AnyParseNode]


class HtmlParseNode(BaseParseNode):

    attributes: dict[str, str]
    body: list[AnyParseNode]


class HtmlmathmlParseNode(BaseParseNode):

    html: list[AnyParseNode]
    mathml: list[AnyParseNode]


class IncludegraphicsParseNode(BaseParseNode):

    alt: str
    width: Measurement
    height: Measurement
    totalheight: Measurement
    src: str


class InfixParseNode(BaseParseNode):

    replaceWith: str
    size: Measurement | None
    token: Token | None


class InternalParseNode(BaseParseNode):
    pass



class KernParseNode(BaseParseNode):

    dimension: Measurement


class LapParseNode(BaseParseNode):

    alignment: str
    body: AnyParseNode


class LeftrightParseNode(BaseParseNode):

    body: list[AnyParseNode]
    left: str
    right: str
    rightColor: str | None


class LeftrightRightParseNode(BaseParseNode):

    delim: str
    color: str | None


class MathchoiceParseNode(BaseParseNode):

    display: list[AnyParseNode]
    text: list[AnyParseNode]
    script: list[AnyParseNode]
    scriptscript: list[AnyParseNode]


class MiddleParseNode(BaseParseNode):

    delim: str


class MclassParseNode(BaseParseNode):

    mclass: str
    body: list[AnyParseNode]
    isCharacterBox: bool


class OperatornameParseNode(BaseParseNode):

    body: list[AnyParseNode]
    alwaysHandleSupSub: bool
    limits: bool
    parentIsSupSub: bool


class OverlineParseNode(BaseParseNode):

    body: AnyParseNode


class PhantomParseNode(BaseParseNode):

    body: list[AnyParseNode]


class HphantomParseNode(BaseParseNode):

    body: AnyParseNode


class VphantomParseNode(BaseParseNode):

    body: AnyParseNode


class PmbParseNode(BaseParseNode):

    mclass: str
    body: list[AnyParseNode]


class RaiseboxParseNode(BaseParseNode):

    dy: Measurement
    body: AnyParseNode


class RuleParseNode(BaseParseNode):

    shift: Measurement | None
    width: Measurement
    height: Measurement


class SizingParseNode(BaseParseNode):

    size: int
    body: list[AnyParseNode]


class SmashParseNode(BaseParseNode):

    body: AnyParseNode
    smashHeight: bool
    smashDepth: bool


class SqrtParseNode(BaseParseNode):

    body: AnyParseNode
    index: AnyParseNode | None


class UnderlineParseNode(BaseParseNode):

    body: AnyParseNode


class VcenterParseNode(BaseParseNode):

    body: AnyParseNode


class XArrowParseNode(BaseParseNode):

    label: str
    body: AnyParseNode
    below: AnyParseNode | None


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


def assert_node_type(node: AnyParseNode | None, expected_type: str) -> AnyParseNode:
    """Assert that a node is of the expected type."""
    if not node or node["type"] != expected_type:
        node_type = node["type"] if node else "None"
        raise ValueError(f"Expected node of type {expected_type}, but got node of type {node_type}")
    return node


def assert_symbol_node_type(node: AnyParseNode | None) -> SymbolParseNode | None:
    """Assert that a node is a symbol node type."""
    if not node:
        return None

    if node["type"] == "atom" or node["type"] in NON_ATOMS:
        return node  # type: ignore

    raise ValueError(f"Expected node of symbol group type, but got node of type {node['type']}")


def check_symbol_node_type(node: AnyParseNode | None) -> SymbolParseNode | None:
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
