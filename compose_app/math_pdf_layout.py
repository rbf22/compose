"""Tiny math layout helpers for the PDF backend.

This module defines a minimal box model and parser for a very small
subset of LaTeX math (superscripts and simple fractions). It is
intended as a proof-of-concept for vector-like math drawing in the PDF
renderer and is *not* a general LaTeX math parser.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional
import sys


class MathBox:
    """Base class for math layout boxes."""


@dataclass
class SymbolBox(MathBox):
    text: str


@dataclass
class SuperBox(MathBox):
    base: MathBox
    superscript: MathBox


@dataclass
class FractionBox(MathBox):
    numerator: MathBox
    denominator: MathBox


@dataclass
class SubBox(MathBox):
    base: MathBox
    subscript: MathBox


@dataclass
class SupSubBox(MathBox):
    base: MathBox
    superscript: MathBox
    subscript: MathBox


def _symbol_box_from_text(text: str) -> SymbolBox:
    return SymbolBox(text=text)


def _box_from_pytex_node(node: Any) -> Optional[MathBox]:
    if not isinstance(node, dict):
        return None

    node_type = node.get("type")

    if node_type in {"mathord", "textord", "atom", "spacing"}:
        text = str(node.get("text", "")).strip()
        return SymbolBox(text=text) if text else None

    if node_type in {"ordgroup", "mclass"}:
        body: List[Any] = node.get("body") or []
        boxes: List[MathBox] = []
        for child in body:
            child_box = _box_from_pytex_node(child)
            if child_box is not None:
                boxes.append(child_box)
        if not boxes:
            return None
        if len(boxes) == 1:
            return boxes[0]
        text = "".join(_flatten_text(b) for b in boxes)
        return SymbolBox(text=text) if text else None

    if node_type == "supsub":
        base_node = node.get("base")
        sup_node = node.get("sup")
        sub_node = node.get("sub")

        base_box = _box_from_pytex_node(base_node) if base_node else None
        sup_box = _box_from_pytex_node(sup_node) if sup_node else None
        sub_box = _box_from_pytex_node(sub_node) if sub_node else None

        if base_box is None:
            return None
        if sup_box is not None and sub_box is not None:
            return SupSubBox(base=base_box, superscript=sup_box, subscript=sub_box)
        if sup_box is not None:
            return SuperBox(base=base_box, superscript=sup_box)
        if sub_box is not None:
            return SubBox(base=base_box, subscript=sub_box)
        return base_box

    if node_type == "genfrac" and node.get("hasBarLine"):
        numer_node = node.get("numer")
        denom_node = node.get("denom")
        numer_box = _box_from_pytex_node(numer_node) if numer_node else None
        denom_box = _box_from_pytex_node(denom_node) if denom_node else None
        if numer_box is not None and denom_box is not None:
            return FractionBox(numerator=numer_box, denominator=denom_box)

    return None


def parse_latex_to_box(expr: str) -> Optional[MathBox]:
    """Parse a tiny subset of LaTeX into a MathBox.

    We first try to use pytex's parse_tree AST for simple ``supsub`` and
    ``genfrac`` nodes. If that fails, we fall back to a minimal
    string-based parser for the same patterns.
    """

    s = expr.strip()
    if not s:
        return None

    # --- Try pytex.parse_tree first -----------------------------------
    try:
        try:
            from pytex.parse_tree import parse_tree as _parse_tree  # type: ignore[import]
            from pytex.settings import Settings as _Settings  # type: ignore[import]
        except Exception:  # pragma: no cover - best-effort fallback
            root = Path(__file__).resolve().parent.parent
            pytex_root = root / "pytex"
            if pytex_root.is_dir() and str(pytex_root) not in sys.path:
                sys.path.append(str(pytex_root))
            from pytex.parse_tree import parse_tree as _parse_tree  # type: ignore[import]
            from pytex.settings import Settings as _Settings  # type: ignore[import]

        settings = _Settings({})
        tree = _parse_tree(s, settings)
    except Exception:
        tree = None

    if tree and isinstance(tree[0], dict):
        root_box = _box_from_pytex_node(tree[0])
        if root_box is not None:
            return root_box

    # --- Fallback: tiny string-based parser ---------------------------

    if s.startswith("\\frac"):
        if not (s.startswith("\\frac{") and "}{" in s and s.endswith("}")):
            return None
        try:
            inner = s[len("\\frac{") : -1]
            num_text, den_text = inner.split("}{", 1)
        except ValueError:
            return None
        num_text = num_text.strip()
        den_text = den_text.strip()
        if not num_text or not den_text:
            return None
        return FractionBox(
            numerator=_symbol_box_from_text(num_text),
            denominator=_symbol_box_from_text(den_text),
        )

    if "^" in s:
        base_text, sup_part = s.split("^", 1)
        base_text = base_text.strip()
        sup_part = sup_part.strip()
        if not base_text or not sup_part:
            return None
        if sup_part.startswith("{") and sup_part.endswith("}"):
            sup_text = sup_part[1:-1].strip()
        else:
            sup_text = sup_part[0]
        if not sup_text:
            return None
        base_box = _symbol_box_from_text(base_text)
        sup_box = _symbol_box_from_text(sup_text)
        return SuperBox(base=base_box, superscript=sup_box)

    return None


def _flatten_text(box: MathBox) -> str:
    """Return a plain-text approximation of a MathBox tree."""

    if isinstance(box, SymbolBox):
        return box.text
    if isinstance(box, SuperBox):
        return f"{_flatten_text(box.base)}^{_flatten_text(box.superscript)}"
    if isinstance(box, SubBox):
        return f"{_flatten_text(box.base)}_{_flatten_text(box.subscript)}"
    if isinstance(box, SupSubBox):
        return (
            f"{_flatten_text(box.base)}^{_flatten_text(box.superscript)}_"
            f"{_flatten_text(box.subscript)}"
        )
    if isinstance(box, FractionBox):
        return f"({_flatten_text(box.numerator)})/({_flatten_text(box.denominator)})"
    return ""


def draw_math_box(pdf, box: MathBox, x: float, y: float, font_family: str, font_size: int) -> float:
    """Draw a MathBox into the given FPDF-like object.

    Returns the approximate width consumed, so callers can advance their
    cursor if desired. This is deliberately naive and exists only to
    validate the overall math→vector plumbing.
    """

    if isinstance(box, SymbolBox):
        pdf.set_font(font_family, size=font_size)
        pdf.text(x, y, box.text)
        return pdf.get_string_width(box.text)

    if isinstance(box, SuperBox):
        # Draw base at the given baseline.
        base_width = draw_math_box(pdf, box.base, x, y, font_family, font_size)

        # Draw superscript in a smaller font, raised above the baseline.
        sup_size = max(int(font_size * 0.7), 1)
        pdf.set_font(font_family, size=sup_size)
        sup_text = _flatten_text(box.superscript)
        sup_width = pdf.get_string_width(sup_text)
        x_sup = x + base_width + 0.5
        y_sup = y - font_size * 0.5
        pdf.text(x_sup, y_sup, sup_text)

        return base_width + 0.5 + sup_width

    if isinstance(box, SubBox):
        base_width = draw_math_box(pdf, box.base, x, y, font_family, font_size)

        sub_size = max(int(font_size * 0.7), 1)
        pdf.set_font(font_family, size=sub_size)
        sub_text = _flatten_text(box.subscript)
        sub_width = pdf.get_string_width(sub_text)
        x_sub = x + base_width + 0.5
        y_sub = y + font_size * 0.3
        pdf.text(x_sub, y_sub, sub_text)

        return base_width + 0.5 + sub_width

    if isinstance(box, SupSubBox):
        base_width = draw_math_box(pdf, box.base, x, y, font_family, font_size)

        sup_size = max(int(font_size * 0.7), 1)
        pdf.set_font(font_family, size=sup_size)
        sup_text = _flatten_text(box.superscript)
        sup_width = pdf.get_string_width(sup_text)
        x_sup = x + base_width + 0.5
        y_sup = y - font_size * 0.5
        pdf.text(x_sup, y_sup, sup_text)

        sub_size = max(int(font_size * 0.7), 1)
        pdf.set_font(font_family, size=sub_size)
        sub_text = _flatten_text(box.subscript)
        sub_width = pdf.get_string_width(sub_text)
        x_sub = x + base_width + 0.5
        y_sub = y + font_size * 0.3
        pdf.text(x_sub, y_sub, sub_text)

        return base_width + 0.5 + max(sup_width, sub_width)

    if isinstance(box, FractionBox):
        # Very simple stacked fraction layout.
        num_text = _flatten_text(box.numerator)
        den_text = _flatten_text(box.denominator)

        pdf.set_font(font_family, size=font_size)
        num_width = pdf.get_string_width(num_text)
        den_width = pdf.get_string_width(den_text)
        width = max(num_width, den_width) + 2

        # Numerator above the line.
        x_num = x + (width - num_width) / 2
        y_num = y - font_size * 0.4
        draw_math_box(pdf, box.numerator, x_num, y_num, font_family, font_size)

        # Denominator below the line.
        x_den = x + (width - den_width) / 2
        y_den = y + font_size * 0.8
        draw_math_box(pdf, box.denominator, x_den, y_den, font_family, font_size)

        # Horizontal fraction bar.
        pdf.line(x, y, x + width, y)

        return width

    # Fallback: draw as plain text.
    text = _flatten_text(box)
    pdf.set_font(font_family, size=font_size)
    pdf.text(x, y, text)
    return pdf.get_string_width(text)
