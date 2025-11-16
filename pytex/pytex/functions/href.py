"""Python port of KaTeX's functions/href.js - hyperlink handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, cast

from ..build_common import make_anchor
from ..define_function import define_function, ordargument
from ..parse_node import assert_node_type
from ..mathml_tree import MathNode

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import HrefParseNode, ParseNode, UrlParseNode


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


def _href_handler(context: Dict[str, Any], args: List[Any], is_url_command: bool) -> Dict[str, Any]:
    r"""Handler for \href and \url commands."""
    parser = context["parser"]

    if is_url_command:
        # \url{url} - URL is both link target and displayed text
        url_node = cast("UrlParseNode", assert_node_type(args[0], "url"))
        href = url_node["url"]
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
        url_node = cast("UrlParseNode", assert_node_type(args[0], "url"))
        href = url_node["url"]
        body = args[1]

    # Security check
    if not parser.settings.is_trusted({
        "command": "\\href" if not is_url_command else "\\url",
        "url": href,
    }):
        return cast(Dict[str, Any], parser.format_unsupported_cmd("\\href" if not is_url_command else "\\url"))

    return {
        "type": "href",
        "mode": parser.mode,
        "href": href,
        "body": ordargument(body),
    }


def _href_html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for hyperlinks."""
    from .. import build_html as html

    href_group = cast("HrefParseNode", group)
    elements = html.build_expression(href_group["body"], options, False)
    return make_anchor(href_group["href"], [], elements, options)


def _href_mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for hyperlinks."""
    from .. import build_mathml as mml

    href_group = cast("HrefParseNode", group)
    math = mml.build_expression_row(href_group["body"], options)
    math.set_attribute("href", href_group["href"])
    return math
