"""Python port of KaTeX's functions/href.js - hyperlink handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..build_common import make_anchor
from ..define_function import define_function, ordargument
from ..parse_node import assert_node_type
from ..mathml_tree import MathNode

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode


# \href command
define_function({
    "type": "href",
    "names": ["\\href"],
    "props": {
        "numArgs": 2,
        "argTypes": ["url", "original"],
        "allowedInText": True,
    },
    "handler": lambda context, args: _href_handler(context, args, False),
    "html_builder": lambda group, options: _href_html_builder(group, options),
    "mathml_builder": lambda group, options: _href_mathml_builder(group, options),
})

# \url command
define_function({
    "type": "href",
    "names": ["\\url"],
    "props": {
        "numArgs": 1,
        "argTypes": ["url"],
        "allowedInText": True,
    },
    "handler": lambda context, args: _href_handler(context, args, True),
    "html_builder": lambda group, options: _href_html_builder(group, options),
    "mathml_builder": lambda group, options: _href_mathml_builder(group, options),
})


def _href_handler(context, args, is_url_command):
    """Handler for href and url commands."""
    parser = context["parser"]

    if is_url_command:
        # \url{url} - URL is both link target and displayed text
        href = assert_node_type(args[0], "url")["url"]
        # Create display text from URL characters
        chars = []
        for c in href:
            if c == "~":
                c = "\\textasciitilde"
            chars.append({
                "type": "textord",
                "mode": "text",
                "text": c,
            })

        body = {
            "type": "text",
            "mode": parser.mode,
            "font": "\\texttt",
            "body": chars,
        }
    else:
        # \href{url}{text} - separate URL and display text
        href = assert_node_type(args[0], "url")["url"]
        body = args[1]

    # Security check
    if not parser.settings.is_trusted({
        "command": "\\href" if not is_url_command else "\\url",
        "url": href,
    }):
        return parser.format_unsupported_cmd("\\href" if not is_url_command else "\\url")

    return {
        "type": "href",
        "mode": parser.mode,
        "href": href,
        "body": ordargument(body),
    }


def _href_html_builder(group: ParseNode, options: Options):
    """Build HTML for hyperlinks."""
    from .. import build_html as html

    elements = html.build_expression(group["body"], options, False)
    return make_anchor(group["href"], [], elements, options)


def _href_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for hyperlinks."""
    from .. import build_mathml as mml

    math = mml.build_expression_row(group["body"], options)
    if not isinstance(math, MathNode):
        math = MathNode("mrow", [math])

    math.set_attribute("href", group["href"])
    return math
