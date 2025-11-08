# tests/test_latex_tokenizer.py
"""Tests for LaTeX tokenization"""

import pytest
from compose.render.latex_tokenizer import (
    LatexTokenizer, TokenType, Token,
    parse_latex_expression, tokenize_latex
)


class TestLatexTokenizer:
    """Test LaTeX tokenization"""

    def test_tokenize_simple_text(self):
        """Test tokenizing simple text"""
        tokenizer = LatexTokenizer()
        tokens = tokenizer.tokenize("hello world")

        assert len(tokens) == 1
        assert tokens[0].type == TokenType.TEXT
        assert tokens[0].value == "hello world"

    def test_tokenize_latex_commands(self):
        """Test tokenizing LaTeX commands"""
        tokenizer = LatexTokenizer()
        tokens = tokenizer.tokenize(r"\alpha + \beta")

        # Should find alpha command
        alpha_tokens = [t for t in tokens if t.value == r'\alpha']
        assert len(alpha_tokens) == 1
        assert alpha_tokens[0].type == TokenType.COMMAND

    def test_tokenize_braces(self):
        """Test tokenizing braces"""
        tokenizer = LatexTokenizer()
        tokens = tokenizer.tokenize("{content}")

        brace_tokens = [t for t in tokens if 'brace' in t.type.value]
        assert len(brace_tokens) == 2
        assert brace_tokens[0].type == TokenType.LBRACE
        assert brace_tokens[1].type == TokenType.RBRACE

    def test_tokenize_subscripts(self):
        """Test tokenizing subscripts"""
        tokenizer = LatexTokenizer()
        tokens = tokenizer.tokenize("x_1")

        subscript_tokens = [t for t in tokens if t.type == TokenType.SUBSCRIPT]
        assert len(subscript_tokens) == 1
        assert subscript_tokens[0].value == "_"

    def test_tokenize_superscripts(self):
        """Test tokenizing superscripts"""
        tokenizer = LatexTokenizer()
        tokens = tokenizer.tokenize("x^2")

        superscript_tokens = [t for t in tokens if t.type == TokenType.SUPERSCRIPT]
        assert len(superscript_tokens) == 1
        assert superscript_tokens[0].value == "^"

    def test_tokenize_complex_expression(self):
        """Test tokenizing complex mathematical expression"""
        expr = r"x^{a+b} + y_{i,j}"
        tokens = tokenize_latex(expr)

        # Should have subscripts and superscripts
        subscripts = [t for t in tokens if t.type == TokenType.SUBSCRIPT]
        superscripts = [t for t in tokens if t.type == TokenType.SUPERSCRIPT]

        assert len(subscripts) >= 1
        assert len(superscripts) >= 1


class TestLatexExpressionParsing:
    """Test LaTeX expression parsing"""

    def test_parse_simple_expression(self):
        """Test parsing simple expression"""
        expr = parse_latex_expression("x + y")

        assert expr is not None
        assert len(expr.elements) > 0

    def test_parse_subscript_expression(self):
        """Test parsing expression with subscripts"""
        expr = parse_latex_expression("x_{sub}")

        # Should have elements with subscript
        subscript_elements = [e for e in expr.elements if e.get("type") == "sub"]
        assert len(subscript_elements) > 0

    def test_parse_superscript_expression(self):
        """Test parsing expression with superscripts"""
        expr = parse_latex_expression("x^{sup}")

        # Should have elements with superscript
        superscript_elements = [e for e in expr.elements if e.get("type") == "super"]
        assert len(superscript_elements) > 0

    def test_parse_complex_expression(self):
        """Test parsing complex expression with both sub and superscripts"""
        expr = parse_latex_expression("x_{i}^{2} + y_{j}")

        # Should have both sub and superscript elements
        sub_elements = [e for e in expr.elements if e.get("type") == "sub"]
        super_elements = [e for e in expr.elements if e.get("type") == "super"]

        assert len(sub_elements) >= 1
        assert len(super_elements) >= 1

    def test_svg_generation(self):
        """Test SVG generation from parsed expression"""
        expr = parse_latex_expression("x^2")

        svg = expr.to_svg_text(16)
        assert isinstance(svg, str)
        assert len(svg) > 0
        assert "baseline-shift" in svg  # Should have superscript positioning
