"""Unit tests for low-level utility and options helpers in pytex.

These tests focus on stable, self-contained helpers that are safe to
exercise even while the full KaTeX port is incomplete. They provide a
good coverage boost without depending on the full parser/rendering
pipeline.
"""

from __future__ import annotations

from typing import Any

import pytest  # type: ignore[import-not-found]

from pytex.font_metrics import get_global_metrics
from pytex.options import Options, default_options, size_at_style
from pytex.style import DEFAULT_STYLES, Style
from pytex.unicode_scripts import script_from_codepoint, supported_codepoint
from pytex.utils import (
    assert_non_null,
    default,
    deflt,
    escape,
    get_base_elem,
    hyphenate,
    is_character_box,
    protocol_from_url,
)


class TestUtilsDefaultAndHyphenate:
    def test_default_and_deflt(self) -> None:
        assert default(None, 42) == 42
        assert default("value", 42) == "value"

        # deflt is just a thin wrapper
        assert deflt(None, "fallback") == "fallback"
        assert deflt("x", "fallback") == "x"

    def test_hyphenate_basic(self) -> None:
        assert hyphenate("camelCase") == "camel-case"
        assert hyphenate("PascalCase") == "-pascal-case"
        # Already hyphenated is unchanged except for additional uppercase
        assert hyphenate("already-hyphenated") == "already-hyphenated"

    def test_escape_coerces_to_string(self) -> None:
        # simple escaping
        assert escape("<tag>&'") == "&lt;tag&gt;&amp;&#x27;"
        # non-string input is converted via str()
        assert escape(123) == "123"


class TestUtilsParseNodeHelpers:
    def test_get_base_elem_unwraps_nested_ordgroup_and_color(self) -> None:
        # ordgroup(color(mathord("x"))) should unwrap to the inner mathord
        inner: dict[str, Any] = {"type": "mathord", "text": "x"}
        node: dict[str, Any] = {
            "type": "ordgroup",
            "body": [
                {
                    "type": "color",
                    "body": [inner],
                }
            ],
        }

        base = get_base_elem(node)
        assert base is inner

    def test_is_character_box_recognizes_ord_types(self) -> None:
        for node_type in ("mathord", "textord", "atom"):
            node: dict[str, Any] = {"type": node_type, "text": "x"}
            assert is_character_box(node)

        non_char_node: dict[str, Any] = {"type": "color", "body": []}
        assert not is_character_box(non_char_node)

    def test_assert_non_null_raises_for_falsy_values(self) -> None:
        assert assert_non_null(1) == 1
        with pytest.raises(ValueError):
            assert_non_null(0)
        with pytest.raises(ValueError):
            assert_non_null("")
        with pytest.raises(ValueError):
            assert_non_null(None)


class TestUtilsProtocolFromUrl:
    @pytest.mark.parametrize(
        "url,expected",
        [
            ("http://example.com", "http"),
            ("https://example.com", "https"),
            ("mailto:user@example.com", "mailto"),
            ("//relative/path", "_relative"),
            ("relative/path", "_relative"),
        ],
    )
    def test_protocol_from_url_basic(self, url: str, expected: str) -> None:
        assert protocol_from_url(url) == expected

    def test_protocol_from_url_rejects_encoded_colon_and_invalid_scheme(self) -> None:
        # Encoded colon
        assert protocol_from_url("javascript&#x3a;alert(1)") is None
        # Invalid scheme characters
        assert protocol_from_url("j@vascript:alert(1)") is None


class TestOptionsAndStyles:
    def test_default_options_uses_text_style_and_infinite_max_size(self) -> None:
        opts = default_options()
        assert opts.style is DEFAULT_STYLES["text"]
        assert opts.max_size == float("inf")
        assert opts.min_rule_thickness == 0.0

    def test_size_at_style_mapping(self) -> None:
        # For small styles (<2) size is unchanged
        assert size_at_style(6, Style.TEXT) == 6
        # For script/script-script styles, mapping table should apply
        assert size_at_style(6, Style.SCRIPT) == 3
        assert size_at_style(6, Style.SCRIPTSCRIPT) == 1

    def test_having_style_and_having_size(self) -> None:
        base = Options(style=Style.TEXT)
        # having_style should adjust size while preserving text_size
        script_opts = base.having_style(Style.SCRIPT)
        assert script_opts.style is Style.SCRIPT
        assert script_opts.size != base.size

        # having_size should reset style to text and update multipliers
        sized = base.having_size(8)
        assert sized.style is sized.style.text()
        assert sized.size == 8
        assert sized.text_size == 8
        assert sized.size_multiplier > base.size_multiplier

    def test_font_helpers_do_not_mutate_original(self) -> None:
        base = Options(style=Style.TEXT)
        colored = base.with_color("red")
        phantom = base.with_phantom()
        bold = base.with_text_font_weight("textbf")

        assert base.color is None
        assert colored.color == "red"
        assert phantom.phantom is True
        assert bold.font_weight == "textbf"

    def test_sizing_classes_helpers(self) -> None:
        base = Options(style=Style.TEXT)
        larger = base.having_size(base.size + 1)

        # When sizes differ, we should get sizing/reset classes
        classes = larger.sizing_classes(base)
        assert "sizing" in classes
        assert any(c.startswith("reset-size") for c in classes)

        # base_sizing_classes returns classes when not at BASESIZE
        base_sized = larger.base_sizing_classes()
        assert base_sized or larger.size == larger.BASESIZE

    def test_font_metrics_cached_and_contains_expected_keys(self) -> None:
        base = Options(style=Style.TEXT)
        metrics = base.font_metrics()
        # Should contain at least some core metrics from SIGMAS_AND_XIS
        for key in ("xHeight", "quad", "axisHeight", "defaultRuleThickness"):
            assert key in metrics


class TestFontMetricsAndUnicodeScripts:
    def test_get_global_metrics_size_buckets(self) -> None:
        # Sizes map into three buckets; check that repeated calls are cached and stable
        small = get_global_metrics(2)
        medium = get_global_metrics(4)
        large = get_global_metrics(6)

        assert small is get_global_metrics(2)
        assert medium is get_global_metrics(3)
        assert large is get_global_metrics(10)

        # Basic sanity checks on a couple of keys
        for metrics in (small, medium, large):
            assert "quad" in metrics
            assert "xHeight" in metrics

    def test_script_from_codepoint_and_supported_codepoint(self) -> None:
        # Latin range
        assert script_from_codepoint(0x0105) == "latin"
        # Cyrillic
        assert script_from_codepoint(0x0410) == "cyrillic"

        assert supported_codepoint(0x0105) is True
        assert supported_codepoint(0x0041) is False  # plain ASCII A is outside configured ranges
