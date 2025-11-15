"""Python port of KaTeX's defineMacro helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Protocol

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

    def expandMacro(self, name: str) -> Optional[List[Token]]:
        ...

    def expandMacroAsText(self, name: str) -> Optional[str]:
        ...

    def expandTokens(self, tokens: List[Token]) -> List[Token]:
        ...

    def consumeArg(self, delims: Optional[List[str]] = None) -> "MacroArg":
        ...

    def consumeArgs(self, numArgs: int) -> List[List[Token]]:
        ...

    def isDefined(self, name: str) -> bool:
        ...

    def isExpandable(self, name: str) -> bool:
        ...


@dataclass
class MacroArg:
    tokens: List[Token]
    start: Token
    end: Token


@dataclass
class MacroExpansion:
    tokens: List[Token]
    num_args: int
    delimiters: Optional[List[List[str]]] = None
    unexpandable: bool = False


MacroDefinition = str | MacroExpansion | Callable[[MacroContextInterface], str | MacroExpansion]
MacroMap = Dict[str, MacroDefinition]


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
