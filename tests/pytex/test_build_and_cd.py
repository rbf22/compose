"""Tests for build_tree/build_html/build_mathml and CD environment helpers.

These tests exercise small, well-defined slices of the rendering
pipeline without relying on the full KaTeX parser. They construct
minimal parse-node dictionaries by hand and verify that the HTML/MathML
builders and CD label helpers behave as expected.
"""

from __future__ import annotations

from typing import Any

import pytest  # type: ignore[import-not-found]

from pytex.build_tree import build_html_tree, build_tree, display_wrap, options_from_settings
from pytex.dom_tree import DomSpan
from pytex.options import default_options
from pytex.settings import Settings
from pytex.style import Style


@pytest.fixture(scope="session", autouse=True)
def _load_font_metrics_and_register_builders() -> None:
    """Ensure font metrics and basic symbol builders are available.

    build_html/build_mathml rely on font metrics and on the mathord/textord
    builders from symbolsOrd. We load metrics and import the module once
    for the whole test session to avoid repeating work.
    """

    from pytex.font_metrics import load_metrics
    from pytex.font_metrics_data import FONT_METRICS_DATA

    load_metrics(FONT_METRICS_DATA)

    # Importing this module registers mathord/textord builders via
    # define_function_builders.
    import pytex.functions.symbolsOrd  # noqa: F401


# ---------------------------------------------------------------------------
# build_html / build_mathml / build_tree
# ---------------------------------------------------------------------------


def _simple_textord_node(text: str = "x") -> dict[str, Any]:
    return {"type": "textord", "mode": "math", "text": text}


def test_build_html_with_simple_textord() -> None:
    from pytex.build_html import build_html

    opts = default_options()
    tree: list[dict[str, Any]] = [_simple_textord_node("x")]

    html_node = build_html(tree, opts)
    markup = html_node.to_markup()

    # We expect a katex-html span containing the text content.
    assert "katex-html" in markup
    assert "x" in markup


def test_build_mathml_with_simple_textord() -> None:
    from pytex.build_mathml import build_mathml

    opts = default_options()
    tree: list[dict[str, Any]] = [_simple_textord_node("y")]

    span = build_mathml(tree, "y", opts, is_display_mode=False, for_mathml_only=True)
    markup = span.to_markup()

    # Expect a MathML <math> element wrapped in a span.
    assert "<math" in markup
    assert "y" in markup


def test_build_tree_html_output() -> None:
    tree: list[dict[str, Any]] = [_simple_textord_node("z")]  # minimal parse tree
    settings = Settings({"output": "html", "display_mode": False})

    node = build_tree(tree, "z", settings)
    markup = node.to_markup()

    # build_tree should produce a katex wrapper with HTML-only content.
    assert "katex" in markup
    assert "z" in markup


def test_build_tree_mathml_and_html_combined() -> None:
    tree: list[dict[str, Any]] = [_simple_textord_node("w")]
    # Default output is htmlAndMathml
    settings = Settings({"display_mode": True})

    node = build_tree(tree, "w", settings)
    markup = node.to_markup()

    # Combined output should contain both MathML and HTML fragments.
    assert "katex-mathml" in markup
    assert "katex-html" in markup
    assert "w" in markup


def test_options_from_settings_and_display_wrap() -> None:
    settings = Settings({
        "display_mode": True,
        "output": "html",
        "leqno": True,
        "fleqn": True,
        "max_size": 10.0,
        "min_rule_thickness": 0.2,
    })

    opts = options_from_settings(settings)
    assert opts.style is Style.DISPLAY
    assert opts.max_size == 10.0
    assert opts.min_rule_thickness == 0.2

    # Verify display_wrap adds appropriate classes in display mode.
    from pytex.build_common import make_span

    base: DomSpan = make_span([], [])
    wrapped = display_wrap(base, settings)
    assert wrapped.has_class("katex-display")
    assert wrapped.has_class("leqno")
    assert wrapped.has_class("fleqn")


def test_build_html_tree_matches_build_html() -> None:
    from pytex.build_html import build_html

    tree: list[dict[str, Any]] = [_simple_textord_node("q")]  # minimal tree
    settings = Settings({"output": "html", "display_mode": False})

    # build_html_tree should wrap build_html with katex and optional display.
    direct = build_html(tree, default_options())
    wrapped = build_html_tree(tree, "q", settings)

    direct_markup = direct.to_markup()
    wrapped_markup = wrapped.to_markup()

    assert "katex-html" in direct_markup
    assert "katex" in wrapped_markup
    assert "q" in wrapped_markup


# ---------------------------------------------------------------------------
# CD environment label builders and parse_cd
# ---------------------------------------------------------------------------


