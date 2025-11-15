"""Python port of KaTeX's parseTree.js - expression parsing wrapper."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .parse_error import ParseError
from .parser import Parser
from .settings import Settings
from .token import Token

if TYPE_CHECKING:
    pass


def parse_tree(to_parse: str, settings: Settings) -> list:
    """Parse an expression using a Parser and return the result."""
    if not isinstance(to_parse, str):
        raise TypeError("KaTeX can only parse string typed expression")

    parser = Parser(to_parse, settings)

    # Blank out any \df@tag to avoid spurious "Duplicate \tag" errors
    if "\\df@tag" in parser.gullet.macros.current:
        del parser.gullet.macros.current["\\df@tag"]

    tree = parser.parse()

    # Prevent a color definition from persisting between calls to katex.render().
    if "\\current@color" in parser.gullet.macros.current:
        del parser.gullet.macros.current["\\current@color"]
    if "\\color" in parser.gullet.macros.current:
        del parser.gullet.macros.current["\\color"]

    # If the input used \tag, it will set the \df@tag macro to the tag.
    # In this case, we separately parse the tag and wrap the tree.
    if parser.gullet.macros.get("\\df@tag"):
        if not settings.display_mode:
            raise ParseError("\\tag works only in display equations")
        tree = [{
            "type": "tag",
            "mode": "text",
            "body": tree,
            "tag": parser.subparse([Token("\\df@tag")]),
        }]

    return tree


__all__ = ["parse_tree"]
