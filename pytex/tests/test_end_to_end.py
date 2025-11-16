"""High-level end-to-end tests for the public KaTeX Python API.

These tests are intentionally high-level and act as usage examples for
pytex.katex. They exercise the main public entry points in a way that
should continue to make sense even as the internal implementation
becomes more complete.
"""

from __future__ import annotations

from typing import Dict

import pytex.katex as katex


class TestEndToEndRenderToString:
    """End-to-end tests for render_to_string."""

    def test_inline_math_basic(self) -> None:
        expr = r"x + y"
        html = katex.render_to_string(expr)

        assert isinstance(html, str)
        assert html.startswith('<span class="katex">')
        assert html.endswith("</span>")
        assert expr in html

    def test_display_math_with_options_dict(self) -> None:
        expr = r"\int_{0}^{1} x^2 \, dx"
        options: Dict[str, object] = {"display_mode": True}
        html = katex.render_to_string(expr, options)

        assert isinstance(html, str)
        assert html.startswith('<span class="katex">')
        assert html.endswith("</span>")
        assert expr in html


class TestEndToEndMacrosAndFunctions:
    """End-to-end style tests for macros and custom functions."""

    def test_define_macro_then_render_expression(self) -> None:
        katex.define_macro(r"\R", r"\mathbb{R}")

        expr = r"f: \R \to \R"
        html = katex.render_to_string(expr)

        assert isinstance(html, str)
        assert html.startswith('<span class="katex">')
        assert html.endswith("</span>")
        # Current implementation does not expand macros yet; the input
        # expression should simply flow through into the output.
        assert r"\R" in html

    def test_define_function_then_render_expression(self) -> None:
        def handler(context, args, opt_args=None):  # type: ignore[unused-argument]
            # Placeholder handler – current render_to_string implementation
            # does not invoke it yet, but registering the function should
            # succeed without affecting rendering.
            return {}

        function_def: Dict[str, object] = {
            "type": "custom",
            "names": [r"\custom"],
            "props": {
                "numArgs": 1,
                "allowedInMath": True,
                "allowedInText": True,
            },
            "handler": handler,
        }

        katex.define_function(function_def)

        expr = r"\custom{x}"
        html = katex.render_to_string(expr)

        assert isinstance(html, str)
        assert html.startswith('<span class="katex">')
        assert html.endswith("</span>")
        assert expr in html


class TestEndToEndRenderHelper:
    """End-to-end tests for the render helper used in web contexts."""

    def test_render_prints_to_stdout_when_element_id_provided(self, capsys) -> None:
        expr = r"x + y"
        katex.render(expr, element_id="output")

        captured = capsys.readouterr()
        assert "Would render to element 'output':" in captured.out
        assert expr in captured.out