def test_cdlabel_html_builder_adds_classes_and_resets_extents() -> None:
    from pytex.environments import cd

    opts = default_options()
    label_node = _simple_textord_node("f")
    group: dict[str, Any] = {"side": "left", "label": label_node}

    span = cd._cdlabel_html_builder(group, opts)  # type: ignore[attr-defined]

    assert span.has_class("cd-label-left")
    # Height/depth are zeroed for proper arrow alignment
    assert span.height == 0
    assert span.depth == 0

    markup = span.to_markup()
    assert "f" in markup


def test_cdlabel_mathml_builder_sets_padding_and_side_specific_attrs() -> None:
    from pytex.environments import cd

    opts = default_options()
    label_node = _simple_textord_node("g")

    left_group: dict[str, Any] = {"side": "left", "label": label_node}
    right_group: dict[str, Any] = {"side": "right", "label": label_node}

    left_math = cd._cdlabel_mathml_builder(left_group, opts)  # type: ignore[attr-defined]
    right_math = cd._cdlabel_mathml_builder(right_group, opts)  # type: ignore[attr-defined]

    left_markup = left_math.to_markup()
    right_markup = right_math.to_markup()

    # Left labels get negative lspace; right labels do not.
    assert 'lspace="-1width"' in left_markup
    assert 'lspace="-1width"' not in right_markup
    # Both apply a vertical offset and are rendered as script-level labels.
    assert 'voffset="0.7em"' in left_markup
    assert 'scriptlevel="1"' in left_markup


def test_cdlabelparent_html_and_mathml_builders_wrap_fragment() -> None:
    from pytex.environments import cd

    opts = default_options()
    fragment = _simple_textord_node("h")
    group: dict[str, Any] = {"fragment": fragment}

    html_span = cd._cdlabelparent_html_builder(group, opts)  # type: ignore[attr-defined]
    math_node = cd._cdlabelparent_mathml_builder(group, opts)  # type: ignore[attr-defined]

    assert html_span.has_class("cd-vert-arrow")
    html_markup = html_span.to_markup()
    math_markup = math_node.to_markup()

    assert "h" in html_markup
    assert "<mrow" in math_markup


class _FakeMacros:
    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    def set(self, name: str, value: Any, global_: bool = False) -> None:  # noqa: D401
        """Store macro values; behaviour is not important for this test."""

        self._store[name] = value


class _FakeGullet:
    def __init__(self) -> None:
        self.macros = _FakeMacros()
        self._groups = 0

    def begin_group(self) -> None:
        self._groups += 1

    def end_group(self) -> None:
        if self._groups > 0:
            self._groups -= 1


class _FakeToken:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeParser:
    """Minimal stub implementing the subset of Parser used by parse_cd.

    We avoid the real Parser (which depends on an incomplete implementation)
    and instead return a pre-defined row of nodes, followed by an empty row
    and a terminating "\\end" token.
    """

    def __init__(self) -> None:
        self.gullet = _FakeGullet()
        self.mode = "math"
        self._phase = 0
        self.next_token: _FakeToken | None = None

    def parse_expression(self, break_on_infix: bool, break_on_token_text: Any) -> list[dict[str, Any]]:  # noqa: D401
        """Return one row of CD parse nodes, then an empty row, then stop."""

        if self._phase == 0:
            # First call returns a simple row with two entries.
            self._phase = 1
            return [
                {"type": "mathord", "mode": "math", "text": "A"},
                {"type": "mathord", "mode": "math", "text": "B"},
            ]
        else:
            # Second call returns an empty row which will be discarded.
            self._phase = 2
            return []

    def fetch(self) -> _FakeToken:
        if self._phase == 1:
            self.next_token = _FakeToken("\\\\")  # end-of-row
        else:
            self.next_token = _FakeToken("\\end")
        return self.next_token

    def consume(self) -> None:
        # parse_cd only calls consume when encountering "&" or "\\"; our
        # stub does not need to update additional state here.
        return


def test_parse_cd_builds_basic_array_node() -> None:
    from pytex.environments import cd

    parser = _FakeParser()
    array_node = cd.parse_cd(parser)

    assert array_node["type"] == "array"
    assert array_node["mode"] == "math"
    assert array_node["colSeparationType"] == "CD"

    body = array_node["body"]
    assert isinstance(body, list)
    assert len(body) >= 1
    first_row = body[0]
    assert isinstance(first_row, list)
    assert len(first_row) >= 1

    # Column descriptions should match the first row length.
    cols = array_node["cols"]
    assert isinstance(cols, list)
    assert len(cols) == len(first_row)
