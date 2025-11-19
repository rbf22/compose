"""Token representation for the Python KaTeX port."""

from __future__ import annotations

from dataclasses import dataclass

from .source_location import SourceLocation


@dataclass
class Token:
    text: str
    loc: SourceLocation | None = None
    noexpand: bool | None = None
    treat_as_relax: bool | None = None

    def range(self, end_token: Token, text: str) -> Token:
        return Token(text, SourceLocation.range(self, end_token))


__all__ = ["Token"]
