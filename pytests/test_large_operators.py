# tests/test_large_operators.py
"""Tests for large operators and radical layout"""

import pytest
from typing import Optional
from compose.render.large_operators import (
    LargeOperatorLayout, RadicalLayout, render_large_operator, render_radical
)
from compose.render.math_images import MathImageGenerator


class TestLargeOperatorLayout:
    """Test large operator layout functionality"""

    def test_large_operator_layout_creation(self):
        """Test creating large operator layout engine"""
        layout = LargeOperatorLayout()
        assert hasattr(layout, 'large_operators')
        assert 'int' in layout.large_operators
        assert 'sum' in layout.large_operators

    def test_layout_simple_operator(self):
        """Test layout of simple operator without limits"""
        layout = LargeOperatorLayout()
        box = layout.layout_large_operator('int')

        assert box is not None
        assert hasattr(box, 'width')
        assert hasattr(box, 'height')

    def test_layout_operator_with_subscript(self):
        """Test layout of operator with subscript (lower limit)"""
        layout = LargeOperatorLayout()
        box = layout.layout_large_operator('int', subscript='0', superscript='∞')

        assert box is not None
        assert box.width > layout.operator_width  # Should be wider with limits

    def test_layout_operator_with_superscript(self):
        """Test layout of operator with superscript (upper limit)"""
        layout = LargeOperatorLayout()
        box = layout.layout_large_operator('sum', subscript='i=1', superscript='n')

        assert box is not None

    def test_layout_display_style_limits(self):
        """Test display style limits (above/below operator)"""
        layout = LargeOperatorLayout()
        box = layout.layout_large_operator('sum', subscript='i=1', superscript='n', display_style=True)

        assert box is not None
        # Display style should have greater height due to stacked limits
        assert box.height > layout.operator_height

    def test_layout_inline_style_limits(self):
        """Test inline style limits (as sub/super scripts)"""
        layout = LargeOperatorLayout()
        box = layout.layout_large_operator('sum', subscript='i', superscript='n', display_style=False)

        assert box is not None

    def test_unknown_operator(self):
        """Test handling of unknown operators"""
        layout = LargeOperatorLayout()
        # Should not crash, should return fallback
        box = layout.layout_large_operator('unknown_op')
        assert box is not None


class TestRadicalLayout:
    """Test radical layout functionality"""

    def test_radical_layout_creation(self):
        """Test creating radical layout engine"""
        layout = RadicalLayout()
        assert layout.radical_symbol == '√'
        assert layout.vinculum_extra == 4

    def test_layout_square_root(self):
        """Test layout of square root"""
        layout = RadicalLayout()
        box = layout.layout_radical('x^2 + y^2')

        assert box is not None
        assert hasattr(box, 'width')
        assert hasattr(box, 'height')

    def test_layout_nth_root(self):
        """Test layout of nth root"""
        layout = RadicalLayout()
        box = layout.layout_radical('8', index='3')

        assert box is not None

    def test_layout_complex_radical(self):
        """Test layout of complex radical expression"""
        layout = RadicalLayout()
        box = layout.layout_radical('a^2 + 2ab + b^2')

        assert box is not None
        assert box.width > 0
        assert box.height > 0


class TestLargeOperatorRendering:
    """Test large operator rendering"""

    def test_render_simple_integral(self):
        """Test rendering simple integral"""
        svg = render_large_operator('int', '0', '1', True)
        assert svg is not None
        assert svg.startswith('data:image/svg+xml;base64,')

    def test_render_summation(self):
        """Test rendering summation with limits"""
        svg = render_large_operator('sum', 'i=1', 'n', True)
        assert svg is not None
        assert 'svg' in svg

    def test_render_product(self):
        """Test rendering product operator"""
        svg = render_large_operator('prod', 'k=1', 'm', True)
        assert svg is not None

    def test_render_inline_limits(self):
        """Test rendering with inline limits"""
        svg = render_large_operator('int', 'a', 'b', False)
        assert svg is not None


class TestRadicalRendering:
    """Test radical rendering"""

    def test_render_square_root(self):
        """Test rendering square root"""
        svg = render_radical('x + 1')
        assert svg is not None
        assert svg.startswith('data:image/svg+xml;base64,')

    def test_render_cube_root(self):
        """Test rendering cube root"""
        svg = render_radical('8', '3')
        assert svg is not None

    def test_render_complex_radical(self):
        """Test rendering complex radical expression"""
        svg = render_radical('a^2 + b^2')
        assert svg is not None


class TestMathImageGeneratorIntegration:
    """Test integration of large operators and radicals with math image generator"""

    def test_detect_large_operators(self):
        """Test detection of large operators in math generator"""
        generator = MathImageGenerator()

        # Test various large operators
        assert generator._contains_large_operator(r'\int_0^1 f(x) dx') == True
        assert generator._contains_large_operator(r'\sum_{i=1}^n x_i') == True
        assert generator._contains_large_operator(r'\prod_{k=1}^m a_k') == True
        assert generator._contains_large_operator(r'x + y') == False

    def test_detect_radicals(self):
        """Test detection of radicals in math generator"""
        generator = MathImageGenerator()

        assert generator._contains_radical(r'\sqrt{x^2 + y^2}') == True
        assert generator._contains_radical(r'\sqrt[3]{8}') == True
        assert generator._contains_radical(r'x + y') == False

    def test_parse_large_operator(self):
        """Test parsing large operator expressions"""
        generator = MathImageGenerator()

        # Test integral with limits
        result = generator._parse_large_operator(r'\int_0^\infty f(x) dx')
        assert result is not None
        assert result['operator'] == 'int'
        assert result['subscript'] == '0'
        assert result['superscript'] == '\\infty'

        # Test summation
        result = generator._parse_large_operator(r'\sum_{i=1}^n a_i')
        assert result is not None
        assert result['operator'] == 'sum'
        assert result['subscript'] == 'i=1'
        assert result['superscript'] == 'n'

    def test_parse_radical(self):
        """Test parsing radical expressions"""
        generator = MathImageGenerator()

        # Test square root
        result = generator._parse_radical(r'\sqrt{x^2 + 1}')
        assert result is not None
        assert result['content'] == 'x^2 + 1'
        assert result['index'] is None

        # Test nth root
        result = generator._parse_radical(r'\sqrt[3]{27}')
        assert result is not None
        assert result['content'] == '27'
        assert result['index'] == '3'

    def test_large_operator_image_generation(self):
        """Test end-to-end large operator image generation"""
        generator = MathImageGenerator()

        # This should use the large operator path
        result = generator.get_math_image(r'\int_0^1 f(x) dx', display_style=True)
        assert result is not None
        assert result.startswith('data:image/svg+xml;base64,')

    def test_radical_image_generation(self):
        """Test end-to-end radical image generation"""
        generator = MathImageGenerator()

        # This should use the radical path
        result = generator.get_math_image(r'\sqrt{a^2 + b^2}', display_style=True)
        assert result is not None
        assert result.startswith('data:image/svg+xml;base64,')
