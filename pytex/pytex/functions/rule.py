"""Python port of KaTeX's functions/rule.js - rule/line handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..build_common import make_span
from ..define_function import define_function
from ..mathml_tree import MathNode
from ..parse_node import assert_node_type
from ..units import calculate_size, make_em

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode, RuleParseNode


def html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for rule commands."""
    rule_group = cast("RuleParseNode", group)
    # Create an empty span for the rule
    rule = make_span(["mord", "rule"], [], options)

    # Calculate dimensions
    width = calculate_size(rule_group["width"], options)
    height = calculate_size(rule_group["height"], options)
    shift = calculate_size(rule_group.get("shift"), options) if rule_group.get("shift") else 0

    # Style the rule
    rule.style["borderRightWidth"] = make_em(width)
    rule.style["borderTopWidth"] = make_em(height)
    rule.style["bottom"] = make_em(shift)

    # Record dimensions
    rule.width = width
    rule.height = height + shift
    rule.depth = -shift

    # Font size calculation for proper space reservation
    rule.max_font_size = height * 1.125 * options.size_multiplier

    return rule


def mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for rule commands."""
    rule_group = cast("RuleParseNode", group)
    width = calculate_size(rule_group["width"], options)
    height = calculate_size(rule_group["height"], options)
    shift = calculate_size(rule_group.get("shift"), options) if rule_group.get("shift") else 0

    # Get color using the proper method
    color = options.get_color() or "black"

    # Create the rule as an mspace with background
    rule = MathNode("mspace")
    rule.set_attribute("mathbackground", color)
    rule.set_attribute("width", make_em(width))
    rule.set_attribute("height", make_em(height))

    # Wrap in mpadded for positioning
    wrapper = MathNode("mpadded", [rule])

    if shift >= 0:
        wrapper.set_attribute("height", make_em(shift))
    else:
        wrapper.set_attribute("height", make_em(shift))
        wrapper.set_attribute("depth", make_em(-shift))

    wrapper.set_attribute("voffset", make_em(shift))

    return wrapper


# Define rule function
define_function({
    "type": "rule",
    "names": ["\\rule"],
    "props": {
        "numArgs": 2,
        "numOptionalArgs": 1,
        "allowedInText": True,
        "allowedInMath": True,
        "argTypes": ["size", "size", "size"],
    },
    "handler": _rule_handler,
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})


def _rule_handler(context, args, opt_args):
    """Handler for \\rule command."""
    return {
        "type": "rule",
        "mode": context["parser"].mode,
        "shift": (assert_node_type(opt_args[0], "size")["value"]
                 if opt_args and opt_args[0] else None),
        "width": assert_node_type(args[0], "size")["value"],
        "height": assert_node_type(args[1], "size")["value"],
    }
