"""Python port of KaTeX's functions/char.js - character code point handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..define_function import define_function
from ..parse_error import ParseError
from ..parse_node import assert_node_type

if TYPE_CHECKING:
    from ..parse_node import OrdgroupParseNode, ParseNode, TextordParseNode


# \@char function for creating characters from Unicode code points
define_function({
    "type": "textord",
    "names": ["\\@char"],
    "props": {
        "numArgs": 1,
        "allowedInText": True,
    },
    "handler": lambda context, args, opt_args: _char_handler(context, args),
})


def _char_handler(context: dict[str, Any], args: list[ParseNode]) -> dict[str, Any]:
    r"""Handler for \@char command that creates characters from code points."""
    arg = cast("OrdgroupParseNode", assert_node_type(args[0], "ordgroup"))
    group = arg["body"]

    # Build the number string from the argument
    number_str = ""
    for node in group:
        text_node = cast("TextordParseNode", assert_node_type(node, "textord"))
        number_str += text_node["text"]

    # Parse the code point
    try:
        code = int(number_str)
    except ValueError:
        raise ParseError(f"\\@char has non-numeric argument {number_str}")

    # Validate code point range
    if code < 0 or code >= 0x10ffff:
        raise ParseError(f"\\@char with invalid code point {number_str}")

    # Convert to character
    if code <= 0xffff:
        text = chr(code)
    else:
        # Astral code point; use surrogate pairs
        code -= 0x10000
        high_surrogate = chr((code >> 10) + 0xd800)
        low_surrogate = chr((code & 0x3ff) + 0xdc00)
        text = high_surrogate + low_surrogate

    return {
        "type": "textord",
        "mode": context["parser"].mode,
        "text": text,
    }
