# compose/render/opentype_math.py
"""
OpenType Math font glyph variant support for Compose.
Provides proper glyph selection for mathematical typography.
"""

from typing import Dict, List, Any, Optional, Tuple
from ..cache_system import math_cache


class MathGlyphVariants:
    """
    Manages mathematical glyph variants for proper typography.
    Implements OpenType MATH table concepts for glyph selection.
    """

    def __init__(self):
        # Math style constants (simplified OpenType MATH table values)
        self.math_styles = {
            'display': 0,
            'inline': 1,
            'script': 2,
            'scriptscript': 3
        }

        # Glyph size ratios for different styles
        self.size_ratios = {
            'display': 1.0,      # Base size
            'inline': 1.0,       # Same as display for inline
            'script': 0.7,       # 70% of display size
            'scriptscript': 0.5  # 50% of display size
        }

        # Common mathematical glyph variants
        self.glyph_variants = {
            # Parentheses - different sizes for different contexts
            '(': {
                'display': '(',
                'inline': '(',
                'script': '(',
                'scriptscript': '('
            },
            ')': {
                'display': ')',
                'inline': ')',
                'script': ')',
                'scriptscript': ')'
            },

            # Summation symbol variants
            '∑': {
                'display': '∑',
                'inline': '∑',
                'script': '∑',
                'scriptscript': '∑'
            },

            # Integral variants (different styles)
            '∫': {
                'display': '∫',
                'inline': '∫',
                'script': '∫',
                'scriptscript': '∫'
            },

            # Product symbol
            '∏': {
                'display': '∏',
                'inline': '∏',
                'script': '∏',
                'scriptscript': '∏'
            },

            # Radical symbols
            '√': {
                'display': '√',
                'inline': '√',
                'script': '√',
                'scriptscript': '√'
            }
        }

        # Font size multipliers for different contexts
        self.font_multipliers = {
            'display': 1.0,
            'inline': 1.0,
            'script': 0.7,
            'scriptscript': 0.5,
            'subscript': 0.6,
            'superscript': 0.6,
            'subsubscript': 0.4,
            'supersuperscript': 0.4
        }

    def get_glyph_variant(self, base_glyph: str, math_style: str = 'display') -> str:
        """
        Get the appropriate glyph variant for a mathematical symbol.

        Args:
            base_glyph: Base glyph/symbol
            math_style: Mathematical style context

        Returns:
            Appropriate glyph variant for the context
        """
        if base_glyph in self.glyph_variants:
            variants = self.glyph_variants[base_glyph]
            return variants.get(math_style, base_glyph)

        return base_glyph

    def get_font_size_multiplier(self, context: str) -> float:
        """
        Get font size multiplier for a given context.

        Args:
            context: Font context (display, script, subscript, etc.)

        Returns:
            Size multiplier relative to base font size
        """
        return self.font_multipliers.get(context, 1.0)

    def determine_math_style(self, nesting_level: int, is_subscript: bool = False,
                           is_superscript: bool = False) -> str:
        """
        Determine the appropriate math style based on context.

        Args:
            nesting_level: How deeply nested the expression is
            is_subscript: Whether this is in a subscript context
            is_superscript: Whether this is in a superscript context

        Returns:
            Appropriate math style
        """
        if is_subscript or is_superscript:
            if nesting_level >= 2:
                return 'scriptscript'
            else:
                return 'script'
        else:
            if nesting_level >= 1:
                return 'inline'
            else:
                return 'display'


