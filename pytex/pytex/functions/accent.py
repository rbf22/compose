"""Python port of KaTeX's functions/accent.js - accent handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast

from ..build_common import make_ord, make_span, make_v_list, static_svg
from ..define_function import define_function, normalize_argument
from ..mathml_tree import MathNode
from ..stretchy import svg_span
from ..utils import is_character_box, get_base_elem
from ..units import make_em

if TYPE_CHECKING:
    from ..dom_tree import DomNode, SymbolNode
    from ..options import Options
    from ..parse_node import AccentParseNode, AnyParseNode, ParseNode


def is_accent_node(node: Any) -> bool:
    """Check if a node is an accent node."""
    return (isinstance(node, dict) and
            node.get("type") == "accent" and
            "base" in node and
            "label" in node)

def html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for accent group."""
    from .. import build_html as html
    from ..dom_tree import assert_symbol_dom_node

    # Handle the supsub case where accent is nested
    supsub_group = None
    accent_dict: Dict[str, Any]
    base_node_opt: Optional[AnyParseNode] = None

    group_dict = cast(Dict[str, Any], group)

    if (isinstance(group, dict) and group_dict.get("type") == "supsub" and
        isinstance(group_dict.get("base"), dict) and is_accent_node(group_dict["base"])):
        accent_dict = group_dict["base"]
        base_node_opt = cast("AnyParseNode", accent_dict.get("base"))
        temp_group = cast("ParseNode", {**group_dict, "base": base_node_opt})
        supsub_group = html.build_group(temp_group, options)
    elif is_accent_node(group_dict):
        accent_dict = group_dict
        base_node_opt = cast("AnyParseNode", accent_dict.get("base"))
    else:
        accent_dict = group_dict
        base_node_opt = cast(Optional[AnyParseNode], accent_dict.get("base"))

    if base_node_opt is None:
        raise ValueError("Accent group missing base parse node")

    base_node = base_node_opt
    accent_group = cast("AccentParseNode", accent_dict)
    body = html.build_group(base_node, options.having_cramped_style())

    # Check if accent needs to shift for character skew
    must_shift = bool(
        accent_group.get("isShifty", False) and
        is_character_box(cast(Dict[str, Any], base_node))
    )

    # Calculate skew
    skew: float = 0.0
    if must_shift:
        base_char_dict = get_base_elem(cast(Dict[str, Any], base_node))
        base_char = cast("AnyParseNode", base_char_dict)
        base_group = html.build_group(base_char, options.having_cramped_style())
        skew = assert_symbol_dom_node(base_group).skew

    accent_below = accent_group.get("label") == "\\c"

    # Calculate clearance between body and accent
    if accent_below:
        clearance = body.height + body.depth
    else:
        clearance = min(body.height, options.font_metrics().get("xHeight", 0.4))

    # Build the accent
    is_stretchy = bool(accent_group.get("isStretchy", False))
    if not is_stretchy:
        # Non-stretchy accent
        label = accent_group.get("label", "")
        if label == "\\vec":
            accent_dom: DomNode = static_svg("vec", options)
            width = 0.471  # From svgData.vec[1]
            symbol_node: Optional[SymbolNode] = None
        else:
            mode = accent_group.get("mode", "math")
            accent_dom_node = make_ord({
                "mode": mode,
                "text": label
            }, options, "textord")
            symbol = cast("DomNode", accent_dom_node)
            symbol_node = assert_symbol_dom_node(symbol)
            symbol_node.italic = 0  # Remove italic correction
            accent_dom = symbol_node
            width = symbol_node.width
            if accent_below:
                clearance += symbol_node.depth

        accent_body = make_span(["accent-body"], [accent_dom])

        # Handle full accents (like \textcircled)
        accent_full = label == "\\textcircled"
        if accent_full:
            accent_body.classes.append("accent-full")
            clearance = body.height

        # Shift accent by skew
        left = skew
        if not accent_full:
            left -= width / 2

        accent_body.style["left"] = make_em(left)

        # Special adjustment for \textcircled
        if label == "\\textcircled":
            accent_body.style["top"] = ".2em"

        accent_body = make_v_list({
            "positionType": "firstBaseline",
            "children": [
                {"type": "elem", "elem": body},
                {"type": "kern", "size": -clearance},
                {"type": "elem", "elem": accent_body},
            ],
        }, options)

    else:
        # Stretchy accent
        accent_body = svg_span(accent_group, options)

        wrapper_style: Optional[Dict[str, str]] = None
        if skew > 0:
            wrapper_style = {
                "width": f"calc(100% - {make_em(2 * skew)})",
                "marginLeft": make_em(2 * skew),
            }

        accent_body = make_v_list({
            "positionType": "firstBaseline",
            "children": [
                {"type": "elem", "elem": body},
                {
                    "type": "elem",
                    "elem": accent_body,
                    "wrapperClasses": ["svg-align"],
                    "wrapperStyle": wrapper_style,
                },
            ],
        }, options)

    accent_wrap = make_span(["mord", "accent"], [accent_body], options)

    # Handle supsub case
    if supsub_group is not None:
        # Replace base child with our accent
        from ..dom_tree import Span as DomSpan

        span_group = cast(DomSpan, supsub_group)
        if span_group.children:
            span_group.children[0] = accent_wrap
        span_group.height = max(accent_wrap.height, span_group.height)
        if span_group.classes:
            span_group.classes[0] = "mord"
        return span_group
    else:
        return accent_wrap


def mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for accent group."""
    from .. import build_mathml as mml
    from ..stretchy import math_ml_node

    accent_group: Any = group
    if accent_group.get("isStretchy", False):
        accent_node = math_ml_node(accent_group["label"])
    else:
        accent_node = MathNode("mo", [mml.make_text(accent_group["label"], accent_group["mode"])])

    node = MathNode("mover", [
        mml.build_group(accent_group["base"], options),
        accent_node
    ])

    node.set_attribute("accent", "true")
    return node


# Non-stretchy accent regex
NON_STRETCHY_ACCENT_REGEX = "|".join([
    r"\\acute", r"\\grave", r"\\ddot", r"\\tilde", r"\\bar", r"\\breve",
    r"\\check", r"\\hat", r"\\vec", r"\\dot", r"\\mathring"
])

# Math accents
define_function({
    "type": "accent",
    "names": [
        "\\acute", "\\grave", "\\ddot", "\\tilde", "\\bar", "\\breve",
        "\\check", "\\hat", "\\vec", "\\dot", "\\mathring", "\\widecheck",
        "\\widehat", "\\widetilde", "\\overrightarrow", "\\overleftarrow",
        "\\Overrightarrow", "\\overleftrightarrow", "\\overgroup",
        "\\overlinesegment", "\\overleftharpoon", "\\overrightharpoon",
    ],
    "props": {
        "numArgs": 1,
    },
    "handler": lambda context, args: _accent_handler(context, args, False),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# Text-mode accents
define_function({
    "type": "accent",
    "names": [
        "\\'", "\\`", "\\^", "\\~", "\\=", "\\u", "\\.", '\\"',
        "\\c", "\\r", "\\H", "\\v", "\\textcircled",
    ],
    "props": {
        "numArgs": 1,
        "allowedInText": True,
        "allowedInMath": True,
        "argTypes": ["primitive"],
    },
    "handler": lambda context, args: _accent_handler(context, args, True),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})


def _accent_handler(context: Dict[str, Any], args: List[Any], is_text_accent: bool) -> Dict[str, Any]:
    """Handler for accent commands."""
    import re

    base = args[0] if is_text_accent else normalize_argument(args[0])

    func_name = context["funcName"]

    # Determine if stretchy
    is_stretchy = not re.search(NON_STRETCHY_ACCENT_REGEX, func_name)

    # Determine if shifty
    is_shifty = not is_stretchy or func_name in [
        "\\widehat", "\\widetilde", "\\widecheck"
    ]

    # Handle text accents
    mode = context["parser"].mode
    if is_text_accent and mode == "math":
        context["parser"].settings.report_nonstrict(
            "mathVsTextAccents",
            f"LaTeX's accent {func_name} works only in text mode"
        )
        mode = "text"

    return {
        "type": "accent",
        "mode": mode,
        "label": func_name,
        "isStretchy": is_stretchy,
        "isShifty": is_shifty,
        "base": base,
    }
