# tests/test_latex_nodes.py
"""Tests for LaTeX node parsing system"""

import pytest
from compose.render.latex_nodes import (
    LatexTokenizer, LatexWalker, parse_latex_to_nodes,
    LatexTokenType, LatexToken,
    LatexCharsNode, LatexMacroNode, LatexGroupNode,
    ParsingState
)


class TestLatexNodeParsing:
    """Test LaTeX node parsing"""

    def test_parse_simple_text(self):
        """Test parsing simple text"""
        nodes = parse_latex_to_nodes("hello world")

        assert len(nodes) == 2  # Should split on space
        assert all(isinstance(node, LatexCharsNode) for node in nodes)
        assert nodes[0].chars == "hello"
        assert nodes[1].chars == "world"

    def test_parse_macro(self):
        """Test parsing LaTeX macro"""
        nodes = parse_latex_to_nodes(r"\alpha")

        assert len(nodes) == 1
        assert isinstance(nodes[0], LatexMacroNode)
        assert nodes[0].macroname == "alpha"

    def test_parse_macro_with_subscript(self):
        """Test parsing macro with subscript"""
        nodes = parse_latex_to_nodes(r"\int_{0}^{\infty}")

        # Should have at least one macro node
        macro_nodes = [n for n in nodes if isinstance(n, LatexMacroNode)]
        assert len(macro_nodes) >= 1

        int_nodes = [n for n in macro_nodes if n.macroname == "int"]
        assert len(int_nodes) >= 1

        # The int node should have a subscript
        int_node = int_nodes[0]
        assert int_node.subscript == "0"

    def test_parse_group(self):
        """Test parsing braced group"""
        nodes = parse_latex_to_nodes("{content}")

        assert len(nodes) == 1
        assert isinstance(nodes[0], LatexGroupNode)
        assert len(nodes[0].nodelist) == 1
        assert isinstance(nodes[0].nodelist[0], LatexCharsNode)
        assert nodes[0].nodelist[0].chars == "content"

    def test_parse_complex_expression(self):
        """Test parsing complex mathematical expression"""
        expr = r"x^{a+b} + \int_{-\infty}^{\infty} f(x) dx"
        nodes = parse_latex_to_nodes(expr)

        # Should parse successfully (not None)
        assert nodes is not None
        assert isinstance(nodes, list)

        # Should have multiple nodes
        assert len(nodes) > 1

        # Should have macro nodes
        macro_nodes = [n for n in nodes if isinstance(n, LatexMacroNode)]
        assert len(macro_nodes) >= 2  # At least x^ and int

    def test_parse_nested_groups(self):
        """Test parsing nested braced groups"""
        nodes = parse_latex_to_nodes("{{nested}}")

        assert len(nodes) == 1
        assert isinstance(nodes[0], LatexGroupNode)

        inner_group = nodes[0].nodelist[0]
        assert isinstance(inner_group, LatexGroupNode)
        assert len(inner_group.nodelist) == 1
        assert inner_group.nodelist[0].chars == "nested"


class TestParsingState:
    """Test parsing state management"""

    def test_parsing_state_initialization(self):
        """Test parsing state initialization"""
        state = ParsingState()
        assert not state.math_mode
        assert not state.in_group
        assert state.group_level == 0

    def test_parsing_state_cloning(self):
        """Test parsing state cloning"""
        state = ParsingState()
        state.math_mode = True
        state.group_level = 2

        cloned = state.clone()
        assert cloned.math_mode == True
        assert cloned.group_level == 2

        # Changes to clone shouldn't affect original
        cloned.math_mode = False
        assert state.math_mode == True


class TestLatexWalker:
    """Test LaTeX walker functionality"""

    def test_walker_initialization(self):
        """Test walker initialization"""
        walker = LatexWalker("test")
        assert walker.s == "test"
        assert len(walker.tokens) > 0

    def test_walker_parsing(self):
        """Test walker parsing"""
        walker = LatexWalker(r"\alpha + \beta")
        nodes = walker.parse_content()

        assert len(nodes) > 0
        macro_nodes = [n for n in nodes if isinstance(n, LatexMacroNode)]
        assert len(macro_nodes) >= 2  # alpha and beta
