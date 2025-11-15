"""Python port of KaTeX's functions/cr.js - line breaks and row breaks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..build_common import make_span
from ..define_function import define_function
from ..mathml_tree import MathNode
from ..parse_node import assert_node_type
from ..units import calculate_size, make_em

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import CrParseNode, ParseNode


# Line break command (\\)
define_function({
    "type": "cr",
    "names": ["\\\\"],
    "props": {
        "numArgs": 0,
        "numOptionalArgs": 0,
        "allowedInText": True,
    },
    "handler": lambda context, args, opt_args: _cr_handler(context, args, opt_args),
    "html_builder": lambda group, options: _cr_html_builder(group, options),
    "mathml_builder": lambda group, options: _cr_mathml_builder(group, options),
})


def _cr_handler(context, args, opt_args) -> Any:
    """Handler for line break (\\) command."""
    parser = context["parser"]

    # Parse optional size argument [size]
    size = parser.parse_size_group(True) if parser.gullet.future()["text"] == "[" else None

    # Determine if this creates a new line
    new_line = (not parser.settings.display_mode or
               not parser.settings.use_strict_behavior(
                   "newLineInDisplayMode",
                   "In LaTeX, \\\\ or \\newline does nothing in display mode"))

    return {
        "type": "cr",
        "mode": parser.mode,
        "newLine": new_line,
        "size": assert_node_type(size, "size")["value"] if size else None,
    }


def _cr_html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for line breaks."""
    cr_group = cast("CrParseNode", group)
    span = make_span(["mspace"], [], options)

    if cr_group.get("newLine"):
        span.classes.append("newline")
        if cr_group.get("size"):
            span.style["marginTop"] = make_em(calculate_size(cr_group["size"], options))

    return span


def _cr_mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for line breaks."""
    cr_group = cast("CrParseNode", group)
    node = MathNode("mspace")

    if cr_group.get("newLine"):
        node.set_attribute("linebreak", "newline")
        if cr_group.get("size"):
            node.set_attribute("height", make_em(calculate_size(cr_group["size"], options)))

    return node
