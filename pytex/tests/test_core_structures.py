"""Tests for core structural helpers: errors, DOM/MathML trees, units, and locations.

These focus on modules that are small but widely used across the
rendering pipeline, providing good coverage gains with low risk.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pytest  # type: ignore[import-not-found]

from pytex.dom_tree import (
    Anchor,
    DomNode,
    Img,
    LineNode,
    PathNode,
    Span,
    SvgNode,
    SymbolNode,
    assert_span,
    assert_symbol_dom_node,
    create_class,
)
from pytex.mathml_tree import MathNode, SpaceNode, TextNode
from pytex.options import Options
from pytex.parse_error import ParseError
from pytex.source_location import SourceLocation
from pytex.style import Style
from pytex.token import Token
from pytex.tree import DocumentFragment
from pytex.units import Measurement, calculate_size, make_em, valid_unit


# ---------------------------------------------------------------------------
# ParseError and SourceLocation / Token
# ---------------------------------------------------------------------------


@dataclass
class _DummyLexer:
    input: str


def test_parse_error_without_token_and_with_invalid_loc() -> None:
    # No token: simple prefix only.
    err = ParseError("simple")
    assert str(err).startswith("KaTeX parse error: simple")

    # Token with invalid loc (start > end) should fall back to plain message.
    lexer = _DummyLexer("abcdef")
    bad_loc = SourceLocation(lexer, 5, 2)
    bad_token = Token("x", bad_loc)
    err2 = ParseError("bad", bad_token)
    assert str(err2).startswith("KaTeX parse error: bad")
    assert "at position" not in str(err2)


def test_parse_error_with_position_and_end_of_input() -> None:
    lexer = _DummyLexer("0123456789")

    # Middle of input: should report a position.
    loc = SourceLocation(lexer, 2, 4)
    token = Token("x", loc)
    err = ParseError("problem", token)
    msg = str(err)
    assert "KaTeX parse error: problem" in msg
    assert "at position 3" in msg

    # End of input: special wording.
    end_loc = SourceLocation(lexer, len(lexer.input), len(lexer.input))
    end_token = Token("y", end_loc)
    err_end = ParseError("at end", end_token)
    msg_end = str(err_end)
    assert "KaTeX parse error: at end" in msg_end
    assert "at end of input" in msg_end


def test_source_location_range_and_token_range() -> None:
    lexer = _DummyLexer("abcdef")
    loc1 = SourceLocation(lexer, 1, 2)
    loc2 = SourceLocation(lexer, 3, 4)

    class _LocHolder:
        def __init__(self, loc: Optional[SourceLocation]):
            self.loc = loc

    first = _LocHolder(loc1)
    second = _LocHolder(loc2)

    # Normal case: combined range uses first.start and second.end.
    combined = SourceLocation.range(first, second)
    assert combined is not None
    assert combined.start == 1
    assert combined.end == 4

    # Second is None: propagate first.loc.
    combined2 = SourceLocation.range(first, None)
    assert combined2 is loc1

    # Mismatched lexers or missing locs -> None.
    other_lexer = _DummyLexer("xyz")
    first_mismatch = _LocHolder(SourceLocation(other_lexer, 0, 1))
    assert SourceLocation.range(first_mismatch, second) is None
    assert SourceLocation.range(_LocHolder(None), second) is None

    # Token.range delegates to SourceLocation.range.
    t1 = Token("a", loc1)
    t2 = Token("b", loc2)
    t3 = t1.range(t2, "ab")
    assert t3.text == "ab"
    assert t3.loc is not None
    assert t3.loc.start == 1
    assert t3.loc.end == 4


# ---------------------------------------------------------------------------
# Dom tree helpers
# ---------------------------------------------------------------------------


def test_create_class_and_add_class_helpers() -> None:
    span = Span()
    span.add_class("foo")
    span.add_class("foo")  # duplicate should be ignored
    span.add_class("bar")
    assert span.has_class("foo") is True
    assert span.has_class("baz") is False

    class_str = create_class(["foo", "", "bar"])
    assert class_str == "foo bar"


def test_set_attribute_and_invalid_attribute_name() -> None:
    node = Span()
    node.set_attribute("data-test", "value")
    assert node.attributes["data-test"] == "value"

    # Attribute names containing spaces are rejected.
    with pytest.raises(ParseError):
        node.set_attribute("bad name", "x")


def test_span_anchor_img_and_symbol_markup() -> None:
    # Span with classes, styles, and attributes.
    span = Span(classes=["cls"], style={"backgroundColor": "red"})
    span.set_attribute("data-x", "1&2")
    child = SymbolNode(text="A", italic=0.2)
    span.children.append(child)
    markup = span.to_markup()
    assert "class=\"cls" in markup
    assert "background-color:red;" in markup
    assert "data-x=\"1&amp;2\"" in markup
    assert "A" in markup

    # Anchor should default href and wrap children.
    a = Anchor(children=[Span()])
    markup_a = a.to_markup()
    assert "<a" in markup_a
    assert "href=\"#\"" in markup_a

    # Img escapes src/alt and emits style if provided.
    img = Img(src="<img>", alt='"alt"', style={"borderRadius": "1em"})
    markup_img = img.to_markup()
    assert "&lt;img&gt;" in markup_img
    assert "alt=\"&quot;alt&quot;\"" in markup_img
    assert "border-radius:1em;" in markup_img

    # SymbolNode without classes/styles renders bare text.
    bare = SymbolNode(text="x")
    assert bare.to_markup() == "x"


def test_svg_and_path_and_line_nodes() -> None:
    path = PathNode(path_data="M0 0L1 1")
    svg = SvgNode(children=[path])
    svg.set_attribute("width", "1em")
    markup_svg = svg.to_markup()
    assert markup_svg.startswith("<svg")
    assert "<path" in markup_svg
    assert "width=\"1em\"" in markup_svg

    line = LineNode()
    line.set_attribute("x1", "0")
    line.set_attribute("x2", "1")
    markup_line = line.to_markup()
    assert markup_line.startswith("<line")
    assert "x1=\"0\"" in markup_line


def test_assert_symbol_dom_node_and_assert_span() -> None:
    sym = SymbolNode(text="z")
    sp = Span()

    assert assert_symbol_dom_node(sym) is sym
    assert assert_span(sp) is sp

    with pytest.raises(TypeError):
        assert_symbol_dom_node(sp)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        assert_span(sym)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# MathML tree and document fragments
# ---------------------------------------------------------------------------


def test_mathml_text_and_math_node_to_markup_and_text() -> None:
    t1 = TextNode("alpha")
    t2 = TextNode("&beta")
    node = MathNode("math", children=[t1, t2])
    node.set_attribute("aria-label", "example")
    node.classes.append("cls")

    markup = node.to_markup()
    assert markup.startswith("<math")
    assert "aria-label=\"example\"" in markup
    assert "class=\"cls\"" in markup
    # The '&' in text must be escaped.
    assert "&amp;beta" in markup

    # to_text should concatenate child text.
    assert node.to_text() == "alpha&beta"
    assert node.get_attribute("missing") is None


def test_mathml_space_node_markup_and_text() -> None:
    # Width in the thin-space special range.
    thin = SpaceNode(0.055555)
    assert thin.to_markup() == "<mtext>\u200a</mtext>"

    # Any other width produces a normal mspace.
    wide = SpaceNode(0.1)
    markup = wide.to_markup()
    assert markup.startswith("<mspace")
    assert "width=\"" in markup
    assert wide.to_text() == " "


def test_document_fragment_to_markup_and_text() -> None:
    class ChildOnlyMarkup:
        def to_markup(self) -> str:
            return "<mrow/>"

    class ChildWithText:
        def to_markup(self) -> str:
            return "<mi>a</mi>"

        def to_text(self) -> str:
            return "a"

    frag = DocumentFragment(children=[ChildOnlyMarkup(), ChildWithText()])
    assert frag.to_markup() == "<mrow/><mi>a</mi>"
    assert frag.to_text() == "a"
    assert frag.has_class("anything") is False


# ---------------------------------------------------------------------------
# Units and size calculation
# ---------------------------------------------------------------------------


def test_valid_unit_and_make_em() -> None:
    assert valid_unit("pt") is True
    assert valid_unit("em") is True
    assert valid_unit("unknown") is False

    em = make_em(1.23456)
    assert em.endswith("em")
    assert em.startswith("1.2346")


def test_calculate_size_absolute_and_relative_units() -> None:
    base_opts = Options(style=Style.TEXT)

    # Absolute units routed through PT_PER_UNIT.
    size_pt = calculate_size({"number": 10.0, "unit": "pt"}, base_opts)
    assert size_pt > 0

    # mu uses cssEmPerMu directly.
    size_mu = calculate_size({"number": 2.0, "unit": "mu"}, base_opts)
    assert size_mu > 0

    # ex/em when style is not tight use xHeight/quad directly.
    size_ex = calculate_size({"number": 1.0, "unit": "ex"}, base_opts)
    size_em = calculate_size({"number": 1.0, "unit": "em"}, base_opts)
    assert size_ex > 0
    assert size_em > 0

    # Tight styles should use text style metrics and adjust by size multiplier.
    tight_opts = Options(style=Style.SCRIPT)
    size_ex_tight = calculate_size({"number": 1.0, "unit": "ex"}, tight_opts)
    assert size_ex_tight > 0


def test_calculate_size_invalid_unit_raises() -> None:
    opts = Options(style=Style.TEXT)
    with pytest.raises(ParseError):
        calculate_size({"number": 1.0, "unit": "foo"}, opts)
