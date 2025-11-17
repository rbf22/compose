"""Python port of KaTeX's functions/op.js - mathematical operators."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Union, cast

from ..build_common import make_span, make_symbol, make_v_list, mathsym, static_svg
from ..define_function import define_function, ordargument
from ..dom_tree import DomNode, DomSpan, SymbolNode
from ..mathml_tree import MathNode, TextNode
from ..tree import VirtualNode
from ..parse_node import AnyParseNode, OpParseNode, ParseNode
from ..style import Style
from ..types import Mode

if TYPE_CHECKING:
    from ..options import Options

# Operators that don't have large successors
NO_SUCCESSOR = ["\\smallint"]


def _as_mode(value: Any) -> Mode:
    try:
        return Mode(value)
    except ValueError:
        return Mode.MATH


def _normalize_body(group: Mapping[str, Any]) -> List[AnyParseNode]:
    raw_body = group.get("body")
    if not isinstance(raw_body, list):
        return []
    typed_nodes = [cast(AnyParseNode, node) for node in raw_body if isinstance(node, dict)]
    return typed_nodes


def _build_text_operator(name: str, mode: Mode, options: "Options") -> DomSpan:
    characters = [mathsym(ch, mode, options) for ch in name]
    dom_children = cast(List[DomNode], characters)
    return make_span(["mop"], dom_children, options)


def html_builder(group: ParseNode, options: "Options") -> DomSpan:
    """Build HTML for operator group."""
    from .. import build_html as html

    op_group = cast("OpParseNode", group)
    sup_group: Optional[AnyParseNode] = None
    sub_group: Optional[AnyParseNode] = None
    op_group_map: Mapping[str, Any] = op_group
    has_limits = False

    if op_group.get("type") == "supsub":
        sup_group = cast(Optional[AnyParseNode], op_group.get("sup"))
        sub_group = cast(Optional[AnyParseNode], op_group.get("sub"))
        op_group_map = cast(Mapping[str, Any], op_group.get("base", op_group))
        has_limits = True

    style = options.style
    large = (
        style.size == Style.DISPLAY.size
        and op_group_map.get("symbol")
        and op_group_map.get("name") not in NO_SUCCESSOR
    )

    base: DomNode
    name = op_group_map.get("name", "")

    if op_group_map.get("symbol"):
        font_name = "Size2-Regular" if large else "Size1-Regular"
        stash = ""
        if name in ("\\oiint", "\\oiiint"):
            stash = name[1:]
            name = "\\iint" if stash == "oiint" else "\\iiint"

        symbol_node = make_symbol(
            name,
            font_name,
            Mode.MATH,
            options,
            ["mop", "op-symbol", "large-op" if large else "small-op"],
        )
        symbol_slant = symbol_node.italic

        if stash:
            oval = static_svg(f"{stash}Size{'2' if large else '1'}", options)
            base = make_v_list(
                {
                    "positionType": "individualShift",
                    "children": [
                        {"type": "elem", "elem": symbol_node, "shift": 0},
                        {"type": "elem", "elem": oval, "shift": 0.08 if large else 0.0},
                    ],
                },
                options,
            )
            base.classes.insert(0, "mop")
            base_slant = symbol_slant
        else:
            base = symbol_node
            base_slant = symbol_slant

    elif op_group_map.get("body"):
        inner_nodes = _normalize_body(op_group_map)
        inner = html.build_expression(inner_nodes, options, True)
        if len(inner) == 1 and isinstance(inner[0], SymbolNode):
            symbol_node = inner[0]
            symbol_node.classes[0] = "mop"
            base = make_span(list(symbol_node.classes), [symbol_node], options)
            base_slant = symbol_node.italic
        else:
            base = make_span(["mop"], inner, options)
            base_slant = 0.0

    else:
        mode = _as_mode(op_group_map.get("mode", Mode.MATH))
        base = _build_text_operator(name[1:] if name.startswith("\\") else name, mode, options)
        base_slant = 0.0

    base_shift = 0.0
    slant = base_slant
    if (
        op_group_map.get("symbol")
        or name in ("\\oiint", "\\oiiint")
    ) and not op_group_map.get("suppressBaseShift", False):
        base_shift = (base.height - base.depth) / 2 - options.font_metrics().get("axisHeight", 0.0)

    if has_limits:
        return assembleSupSub(base, sup_group, sub_group, options, style, slant, base_shift)

    if base_shift:
        base.style["position"] = "relative"
        base.style["top"] = f"{base_shift:.4f}em"
    return base


def mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for operator group."""
    from .. import build_mathml as mml

    op_group = cast("OpParseNode", group)
    if op_group.get("symbol"):
        mode = _as_mode(op_group.get("mode", Mode.MATH))
        raw_name = op_group.get("name")
        symbol_name: str = raw_name if isinstance(raw_name, str) else ""
        node = MathNode("mo", [mml.make_text(symbol_name, mode)])
        if symbol_name in NO_SUCCESSOR:
            node.set_attribute("largeop", "false")
        return node

    if op_group.get("body"):
        body_nodes = _normalize_body(op_group)
        inner = mml.build_expression(body_nodes, options)
        return MathNode("mo", cast(List[VirtualNode], inner))

    raw_name = op_group.get("name")
    identifier_name: str = raw_name if isinstance(raw_name, str) else ""
    identifier = MathNode("mi", [TextNode(identifier_name[1:])])
    operator = MathNode("mo", [mml.make_text("\u2061", Mode.TEXT)])
    if op_group.get("parentIsSupSub"):
        return MathNode("mrow", [identifier, operator])
    return MathNode("mrow", [identifier, operator])


