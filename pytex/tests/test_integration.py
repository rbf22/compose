"""Integration and edge case tests for KaTeX Python."""

import pytest  # type: ignore[import-not-found]


class TestKaTeXIntegration:
    """Integration tests combining multiple features."""

    def test_complex_expression_with_multiple_features(self) -> None:
        """Test complex expressions that use multiple KaTeX features."""
        import pytex.katex as katex

        # Complex expression combining multiple features
        expr = r"""
        \sum_{i=1}^{n} \frac{\partial^2 f}{\partial x_i^2} +
        \int_{-\infty}^{\infty} \frac{1}{\sqrt{2\pi\sigma^2}}
        e^{-\frac{(x-\mu)^2}{2\sigma^2}} \, dx
        """

        result = katex.render_to_string(expr)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_nested_environments(self) -> None:
        """Test expressions with nested mathematical constructs."""
        import pytex.katex as katex

        expressions = [
            r"\frac{\sum_{i=1}^{n} x_i}{n}",
            r"\sqrt{\int_0^1 x^2 \, dx}",
            r"x^{a^{b^c}}",
            r"\begin{pmatrix} \frac{a}{b} & c \\ d & e^{\sqrt{f}} \end{pmatrix}",
        ]

        for expr in expressions:
            result = katex.render_to_string(expr)
            assert isinstance(result, str)
            assert len(result) > 0


class TestKaTeXEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_expressions(self) -> None:
        """Test handling of empty or minimal expressions."""
        import pytex.katex as katex

        test_cases = ["", " ", "\t", "\n"]

        for expr in test_cases:
            result = katex.render_to_string(expr)
            assert isinstance(result, str)

    def test_special_characters(self) -> None:
        """Test handling of special characters."""
        import pytex.katex as katex

        # Test various special characters that might appear in LaTeX
        expressions = [
            r"x \& y",  # Escaped ampersand
            r"x \% y",  # Escaped percent
            r"x \_ y",  # Escaped underscore
            r"x \{ y \}",  # Escaped braces
            r"x \$ y",  # Escaped dollar
        ]

        for expr in expressions:
            result = katex.render_to_string(expr)
            assert isinstance(result, str)

    def test_unicode_characters(self) -> None:
        """Test handling of Unicode characters in expressions."""
        import pytex.katex as katex

        expressions = [
            "α + β + γ",  # Greek letters
            "∑ ∫ √ ∞",   # Mathematical symbols
            "≤ ≥ ≠ ≈",    # Comparison operators
        ]

        for expr in expressions:
            result = katex.render_to_string(expr)
            assert isinstance(result, str)


class TestKaTeXPerformance:
    """Basic performance tests."""

    def test_multiple_rendering_calls(self) -> None:
        """Test that multiple rendering calls work efficiently."""
        import pytex.katex as katex

        expressions = [f"x_{i}" for i in range(100)]

        # This should not raise any exceptions
        for expr in expressions:
            result = katex.render_to_string(expr)
            assert isinstance(result, str)
            assert len(result) > 0


class TestKaTeXConfiguration:
    """Test configuration and options handling."""

    def test_display_mode_option(self) -> None:
        """Test display mode configuration."""
        import pytex.katex as katex

        expr = r"\sum_{i=1}^{n} x_i"

        # Test both modes
        inline = katex.render_to_string(expr, {"display_mode": False})
        display = katex.render_to_string(expr, {"display_mode": True})

        assert isinstance(inline, str)
        assert isinstance(display, str)

    def test_options_dict_handling(self) -> None:
        """Test that options dictionary is handled properly."""
        import pytex.katex as katex

        # Test with various option combinations
        options_list = [
            {},
            {"display_mode": True},
            {"display_mode": False},
            {"throw_on_error": False},
            {"display_mode": True, "throw_on_error": False},
        ]

        for options in options_list:
            result = katex.render_to_string("x + y", options)
            assert isinstance(result, str)


class TestKaTeXCompatibility:
    """Test compatibility with different LaTeX constructs."""

    def test_amsmath_compatibility(self) -> None:
        """Test compatibility with AMS math constructs."""
        import pytex.katex as katex

        # AMS math expressions (when implemented)
        ams_expressions = [
            r"\text{Let } x = y",  # \text command
            r"x \equiv y",         # \equiv symbol
            r"\dot{x} + \ddot{y}", # Accents
        ]

        for expr in ams_expressions:
            result = katex.render_to_string(expr)
            assert isinstance(result, str)

    def test_color_commands(self) -> None:
        """Test color command compatibility."""
        import pytex.katex as katex

        color_expressions = [
            r"\color{red} x",
            r"\textcolor{blue}{y}",
            r"\colorbox{yellow}{z}",
        ]

        for expr in color_expressions:
            result = katex.render_to_string(expr)
            assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