class MathExpressionStyler:
    """
    Applies mathematical styling to expressions based on context.
    Handles font sizes, glyph variants, and positioning.
    """

    def __init__(self):
        self.glyph_variants = MathGlyphVariants()

    def style_expression(self, expression: str, context: str = 'display') -> Dict[str, Any]:
        """
        Apply mathematical styling to an expression.

        Args:
            expression: Mathematical expression
            context: Styling context

        Returns:
            Styled expression with font and positioning information
        """
        # Analyze expression structure
        styled_parts = self._analyze_expression_structure(expression, context)

        return {
            'expression': expression,
            'styled_parts': styled_parts,
            'base_context': context,
            'recommended_font_size': self._get_recommended_font_size(context)
        }

    def _analyze_expression_structure(self, expression: str, context: str) -> List[Dict[str, Any]]:
        """
        Analyze expression structure and apply appropriate styling.

        Returns:
            List of styled parts with font and positioning info
        """
        parts = []

        # Simple analysis - in a full implementation this would parse the expression tree
        i = 0
        while i < len(expression):
            char = expression[i]

            # Check for multi-character symbols
            if i + 1 < len(expression):
                two_char = expression[i:i+2]
                if two_char in ['∫∫', '∫∫∫', '∑', '∏', '√']:
                    styled_part = self._create_styled_part(two_char, context, 'operator')
                    parts.append(styled_part)
                    i += 2
                    continue

            # Single character analysis
            part_type = self._classify_character(char)
            styled_part = self._create_styled_part(char, context, part_type)
            parts.append(styled_part)
            i += 1

        return parts

    def _classify_character(self, char: str) -> str:
        """Classify a character for styling purposes."""
        if char in '∫∑∏∐⋂⋃':
            return 'large_operator'
        elif char in '()[]{}':
            return 'delimiter'
        elif char in '√':
            return 'radical'
        elif char in '0123456789':
            return 'number'
        elif char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ':
            return 'variable'
        elif char in '+-×÷=≠≤≥':
            return 'operator'
        else:
            return 'other'

    def _create_styled_part(self, text: str, context: str, part_type: str) -> Dict[str, Any]:
        """Create a styled part with appropriate font and positioning."""
        # Get glyph variant
        glyph = self.glyph_variants.get_glyph_variant(text, context)

        # Determine font size multiplier
        size_multiplier = self._get_size_multiplier_for_type(part_type, context)

        # Determine positioning
        positioning = self._get_positioning_for_type(part_type)

        return {
            'text': glyph,
            'original': text,
            'type': part_type,
            'context': context,
            'font_size_multiplier': size_multiplier,
            'positioning': positioning
        }

    def _get_size_multiplier_for_type(self, part_type: str, context: str) -> float:
        """Get font size multiplier for a part type in a context."""
        base_multiplier = self.glyph_variants.get_font_size_multiplier(context)

        # Adjust based on part type
        type_multipliers = {
            'large_operator': 1.2,  # Slightly larger for operators
            'delimiter': 1.0,
            'radical': 1.1,
            'number': 1.0,
            'variable': 1.0,
            'operator': 0.9,  # Slightly smaller for operators
            'subscript': 0.6,
            'superscript': 0.6,
            'other': 1.0
        }

        return base_multiplier * type_multipliers.get(part_type, 1.0)

    def _get_positioning_for_type(self, part_type: str) -> Dict[str, Any]:
        """Get positioning information for a part type."""
        # Basic positioning - in a full implementation this would be more sophisticated
        positioning = {
            'baseline_offset': 0,
            'horizontal_offset': 0
        }

        if part_type == 'subscript':
            positioning['baseline_offset'] = -0.3  # Lower baseline
        elif part_type == 'superscript':
            positioning['baseline_offset'] = 0.5   # Raise baseline

        return positioning

    def _get_recommended_font_size(self, context: str) -> int:
        """Get recommended font size for a context."""
        base_sizes = {
            'display': 18,
            'inline': 16,
            'script': 12,
            'scriptscript': 10
        }
        return base_sizes.get(context, 16)


class DelimiterSizer:
    """
    Handles automatic sizing of delimiters (parentheses, brackets, etc.)
    based on content height.
    """

    def __init__(self):
        # Delimiter size variants (simplified)
        self.delimiter_sizes = {
            '(': ['(', '⦅', '⦗', '⧘'],
            ')': [')', '⦆', '⦘', '⧙'],
            '[': ['[', '⟦', '⦋', '⦍'],
            ']': [']', '⟧', '⦌', '⦎'],
            '{': ['{', '⦃', '⦏', '⦑'],
            '}': ['}', '⦄', '⦐', '⦒'],
            '|': ['|', '‖', '⦶', '⦸']
        }

    def select_delimiter_size(self, delimiter: str, content_height: float) -> str:
        """
        Select appropriate delimiter size based on content height.

        Args:
            delimiter: Base delimiter character
            content_height: Height of content in pixels

        Returns:
            Appropriate delimiter variant
        """
        if delimiter not in self.delimiter_sizes:
            return delimiter

        sizes = self.delimiter_sizes[delimiter]

        # Simple size selection based on height
        if content_height < 20:
            return sizes[0]  # Normal size
        elif content_height < 40:
            return sizes[1]  # Medium size
        elif content_height < 60:
            return sizes[2]  # Large size
        else:
            return sizes[3]  # Extra large size

    def get_delimiter_pair(self, left_delim: str, right_delim: str,
                          content_height: float) -> Tuple[str, str]:
        """
        Get appropriately sized delimiter pair.

        Args:
            left_delim: Left delimiter
            right_delim: Right delimiter
            content_height: Content height

        Returns:
            Tuple of (left, right) delimiters
        """
        left = self.select_delimiter_size(left_delim, content_height)
        right = self.select_delimiter_size(right_delim, content_height)

        return left, right


# Global instances
math_glyph_variants = MathGlyphVariants()
math_expression_styler = MathExpressionStyler()
delimiter_sizer = DelimiterSizer()


def style_mathematical_expression(expression: str, context: str = 'display') -> Dict[str, Any]:
    """
    Apply comprehensive mathematical styling to an expression.

    Args:
        expression: Mathematical expression
        context: Styling context

    Returns:
        Styled expression information
    """
    return math_expression_styler.style_expression(expression, context)


def select_delimiter_size(delimiter: str, content_height: float) -> str:
    """
    Select appropriate delimiter size.

    Args:
        delimiter: Base delimiter
        content_height: Content height in pixels

    Returns:
        Sized delimiter
    """
    return delimiter_sizer.select_delimiter_size(delimiter, content_height)
