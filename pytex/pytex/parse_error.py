"""Exception types for the Python KaTeX port."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


def _decorate_message(message: str, token: Optional[Any]) -> str:
    if token is None:
        return f"KaTeX parse error: {message}"

    loc = getattr(token, "loc", None)
    if loc is None or loc.start is None or loc.end is None or loc.start > loc.end:
        return f"KaTeX parse error: {message}"

    input_text = getattr(loc.lexer, "input", "")
    start = loc.start
    end = loc.end

    if start == len(input_text):
        prefix = " at end of input: "
    else:
        prefix = f" at position {start + 1}: "

    snippet = input_text[start:end]
    underlined = "".join(f"{ch}\u0332" for ch in snippet)

    left = "…" + input_text[start - 15:start] if start > 15 else input_text[:start]
    right = input_text[end:end + 15] + "…" if end + 15 < len(input_text) else input_text[end:]

    return f"KaTeX parse error: {message}{prefix}{left}{underlined}{right}"


@dataclass
class ParseError(Exception):
    raw_message: str
    token: Optional[Any] = None

    def __post_init__(self) -> None:
        self.message = _decorate_message(self.raw_message, self.token)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message
