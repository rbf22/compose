"""Python port of KaTeX's buildMathML.js - MathML output generation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, List, Optional, cast

from .build_common import make_span
from .font_metrics import get_character_metrics
from .mathml_tree import MathNode, TextNode
from .parse_error import ParseError
from .tree import VirtualNode
from .types import FontVariant, Mode

SymbolTable = Dict[Mode, Dict[str, Dict[str, str]]]
LigatureTable = Dict[str, bool]

try:
    from .symbols_data import symbols as _SYMBOLS, ligatures as _LIGATURES
except ImportError:
    SYMBOLS: SymbolTable = {}
    LIGATURES: LigatureTable = {}
else:
    SYMBOLS = cast(SymbolTable, _SYMBOLS)
    LIGATURES = _LIGATURES

try:
    from .define_function import _mathmlGroupBuilders as group_builders
except ImportError:
    group_builders = {}

if TYPE_CHECKING:
    from .options import Options
    from .parse_node import AnyParseNode, SymbolParseNode
    from .dom_tree import DomSpan, DomNode

    GroupBuilder = Callable[[AnyParseNode, Options], MathNode]

def make_text(text: str, mode: Mode, options: Optional[Options] = None) -> TextNode:
    """Create a MathML text node with optional symbol replacement."""
    # SYMBOLS is keyed by the string mode names ("math"/"text"), while the
    # builder code often passes a Mode enum. Normalise here so lookups work
    # regardless of how the caller represents the mode.
    mode_key = mode.value if isinstance(mode, Mode) else mode

    if (SYMBOLS.get(mode_key, {}).get(text) and
        SYMBOLS[mode_key][text].get("replace") and
        ord(text[0]) != 0xD835 and  # not surrogate pair
        not (LIGATURES.get(text) and options and
             ((options.font_family and "tt" in options.font_family) or
              (options.font and "tt" in options.font)))):

        text = SYMBOLS[mode_key][text]["replace"]

    return TextNode(text)


def make_row(body: List[MathNode]) -> MathNode:
    """Wrap nodes in an <mrow> if needed."""
    if len(body) == 1:
        return body[0]
    else:
        return MathNode("mrow", cast(List[VirtualNode], body))


def get_variant(group: SymbolParseNode, options: Options) -> Optional[FontVariant]:
    """Get the math variant for a symbol group."""
    # Handle font family variants
    if options.font_family == "texttt":
        return FontVariant.MONOSPACE
    elif options.font_family == "textsf":
        if options.font_shape == "textit" and options.font_weight == "textbf":
            return FontVariant.SANS_SERIF_BOLD_ITALIC
        elif options.font_shape == "textit":
            return FontVariant.SANS_SERIF_ITALIC
        elif options.font_weight == "textbf":
            return FontVariant.BOLD_SANS_SERIF
        else:
            return FontVariant.SANS_SERIF
    elif options.font_shape == "textit" and options.font_weight == "textbf":
        return FontVariant.BOLD_ITALIC
    elif options.font_shape == "textit":
        return FontVariant.ITALIC
    elif options.font_weight == "textbf":
        return FontVariant.BOLD

    font = options.font
    if not font or font == "mathnormal":
        return None

    mode = group["mode"]
    if font == "mathit":
        return FontVariant.ITALIC
    elif font == "boldsymbol":
        return FontVariant.BOLD if group["type"] == "textord" else FontVariant.BOLD_ITALIC
    elif font == "mathbf":
        return FontVariant.BOLD
    elif font == "mathbb":
        return FontVariant.DOUBLE_STRUCK
    elif font == "mathsfit":
        return FontVariant.SANS_SERIF_ITALIC
    elif font == "mathfrak":
        return FontVariant.FRAKTUR
    elif font in ("mathscr", "mathcal"):
        return FontVariant.SCRIPT
    elif font == "mathsf":
        return FontVariant.SANS_SERIF
    elif font == "mathtt":
        return FontVariant.MONOSPACE

    text = group["text"]
    if text in ["\\imath", "\\jmath"]:
        return None

    mode_key = mode.value if isinstance(mode, Mode) else mode
    if SYMBOLS.get(mode_key, {}).get(text, {}).get("replace"):
        text = SYMBOLS[mode_key][text]["replace"]

    # Check if we can use this font variant
    from .build_common import FONT_MAP
    if font in FONT_MAP and get_character_metrics(text, FONT_MAP[font]["fontName"], mode):
        # FONT_MAP stores variant names as strings; convert to FontVariant enum.
        return FontVariant(FONT_MAP[font]["variant"])

    return None


def is_number_punctuation(group: Optional[MathNode]) -> bool:
    """Check if group is number punctuation (dot or comma)."""
    if not group:
        return False

    if (group.type == 'mi' and len(group.children) == 1 and
        isinstance(group.children[0], TextNode) and group.children[0].text == '.'):
        return True
    elif (group.type == 'mo' and len(group.children) == 1 and
          group.get_attribute('separator') == 'true' and
          group.get_attribute('lspace') == '0em' and
          group.get_attribute('rspace') == '0em' and
          isinstance(group.children[0], TextNode) and group.children[0].text == ','):
        return True

    return False


def build_expression(
    expression: List[AnyParseNode],
    options: Options,
    is_ordgroup: Optional[bool] = None,
) -> List[MathNode]:
    """Build MathML nodes from parse nodes."""
    if len(expression) == 1:
        group = build_group(expression[0], options)
        if (is_ordgroup and isinstance(group, MathNode) and group.type == "mo"):
            # Suppress spacing on operators in braces
            group.set_attribute("lspace", "0em")
            group.set_attribute("rspace", "0em")
        return [group]

    groups: List[MathNode] = []
    last_group: Optional[MathNode] = None

    for i, expr in enumerate(expression):
        group = build_group(expr, options)

        if isinstance(group, MathNode) and isinstance(last_group, MathNode):
            # Concatenate adjacent <mtext>s
            if (group.type == 'mtext' and last_group.type == 'mtext' and
                group.get_attribute('mathvariant') == last_group.get_attribute('mathvariant')):
                last_group.children.extend(group.children)
                continue
            # Concatenate adjacent <mn>s
            elif group.type == 'mn' and last_group.type == 'mn':
                last_group.children.extend(group.children)
                continue
            # Concatenate <mn> followed by punctuation
            elif is_number_punctuation(group) and last_group.type == 'mn':
                last_group.children.extend(group.children)
                continue
            # Concatenate punctuation followed by <mn>
            elif (group.type == 'mn' and is_number_punctuation(last_group)):
                group.children = last_group.children + group.children
                groups.pop()
            # Put numbers into base of sup/sub
            elif ((group.type in ('msup', 'msub')) and len(group.children) >= 1 and
                  (last_group.type == 'mn' or is_number_punctuation(last_group))):
                base = group.children[0]
                if isinstance(base, MathNode) and base.type == 'mn':
                    base.children = last_group.children + base.children
                    groups.pop()
            # Handle \not combining character
            elif (last_group.type == 'mi' and len(last_group.children) == 1 and
                  isinstance(last_group.children[0], TextNode) and
                  last_group.children[0].text == '\u0338' and
                  group.type in ('mo', 'mi', 'mn')):
                child = group.children[0]
                if isinstance(child, TextNode) and len(child.text) > 0:
                    # Overlay with combining character long solidus
                    child.text = child.text[0] + "\u0338" + child.text[1:]
                    groups.pop()

        groups.append(group)
        last_group = group

    return groups


def build_expression_row(
    expression: List[AnyParseNode],
    options: Options,
    is_ordgroup: Optional[bool] = None,
) -> MathNode:
    """Build expression and wrap in mrow if needed."""
    return make_row(build_expression(expression, options, is_ordgroup))


def build_group(group: Optional[AnyParseNode], options: Options) -> MathNode:
    """Build a single MathML group."""
    if not group:
        return MathNode("mrow")

    if group["type"] in group_builders:
        # Call the group builder function
        builder = group_builders[group["type"]]
        if TYPE_CHECKING:
            # Help mypy understand the builder signature
            builder_typed: "GroupBuilder" = builder
            result = builder_typed(group, options)
        else:
            result = builder(group, options)
        if isinstance(result, MathNode):
            return result
        raise TypeError("Expected MathNode from mathml group builder")
    else:
        raise ParseError(f"Got group of unknown type: '{group['type']}'")


def build_mathml(
    tree: List[AnyParseNode],
    tex_expression: str,
    options: Options,
    is_display_mode: bool,
    for_mathml_only: bool,
) -> DomSpan:
    """Build complete MathML representation."""
    expression = build_expression(tree, options)

    # Wrap in mrow if needed
    if (len(expression) == 1 and isinstance(expression[0], MathNode) and
        expression[0].type in ["mrow", "mtable"]):
        wrapper = expression[0]
    else:
        wrapper = MathNode("mrow", cast(List[VirtualNode], expression))

    # Build TeX annotation
    annotation = MathNode("annotation", [TextNode(tex_expression)])
    annotation.set_attribute("encoding", "application/x-tex")

    # Create semantics element
    semantics = MathNode("semantics", [wrapper, annotation])

    # Create math element
    math = MathNode("math", [semantics])
    math.set_attribute("xmlns", "http://www.w3.org/1998/Math/MathML")
    if is_display_mode:
        math.set_attribute("display", "block")

    # Wrap in span for styling
    wrapper_class = "katex" if for_mathml_only else "katex-mathml"
    return make_span([wrapper_class], [cast("DomNode", math)])


__all__ = [
    "make_text",
    "make_row",
    "get_variant",
    "build_expression",
    "build_expression_row",
    "build_group",
    "build_mathml",
]
