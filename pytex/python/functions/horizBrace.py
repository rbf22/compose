"""Python port of KaTeX's functions/horizBrace.js - horizontal brace handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..build_common import make_span, make_v_list
from ..define_function import define_function
from ..mathml_tree import MathNode
from ..stretchy import svg_span
from ..style import Style

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode


def html_builder(group: ParseNode, options: Options):
    """Build HTML for horizontal braces."""
    from .. import build_html as html

    style = options.style

    # Handle supsub delegation
    sup_sub_group = None
    if group.get("type") == "supsub":
        # LaTeX treats braces like operators with limits
        if group.get("sup"):
            sup_sub_group = html.build_group(
                group["sup"], options.having_style(style.sup()), options
            )
        elif group.get("sub"):
            sup_sub_group = html.build_group(
                group["sub"], options.having_style(style.sub()), options
            )
        group = group["base"]  # The horizBrace is in the base

    # Build the base group with display style
    body = html.build_group(group["base"], options.having_base_style(Style.DISPLAY))

    # Create the stretchy brace
    brace_body = svg_span(group, options)

    # Generate the vlist
    if group.get("isOver", False):
        vlist = make_v_list({
            "positionType": "firstBaseline",
            "children": [
                {"type": "elem", "elem": body},
                {"type": "kern", "size": 0.1},
                {"type": "elem", "elem": brace_body},
            ],
        }, options)
        # Add svg-align class to the body element
        if (len(vlist.children) > 0 and hasattr(vlist.children[0], 'children') and
            len(vlist.children[0].children) > 0 and hasattr(vlist.children[0].children[0], 'children') and
            len(vlist.children[0].children[0].children) > 1):
            vlist.children[0].children[0].children[1].classes.append("svg-align")
    else:
        vlist = make_v_list({
            "positionType": "bottom",
            "positionData": body.depth + 0.1 + brace_body.height,
            "children": [
                {"type": "elem", "elem": brace_body},
                {"type": "kern", "size": 0.1},
                {"type": "elem", "elem": body},
            ],
        }, options)
        # Add svg-align class to the brace element
        if (len(vlist.children) > 0 and hasattr(vlist.children[0], 'children') and
            len(vlist.children[0].children) > 0 and hasattr(vlist.children[0].children[0], 'children') and
            len(vlist.children[0].children[0].children) > 0):
            vlist.children[0].children[0].children[0].classes.append("svg-align")

    if sup_sub_group:
        # Handle supsub with braces
        v_span = make_span(
            ["mord", "mover" if group.get("isOver") else "munder"],
            [vlist], options
        )

        if group.get("isOver"):
            vlist = make_v_list({
                "positionType": "firstBaseline",
                "children": [
                    {"type": "elem", "elem": v_span},
                    {"type": "kern", "size": 0.2},
                    {"type": "elem", "elem": sup_sub_group},
                ],
            }, options)
        else:
            vlist = make_v_list({
                "positionType": "bottom",
                "positionData": (v_span.depth + 0.2 + sup_sub_group.height +
                               sup_sub_group.depth),
                "children": [
                    {"type": "elem", "elem": sup_sub_group},
                    {"type": "kern", "size": 0.2},
                    {"type": "elem", "elem": v_span},
                ],
            }, options)

    return make_span(
        ["mord", "mover" if group.get("isOver") else "munder"],
        [vlist], options
    )


def mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for horizontal braces."""
    from .. import build_mathml as mml
    from ..stretchy import math_ml_node

    accent_node = math_ml_node(group.get("label", ""))
    return MathNode(
        "mover" if group.get("isOver") else "munder",
        [mml.build_group(group["base"], options), accent_node]
    )


# Define horizontal brace functions
define_function({
    "type": "horizBrace",
    "names": ["\\overbrace", "\\underbrace"],
    "props": {
        "numArgs": 1,
    },
    "handler": lambda context, args: {
        "type": "horizBrace",
        "mode": context["parser"].mode,
        "label": context["funcName"],
        "isOver": context["funcName"].startswith("\\over"),
        "base": args[0],
    },
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})
