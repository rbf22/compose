"""Python port of KaTeX's functions/overline.js - overline handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..build_common import make_line_span, make_span, make_v_list
from ..define_function import define_function
from ..mathml_tree import MathNode, TextNode

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import OverlineParseNode, ParseNode


# Overline command
define_function({
    "type": "overline",
    "names": ["\\overline"],
    "props": {
        "numArgs": 1,
    },
    "handler": lambda context, args, opt_args: {
        "type": "overline",
        "mode": context["parser"].mode,
        "body": args[0],
    },
    "html_builder": lambda group, options: _overline_html_builder(group, options),
    "mathml_builder": lambda group, options: _overline_mathml_builder(group, options),
})


def _overline_html_builder(group: ParseNode, options: Options) -> Any:
    """Build HTML for overline command."""
    from .. import build_html as html

    overline_group = cast("OverlineParseNode", group)
    # Build the inner group in cramped style (TeXbook Rule 9)
    inner_group = html.build_group(overline_group["body"], options.having_cramped_style())

    # Create the line above the body
    line = make_line_span("overline-line", options)

    # Generate the vlist with proper kerning
    default_rule_thickness = options.font_metrics().get("defaultRuleThickness", 0.04)

    vlist = make_v_list({
        "positionType": "firstBaseline",
        "children": [
            {"type": "elem", "elem": inner_group},
            {"type": "kern", "size": 3 * default_rule_thickness},
            {"type": "elem", "elem": line},
            {"type": "kern", "size": default_rule_thickness},
        ],
    }, options)

    return make_span(["mord", "overline"], [vlist], options)


def _overline_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for overline command."""
    from .. import build_mathml as mml

    overline_group = cast("OverlineParseNode", group)
    # Use Unicode overline character
    operator = MathNode("mo", [TextNode("\u203e")])
    operator.set_attribute("stretchy", "true")

    node = MathNode("mover", [
        mml.build_group(overline_group["body"], options),
        operator
    ])
    node.set_attribute("accent", "true")

    return node
