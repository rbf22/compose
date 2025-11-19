"""Source location utilities for lexer/parser error reporting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class LexerInterface(Protocol):
    input: str


class Locatable(Protocol):
    loc: SourceLocation | None


@dataclass(frozen=True)
class SourceLocation:
    lexer: LexerInterface
    start: int
    end: int

    @staticmethod
    def range(first: Locatable | None, second: Locatable | None) -> SourceLocation | None:
        if second is None:
            return first.loc if first else None
        if (
            first is None
            or first.loc is None
            or second.loc is None
            or first.loc.lexer is not second.loc.lexer
        ):
            return None
        return SourceLocation(first.loc.lexer, first.loc.start, second.loc.end)


__all__ = ["SourceLocation", "LexerInterface", "Locatable"]
