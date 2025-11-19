"""Python port of KaTeX's functions/underline.js - text underlining."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..build_common import make_line_span, make_span, make_v_list
from ..define_function import define_function
from ..mathml_tree import MathNode, TextNode

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode, UnderlineParseNode


# Underline command
define_function({
    "type": "underline",
    "names": ["\\underline"],
    "props": {
        "numArgs": 1,
        "allowedInText": True,
    },
    "handler": lambda context, args, opt_args: {
        "type": "underline",
        "mode": context["parser"].mode,
        "body": args[0],
    },
    "html_builder": lambda group, options: _underline_html_builder(group, options),
    "mathml_builder": lambda group, options: _underline_mathml_builder(group, options),
})


def _underline_html_builder(group: ParseNode, options: Options) -> Any:
    """Build HTML for underline command."""
    from .. import build_html as html

    underline_group = cast("UnderlineParseNode", group)
    # Build the inner group
    inner_group = html.build_group(underline_group["body"], options)

    # Create the line to go below the body
    line = make_line_span("underline-line", options)

    # Generate the vlist with proper spacing (TeXbook Rule 10)
    default_rule_thickness = options.font_metrics().get("defaultRuleThickness", 0.04)

    vlist = make_v_list({
        "positionType": "top",
        "positionData": inner_group.height,
        "children": [
            {"type": "kern", "size": default_rule_thickness},
            {"type": "elem", "elem": line},
            {"type": "kern", "size": 3 * default_rule_thickness},
            {"type": "elem", "elem": inner_group},
        ],
    }, options)

    return make_span(["mord", "underline"], [vlist], options)


def _underline_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for underline command."""
    from .. import build_mathml as mml

    underline_group = cast("UnderlineParseNode", group)
    # Use Unicode overline character
    operator = MathNode("mo", [TextNode("\u203e")])
    operator.set_attribute("stretchy", "true")

    node = MathNode("munder", [
        mml.build_group(underline_group["body"], options),
        operator
    ])
    node.set_attribute("accentunder", "true")

    return node
