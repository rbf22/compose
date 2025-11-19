"""Focused tests for shared rendering helpers in pytex.build_common.

These tests aim to exercise the core helper functions that are widely
used by the HTML/MathML builders, without requiring the full parsing
pipeline.
"""

from __future__ import annotations

from typing import Any

import pytest  # type: ignore[import-not-found]

import pytex.build_common as bc
from pytex.build_common import (
    make_anchor,
    make_fragment,
    make_glue,
    make_line_span,
    make_span,
    make_svg_span,
    make_v_list,
    mathsym,
    retrieve_text_font_name,
    static_svg,
    try_combine_chars,
)
from pytex.dom_tree import Anchor, DomNode, Span, SymbolNode
from pytex.options import Options, default_options
from pytex.style import Style

# ---------------------------------------------------------------------------
# Symbol creation and combination
# ---------------------------------------------------------------------------


def _fake_metrics(_: str, __: str, ___: str) -> dict[str, float]:
    return {"height": 1.0, "depth": 0.2, "italic": 0.1, "skew": 0.0, "width": 0.5}


def test_make_symbol_applies_metrics_tight_style_and_color() -> None:
    orig = bc.get_character_metrics
    bc.get_character_metrics = _fake_metrics
    try:
        opts = Options(style=Style.SCRIPT).with_color("blue")
        sym = bc.make_symbol("x", "Main-Regular", "math", opts, classes=["mord"])
        assert isinstance(sym, SymbolNode)
        assert sym.height == pytest.approx(1.0)
        assert sym.depth == pytest.approx(0.2)
        assert "mtight" in sym.classes
        assert sym.style["color"] == "blue"
        assert sym.max_font_size == opts.size_multiplier
    finally:
        bc.get_character_metrics = orig


def test_make_symbol_suppresses_italic_in_text_mode() -> None:
    orig = bc.get_character_metrics
    bc.get_character_metrics = _fake_metrics
    try:
        opts = Options(style=Style.TEXT)
        sym = bc.make_symbol("y", "Main-Regular", "text", opts)
        # In text mode, italic should be zeroed and marginRight omitted.
        assert sym.italic == 0
        assert "marginRight" not in sym.style
    finally:
        bc.get_character_metrics = orig


def test_mathsym_uses_boldsymbol_main_and_ams_fonts() -> None:
    orig = bc.get_character_metrics
    bc.get_character_metrics = _fake_metrics
    try:
        # boldsymbol branch -> Main-Bold + "mathbf" class
        opts_bold = Options(style=Style.TEXT)
        opts_bold.font = "boldsymbol"
        bold_sym = mathsym("+", "math", opts_bold, classes=["mbin"])
        assert isinstance(bold_sym, SymbolNode)
        assert "mathbf" in bold_sym.classes

        # main font branch via value == "\\"
        opts_main = Options(style=Style.TEXT)
        main_sym = mathsym("\\", "math", opts_main)
        assert isinstance(main_sym, SymbolNode)

        # AMS branch: patch SYMBOLS to mark a value as ams.
        original_symbols = bc.SYMBOLS
        try:
            bc.SYMBOLS = {"math": {"v": {"font": "ams"}}}
            opts_ams = Options(style=Style.TEXT)
            ams_sym = mathsym("v", "math", opts_ams, classes=["mrel"])
            assert isinstance(ams_sym, SymbolNode)
            assert "amsrm" in ams_sym.classes
        finally:
            bc.SYMBOLS = original_symbols
    finally:
        bc.get_character_metrics = orig


def test_try_combine_chars_combines_and_skips_mord() -> None:
    # Symbols with matching classes/styles should combine.
    s1 = SymbolNode(text="a", height=1.0, depth=0.2)
    s2 = SymbolNode(text="b", height=0.8, depth=0.1)
    # Normalise properties that affect can_combine.
    s1.classes = ["x"]
    s2.classes = ["x"]
    s1.skew = s2.skew = 0.0
    s1.max_font_size = s2.max_font_size = 1.0
    s1.style.clear()
    s2.style.clear()

    combined: list[DomNode] = try_combine_chars([s1, s2])
    assert len(combined) == 1
    assert isinstance(combined[0], SymbolNode)
    assert combined[0].text == "ab"

    # "mord" single-class symbols should not combine.
    m1 = SymbolNode(text="x")
    m2 = SymbolNode(text="y")
    m1.classes = ["mord"]
    m2.classes = ["mord"]
    separate = try_combine_chars([m1, m2])
    assert len(separate) == 2


# ---------------------------------------------------------------------------
# Span/anchor/fragment helpers
# ---------------------------------------------------------------------------


