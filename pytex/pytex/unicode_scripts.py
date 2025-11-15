"""Unicode script metadata for the KaTeX Python port."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import chain
from typing import Optional, Tuple


@dataclass(frozen=True)
class ScriptBlock:
    name: str
    ranges: Tuple[Tuple[int, int], ...]

    def contains(self, codepoint: int) -> bool:
        return any(start <= codepoint <= end for start, end in self.ranges)


SCRIPT_DATA: Tuple[ScriptBlock, ...] = (
    ScriptBlock(
        "latin",
        (
            (0x0100, 0x024F),
            (0x0300, 0x036F),
        ),
    ),
    ScriptBlock("cyrillic", ((0x0400, 0x04FF),)),
    ScriptBlock("armenian", ((0x0530, 0x058F),)),
    ScriptBlock("brahmic", ((0x0900, 0x109F),)),
    ScriptBlock("georgian", ((0x10A0, 0x10FF),)),
    ScriptBlock(
        "cjk",
        (
            (0x3000, 0x30FF),
            (0x4E00, 0x9FAF),
            (0xFF00, 0xFF60),
        ),
    ),
    ScriptBlock("hangul", ((0xAC00, 0xD7AF),)),
)


def script_from_codepoint(codepoint: int) -> Optional[str]:
    for block in SCRIPT_DATA:
        if block.contains(codepoint):
            return block.name
    return None


_ALL_RANGES: Tuple[Tuple[int, int], ...] = tuple(chain.from_iterable(block.ranges for block in SCRIPT_DATA))


def supported_codepoint(codepoint: int) -> bool:
    for start, end in _ALL_RANGES:
        if start <= codepoint <= end:
            return True
    return False


__all__ = ["ScriptBlock", "SCRIPT_DATA", "script_from_codepoint", "supported_codepoint"]
