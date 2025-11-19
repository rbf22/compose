"""Python port of KaTeX's defineMacro helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from .token import Token


class MacroContextInterface(Protocol):
    mode: str

    def future(self) -> Token:
        ...

    def popToken(self) -> Token:
        ...

    def consumeSpaces(self) -> None:
        ...

    def expandOnce(self, expandableOnly: bool = False) -> int | bool:
        ...

    def expandAfterFuture(self) -> Token:
        ...

    def expandNextToken(self) -> Token:
        ...

    def expandMacro(self, name: str) -> list[Token] | None:
        ...

    def expandMacroAsText(self, name: str) -> str | None:
        ...

    def expandTokens(self, tokens: list[Token]) -> list[Token]:
        ...

    def consumeArg(self, delims: list[str] | None = None) -> MacroArg:
        ...

    def consumeArgs(self, numArgs: int) -> list[list[Token]]:
        ...

    def isDefined(self, name: str) -> bool:
        ...

    def isExpandable(self, name: str) -> bool:
        ...


@dataclass
class MacroArg:
    tokens: list[Token]
    start: Token
    end: Token


@dataclass
class MacroExpansion:
    tokens: list[Token]
    num_args: int
    delimiters: list[list[str]] | None = None
    unexpandable: bool = False


MacroDefinition = str | MacroExpansion | Callable[[MacroContextInterface], str | MacroExpansion]
MacroMap = dict[str, MacroDefinition]


_macros: MacroMap = {}


def define_macro(name: str, body: MacroDefinition) -> None:
    _macros[name] = body


def defineMacro(name: str, body: MacroDefinition) -> None:
    """Compatibility wrapper matching the original KaTeX camelCase API."""
    define_macro(name, body)


__all__ = [
    "define_macro",
    "defineMacro",
    "_macros",
    "MacroContextInterface",
    "MacroArg",
    "MacroExpansion",
]
