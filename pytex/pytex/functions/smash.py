"""Python port of KaTeX's functions/smash.js - smash command for height/depth control."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, cast

from ..build_common import make_span, make_v_list
from ..define_function import define_function
from ..mathml_tree import MathNode
from ..parse_node import assert_node_type

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import AnyParseNode, OrdgroupParseNode, ParseNode, SmashParseNode


def html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for smash command."""
    from .. import build_html as html

    smash_group = cast("SmashParseNode", group)
    node = make_span([], [html.build_group(smash_group["body"], options)])

    if not smash_group.get("smashHeight", False) and not smash_group.get("smashDepth", False):
        return node

    if smash_group.get("smashHeight", False):
        node.height = 0
        # Reset child heights to influence makeVList
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                child.height = 0

    if smash_group.get("smashDepth", False):
        node.depth = 0
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                child.depth = 0

    # Use makeVList to apply display: table-cell and prevent browser line height issues
    smashed_node = make_v_list({
        "positionType": "firstBaseline",
        "children": [{"type": "elem", "elem": node}],
    }, options)

    # TeX treats \smash as a math group (same spacing as ord)
    return make_span(["mord"], [smashed_node], options)


def mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for smash command."""
    from .. import build_mathml as mml

    smash_group = cast("SmashParseNode", group)
    node = MathNode("mpadded", [mml.build_group(smash_group["body"], options)])

    if smash_group.get("smashHeight", False):
        node.set_attribute("height", "0px")

    if smash_group.get("smashDepth", False):
        node.set_attribute("depth", "0px")

    return node


# Define smash function
define_function({
    "type": "smash",
    "names": ["\\smash"],
    "props": {
        "numArgs": 1,
        "numOptionalArgs": 1,
        "allowedInText": True,
    },
    "handler": lambda context, args, opt_args: _smash_handler(context, args, opt_args),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})


def _smash_handler(context: Dict[str, Any], args: List[AnyParseNode], opt_args: List[AnyParseNode]) -> Dict[str, Any]:
    r"""Handler for \smash command."""
    smash_height = False
    smash_depth = False

    # Check for optional [tb] argument
    tb_arg = opt_args and opt_args[0] and cast("OrdgroupParseNode", assert_node_type(opt_args[0], "ordgroup"))
    if tb_arg:
        # Parse the [tb] argument
        letter: str = ""
        for node in tb_arg["body"]:
            letter = str(node.get("text", ""))
            if letter == "t":
                smash_height = True
            elif letter == "b":
                smash_depth = True
            else:
                smash_height = False
                smash_depth = False
                break
    else:
        # Default: smash both height and depth
        smash_height = True
        smash_depth = True

    return {
        "type": "smash",
        "mode": context["parser"].mode,
        "body": args[0],
        "smashHeight": smash_height,
        "smashDepth": smash_depth,
    }
