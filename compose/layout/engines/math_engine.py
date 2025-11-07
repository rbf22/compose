# compose/layout/engines/math_engine.py
"""
Mathematical expression layout engine.

This module implements the core layout algorithms for mathematical
expressions, following TeX's approach to mathematical typesetting.
"""

from typing import List, Optional, Tuple
from ..box_model import MathBox, BoxType, Dimensions, GlueSpace, create_fraction_box
from ..font_metrics import MathFontMetrics, FontStyle, default_math_font


class MathLayoutEngine:
    """
    Core mathematical layout engine.
    
    This class implements TeX's mathematical layout algorithms,
    including proper spacing, positioning, and sizing of mathematical
    elements.
    """
    
    def __init__(self, font_metrics: Optional[MathFontMetrics] = None):
        self.font_metrics = font_metrics or default_math_font
        self.display_style = False  # True for display math, False for inline
    
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
        params = self.font_metrics.get_font_parameters()
        
        # Scale numerator and denominator for fraction context
        num_scaled = self._scale_for_fraction(numerator, is_numerator=True)
        den_scaled = self._scale_for_fraction(denominator, is_numerator=False)
        
        # Create the fraction box
        fraction = create_fraction_box(num_scaled, den_scaled, params.rule_thickness)
        
        # Adjust positioning based on display vs inline style
        if self.display_style:
            fraction.shift_up = params.num_shift_up
        else:
            fraction.shift_up = params.num_shift_up * 0.8
        
        return fraction
    
    def layout_superscript(self, base: MathBox, superscript: MathBox) -> MathBox:
        """Layout superscript with proper positioning."""
        params = self.font_metrics.get_font_parameters()
        
        # Scale superscript
        sup_scaled = self._scale_for_script(superscript)
        
        # Calculate positioning
        sup_shift = max(
            params.sup_shift_up,
            base.dimensions.height - params.sup_drop
        )
        
        # Position superscript
        sup_scaled.shift_up = sup_shift
        sup_scaled.shift_right = base.dimensions.width
        
        # Calculate composite dimensions
        total_width = base.dimensions.width + sup_scaled.dimensions.width
        total_height = max(
            base.dimensions.height,
            sup_shift + sup_scaled.dimensions.height
        )
        
        composite = MathBox(
            content=[base, sup_scaled],
            box_type=BoxType.SCRIPT,
            dimensions=Dimensions(total_width, total_height, base.dimensions.depth)
        )
        
        return composite
    
    def layout_subscript(self, base: MathBox, subscript: MathBox) -> MathBox:
        """Layout subscript with proper positioning."""
        params = self.font_metrics.get_font_parameters()
        
        # Scale subscript
        sub_scaled = self._scale_for_script(subscript)
        
        # Calculate positioning
        sub_shift = max(
            params.sub_shift_down,
            base.dimensions.depth + params.sub_drop
        )
        
        # Position subscript
        sub_scaled.shift_up = -sub_shift  # Negative = down
        sub_scaled.shift_right = base.dimensions.width
        
        # Calculate composite dimensions
        total_width = base.dimensions.width + sub_scaled.dimensions.width
        total_depth = max(
            base.dimensions.depth,
            sub_shift + sub_scaled.dimensions.depth
        )
        
        composite = MathBox(
            content=[base, sub_scaled],
            box_type=BoxType.SCRIPT,
            dimensions=Dimensions(total_width, base.dimensions.height, total_depth)
        )
        
        return composite
    
    def layout_subsuperscript(self, base: MathBox, subscript: MathBox, 
                            superscript: MathBox) -> MathBox:
        """Layout both subscript and superscript."""
        params = self.font_metrics.get_font_parameters()
        
        # Scale scripts
        sup_scaled = self._scale_for_script(superscript)
        sub_scaled = self._scale_for_script(subscript)
        
        # Calculate positioning with collision avoidance
        sup_shift = max(
            params.sup_shift_up,
            base.dimensions.height - params.sup_drop
        )
        
        sub_shift = max(
            params.sub_shift_down,
            base.dimensions.depth + params.sub_drop
        )
        
        # Check for collision and adjust if necessary
        gap = sup_shift + sub_shift - (sup_scaled.dimensions.depth + sub_scaled.dimensions.height)
        min_gap = 4 * params.rule_thickness  # Minimum gap between scripts
        
        if gap < min_gap:
            adjustment = (min_gap - gap) / 2
            sup_shift += adjustment
            sub_shift += adjustment
        
        # Position scripts
        sup_scaled.shift_up = sup_shift
        sup_scaled.shift_right = base.dimensions.width
        
        sub_scaled.shift_up = -sub_shift
        sub_scaled.shift_right = base.dimensions.width
        
        # Calculate composite dimensions
        script_width = max(sup_scaled.dimensions.width, sub_scaled.dimensions.width)
        total_width = base.dimensions.width + script_width
        
        total_height = max(
            base.dimensions.height,
            sup_shift + sup_scaled.dimensions.height
        )
        
        total_depth = max(
            base.dimensions.depth,
            sub_shift + sub_scaled.dimensions.depth
        )
        
        composite = MathBox(
            content=[base, sup_scaled, sub_scaled],
            box_type=BoxType.SCRIPT,
            dimensions=Dimensions(total_width, total_height, total_depth)
        )
        
        return composite
    
    def _apply_spacing_rules(self, boxes: List[MathBox]) -> List[MathBox]:
        """Apply TeX spacing rules between adjacent boxes."""
        if len(boxes) <= 1:
            return boxes
        
        result = [boxes[0]]
        
        for i in range(1, len(boxes)):
            prev_box = boxes[i-1]
            curr_box = boxes[i]
            
            # Get spacing between box types
            spacing = self.font_metrics.get_operator_spacing(
                prev_box.box_type.value,
                curr_box.box_type.value
            )
            
            if spacing > 0:
                # Insert glue space
                curr_box.left_glue = GlueSpace(
                    natural_width=spacing,
                    stretch=spacing * 0.5,
                    shrink=spacing * 0.3
                )
            
            result.append(curr_box)
        
        return result
    
    def _create_composite_box(self, boxes: List[MathBox]) -> MathBox:
        """Create a composite box containing multiple boxes."""
        if not boxes:
            return self._create_empty_box()
        
        # Calculate total dimensions
        total_width = sum(box.total_width() for box in boxes)
        max_height = max(box.dimensions.height + box.shift_up for box in boxes)
        max_depth = max(box.dimensions.depth - box.shift_up for box in boxes)
        
        # Position boxes horizontally
        x_offset = 0
        positioned_boxes = []
        
        for box in boxes:
            box.shift_right = x_offset
            positioned_boxes.append(box)
            x_offset += box.total_width()
        
        return MathBox(
            content=positioned_boxes,
            box_type=BoxType.ATOM,  # Composite acts as atom
            dimensions=Dimensions(total_width, max_height, max_depth)
        )
    
    def _scale_for_fraction(self, box: MathBox, is_numerator: bool) -> MathBox:
        """Scale a box for use in a fraction."""
        # In TeX, fraction contents are typically in script style
        scale_factor = 0.8 if self.display_style else 0.7
        
        scaled_box = MathBox(
            content=box.content,
            box_type=box.box_type,
            dimensions=Dimensions(
                box.dimensions.width * scale_factor,
                box.dimensions.height * scale_factor,
                box.dimensions.depth * scale_factor
            ),
            font_size=box.font_size * scale_factor
        )
        
        return scaled_box
    
    def _scale_for_script(self, box: MathBox) -> MathBox:
        """Scale a box for use as superscript or subscript."""
        # Scripts are typically 70% of the base size
        scale_factor = 0.7
        
        scaled_box = MathBox(
            content=box.content,
            box_type=box.box_type,
            dimensions=Dimensions(
                box.dimensions.width * scale_factor,
                box.dimensions.height * scale_factor,
                box.dimensions.depth * scale_factor
            ),
            font_size=box.font_size * scale_factor
        )
        
        return scaled_box
    
    def _create_empty_box(self) -> MathBox:
        """Create an empty box."""
        return MathBox(
            content="",
            box_type=BoxType.ATOM,
            dimensions=Dimensions(0, 0, 0)
        )


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
        from ..content.math_parser import MathExpressionParser
        
        parser = MathExpressionParser()
        boxes = []
        
        for element in elements:
            box = parser.parse_atom(element)
            boxes.append(box)
        
        return self.engine.layout_expression(boxes)
    
    def layout_fraction(self, numerator_text: str, denominator_text: str) -> MathBox:
        """Layout a fraction from text strings."""
        from ..content.math_parser import MathExpressionParser
        
        parser = MathExpressionParser()
        num_box = parser.parse_expression(numerator_text)
        den_box = parser.parse_expression(denominator_text)
        
        return self.engine.layout_fraction(num_box, den_box)
    
    def layout_power(self, base_text: str, exponent_text: str) -> MathBox:
        """Layout base^exponent."""
        from ..content.math_parser import MathExpressionParser
        
        parser = MathExpressionParser()
        base_box = parser.parse_expression(base_text)
        exp_box = parser.parse_expression(exponent_text)
        
        return self.engine.layout_superscript(base_box, exp_box)
