"""Python port of KaTeX's functions/accentunder.js - under-accent functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..build_common import make_span, make_v_list
from ..define_function import define_function
from ..mathml_tree import MathNode

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode


# Under-accent functions
define_function({
    "type": "accentUnder",
    "names": [
        "\\underleftarrow", "\\underrightarrow", "\\underleftrightarrow",
        "\\undergroup", "\\underlinesegment", "\\utilde",
    ],
    "props": {
        "numArgs": 1,
    },
    "handler": lambda context, args: {
        "type": "accentUnder",
        "mode": context["parser"].mode,
        "label": context["funcName"],
        "base": args[0],
    },
    "html_builder": lambda group, options: _accent_under_html_builder(group, options),
    "mathml_builder": lambda group, options: _accent_under_mathml_builder(group, options),
})


def _accent_under_html_builder(group: ParseNode, options: Options):
    """Build HTML for under-accent commands."""
    from .. import build_html as html
    from .. import stretchy

    # Build the base group
    inner_group = html.build_group(group["base"], options)

    # Create the stretchy accent
    accent_body = stretchy.svg_span(group, options)

    # Kern adjustment for \utilde
    kern = 0.12 if group["label"] == "\\utilde" else 0

    # Generate the vlist
    vlist = make_v_list({
        "positionType": "top",
        "positionData": inner_group.height,
        "children": [
            {"type": "elem", "elem": accent_body, "wrapperClasses": ["svg-align"]},
            {"type": "kern", "size": kern},
            {"type": "elem", "elem": inner_group},
        ],
    }, options)

    return make_span(["mord", "accentunder"], [vlist], options)


def _accent_under_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for under-accent commands."""
    from .. import build_mathml as mml
    from .. import stretchy

    accent_node = stretchy.math_ml_node(group["label"])
    node = MathNode(
        "munder",
        [mml.build_group(group["base"], options), accent_node]
    )
    node.set_attribute("accentunder", "true")

    return node
