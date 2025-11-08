# compose/layout/engines/math_engine.py
"""
Mathematical expression layout engine.

This module implements the core layout algorithms for mathematical
expressions, following TeX's approach to mathematical typesetting.
"""

from typing import List, Dict, Any, Optional, Tuple
from ..universal_box import Dimensions
from ..box_model import (
    MathBox,
    BoxType,
    create_atom_box,
    create_operator_box,
    create_fraction_box,
    MathSpacing,
)
from ..font_metrics import MathFontMetrics
from ..math_layout import MathLayoutEngine as _AdvancedMathLayout, MathStyle, layout_matrix, layout_fraction as layout_fraction_simple, layout_large_operator, layout_radical
from ..knuth_plass import MathKnuthPlassBreaker


class MathLayoutEngine:
    """
    Core mathematical layout engine.
    
    This class implements TeX's mathematical layout algorithms,
    including proper spacing, positioning, and sizing of mathematical
    elements.
    """
    
    def __init__(self):
        self.display_style = False  # True for display math, False for inline
        # Provide default math font metrics for parser/tests
        self.font_metrics = MathFontMetrics()
        # Advanced math layout (kept for convenience functions)
        self._advanced = _AdvancedMathLayout()
    
    def layout_expression(self, boxes: List[MathBox]) -> MathBox:
        """
        Layout a sequence of mathematical boxes into a single composite box.
        
        This is the main entry point for mathematical layout.
        """
        if not boxes:
            return self._create_empty_box()
        
        if len(boxes) == 1:
            return boxes[0]
        
        # Apply spacing rules between adjacent boxes
        spaced_boxes = self._apply_spacing_rules(boxes)
        
        # Create composite box
        return self._create_composite_box(spaced_boxes)
    
    def layout_fraction(self, numerator: MathBox, denominator: MathBox) -> MathBox:
        """
        Layout a fraction with proper positioning and rule thickness.
        
        This implements TeX's fraction layout algorithm.
        """
        # Use classic MathBox fraction for compatibility with tests
        return create_fraction_box(numerator, denominator)
    
    def layout_superscript(self, base: MathBox, superscript: MathBox) -> MathBox:
        """Layout superscript as a SCRIPT MathBox."""
        # Approximate script dimensions
        width = base.dimensions.width + superscript.dimensions.width * 0.6
        height = max(base.dimensions.height + superscript.dimensions.height * 0.6, base.dimensions.height)
        depth = base.dimensions.depth
        return MathBox(content=[base, superscript], box_type=BoxType.SCRIPT, dimensions=Dimensions(width, height, depth))

    def layout_subscript(self, base: MathBox, subscript: MathBox) -> MathBox:
        """Layout subscript as a SCRIPT MathBox."""
        width = base.dimensions.width + subscript.dimensions.width * 0.6
        height = base.dimensions.height
        depth = max(base.dimensions.depth + subscript.dimensions.height * 0.6, base.dimensions.depth)
        return MathBox(content=[base, subscript], box_type=BoxType.SCRIPT, dimensions=Dimensions(width, height, depth))

    def layout_subsuperscript(self, base: MathBox, subscript: MathBox,
                            superscript: MathBox) -> MathBox:
        """Layout both subscript and superscript as a SCRIPT MathBox."""
        width = base.dimensions.width + max(subscript.dimensions.width, superscript.dimensions.width) * 0.6
        height = max(base.dimensions.height + superscript.dimensions.height * 0.6, base.dimensions.height)
        depth = max(base.dimensions.depth + subscript.dimensions.height * 0.6, base.dimensions.depth)
        return MathBox(content=[base, superscript, subscript], box_type=BoxType.SCRIPT, dimensions=Dimensions(width, height, depth))
    
    def layout_matrix(self, rows: List[List[str]], style: MathStyle = MathStyle.DISPLAY):
        """Layout a matrix with proper alignment"""
        # Delegate to advanced layout for matrix (used by other tests)
        return layout_matrix(rows, style)

    def layout_large_operator(self, operator: str, lower_limit: Optional[str] = None,
                            upper_limit: Optional[str] = None, style: MathStyle = MathStyle.DISPLAY):
        """Layout a large operator with limits"""
        return layout_large_operator(operator, lower_limit, upper_limit, style)

    def layout_radical(self, radicand: str, index: Optional[str] = None,
                      style: MathStyle = MathStyle.INLINE):
        """Layout a radical expression"""
        return layout_radical(radicand, index, style)

    def apply_knuth_plass_breaking(self, text: str, line_width: float) -> List[str]:
        """
        Apply Knuth-Plass line breaking to mathematical text.

        Args:
            text: Mathematical text to break
            line_width: Target line width

        Returns:
            List of line strings
        """
        breaker = MathKnuthPlassBreaker(line_width)
        # This is a simplified implementation - would need proper breakpoint creation
        # For now, just return the original text as a single line
        return [text]

    # Convenience methods for advanced layouts
    def create_matrix_box(self, rows: List[List[str]]):
        """Create a matrix box"""
        return self.layout_matrix(rows)

    def create_large_operator_box(self, operator: str, lower_limit: Optional[str] = None,
                                upper_limit: Optional[str] = None):
        """Create a large operator box with limits"""
        return self.layout_large_operator(operator, lower_limit, upper_limit)

    def create_radical_box(self, radicand: str, index: Optional[str] = None):
        """Create a radical box"""
        return self.layout_radical(radicand, index)
    
    def _apply_spacing_rules(self, boxes: List[MathBox]) -> List[MathBox]:
        """Apply simplified TeX spacing rules by adding glue to operator/relation boxes."""
        if len(boxes) <= 1:
            return boxes
        
        # Clone list to avoid mutating inputs
        result = list(boxes)
        for i in range(1, len(result) - 0):
            prev_box = result[i - 1]
            curr_box = result[i]
            # Apply medium space for operator, thick for relation
            if curr_box.box_type == BoxType.OPERATOR:
                space = MathSpacing.MEDIUM_SPACE
                curr_box.left_glue = curr_box.left_glue or curr_box.left_glue or None
                prev_box.right_glue = prev_box.right_glue or None
            elif curr_box.box_type == BoxType.RELATION:
                space = MathSpacing.THICK_SPACE
                curr_box.left_glue = curr_box.left_glue or curr_box.left_glue or None
                prev_box.right_glue = prev_box.right_glue or None
            else:
                continue
            # Set glue explicitly
            from ..universal_box import GlueSpace as _Glue
            if curr_box.left_glue is None:
                curr_box.left_glue = _Glue(space, space / 2.0, space / 3.0)
            if prev_box.right_glue is None:
                prev_box.right_glue = _Glue(space, space / 2.0, space / 3.0)
        return result
    
    def _create_composite_box(self, boxes: List[MathBox]) -> MathBox:
        """Create a composite MathBox containing multiple boxes."""
        if not boxes:
            return self._create_empty_box()
        total_width = sum(b.total_width() for b in boxes)
        max_height = max(b.dimensions.height for b in boxes)
        max_depth = max(b.dimensions.depth for b in boxes)
        return MathBox(content=boxes, box_type=BoxType.ATOM, dimensions=Dimensions(total_width, max_height, max_depth))
    
    def _create_empty_box(self) -> MathBox:
        """Create an empty MathBox."""
        return MathBox(content="", box_type=BoxType.ATOM, dimensions=Dimensions(0, 0, 0))


class ExpressionLayout:
    """
    High-level interface for mathematical expression layout.
    
    This class provides a convenient API for laying out common
    mathematical structures.
    """
    
    def __init__(self, display_style: bool = False):
        self.engine = MathLayoutEngine()
        self.engine.display_style = display_style
    
    def layout_simple_expression(self, elements: List[str]) -> MathBox:
        """Layout a simple sequence of mathematical elements."""
        boxes: List[MathBox] = []
        for element in elements:
            if element in {"+", "-", "*", "/", "=", ","}:
                boxes.append(create_operator_box(element))
            else:
                boxes.append(create_atom_box(element))
        return self.engine.layout_expression(boxes)
    
    def layout_fraction(self, numerator_text: str, denominator_text: str) -> MathBox:
        """Layout a fraction from text strings."""
        num_box = create_atom_box(numerator_text)
        den_box = create_atom_box(denominator_text)
        return self.engine.layout_fraction(num_box, den_box)
    
    def layout_power(self, base_text: str, exponent_text: str) -> MathBox:
        """Layout base^exponent."""
        base_box = create_atom_box(base_text)
        exp_box = create_atom_box(exponent_text)
        return self.engine.layout_superscript(base_box, exp_box)
