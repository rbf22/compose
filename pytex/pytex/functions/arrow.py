"""Python port of KaTeX's functions/arrow.js - extensible arrows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..build_common import make_span, make_v_list, wrap_fragment
from ..define_function import define_function
from ..mathml_tree import MathNode

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode


def padded_node(group=None):
    """Create a padded MathML node."""
    node = MathNode("mpadded", [group] if group else [])
    node.set_attribute("width", "+0.6em")
    node.set_attribute("lspace", "0.3em")
    return node


# Extensible arrows with optional arguments
define_function({
    "type": "xArrow",
    "names": [
        "\\xleftarrow", "\\xrightarrow", "\\xLeftarrow", "\\xRightarrow",
        "\\xleftrightarrow", "\\xLeftrightarrow", "\\xhookleftarrow",
        "\\xhookrightarrow", "\\xmapsto", "\\xrightharpoondown",
        "\\xrightharpoonup", "\\xleftharpoondown", "\\xleftharpoonup",
        "\\xrightleftharpoons", "\\xleftrightharpoons", "\\xlongequal",
        "\\xtwoheadrightarrow", "\\xtwoheadleftarrow", "\\xtofrom",
        # Support for mhchem extension
        "\\xrightleftarrows", "\\xrightequilibrium", "\\xleftequilibrium",
        # Support for CD environment
        "\\\\cdrightarrow", "\\\\cdleftarrow", "\\\\cdlongequal",
    ],
    "props": {
        "numArgs": 1,
        "numOptionalArgs": 1,
    },
    "handler": lambda context, args, opt_args: {
        "type": "xArrow",
        "mode": context["parser"].mode,
        "label": context["funcName"],
        "body": args[0],
        "below": opt_args[0] if opt_args else None,
    },
    "html_builder": lambda group, options: _xarrow_html_builder(group, options),
    "mathml_builder": lambda group, options: _xarrow_mathml_builder(group, options),
})


def _xarrow_html_builder(group: ParseNode, options: Options):
    """Build HTML for extensible arrows."""
    from .. import build_html as html
    from .. import stretchy

    style = options.style

    # Build upper group
    new_options = options.having_style(style.sup())
    upper_group = wrap_fragment(
        html.build_group(group["body"], new_options, options), options
    )

    arrow_prefix = "x" if group["label"].startswith("\\x") else "cd"
    upper_group.classes.append(f"{arrow_prefix}-arrow-pad")

    # Build lower group if present
    lower_group = None
    if group.get("below"):
        new_options = options.having_style(style.sub())
        lower_group = wrap_fragment(
            html.build_group(group["below"], new_options, options), options
        )
        lower_group.classes.append(f"{arrow_prefix}-arrow-pad")

    # Create the arrow body
    arrow_body = stretchy.svg_span(group, options)

    # Calculate shifts
    arrow_shift = (-options.font_metrics().get("axisHeight", 0.25) +
                   0.5 * arrow_body.height)

    # Upper shift (2 mu kern = 0.111 em)
    upper_shift = (-options.font_metrics().get("axisHeight", 0.25) -
                   0.5 * arrow_body.height - 0.111)

    if (upper_group.depth > 0.25 or group["label"] == "\\xleftequilibrium"):
        upper_shift -= upper_group.depth  # Shift up if depth encroaches

    # Generate vlist
    if lower_group:
        lower_shift = (-options.font_metrics().get("axisHeight", 0.25) +
                      lower_group.height + 0.5 * arrow_body.height + 0.111)

        vlist = make_v_list({
            "positionType": "individualShift",
            "children": [
                {"type": "elem", "elem": upper_group, "shift": upper_shift},
                {"type": "elem", "elem": arrow_body, "shift": arrow_shift},
                {"type": "elem", "elem": lower_group, "shift": lower_shift},
            ],
        }, options)
    else:
        vlist = make_v_list({
            "positionType": "individualShift",
            "children": [
                {"type": "elem", "elem": upper_group, "shift": upper_shift},
                {"type": "elem", "elem": arrow_body, "shift": arrow_shift},
            ],
        }, options)

    # Add svg-align class
    if (len(vlist.children) > 0 and hasattr(vlist.children[0], 'children') and
        len(vlist.children[0].children) > 0 and hasattr(vlist.children[0].children[0], 'children') and
        len(vlist.children[0].children[0].children) > 1):
        vlist.children[0].children[0].children[1].classes.append("svg-align")

    return make_span(["mrel", "x-arrow"], [vlist], options)


def _xarrow_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for extensible arrows."""
    from .. import build_mathml as mml
    from .. import stretchy

    arrow_node = stretchy.math_ml_node(group["label"])
    # Set minimum size
    min_size = "1.75em" if group["label"].startswith("\\x") else "3.0em"
    arrow_node.set_attribute("minsize", min_size)

    if group.get("body"):
        upper_node = padded_node(mml.build_group(group["body"], options))
        if group.get("below"):
            lower_node = padded_node(mml.build_group(group["below"], options))
            node = MathNode("munderover", [arrow_node, lower_node, upper_node])
        else:
            node = MathNode("mover", [arrow_node, upper_node])
    elif group.get("below"):
        lower_node = padded_node(mml.build_group(group["below"], options))
        node = MathNode("munder", [arrow_node, lower_node])
    else:
        # This should never happen - parser ensures there's an argument
        node = MathNode("mover", [arrow_node, padded_node()])

    return node
