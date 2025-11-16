"""Python port of KaTeX's functions/color.js - color handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, cast

from ..build_common import make_fragment
from ..define_function import define_function, ordargument
from ..mathml_tree import MathNode
from ..tree import VirtualNode
from ..parse_node import assert_node_type

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ColorParseNode, ColorTokenParseNode, ParseNode


def html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for color group."""
    from .. import build_html as html

    color_group: ColorParseNode = cast("ColorParseNode", group)
    # Build expression with color applied
    elements = html.build_expression(
        color_group["body"],
        options.with_color(color_group["color"]),
        False
    )

    # Wrap in fragment so color doesn't affect element types
    return make_fragment(elements)


def mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for color group."""
    from .. import build_mathml as mml

    color_group: ColorParseNode = cast("ColorParseNode", group)
    # Build expression with color applied
    inner = mml.build_expression(color_group["body"], options.with_color(color_group["color"]))

    # Wrap in mstyle with mathcolor attribute
    node = MathNode("mstyle", cast(List[VirtualNode], inner))
    node.set_attribute("mathcolor", color_group["color"])

    return node


# \textcolor command
define_function({
    "type": "color",
    "names": ["\\textcolor"],
    "props": {
        "numArgs": 2,
        "allowedInText": True,
        "argTypes": ["color", "original"],
    },
    "handler": lambda context, args: {
        "type": "color",
        "mode": context["parser"].mode,
        "color": cast("ColorTokenParseNode", assert_node_type(args[0], "color-token"))["color"],
        "body": ordargument(args[1]),
    },
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# \color command
define_function({
    "type": "color",
    "names": ["\\color"],
    "props": {
        "numArgs": 1,
        "allowedInText": True,
        "argTypes": ["color"],
    },
    "handler": lambda context, args: _color_handler(context, args),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})


def _color_handler(context: Dict[str, Any], args: List[Any]) -> Dict[str, Any]:
    r"""Handler for \color command."""
    color = cast("ColorTokenParseNode", assert_node_type(args[0], "color-token"))["color"]

    # Set \current@color macro to store current color
    context["parser"].gullet.macros.set("\\current@color", color)

    # Parse implicit body that should be colored
    body = context["parser"].parse_expression(True, context.get("breakOnTokenText"))

    return {
        "type": "color",
        "mode": context["parser"].mode,
        "color": color,
        "body": body,
    }
