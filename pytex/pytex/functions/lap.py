"""Python port of KaTeX's functions/lap.js - horizontal overlap functions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..build_common import make_span
from ..define_function import define_function
from ..mathml_tree import MathNode
from ..units import make_em

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import LapParseNode, ParseNode


# Define lap functions
define_function({
    "type": "lap",
    "names": ["\\mathllap", "\\mathrlap", "\\mathclap"],
    "props": {
        "numArgs": 1,
        "allowedInText": True,
    },
    "handler": lambda context, args, opt_args: {
        "type": "lap",
        "mode": context["parser"].mode,
        "alignment": context["funcName"][5:],  # Remove "\\math" prefix
        "body": args[0],
    },
    "html_builder": lambda group, options: _lap_html_builder(group, options),
    "mathml_builder": lambda group, options: _lap_mathml_builder(group, options),
})


def _lap_html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for lap commands."""
    from .. import build_html as html

    lap_group = cast("LapParseNode", group)
    alignment = lap_group["alignment"]

    if alignment == "clap":
        # Center alignment - special handling
        inner = make_span([], [html.build_group(lap_group["body"], options)])
        # Wrap for CSS centering
        inner = make_span(["inner"], [inner], options)
    else:
        # Left or right alignment
        inner = make_span(["inner"], [html.build_group(lap_group["body"], options)])

    fix = make_span(["fix"], [])
    node = make_span([alignment], [inner, fix], options)

    # Add strut to prevent vertical misplacement (issue #1153)
    strut = make_span(["strut"])
    strut.style["height"] = make_em(node.height + node.depth)
    if node.depth:
        strut.style["verticalAlign"] = make_em(-node.depth)
    node.children.insert(0, strut)

    # Prevent vertical misplacement when next to tall elements (issue #1234)
    node = make_span(["thinbox"], [node], options)
    return make_span(["mord", "vbox"], [node], options)


def _lap_mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for lap commands."""
    from .. import build_mathml as mml

    lap_group = cast("LapParseNode", group)
    node = MathNode("mpadded", [mml.build_group(lap_group["body"], options)])

    alignment = lap_group["alignment"]

    # Set horizontal offset
    if alignment != "rlap":
        offset = "-1" if alignment == "llap" else "-0.5"
        node.set_attribute("lspace", offset + "width")

    # Zero width to prevent affecting layout
    node.set_attribute("width", "0px")

    return node
