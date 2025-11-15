"""Python port of KaTeX's functions/includegraphics.js - image inclusion."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..define_function import define_function
from ..parse_error import ParseError
from ..parse_node import assert_node_type
from ..units import calculate_size, valid_unit, make_em

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import IncludegraphicsParseNode, ParseNode


def size_data(size_str: str):
    """Parse size specification for includegraphics."""
    import re

    # Check if it's just a number (default unit is bp)
    if re.match(r'^[-+]? *(\d+(\.\d*)?|\.\d+)$', size_str):
        return {"number": float(size_str), "unit": "bp"}

    # Parse number with unit
    match = re.match(r'([-+]?) *(\d+(?:\.\d*)?|\.\d+) *([a-z]{2})', size_str)
    if not match:
        raise ParseError(f"Invalid size: '{size_str}' in \\includegraphics")

    number = float(match.group(1) + match.group(2))
    unit = match.group(3)

    data = {"number": number, "unit": unit}
    if not valid_unit(data):
        raise ParseError(f"Invalid unit: '{unit}' in \\includegraphics.")

    return data


# \includegraphics command
define_function({
    "type": "includegraphics",
    "names": ["\\includegraphics"],
    "props": {
        "numArgs": 1,
        "numOptionalArgs": 1,
        "argTypes": ["raw", "url"],
        "allowedInText": False,
    },
    "handler": lambda context, args, opt_args: _includegraphics_handler(context, args, opt_args),
    "html_builder": lambda group, options: _includegraphics_html_builder(group, options),
    "mathml_builder": lambda group, options: _includegraphics_mathml_builder(group, options),
})


def _includegraphics_handler(context, args, opt_args) -> ParseNode:
    """Handler for \includegraphics command."""
    # Default values
    width = {"number": 0, "unit": "em"}
    height = {"number": 0.9, "unit": "em"}  # Character-sized
    totalheight = {"number": 0, "unit": "em"}
    alt = ""

    # Parse optional arguments
    if opt_args and opt_args[0]:
        attribute_str = assert_node_type(opt_args[0], "raw")["string"]
        attributes = attribute_str.split(",")

        for attr in attributes:
            if "=" in attr:
                key, value = attr.split("=", 1)
                key = key.strip()
                value = value.strip()

                if key == "alt":
                    alt = value
                elif key == "width":
                    width = size_data(value)
                elif key == "height":
                    height = size_data(value)
                elif key == "totalheight":
                    totalheight = size_data(value)
                else:
                    raise ParseError(f"Invalid key: '{key}' in \\includegraphics.")

    # Get source URL
    src = assert_node_type(args[0], "url")["url"]

    # Set default alt text if not provided
    if not alt:
        # Use filename without path or extension
        alt = src.split('/')[-1].split('\\')[-1]  # Handle both / and \
        alt = alt.rsplit('.', 1)[0] if '.' in alt else alt

    # Security check
    if not context["parser"].settings.is_trusted({
        "command": "\\includegraphics",
        "url": src,
    }):
        return context["parser"].format_unsupported_cmd("\\includegraphics")

    return {
        "type": "includegraphics",
        "mode": context["parser"].mode,
        "alt": alt,
        "width": width,
        "height": height,
        "totalheight": totalheight,
        "src": src,
    }


def _includegraphics_html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for includegraphics."""
    ig_group = cast("IncludegraphicsParseNode", group)
    height = calculate_size(ig_group["height"], options)
    depth = 0

    if ig_group["totalheight"]["number"] > 0:
        depth = calculate_size(ig_group["totalheight"], options) - height

    width = 0
    if ig_group["width"]["number"] > 0:
        width = calculate_size(ig_group["width"], options)

    style = {"height": make_em(height + depth)}
    if width > 0:
        style["width"] = make_em(width)
    if depth > 0:
        style["verticalAlign"] = make_em(-depth)

    # Create image node
    from ..dom_tree import Img
    node = Img(ig_group["src"], ig_group["alt"], style)
    node.height = height
    node.depth = depth

    return node


def _includegraphics_mathml_builder(group: ParseNode, options: "Options") -> Any:
    """Build MathML for includegraphics."""
    from ..mathml_tree import MathNode

    ig_group = cast("IncludegraphicsParseNode", group)
    node = MathNode("mglyph", [])
    node.set_attribute("alt", ig_group["alt"])
    node.set_attribute("src", ig_group["src"])

    height = calculate_size(ig_group["height"], options)
    depth = 0

    if ig_group["totalheight"]["number"] > 0:
        depth = calculate_size(ig_group["totalheight"], options) - height
        node.set_attribute("valign", make_em(-depth))

    node.set_attribute("height", make_em(height + depth))

    if ig_group["width"]["number"] > 0:
        width = calculate_size(ig_group["width"], options)
        node.set_attribute("width", make_em(width))

    return node
