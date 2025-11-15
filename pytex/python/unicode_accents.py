"""Mapping of Unicode combining accents to LaTeX commands."""

from __future__ import annotations

ACCENTS = {
    "\u0301": {"text": "\\'", "math": "\\acute"},
    "\u0300": {"text": "\\`", "math": "\\grave"},
    "\u0308": {"text": '\\"', "math": "\\ddot"},
    "\u0303": {"text": "\\~", "math": "\\tilde"},
    "\u0304": {"text": "\\=", "math": "\\bar"},
    "\u0306": {"text": "\\u", "math": "\\breve"},
    "\u030C": {"text": "\\v", "math": "\\check"},
    "\u0302": {"text": "\\^", "math": "\\hat"},
    "\u0307": {"text": "\\.", "math": "\\dot"},
    "\u030A": {"text": "\\r", "math": "\\mathring"},
    "\u030B": {"text": "\\H"},
    "\u0327": {"text": "\\c"},
}


__all__ = ["ACCENTS"]
