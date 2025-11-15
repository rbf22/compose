"""Python port of KaTeX's Style helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Style:
    id: int
    size: int
    cramped: bool

    def sup(self) -> "Style":
        return STYLES[_SUP[self.id]]

    def sub(self) -> "Style":
        return STYLES[_SUB[self.id]]

    def frac_num(self) -> "Style":
        return STYLES[_FRAC_NUM[self.id]]

    def frac_den(self) -> "Style":
        return STYLES[_FRAC_DEN[self.id]]

    def cramp(self) -> "Style":
        return STYLES[_CRAMP[self.id]]

    def text(self) -> "Style":
        return STYLES[_TEXT[self.id]]

    def is_tight(self) -> bool:
        return self.size >= 2


D, DC, T, TC, S, SC, SS, SSC = range(8)

STYLES = (
    Style(D, 0, False),
    Style(DC, 0, True),
    Style(T, 1, False),
    Style(TC, 1, True),
    Style(S, 2, False),
    Style(SC, 2, True),
    Style(SS, 3, False),
    Style(SSC, 3, True),
)

_SUP = (S, SC, S, SC, SS, SSC, SS, SSC)
_SUB = (SC, SC, SC, SC, SSC, SSC, SSC, SSC)
_FRAC_NUM = (T, TC, S, SC, SS, SSC, SS, SSC)
_FRAC_DEN = (TC, TC, SC, SC, SSC, SSC, SSC, SSC)
_CRAMP = (DC, DC, TC, TC, SC, SC, SSC, SSC)
_TEXT = (D, DC, T, TC, T, TC, T, TC)


DEFAULT_STYLES: Dict[str, Style] = {
    "display": STYLES[D],
    "text": STYLES[T],
    "script": STYLES[S],
    "scriptscript": STYLES[SS],
}


__all__ = ["Style", "STYLES", "DEFAULT_STYLES"]
