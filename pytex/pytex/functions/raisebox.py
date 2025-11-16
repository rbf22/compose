"""Python port of KaTeX's functions/raisebox.js - vertical box positioning."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..build_common import make_v_list
from ..define_function import define_function
from ..mathml_tree import MathNode
from ..parse_node import assert_node_type
from ..units import calculate_size

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode, RaiseboxParseNode, SizeParseNode


# Raisebox for vertical positioning
define_function({
    "type": "raisebox",
    "names": ["\\raisebox"],
    "props": {
        "numArgs": 2,
        "argTypes": ["size", "hbox"],
        "allowedInText": True,
    },
    "handler": lambda context, args: _raisebox_handler(context, args),
    "html_builder": lambda group, options: _raisebox_html_builder(group, options),
    "mathml_builder": lambda group, options: _raisebox_mathml_builder(group, options),
})


def _raisebox_handler(context: Any, args: Any) -> Any:
    size_node = cast("SizeParseNode", assert_node_type(args[0], "size"))
    return {
        "type": "raisebox",
        "mode": context["parser"].mode,
        "dy": size_node["value"],
        "body": args[1],
    }


def _raisebox_html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for raisebox."""
    from .. import build_html as html

    raisebox_group = cast("RaiseboxParseNode", group)
    body = html.build_group(raisebox_group["body"], options)
    dy = calculate_size(raisebox_group["dy"], options)

    return make_v_list({
        "positionType": "shift",
        "positionData": -dy,
        "children": [{"type": "elem", "elem": body}],
    }, options)


def _raisebox_mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for raisebox."""
    from .. import build_mathml as mml

    raisebox_group = cast("RaiseboxParseNode", group)
    node = MathNode("mpadded", [mml.build_group(raisebox_group["body"], options)])
    dy = f"{raisebox_group['dy']['number']}{raisebox_group['dy']['unit']}"
    node.set_attribute("voffset", dy)

    return node
