"""Python port of KaTeX's functions/cr.js - line breaks and row breaks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast

from ..build_common import make_span
from ..define_function import define_function
from ..mathml_tree import MathNode
from ..parse_node import assert_node_type
from ..units import Measurement, calculate_size, make_em

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import CrParseNode, ParseNode, SizeParseNode


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


def _cr_handler(context: Dict[str, Any], args: List[Any], opt_args: List[Any]) -> Dict[str, Any]:
    """Handler for line break (\\) command."""
    parser = context["parser"]

    # Parse optional size argument [size].  The macro expander's future()
    # method returns a Token, so we inspect its .text attribute.
    future_tok = parser.gullet.future()
    size_node = parser.parse_size_group(True) if future_tok.text == "[" else None
    size_value: Optional[Measurement] = None
    if size_node is not None:
        size_value = cast("SizeParseNode", assert_node_type(size_node, "size"))["value"]

    # Determine if this creates a new line based on the display_mode
    # setting and strict behavior.
    new_line = (
        not parser.settings.display_mode
        or not parser.settings.use_strict_behavior(
            "newLineInDisplayMode",
            "In LaTeX, \\ or \\newline does nothing in display mode",
        )
    )

    return {
        "type": "cr",
        "mode": parser.mode,
        "newLine": new_line,
        "size": size_value,
    }


def _cr_html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for line breaks."""
    cr_group = cast("CrParseNode", group)
    span = make_span(["mspace"], [], options)

    if cr_group.get("newLine"):
        span.classes.append("newline")
        size = cr_group.get("size")
        if size is not None:
            span.style["marginTop"] = make_em(calculate_size(size, options))

    return span


def _cr_mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for line breaks."""
    cr_group = cast("CrParseNode", group)
    node = MathNode("mspace")

    if cr_group.get("newLine"):
        node.set_attribute("linebreak", "newline")
        size = cr_group.get("size")
        if size is not None:
            node.set_attribute("height", make_em(calculate_size(size, options)))

    return node