# Single character big operators mapping
SINGLE_CHAR_BIG_OPS = {
    "\u220F": "\\prod",
    "\u2210": "\\coprod",
    "\u2211": "\\sum",
    "\u22c0": "\\bigwedge",
    "\u22c1": "\\bigvee",
    "\u22c2": "\\bigcap",
    "\u22c3": "\\bigcup",
    "\u2a00": "\\bigodot",
    "\u2a01": "\\bigoplus",
    "\u2a02": "\\bigotimes",
    "\u2a04": "\\biguplus",
    "\u2a06": "\\bigsqcup",
}

# Single character integrals mapping
SINGLE_CHAR_INTEGRALS = {
    "\u222b": "\\int",
    "\u222c": "\\iint",
    "\u222d": "\\iiint",
    "\u222e": "\\oint",
    "\u222f": "\\oiint",
    "\u2230": "\\oiiint",
}

# Big operators (limits, symbols)
define_function({
    "type": "op",
    "names": [
        "\\coprod", "\\bigvee", "\\bigwedge", "\\biguplus", "\\bigcap",
        "\\bigcup", "\\intop", "\\prod", "\\sum", "\\bigotimes",
        "\\bigoplus", "\\bigodot", "\\bigsqcup", "\\smallint",
        "\u220F", "\u2210", "\u2211", "\u22c0", "\u22c1", "\u22c2", "\u22c3",
        "\u2a00", "\u2a01", "\u2a02", "\u2a04", "\u2a06",
    ],
    "props": {
        "numArgs": 0,
    },
    "handler": lambda context, args, opt_args: _op_handler(context, args, limits=True, symbol=True),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# Mathop command
define_function({
    "type": "op",
    "names": ["\\mathop"],
    "props": {
        "numArgs": 1,
        "primitive": True,
    },
    "handler": lambda context, args, opt_args: {
        "type": "op",
        "mode": context["parser"].mode,
        "limits": False,
        "parentIsSupSub": False,
        "symbol": False,
        "body": ordargument(args[0]),
    },
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# No limits, not symbols (function names)
define_function({
    "type": "op",
    "names": [
        "\\arcsin", "\\arccos", "\\arctan", "\\arctg", "\\arcctg",
        "\\arg", "\\ch", "\\cos", "\\cosec", "\\cosh", "\\cot", "\\cotg",
        "\\coth", "\\csc", "\\ctg", "\\cth", "\\deg", "\\dim", "\\exp",
        "\\hom", "\\ker", "\\lg", "\\ln", "\\log", "\\sec", "\\sin",
        "\\sinh", "\\sh", "\\tan", "\\tanh", "\\tg", "\\th",
    ],
    "props": {
        "numArgs": 0,
    },
    "handler": lambda context, args, opt_args: _op_handler(context, args, limits=False, symbol=False),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# Limits, not symbols (operators like lim, max, etc.)
define_function({
    "type": "op",
    "names": [
        "\\det", "\\gcd", "\\inf", "\\lim", "\\max", "\\min", "\\Pr", "\\sup",
    ],
    "props": {
        "numArgs": 0,
    },
    "handler": lambda context, args, opt_args: _op_handler(context, args, limits=True, symbol=False),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# No limits, symbols (integrals)
define_function({
    "type": "op",
    "names": [
        "\\int", "\\iint", "\\iiint", "\\oint", "\\oiint", "\\oiiint",
        "\u222b", "\u222c", "\u222d", "\u222e", "\u222f", "\u2230",
    ],
    "props": {
        "numArgs": 0,
    },
    "handler": lambda context, args, opt_args: _op_handler(context, args, limits=False, symbol=True),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})


def _op_handler(context: Dict[str, Any], args: List[AnyParseNode], limits: bool, symbol: bool) -> Dict[str, Any]:
    """Common handler for operator functions."""
    func_name = context["funcName"]
    if len(func_name) == 1:
        if symbol and limits:
            func_name = SINGLE_CHAR_BIG_OPS.get(func_name, func_name)
        elif symbol:
            func_name = SINGLE_CHAR_INTEGRALS.get(func_name, func_name)

    return {
        "type": "op",
        "mode": context["parser"].mode,
        "limits": limits,
        "parentIsSupSub": False,
        "symbol": symbol,
        "name": func_name,
    }


# Import assembleSupSub utility
try:
    from .utils.assembleSupSub import assembleSupSub
except ImportError:
    def assembleSupSub(
        base: Union[SymbolNode, DomSpan],
        sup_group: Optional[AnyParseNode],
        sub_group: Optional[AnyParseNode],
        options: "Options",
        style: Style,
        slant: float,
        base_shift: float,
    ) -> DomSpan:
        span = base if isinstance(base, DomSpan) else make_span(list(base.classes), [base], options)
        return span
