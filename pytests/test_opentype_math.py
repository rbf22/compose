# tests/test_opentype_math.py
"""Tests for OpenType Math font glyph variants and delimiter sizing"""

import pytest
from compose.render.opentype_math import (
    MathGlyphVariants, MathExpressionStyler, DelimiterSizer,
    style_mathematical_expression, select_delimiter_size
)


class TestMathGlyphVariants:
    """Test math glyph variant functionality"""

    def test_glyph_variants_creation(self):
        """Test creating math glyph variants handler"""
        variants = MathGlyphVariants()
        assert hasattr(variants, 'glyph_variants')
        assert '∫' in variants.glyph_variants

    def test_get_glyph_variant(self):
        """Test getting glyph variants for different styles"""
        variants = MathGlyphVariants()

        # Test integral symbol
        display_integral = variants.get_glyph_variant('∫', 'display')
        script_integral = variants.get_glyph_variant('∫', 'script')

        assert display_integral == '∫'
        assert script_integral == '∫'  # Same for now, but could differ

    def test_get_font_size_multiplier(self):
        """Test getting font size multipliers"""
        variants = MathGlyphVariants()

        display_multiplier = variants.get_font_size_multiplier('display')
        assert display_multiplier == 1.0

        script_multiplier = variants.get_font_size_multiplier('script')
        assert script_multiplier == 0.7

        subscript_multiplier = variants.get_font_size_multiplier('subscript')
        assert subscript_multiplier == 0.6

    def test_determine_math_style(self):
        """Test determining appropriate math style"""
        variants = MathGlyphVariants()

        # Display style for top level
        style = variants.determine_math_style(0, False, False)
        assert style == 'display'

        # Inline style for nested
        style = variants.determine_math_style(1, False, False)
        assert style == 'inline'

        # Script style for subscripts
        style = variants.determine_math_style(0, True, False)
        assert style == 'script'

        # Scriptscript style for deeply nested subscripts
        style = variants.determine_math_style(2, True, False)
        assert style == 'scriptscript'


class TestMathExpressionStyler:
    """Test math expression styling"""

    def test_expression_styler_creation(self):
        """Test creating math expression styler"""
        styler = MathExpressionStyler()
        assert hasattr(styler, 'glyph_variants')

    def test_style_simple_expression(self):
        """Test styling a simple expression"""
        styler = MathExpressionStyler()

        result = styler.style_expression('x + y', 'display')

        assert result['expression'] == 'x + y'
        assert result['base_context'] == 'display'
        assert isinstance(result['styled_parts'], list)
        assert len(result['styled_parts']) > 0

    def test_style_expression_with_operators(self):
        """Test styling expression with mathematical operators"""
        styler = MathExpressionStyler()

        result = styler.style_expression('∫ f(x) dx', 'display')

        assert result['expression'] == '∫ f(x) dx'
        assert len(result['styled_parts']) > 0

        # Should contain operator styling
        operator_parts = [p for p in result['styled_parts'] if p['type'] == 'large_operator']
        assert len(operator_parts) > 0

    def test_analyze_expression_structure(self):
        """Test expression structure analysis"""
        styler = MathExpressionStyler()

        parts = styler._analyze_expression_structure('a + b', 'display')

        assert isinstance(parts, list)
        assert len(parts) > 0

        # Should classify characters appropriately
        var_parts = [p for p in parts if p['type'] == 'variable']
        assert len(var_parts) >= 2  # a and b

    def test_classify_characters(self):
        """Test character classification"""
        styler = MathExpressionStyler()

        assert styler._classify_character('∫') == 'large_operator'
        assert styler._classify_character('(') == 'delimiter'
        assert styler._classify_character('√') == 'radical'
        assert styler._classify_character('5') == 'number'
        assert styler._classify_character('x') == 'variable'
        assert styler._classify_character('+') == 'operator'
        assert styler._classify_character('@') == 'other'


class TestDelimiterSizer:
    """Test delimiter sizing functionality"""

    def test_delimiter_sizer_creation(self):
        """Test creating delimiter sizer"""
        sizer = DelimiterSizer()
        assert hasattr(sizer, 'delimiter_sizes')
        assert '(' in sizer.delimiter_sizes

    def test_select_delimiter_size_small(self):
        """Test selecting delimiter size for small content"""
        sizer = DelimiterSizer()

        result = sizer.select_delimiter_size('(', 10)  # Small content
        assert result == '('  # Normal size

    def test_select_delimiter_size_medium(self):
        """Test selecting delimiter size for medium content"""
        sizer = DelimiterSizer()

        result = sizer.select_delimiter_size('(', 30)  # Medium content
        assert result == '⦅'  # Medium size

    def test_select_delimiter_size_large(self):
        """Test selecting delimiter size for large content"""
        sizer = DelimiterSizer()

        result = sizer.select_delimiter_size('(', 50)  # Large content
        assert result in ['⦗', '⧘']  # Large sizes

    def test_get_delimiter_pair(self):
        """Test getting sized delimiter pairs"""
        sizer = DelimiterSizer()

        left, right = sizer.get_delimiter_pair('(', ')', 25)

        assert left in ['(', '⦅', '⦗', '⧘']
        assert right in [')', '⦆', '⦘', '⧙']

    def test_unknown_delimiter(self):
        """Test handling unknown delimiters"""
        sizer = DelimiterSizer()

        result = sizer.select_delimiter_size('@', 50)
        assert result == '@'  # Should return unchanged


class TestOpenTypeMathIntegration:
    """Test OpenType math integration functions"""

    def test_style_mathematical_expression(self):
        """Test the main styling function"""
        result = style_mathematical_expression('∫_0^∞ f(x) dx', 'display')

        assert result['expression'] == '∫_0^∞ f(x) dx'
        assert result['base_context'] == 'display'
        assert isinstance(result['styled_parts'], list)
        assert result['recommended_font_size'] == 18  # Display size

    def test_style_inline_expression(self):
        """Test styling inline expressions"""
        result = style_mathematical_expression('x^2 + y^2', 'inline')

        assert result['base_context'] == 'inline'
        assert result['recommended_font_size'] == 16  # Inline size

    def test_select_delimiter_size_function(self):
        """Test the global delimiter sizing function"""
        result = select_delimiter_size('(', 30)
        assert result in ['(', '⦅', '⦗', '⧘']

    def test_styling_complex_expression(self):
        """Test styling a complex mathematical expression"""
        expression = '∑_{i=1}^n ∫_0^∞ f(x) dx'

        result = style_mathematical_expression(expression, 'display')

        assert result['expression'] == expression
        assert len(result['styled_parts']) > 0

        # Should identify operators
        operator_parts = [p for p in result['styled_parts'] if p['type'] == 'large_operator']
        assert len(operator_parts) >= 2  # Sum and integral


class TestMathStylingContexts:
    """Test different mathematical styling contexts"""

    def test_display_vs_inline_styling(self):
        """Test styling differences between display and inline contexts"""
        styler = MathExpressionStyler()

        display_result = styler.style_expression('∫ f(x) dx', 'display')
        inline_result = styler.style_expression('∫ f(x) dx', 'inline')

        # Font sizes should differ
        assert display_result['recommended_font_size'] > inline_result['recommended_font_size']

    def test_script_vs_display_styling(self):
        """Test styling differences between script and display contexts"""
        styler = MathExpressionStyler()

        display_result = styler.style_expression('x^2', 'display')
        script_result = styler.style_expression('x^2', 'script')

        # Font sizes should differ significantly
        assert display_result['recommended_font_size'] > script_result['recommended_font_size']
