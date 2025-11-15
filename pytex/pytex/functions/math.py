"""Python port of KaTeX's functions/math.js - math mode switching."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..define_function import define_function
from ..parse_error import ParseError

if TYPE_CHECKING:
    from ..parse_node import ParseNode


# Math mode delimiters - switching from text mode to math mode
define_function({
    "type": "styling",
    "names": ["\\(", "$"],
    "props": {
        "numArgs": 0,
        "allowedInText": True,
        "allowedInMath": False,
    },
    "handler": lambda context, args: _math_delimiter_handler(context, args),
})

# Closing math delimiters - check for mismatched delimiters
define_function({
    "type": "text",  # Type doesn't matter for error handling
    "names": ["\\)", "\\]"],
    "props": {
        "numArgs": 0,
        "allowedInText": True,
        "allowedInMath": False,
    },
    "handler": lambda context, args: _closing_delimiter_handler(context, args),
})


def _math_delimiter_handler(context, args) -> ParseNode:
    """Handler for opening math delimiters (\(, $)."""
    func_name = context["funcName"]
    parser = context["parser"]

    outer_mode = parser.mode
    parser.switch_mode("math")

    # Determine closing delimiter
    close = "\\)" if func_name == "\\(" else "$"

    # Parse math expression until closing delimiter
    body = parser.parse_expression(False, close)
    parser.expect(close)
    parser.switch_mode(outer_mode)

    return {
        "type": "styling",
        "mode": parser.mode,
        "style": "text",
        "body": body,
    }


def _closing_delimiter_handler(context, args) -> None:
    """Handler for closing math delimiters (\), \]) - throws error for mismatches."""
    func_name = context["funcName"]
    raise ParseError(f"Mismatched {func_name}")
