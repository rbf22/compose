"""Python port of KaTeX's functions/htmlmathml.js - HTML/MathML conditional output."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..build_common import make_fragment
from ..define_function import define_function, ordargument

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import HtmlmathmlParseNode, ParseNode


# \html@mathml - provide different content for HTML vs MathML output
define_function({
    "type": "htmlmathml",
    "names": ["\\html@mathml"],
    "props": {
        "numArgs": 2,
        "allowedInText": True,
    },
    "handler": lambda context, args: {
        "type": "htmlmathml",
        "mode": context["parser"].mode,
        "html": ordargument(args[0]),
        "mathml": ordargument(args[1]),
    },
    "html_builder": lambda group, options: _htmlmathml_html_builder(group, options),
    "mathml_builder": lambda group, options: _htmlmathml_mathml_builder(group, options),
})


def _htmlmathml_html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML using the HTML argument."""
    from .. import build_html as html

    htmlmathml_group = cast("HtmlmathmlParseNode", group)
    elements = html.build_expression(htmlmathml_group["html"], options, False)
    return make_fragment(elements)


def _htmlmathml_mathml_builder(group: ParseNode, options: "Options") -> Any:
    """Build MathML using the MathML argument."""
    from .. import build_mathml as mml

    htmlmathml_group = cast("HtmlmathmlParseNode", group)
    return mml.build_expression_row(htmlmathml_group["mathml"], options)
