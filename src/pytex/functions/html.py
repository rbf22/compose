"""Python port of KaTeX's functions/html.js - HTML extension commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..build_common import make_span
from ..define_function import define_function, ordargument
from ..mathml_tree import MathNode
from ..parse_error import ParseError
from ..parse_node import assert_node_type

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import HtmlParseNode, ParseNode, RawParseNode


# HTML extension commands for adding attributes to math expressions
define_function({
    "type": "html",
    "names": ["\\htmlClass", "\\htmlId", "\\htmlStyle", "\\htmlData"],
    "props": {
        "numArgs": 2,
        "argTypes": ["raw", "original"],
        "allowedInText": True,
    },
    "handler": lambda context, args, opt_args: _html_handler(context, args),
    "html_builder": lambda group, options: _html_html_builder(group, options),
    "mathml_builder": lambda group, options: _html_mathml_builder(group, options),
})


def _html_handler(context: dict[str, Any], args: list[Any]) -> dict[str, Any]:
    """Handler for HTML extension commands."""
    raw_node = cast("RawParseNode", assert_node_type(args[0], "raw"))
    value = raw_node["string"]
    body = args[1]
    func_name = context["funcName"]
    parser = context["parser"]

    # Check strict mode
    if parser.settings.strict:
        parser.settings.report_nonstrict(
            "htmlExtension",
            "HTML extension is disabled on strict mode"
        )

    attributes: dict[str, str] = {}
    trust_context: dict[str, Any] | None = None

    if func_name == "\\htmlClass":
        attributes["class"] = value
        trust_context = {
            "command": "\\htmlClass",
            "class": value,
        }
    elif func_name == "\\htmlId":
        attributes["id"] = value
        trust_context = {
            "command": "\\htmlId",
            "id": value,
        }
    elif func_name == "\\htmlStyle":
        attributes["style"] = value
        trust_context = {
            "command": "\\htmlStyle",
            "style": value,
        }
    elif func_name == "\\htmlData":
        # Parse comma-separated key=value pairs
        data_pairs = value.split(",")
        for pair in data_pairs:
            if "=" not in pair:
                raise ParseError("Error parsing key-value for \\htmlData")
            key, val = pair.split("=", 1)
            attributes[f"data-{key.strip()}"] = val.strip()

        trust_context = {
            "command": "\\htmlData",
            "attributes": attributes,
        }
    else:
        raise ValueError("Unrecognized html command")

    # Security check
    if not parser.settings.is_trusted(trust_context):
        return cast(dict[str, Any], parser.format_unsupported_cmd(func_name))

    return {
        "type": "html",
        "mode": parser.mode,
        "attributes": attributes,
        "body": ordargument(body),
    }


def _html_html_builder(group: ParseNode, options: Options) -> Any:
    """Build HTML for HTML extension commands."""
    from .. import build_html as html

    html_group = cast("HtmlParseNode", group)
    elements = html.build_expression(html_group["body"], options, False)

    classes = ["enclosing"]
    if "class" in html_group["attributes"]:
        # Split class string on whitespace and add to classes
        classes.extend(html_group["attributes"]["class"].split())

    span = make_span(classes, elements, options)

    # Set other attributes
    for attr, value in html_group["attributes"].items():
        if attr != "class":
            span.set_attribute(attr, value)

    return span


def _html_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for HTML extension commands."""
    from .. import build_mathml as mml

    html_group = cast("HtmlParseNode", group)
    math = mml.build_expression_row(html_group["body"], options)
    return math
