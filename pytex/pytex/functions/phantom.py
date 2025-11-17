"""Python port of KaTeX's functions/phantom.js - phantom box handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, cast

from ..build_common import make_fragment, make_span, make_v_list
from ..define_function import define_function, ordargument
from ..mathml_tree import MathNode
from ..tree import VirtualNode

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import HphantomParseNode, ParseNode, PhantomParseNode, VphantomParseNode


# \phantom - invisible box with full dimensions
define_function({
    "type": "phantom",
    "names": ["\\phantom"],
    "props": {
        "numArgs": 1,
        "allowedInText": True,
    },
    "handler": lambda context, args, opt_args: {
        "type": "phantom",
        "mode": context["parser"].mode,
        "body": ordargument(args[0]),
    },
    "html_builder": lambda group, options: _phantom_html_builder(group, options),
    "mathml_builder": lambda group, options: _phantom_mathml_builder(group, options),
})

# \hphantom - horizontal phantom (only width, zero height/depth)
define_function({
    "type": "hphantom",
    "names": ["\\hphantom"],
    "props": {
        "numArgs": 1,
        "allowedInText": True,
    },
    "handler": lambda context, args, opt_args: {
        "type": "hphantom",
        "mode": context["parser"].mode,
        "body": args[0],
    },
    "html_builder": lambda group, options: _hphantom_html_builder(group, options),
    "mathml_builder": lambda group, options: _hphantom_mathml_builder(group, options),
})

# \vphantom - vertical phantom (only height/depth, zero width)
define_function({
    "type": "vphantom",
    "names": ["\\vphantom"],
    "props": {
        "numArgs": 1,
        "allowedInText": True,
    },
    "handler": lambda context, args, opt_args: {
        "type": "vphantom",
        "mode": context["parser"].mode,
        "body": args[0],
    },
    "html_builder": lambda group, options: _vphantom_html_builder(group, options),
    "mathml_builder": lambda group, options: _vphantom_mathml_builder(group, options),
})


def _phantom_html_builder(group: ParseNode, options: "Options") -> Any:
    r"""Build HTML for \phantom."""
    from .. import build_html as html

    phantom_group = cast("PhantomParseNode", group)
    elements = html.build_expression(
        phantom_group["body"],
        options.with_phantom(),
        False
    )

    # Phantom doesn't affect the elements it contains
    return make_fragment(elements)


def _phantom_mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    r"""Build MathML for \phantom."""
    from .. import build_mathml as mml

    phantom_group = cast("PhantomParseNode", group)
    inner = mml.build_expression(phantom_group["body"], options)
    return MathNode("mphantom", cast(List[VirtualNode], inner))


def _hphantom_html_builder(group: ParseNode, options: "Options") -> Any:
    r"""Build HTML for \hphantom."""
    from .. import build_html as html

    hphantom_group = cast("HphantomParseNode", group)
    node = make_span(
        [], [html.build_group(hphantom_group["body"], options.with_phantom())]
    )
    node.height = 0
    node.depth = 0

    # Zero out child dimensions
    if hasattr(node, 'children') and node.children:
        for child in node.children:
            child.height = 0
            child.depth = 0

    # Use vlist for proper baseline handling
    node = make_v_list({
        "positionType": "firstBaseline",
        "children": [{"type": "elem", "elem": node}],
    }, options)

    # TeX treats hphantom as a math group
    return make_span(["mord"], [node], options)


def _hphantom_mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    r"""Build MathML for \hphantom."""
    from .. import build_mathml as mml

    hphantom_group = cast("HphantomParseNode", group)
    inner = mml.build_expression(ordargument(hphantom_group["body"]), options)
    phantom = MathNode("mphantom", cast(List[VirtualNode], inner))
    node = MathNode("mpadded", cast(List[VirtualNode], [phantom]))
    node.set_attribute("height", "0px")
    node.set_attribute("depth", "0px")
    return node


def _vphantom_html_builder(group: ParseNode, options: "Options") -> Any:
    r"""Build HTML for \vphantom."""
    from .. import build_html as html

    vphantom_group = cast("VphantomParseNode", group)
    inner = make_span(
        ["inner"],
        [html.build_group(vphantom_group["body"], options.with_phantom())]
    )
    fix = make_span(["fix"], [])

    return make_span(["mord", "rlap"], [inner, fix], options)


def _vphantom_mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    r"""Build MathML for \vphantom."""
    from .. import build_mathml as mml

    vphantom_group = cast("VphantomParseNode", group)
    inner = mml.build_expression(ordargument(vphantom_group["body"]), options)
    phantom = MathNode("mphantom", cast(List[VirtualNode], inner))
    node = MathNode("mpadded", cast(List[VirtualNode], [phantom]))
    node.set_attribute("width", "0px")
    return node
