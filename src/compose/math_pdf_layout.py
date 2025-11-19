"""Tiny math layout helpers for the PDF backend.

This module defines a minimal box model and parser for a very small
subset of LaTeX math (superscripts and simple fractions). It is
intended as a proof-of-concept for vector-like math drawing in the PDF
renderer and is *not* a general LaTeX math parser.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from pytex.font_metrics import (
        SIGMAS_AND_XIS,
        get_character_metrics,
        get_global_metrics,
        load_metrics,
    )
    from pytex.font_metrics_data import FONT_METRICS_DATA
except Exception:
    get_character_metrics = None
    get_global_metrics = None
    load_metrics = None
    SIGMAS_AND_XIS = {}
    FONT_METRICS_DATA = {}

_METRICS_INITIALIZED = False
_DEFAULT_METRIC_FONT = "Main-Regular"
_DEFAULT_GLOBAL_SIZE = 5


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


@dataclass
class SqrtBox(MathBox):
    body: MathBox


@dataclass
class BoxMetrics:
    """Approximate layout metrics for a MathBox.

    height/depth are measured relative to the baseline. These are rough
    heuristics intended for basic line height and spacing decisions, not
    pixel-perfect layout.
    """

    width: float
    height: float  # above baseline
    depth: float   # below baseline


def _ensure_pytex_metrics() -> None:
    global _METRICS_INITIALIZED
    if _METRICS_INITIALIZED:
        return
    if load_metrics and FONT_METRICS_DATA:
        try:
            load_metrics(FONT_METRICS_DATA)
        except Exception:
            pass
    _METRICS_INITIALIZED = True


def _get_global_metrics_for_size(size: int):
    if get_global_metrics is None:
        return None
    _ensure_pytex_metrics()
    try:
        return get_global_metrics(size)
    except Exception:
        return None


def _em_to_units(value: float, font_size: int) -> float:
    return value * font_size


def _symbol_box_from_text(text: str) -> SymbolBox:
    return SymbolBox(text=text)


def _box_from_pytex_node(node: Any) -> MathBox | None:
    if not isinstance(node, dict):
        return None

    node_type = node.get("type")

    if node_type in {"mathord", "textord", "atom", "spacing"}:
        text = str(node.get("text", "")).strip()
        return SymbolBox(text=text) if text else None

    if node_type in {"ordgroup", "mclass"}:
        body: list[Any] = node.get("body") or []
        boxes: list[MathBox] = []
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

    if node_type == "sqrt":
        body_node = node.get("body")
        body_box = _box_from_pytex_node(body_node) if body_node else None
        if body_box is not None:
            return SqrtBox(body=body_box)

    if node_type == "delimsizing":
        delim = str(node.get("delim", "")).strip()
        return SymbolBox(text=delim) if delim else None

    return None


def parse_latex_to_box(expr: str) -> MathBox | None:
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

    # pytex parse_tree returns a list of nodes. For simple expressions,
    # we try to convert the first node. If it's an unparsed LaTeX command
    # (SymbolBox with backslash), fall through to the string parser.
    if tree and isinstance(tree, list) and len(tree) > 0:
        root_box = _box_from_pytex_node(tree[0])
        if root_box is not None:
            # If pytex returned an unparsed command (e.g., \frac as a symbol),
            # fall through to the string-based parser
            if isinstance(root_box, SymbolBox) and root_box.text.startswith("\\"):
                pass  # Fall through to fallback parser
            else:
                return root_box

    # --- Fallback: tiny string-based parser ---------------------------

    if s.startswith(r"\frac"):
        if not (s.startswith(r"\frac{") and "}{" in s and s.endswith("}")):
            return None
        try:
            inner = s[len(r"\frac{") : -1]
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
    if isinstance(box, SqrtBox):
        return f"√({_flatten_text(box.body)})"
    if isinstance(box, FractionBox):
        return f"({_flatten_text(box.numerator)})/({_flatten_text(box.denominator)})"
    return ""


def measure_math_box(pdf, box: MathBox, font_family: str, font_size: int) -> BoxMetrics:
    """Return approximate width/height/depth metrics for a MathBox.

    This uses the same rough assumptions as draw_math_box. All values
    are in the PDF coordinate system (matching FPDF units).
    """

    # Baseline text metrics: these are intentionally simplistic.
    def _text_metrics(text: str, size: int) -> BoxMetrics:
        if not text:
            return BoxMetrics(width=0.0, height=0.0, depth=0.0)
        pdf.set_font(font_family, size=size)
        width = pdf.get_string_width(text)
        if get_character_metrics is None:
            height = 0.8 * size
            depth = 0.2 * size
            return BoxMetrics(width=width, height=height, depth=depth)
        _ensure_pytex_metrics()
        max_height_em = 0.0
        max_depth_em = 0.0
        for ch in text:
            try:
                metrics = get_character_metrics(ch, _DEFAULT_METRIC_FONT, "math")
            except Exception:
                metrics = None
            if not metrics:
                continue
            max_height_em = max(max_height_em, float(metrics.get("height", 0.0)))
            max_depth_em = max(max_depth_em, float(metrics.get("depth", 0.0)))
        if max_height_em == 0.0 and max_depth_em == 0.0:
            height = 0.8 * size
            depth = 0.2 * size
        else:
            height = max_height_em * size
            depth = max_depth_em * size
        return BoxMetrics(width=width, height=height, depth=depth)

    if isinstance(box, SymbolBox):
        return _text_metrics(box.text, font_size)

    if isinstance(box, SuperBox):
        base = measure_math_box(pdf, box.base, font_family, font_size)
        sup_size = max(int(font_size * 0.7), 1)
        sup = measure_math_box(pdf, box.superscript, font_family, sup_size)
        width = base.width + 0.5 + sup.width
        global_metrics = _get_global_metrics_for_size(_DEFAULT_GLOBAL_SIZE)
        if global_metrics:
            sup_drop = float(global_metrics.get("supDrop", 0.0))
            sup_shift = _em_to_units(sup_drop, font_size)
            height = max(base.height, base.height + sup_shift + sup.height)
            depth = max(base.depth, sup.depth)
        else:
            height = max(base.height, base.height + 0.5 * font_size + sup.height)
            depth = max(base.depth, sup.depth)
        return BoxMetrics(width=width, height=height, depth=depth)

    if isinstance(box, SubBox):
        base = measure_math_box(pdf, box.base, font_family, font_size)
        sub_size = max(int(font_size * 0.7), 1)
        sub = measure_math_box(pdf, box.subscript, font_family, sub_size)
        width = base.width + 0.5 + sub.width
        global_metrics = _get_global_metrics_for_size(_DEFAULT_GLOBAL_SIZE)
        if global_metrics:
            sub_drop = float(global_metrics.get("subDrop", 0.0))
            sub_shift = _em_to_units(sub_drop, font_size)
            height = max(base.height, sub.height)
            depth = max(base.depth, base.depth + sub_shift + sub.depth)
        else:
            height = max(base.height, sub.height)
            depth = max(base.depth, base.depth + 0.3 * font_size + sub.depth)
        return BoxMetrics(width=width, height=height, depth=depth)

    if isinstance(box, SupSubBox):
        base = measure_math_box(pdf, box.base, font_family, font_size)
        sub_size = max(int(font_size * 0.7), 1)
        sup_size = max(int(font_size * 0.7), 1)
        sup = measure_math_box(pdf, box.superscript, font_family, sup_size)
        sub = measure_math_box(pdf, box.subscript, font_family, sub_size)
        width = base.width + 0.5 + max(sup.width, sub.width)
        global_metrics = _get_global_metrics_for_size(_DEFAULT_GLOBAL_SIZE)
        if global_metrics:
            sup_drop = float(global_metrics.get("supDrop", 0.0))
            sub_drop = float(global_metrics.get("subDrop", 0.0))
            sup_shift = _em_to_units(sup_drop, font_size)
            sub_shift = _em_to_units(sub_drop, font_size)
            height = max(base.height, base.height + sup_shift + sup.height)
            depth = max(base.depth, base.depth + sub_shift + sub.depth)
        else:
            height = max(base.height, base.height + 0.5 * font_size + sup.height)
            depth = max(base.depth, base.depth + 0.3 * font_size + sub.depth)
        return BoxMetrics(width=width, height=height, depth=depth)

    if isinstance(box, FractionBox):
        num = measure_math_box(pdf, box.numerator, font_family, font_size)
        den = measure_math_box(pdf, box.denominator, font_family, font_size)
        width = max(num.width, den.width) + 2
        # Extra vertical space for bar and gaps.
        global_metrics = _get_global_metrics_for_size(_DEFAULT_GLOBAL_SIZE)
        if global_metrics:
            axis_height = float(global_metrics.get("axisHeight", 0.25))
            num1 = float(global_metrics.get("num1", 0.677))
            denom1 = float(global_metrics.get("denom1", 0.686))
            rule_thickness = float(global_metrics.get("defaultRuleThickness", 0.04))
            height = num.height + _em_to_units(num1 - axis_height, font_size) + _em_to_units(rule_thickness, font_size)
            depth = den.depth + _em_to_units(denom1 + axis_height, font_size) + _em_to_units(rule_thickness, font_size)
        else:
            height = num.height + 0.4 * font_size
            depth = den.depth + 0.8 * font_size
        return BoxMetrics(width=width, height=height, depth=depth)

    if isinstance(box, SqrtBox):
        body = measure_math_box(pdf, box.body, font_family, font_size)
        global_metrics = _get_global_metrics_for_size(_DEFAULT_GLOBAL_SIZE)
        if global_metrics:
            axis_height = float(global_metrics.get("axisHeight", 0.25))
            rule_thickness = float(global_metrics.get("sqrtRuleThickness", 0.04))
            extra = _em_to_units(axis_height + rule_thickness, font_size)
        else:
            extra = 0.5 * font_size
        width = body.width + font_size * 0.6
        height = body.height + extra
        depth = body.depth
        return BoxMetrics(width=width, height=height, depth=depth)

    # Fallback: treat any unknown box as plain text.
    text = _flatten_text(box)
    return _text_metrics(text, font_size)


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
        global_metrics = _get_global_metrics_for_size(_DEFAULT_GLOBAL_SIZE)
        if global_metrics:
            sup_drop = float(global_metrics.get("supDrop", 0.0))
            sup_shift = _em_to_units(sup_drop, font_size)
        else:
            sup_shift = 0.5 * font_size
        x_sup = x + base_width + 0.5
        y_sup = y - sup_shift
        pdf.text(x_sup, y_sup, sup_text)

        return base_width + 0.5 + sup_width

    if isinstance(box, SubBox):
        base_width = draw_math_box(pdf, box.base, x, y, font_family, font_size)

        sub_size = max(int(font_size * 0.7), 1)
        pdf.set_font(font_family, size=sub_size)
        sub_text = _flatten_text(box.subscript)
        sub_width = pdf.get_string_width(sub_text)
        x_sub = x + base_width + 0.5
        global_metrics = _get_global_metrics_for_size(_DEFAULT_GLOBAL_SIZE)
        if global_metrics:
            sub_drop = float(global_metrics.get("subDrop", 0.0))
            sub_shift = _em_to_units(sub_drop, font_size)
        else:
            sub_shift = 0.3 * font_size
        y_sub = y + sub_shift
        pdf.text(x_sub, y_sub, sub_text)

        return base_width + 0.5 + sub_width

    if isinstance(box, SupSubBox):
        base_width = draw_math_box(pdf, box.base, x, y, font_family, font_size)

        sup_size = max(int(font_size * 0.7), 1)
        pdf.set_font(font_family, size=sup_size)
        sup_text = _flatten_text(box.superscript)
        sup_width = pdf.get_string_width(sup_text)
        sub_size = max(int(font_size * 0.7), 1)
        pdf.set_font(font_family, size=sub_size)
        sub_text = _flatten_text(box.subscript)
        sub_width = pdf.get_string_width(sub_text)

        global_metrics = _get_global_metrics_for_size(_DEFAULT_GLOBAL_SIZE)
        if global_metrics:
            sup_drop = float(global_metrics.get("supDrop", 0.0))
            sub_drop = float(global_metrics.get("subDrop", 0.0))
            sup_shift = _em_to_units(sup_drop, font_size)
            sub_shift = _em_to_units(sub_drop, font_size)
        else:
            sup_shift = 0.5 * font_size
            sub_shift = 0.3 * font_size

        x_sup = x + base_width + 0.5
        y_sup = y - sup_shift
        pdf.text(x_sup, y_sup, sup_text)

        x_sub = x + base_width + 0.5
        y_sub = y + sub_shift
        pdf.text(x_sub, y_sub, sub_text)

        return base_width + 0.5 + max(sup_width, sub_width)

    if isinstance(box, FractionBox):
        # Very simple stacked fraction layout.
        frac_metrics = measure_math_box(pdf, box, font_family, font_size)
        num_metrics = measure_math_box(pdf, box.numerator, font_family, font_size)
        den_metrics = measure_math_box(pdf, box.denominator, font_family, font_size)
        width = frac_metrics.width

        # Numerator above the line.
        x_num = x + (width - num_metrics.width) / 2
        y_num = y - (frac_metrics.height - num_metrics.height)
        draw_math_box(pdf, box.numerator, x_num, y_num, font_family, font_size)

        # Denominator below the line.
        x_den = x + (width - den_metrics.width) / 2
        y_den = y + (frac_metrics.depth - den_metrics.depth)
        draw_math_box(pdf, box.denominator, x_den, y_den, font_family, font_size)

        # Horizontal fraction bar.
        pdf.line(x, y, x + width, y)

        return width

    if isinstance(box, SqrtBox):
        body_metrics = measure_math_box(pdf, box.body, font_family, font_size)
        sqrt_metrics = measure_math_box(pdf, box, font_family, font_size)

        root_text = "√"
        pdf.set_font(font_family, size=font_size)
        root_width = sqrt_metrics.width - body_metrics.width
        if root_width <= 0:
            root_width = pdf.get_string_width(root_text)

        x_root = x
        pdf.text(x_root, y, root_text)

        x_body = x_root + root_width
        draw_math_box(pdf, box.body, x_body, y, font_family, font_size)

        global_metrics = _get_global_metrics_for_size(_DEFAULT_GLOBAL_SIZE)
        body_top_y = y - body_metrics.height
        if global_metrics:
            axis_height = float(global_metrics.get("axisHeight", 0.25))
            y_bar = body_top_y - _em_to_units(axis_height, font_size)
        else:
            extra = sqrt_metrics.height - body_metrics.height
            y_bar = body_top_y - 0.5 * extra

        pdf.line(x_body, y_bar, x_body + body_metrics.width, y_bar)

        return sqrt_metrics.width

    # Fallback: draw as plain text.
    text = _flatten_text(box)
    pdf.set_font(font_family, size=font_size)
    pdf.text(x, y, text)
    return pdf.get_string_width(text)
