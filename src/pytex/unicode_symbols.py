"""Generate Unicode accent mappings for Parser helpers."""

from __future__ import annotations

import unicodedata

from .unicode_accents import ACCENTS


def build_unicode_symbol_map() -> dict[str, str]:
    result: dict[str, str] = {}
    letters = (
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "αβγδεϵζηθϑικλμνξοπϖρϱςστυφϕχψωΓΔΘΛΞΠΣΥΦΨΩ"
    )

    accent_names = list(ACCENTS.keys())

    for letter in letters:
        for accent in accent_names:
            combined = letter + accent
            normalized = unicodedata.normalize("NFC", combined)
            if len(normalized) == 1:
                result[normalized] = combined
            for accent2 in accent_names:
                if accent == accent2:
                    continue
                combined2 = combined + accent2
                normalized2 = unicodedata.normalize("NFC", combined2)
                if len(normalized2) == 1:
                    result[normalized2] = combined2
    return result


UNICODE_SYMBOLS = build_unicode_symbol_map()


__all__ = ["UNICODE_SYMBOLS", "build_unicode_symbol_map"]
