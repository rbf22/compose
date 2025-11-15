"""Token representation for the Python KaTeX port."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .source_location import SourceLocation


@dataclass
class Token:
    text: str
    loc: Optional[SourceLocation] = None
    noexpand: Optional[bool] = None
    treat_as_relax: Optional[bool] = None

    def range(self, end_token: "Token", text: str) -> "Token":
        return Token(text, SourceLocation.range(self, end_token))


__all__ = ["Token"]
