"""Shared type enums mirroring KaTeX's Flow types."""

from __future__ import annotations

from enum import Enum


class Mode(str, Enum):
    MATH = "math"
    TEXT = "text"


class ArgType(str, Enum):
    COLOR = "color"
    SIZE = "size"
    URL = "url"
    RAW = "raw"
    ORIGINAL = "original"
    HBOX = "hbox"
    PRIMITIVE = "primitive"
    MATH = Mode.MATH.value
    TEXT = Mode.TEXT.value


class StyleStr(str, Enum):
    TEXT = "text"
    DISPLAY = "display"
    SCRIPT = "script"
    SCRIPTSCRIPT = "scriptscript"


class BreakToken(str, Enum):
    CLOSE_BRACKET = "]"
    CLOSE_BRACE = "}"
    ENDGROUP = "\\endgroup"
    DOLLAR = "$"
    CLOSE_PAREN = "\\)"
    DOUBLE_BACKSLASH = "\\\\"
    END = "\\end"
    EOF = "EOF"


class FontVariant(str, Enum):
    BOLD = "bold"
    BOLD_ITALIC = "bold-italic"
    BOLD_SANS_SERIF = "bold-sans-serif"
    DOUBLE_STRUCK = "double-struck"
    FRAKTUR = "fraktur"
    ITALIC = "italic"
    MONOSPACE = "monospace"
    NORMAL = "normal"
    SANS_SERIF = "sans-serif"
    SANS_SERIF_BOLD_ITALIC = "sans-serif-bold-italic"
    SANS_SERIF_ITALIC = "sans-serif-italic"
    SCRIPT = "script"


__all__ = [
    "Mode",
    "ArgType",
    "StyleStr",
    "BreakToken",
    "FontVariant",
]
