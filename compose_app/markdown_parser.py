"""Markdown parsing wrapper built on top of mistletoe.

This module exposes a small, stable API for turning Markdown text into a
mistletoe Document AST. It is intentionally thin so that renderers can
share the same tree for HTML and, later, PDF output.
"""

from __future__ import annotations

import mistletoe


def parse_markdown(text: str) -> mistletoe.Document:
    """Parse Markdown text into a mistletoe Document AST."""

    # mistletoe.Document accepts either an iterable of lines or a single
    # string; in the latter case it splits into lines internally.
    return mistletoe.Document(text)
