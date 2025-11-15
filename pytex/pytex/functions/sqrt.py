"""Python port of KaTeX's functions/sqrt.js - square root handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, cast

from ..build_common import make_span, make_v_list, wrap_fragment
from ..define_function import define_function
from ..dom_tree import DomSpan, SvgSpan
from ..mathml_tree import MathNode
from ..style import DEFAULT_STYLES

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import AnyParseNode, ParseNode, SqrtParseNode


def html_builder(group: ParseNode, options: "Options") -> DomSpan:
    """Build HTML for square root."""
    from .. import build_html as html
    from .. import delimiter

    sqrt_group = cast("SqrtParseNode", group)
    # Build the inner content with cramped style
    inner = html.build_group(sqrt_group.get("body"), options.having_cramped_style())

    if inner.height == 0:
        # Render a small surd
        inner.height = options.font_metrics().get("xHeight", 0.4)

    # Wrap fragments in spans
    inner = wrap_fragment(inner, options)

    # Calculate minimum size for surd delimiter
    metrics = options.font_metrics()
    theta = metrics.get("defaultRuleThickness", 0.04)

    phi = theta
    text_style = DEFAULT_STYLES["text"]
    if options.style.id < text_style.id:
        phi = metrics.get("xHeight", 0.4)

    # Calculate clearance between body and line
    line_clearance = theta + phi / 4
    min_delimiter_height = inner.height + inner.depth + line_clearance + theta

    # Create sqrt SVG
    sqrt_result = delimiter.make_sqrt_image(min_delimiter_height, options)
    img = cast(SvgSpan, sqrt_result["span"])
    rule_width = cast(float, sqrt_result["ruleWidth"])
    advance_width = cast(float, sqrt_result["advanceWidth"])

    delim_depth = img.height - rule_width

    # Adjust clearance based on delimiter size
    if delim_depth > inner.height + inner.depth + line_clearance:
        line_clearance = (line_clearance + delim_depth - inner.height - inner.depth) / 2

    # Shift the sqrt image
    img_shift = img.height - inner.height - line_clearance - rule_width

    inner.style["paddingLeft"] = f"{advance_width}em"

    # Overlay the image and the argument
    body = make_v_list({
        "positionType": "firstBaseline",
        "children": [
            {"type": "elem", "elem": inner, "wrapperClasses": ["svg-align"]},
            {"type": "kern", "size": -(inner.height + img_shift)},
            {"type": "elem", "elem": img},
            {"type": "kern", "size": rule_width},
        ],
    }, options)

    if not sqrt_group.get("index"):
        return make_span(["mord", "sqrt"], [body], options)
    else:
        # Handle optional root index
        script_style = DEFAULT_STYLES["scriptscript"]
        new_options = options.having_style(script_style)
        rootm = html.build_group(sqrt_group.get("index"), new_options, options)

        # Amount the index is shifted (from TeX source)
        to_shift = 0.6 * (body.height - body.depth)

        # Build VList with superscript shifted up
        root_vlist = make_v_list({
            "positionType": "shift",
            "positionData": -to_shift,
            "children": [{"type": "elem", "elem": rootm}],
        }, options)

        # Add class for kerning
        root_vlist_wrap = make_span(["root"], [root_vlist])

        return make_span(["mord", "sqrt"], [root_vlist_wrap, body], options)


def mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for square root."""
    from .. import build_mathml as mml

    sqrt_group = cast("SqrtParseNode", group)
    body = sqrt_group["body"]
    index = sqrt_group.get("index")

    if index:
        return MathNode("mroot", [
            mml.build_group(body, options),
            mml.build_group(index, options),
        ])
    else:
        return MathNode("msqrt", [mml.build_group(body, options)])


# Register the sqrt function
define_function({
    "type": "sqrt",
    "names": ["\\sqrt"],
    "props": {
        "numArgs": 1,
        "numOptionalArgs": 1,
    },
    "handler": lambda context, args, opt_args=None: _sqrt_handler(context, args, opt_args or []),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})


def _sqrt_handler(context: Dict[str, Any], args: List[AnyParseNode], opt_args: List[AnyParseNode]) -> Dict[str, Any]:
    parser = context["parser"]
    return {
        "type": "sqrt",
        "mode": parser.mode,
        "body": args[0],
        "index": opt_args[0] if opt_args else None,
    }