def test_make_span_svg_span_anchor_and_fragment() -> None:
    child = SymbolNode(text="z")
    child.height = 1.0
    child.depth = 0.3
    child.max_font_size = 2.0

    span = make_span(["cls"], [child], None)
    assert isinstance(span, Span)
    assert span.height == pytest.approx(1.0)
    assert span.depth == pytest.approx(0.3)
    assert span.max_font_size == pytest.approx(2.0)

    svg_span = make_svg_span(["svg"], [child], None)
    assert svg_span.height == pytest.approx(1.0)
    assert svg_span.depth == pytest.approx(0.3)

    opts = default_options()
    line = make_line_span("overline", opts)
    assert "borderBottomWidth" in line.style

    anchor = make_anchor("/path", ["link"], [child], opts)
    assert isinstance(anchor, Anchor)
    assert anchor.attributes["href"] == "/path"
    assert anchor.height >= child.height

    fragment = make_fragment([child])
    assert fragment.height == child.height
    wrapped = bc.wrap_fragment(fragment, opts)
    assert isinstance(wrapped, Span)
    assert wrapped.children[0] is fragment


# ---------------------------------------------------------------------------
# VList and glue/static SVG helpers
# ---------------------------------------------------------------------------


def test_get_v_list_children_and_depth_and_make_v_list() -> None:
    opts = default_options()

    # individualShift branch
    elem1 = make_span([], [], opts)
    elem1.height = 1.0
    elem1.depth = 0.5
    child1: dict[str, Any] = {"type": "elem", "elem": elem1, "shift": 0.0}

    elem2 = make_span([], [], opts)
    elem2.height = 0.5
    elem2.depth = 0.2
    child2: dict[str, Any] = {"type": "elem", "elem": elem2, "shift": -0.5}

    params: dict[str, Any] = {
        "positionType": "individualShift",
        "children": [child1, child2],
    }
    children, depth = bc.get_v_list_children_and_depth(params)
    assert isinstance(children, list)
    assert depth < 0

    vlist = make_v_list({"positionType": "individualShift", "children": [child1, child2]}, opts)
    assert vlist.has_class("vlist-t")

    # top and bottom branches
    params_top: dict[str, Any] = {
        "positionType": "top",
        "positionData": 2.0,
        "children": [child1],
    }
    children_top, depth_top = bc.get_v_list_children_and_depth(params_top)
    assert children_top is params_top["children"]
    assert depth_top <= 2.0

    params_bottom: dict[str, Any] = {
        "positionType": "bottom",
        "positionData": 1.0,
        "children": [child1],
    }
    _, depth_bottom = bc.get_v_list_children_and_depth(params_bottom)
    assert depth_bottom == -1.0

    # shift and firstBaseline branches + error for invalid type
    params_shift: dict[str, Any] = {
        "positionType": "shift",
        "positionData": 0.3,
        "children": [child1],
    }
    _, depth_shift = bc.get_v_list_children_and_depth(params_shift)
    assert depth_shift < 0

    params_first: dict[str, Any] = {
        "positionType": "firstBaseline",
        "children": [child1],
    }
    _, depth_first = bc.get_v_list_children_and_depth(params_first)
    assert depth_first == -elem1.depth

    # First child must be elem.
    bad_params = {
        "positionType": "shift",
        "positionData": 0.0,
        "children": [{"type": "kern", "size": 1.0}],
    }
    with pytest.raises(ValueError):
        bc.get_v_list_children_and_depth(bad_params)

    bad_type = {
        "positionType": "unknown",
        "positionData": 0.0,
        "children": [child1],
    }
    with pytest.raises(ValueError):
        bc.get_v_list_children_and_depth(bad_type)


def test_make_glue_and_static_svg() -> None:
    opts = default_options()
    glue = make_glue({"number": 1.0, "unit": "em"}, opts)
    assert glue.has_class("mspace")
    assert "marginRight" in glue.style

    svg_span = static_svg("vec", opts)
    markup = svg_span.to_markup()
    assert "<svg" in markup
    assert "vec" in markup
    assert "width=" in markup


# ---------------------------------------------------------------------------
# Font family/name mapping
# ---------------------------------------------------------------------------


def test_retrieve_text_font_name_variants() -> None:
    assert retrieve_text_font_name("textrm", "", "") == "Main-Regular"
    assert retrieve_text_font_name("textrm", "textbf", "") == "Main-Bold"
    assert retrieve_text_font_name("textrm", "", "textit") == "Main-Italic"
    assert retrieve_text_font_name("textrm", "textbf", "textit") == "Main-BoldItalic"

    # Unknown family should be passed through.
    assert retrieve_text_font_name("custom", "", "") == "custom-Regular"
