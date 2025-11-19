"""Support for Unicode mathematical alphanumeric symbols (U+1D400–U+1D7FF)."""

from __future__ import annotations

from .parse_error import ParseError

# Each entry: (math CSS class, text CSS class, font name)
WIDE_LATIN_LETTER_DATA: list[tuple[str, str, str]] = [
    ("mathbf", "textbf", "Main-Bold"),  # A-Z bold upright
    ("mathbf", "textbf", "Main-Bold"),  # a-z bold upright
    ("mathnormal", "textit", "Math-Italic"),  # A-Z italic
    ("mathnormal", "textit", "Math-Italic"),  # a-z italic
    ("boldsymbol", "boldsymbol", "Main-BoldItalic"),  # A-Z bold italic
    ("boldsymbol", "boldsymbol", "Main-BoldItalic"),  # a-z bold italic
    ("mathscr", "textscr", "Script-Regular"),  # A-Z script
    ("", "", ""),  # a-z script (no font)
    ("", "", ""),  # A-Z bold script (no font)
    ("", "", ""),  # a-z bold script (no font)
    ("mathfrak", "textfrak", "Fraktur-Regular"),  # A-Z Fraktur
    ("mathfrak", "textfrak", "Fraktur-Regular"),  # a-z Fraktur
    ("mathbb", "textbb", "AMS-Regular"),  # A-Z double-struck
    ("mathbb", "textbb", "AMS-Regular"),  # k double-struck
    ("mathboldfrak", "textboldfrak", "Fraktur-Regular"),  # A-Z bold Fraktur
    ("mathboldfrak", "textboldfrak", "Fraktur-Regular"),  # a-z bold Fraktur
    ("mathsf", "textsf", "SansSerif-Regular"),  # A-Z sans-serif
    ("mathsf", "textsf", "SansSerif-Regular"),  # a-z sans-serif
    ("mathboldsf", "textboldsf", "SansSerif-Bold"),  # A-Z bold sans-serif
    ("mathboldsf", "textboldsf", "SansSerif-Bold"),  # a-z bold sans-serif
    ("mathitsf", "textitsf", "SansSerif-Italic"),  # A-Z italic sans-serif
    ("mathitsf", "textitsf", "SansSerif-Italic"),  # a-z italic sans-serif
    ("", "", ""),  # A-Z bold italic sans (no font)
    ("", "", ""),  # a-z bold italic sans (no font)
    ("mathtt", "texttt", "Typewriter-Regular"),  # A-Z monospace
    ("mathtt", "texttt", "Typewriter-Regular"),  # a-z monospace
]

WIDE_NUMERAL_DATA: list[tuple[str, str, str]] = [
    ("mathbf", "textbf", "Main-Bold"),  # 0-9 bold
    ("", "", ""),  # 0-9 double-struck (no font)
    ("mathsf", "textsf", "SansSerif-Regular"),  # 0-9 sans-serif
    ("mathboldsf", "textboldsf", "SansSerif-Bold"),  # 0-9 bold sans-serif
    ("mathtt", "texttt", "Typewriter-Regular"),  # 0-9 monospace
]


def wide_character_font(wide_char: str, mode: str) -> tuple[str, str]:
    if len(wide_char) < 2:
        raise ParseError("Wide character must be a surrogate pair")

    high = ord(wide_char[0])
    low = ord(wide_char[1])
    code_point = ((high - 0xD800) * 0x400) + (low - 0xDC00) + 0x10000

    column = 0 if mode == "math" else 1

    if 0x1D400 <= code_point < 0x1D6A4:
        index = (code_point - 0x1D400) // 26
        font_name, css_class = WIDE_LATIN_LETTER_DATA[index][2], WIDE_LATIN_LETTER_DATA[index][column]
        return font_name, css_class

    if 0x1D7CE <= code_point <= 0x1D7FF:
        index = (code_point - 0x1D7CE) // 10
        font_name, css_class = WIDE_NUMERAL_DATA[index][2], WIDE_NUMERAL_DATA[index][column]
        return font_name, css_class

    if code_point in (0x1D6A5, 0x1D6A6):
        font_name, css_class = WIDE_LATIN_LETTER_DATA[0][2], WIDE_LATIN_LETTER_DATA[0][column]
        return font_name, css_class

    if 0x1D6A6 < code_point < 0x1D7CE:
        return "", ""

    raise ParseError(f"Unsupported character: {wide_char}")


__all__ = ["wide_character_font"]
