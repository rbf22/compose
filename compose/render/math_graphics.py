# compose/render/math_graphics.py
"""
TeX-style PDF graphics renderer for mathematical expressions.

This module converts MathBox structures into PDF graphics commands,
rendering proper mathematical typesetting with fractions, radicals,
superscripts, and other mathematical elements.
"""

from typing import List, Tuple, Optional
from ..layout.box_model import MathBox, BoxType
from ..layout.universal_box import Dimensions


class MathGraphicsRenderer:
    """
    Renders MathBox structures to PDF graphics commands.
    
    This renderer takes the structured MathBox tree and emits PDF
    drawing commands to render proper mathematical typesetting,
    including fractions with horizontal bars, radicals, and proper
    glyph positioning.
    """
    
    def __init__(self, pdf_renderer=None):
        """
        Initialize the math graphics renderer.
        
        Args:
            pdf_renderer: Reference to the PDF renderer for accessing
                         helper methods like _measure_text_width, etc.
        """
        self.pdf_renderer = pdf_renderer
        self.commands = []
        self.current_x = 0.0
        self.current_y = 0.0
        self.baseline_y = 0.0
    
    def render_math_box(self, math_box: MathBox, x: float, y: float, 
                       baseline_y: float) -> Tuple[List[str], float]:
        """
        Render a MathBox to PDF commands.
        
        Args:
            math_box: The MathBox structure to render
            x: X position (left edge)
            y: Y position (top of box)
            baseline_y: Y position of the baseline
            
        Returns:
            Tuple of (pdf_commands, total_width_used)
        """
        self.commands = []
        self.current_x = x
        self.current_y = y
        self.baseline_y = baseline_y
        
        width = self._render_box(math_box, x, baseline_y)
        
        return self.commands, width
    
    def _render_box(self, box: MathBox, x: float, baseline_y: float) -> float:
        """
        Recursively render a box and return its width.
        
        Args:
            box: The MathBox to render
            x: X position for rendering
            baseline_y: Y position of baseline
            
        Returns:
            Width of rendered box
        """
        # Handle composite boxes (list of items)
        if box.is_composite() and box.box_type == BoxType.ATOM:
            return self._render_composite_atom(box, x, baseline_y)
        
        if box.box_type == BoxType.ATOM:
            return self._render_atom(box, x, baseline_y)
        elif box.box_type == BoxType.OPERATOR:
            return self._render_operator(box, x, baseline_y)
        elif box.box_type == BoxType.RELATION:
            return self._render_relation(box, x, baseline_y)
        elif box.box_type == BoxType.FRACTION:
            return self._render_fraction(box, x, baseline_y)
        elif box.box_type == BoxType.RADICAL:
            return self._render_radical(box, x, baseline_y)
        elif box.box_type == BoxType.SCRIPT:
            return self._render_script(box, x, baseline_y)
        elif box.box_type == BoxType.LARGE_OP:
            return self._render_large_operator(box, x, baseline_y)
        elif box.box_type == BoxType.OPENING or box.box_type == BoxType.CLOSING:
            return self._render_delimiter(box, x, baseline_y)
        elif box.box_type == BoxType.PUNCTUATION:
            return self._render_punctuation(box, x, baseline_y)
        elif box.box_type == BoxType.ACCENT:
            return self._render_accent(box, x, baseline_y)
        else:
            # Fallback: render as atom
            return self._render_atom(box, x, baseline_y)
    
    def _render_composite_atom(self, box: MathBox, x: float, baseline_y: float) -> float:
        """
        Render a composite atom box (sequence of items laid out horizontally).
        
        This handles expressions like "E = mc^2" which are parsed as a list
        of boxes that need to be rendered sequentially.
        """
        if not isinstance(box.content, list):
            return 0.0
        
        current_x = x
        total_width = 0.0
        
        for item in box.content:
            # Render each item
            item_width = self._render_box(item, current_x, baseline_y)
            current_x += item_width
            total_width += item_width
            
            # Add spacing from glue if present
            if item.right_glue:
                glue_width = item.right_glue.natural_width
                current_x += glue_width
                total_width += glue_width
        
        return total_width
    
    def _render_atom(self, box: MathBox, x: float, baseline_y: float) -> float:
        """Render an atomic box (single character/symbol)."""
        if not isinstance(box.content, str):
            return 0.0
        
        # Apply positioning adjustments
        render_x = x + box.shift_right
        render_y = baseline_y + box.shift_up
        
        # Get font information
        font_name = self._get_font_name(box.font_style)
        font_size = box.font_size
        
        # Emit text rendering commands
        self.commands.extend([
            "BT",
            "0 0 0 rg",
            f"/{font_name} {font_size} Tf",
            f"1 0 0 1 {render_x} {render_y} Tm",
            f"{self._to_pdf_literal(box.content)} Tj",
            "ET"
        ])
        
        return box.dimensions.width
    
    def _render_operator(self, box: MathBox, x: float, baseline_y: float) -> float:
        """Render an operator with proper spacing."""
        # Operators are rendered like atoms but with spacing
        return self._render_atom(box, x, baseline_y)
    
    def _render_relation(self, box: MathBox, x: float, baseline_y: float) -> float:
        """Render a relation symbol with proper spacing."""
        # Relations are rendered like atoms but with spacing
        return self._render_atom(box, x, baseline_y)
    
    def _render_fraction(self, box: MathBox, x: float, baseline_y: float) -> float:
        """
        Render a fraction with numerator, denominator, and horizontal bar.
        
        Fractions are rendered with:
        - Numerator positioned above the baseline
        - Denominator positioned below the baseline
        - Horizontal rule between them
        """
        if not isinstance(box.content, list) or len(box.content) < 2:
            return 0.0
        
        numerator = box.content[0]
        denominator = box.content[1]
        
        # Calculate positioning
        rule_thickness = 0.4  # Points
        spacing = 2.0  # Space above/below rule
        
        # Numerator is positioned above baseline
        num_baseline = baseline_y + numerator.dimensions.height + spacing + rule_thickness
        num_width = self._render_box(numerator, x, num_baseline)
        
        # Denominator is positioned below baseline
        den_baseline = baseline_y - denominator.dimensions.depth - spacing - rule_thickness
        den_width = self._render_box(denominator, x, den_baseline)
        
        # Draw horizontal rule
        rule_x1 = x
        rule_x2 = x + max(num_width, den_width)
        rule_y = baseline_y - rule_thickness / 2
        
        self._draw_line(rule_x1, rule_y, rule_x2, rule_y, rule_thickness)
        
        # Return total width
        return max(num_width, den_width)
    
    def _render_radical(self, box: MathBox, x: float, baseline_y: float) -> float:
        """
        Render a radical (square root) with radical sign.
        
        Radicals include:
        - Radical sign (√)
        - Content under the radical
        - Optional index (for nth roots)
        """
        if not isinstance(box.content, list) or len(box.content) == 0:
            return 0.0
        
        # For now, render the content and add a radical sign
        # Full implementation would draw the radical sign glyph
        content = box.content[0]
        
        # Render the content
        content_width = self._render_box(content, x + 8, baseline_y)
        
        # Draw radical sign (simplified as vertical line + horizontal line)
        # This is a placeholder - real radical signs are more complex
        radical_x = x + 2
        radical_y_top = baseline_y + content.dimensions.height + 2
        radical_y_bottom = baseline_y - content.dimensions.depth - 2
        
        # Vertical stroke of radical
        self._draw_line(radical_x, radical_y_bottom, radical_x + 3, radical_y_top, 0.5)
        
        # Horizontal stroke of radical
        self._draw_line(radical_x + 3, radical_y_top, x + 8 + content_width, radical_y_top, 0.5)
        
        return 8 + content_width
    
    def _render_script(self, box: MathBox, x: float, baseline_y: float) -> float:
        """
        Render superscripts and subscripts.
        
        Scripts are positioned relative to the base box:
        - Superscripts: positioned above and to the right
        - Subscripts: positioned below and to the right
        """
        if not isinstance(box.content, list) or len(box.content) == 0:
            return 0.0
        
        # First element is the base
        base = box.content[0]
        base_width = self._render_box(base, x, baseline_y)
        
        # Remaining elements are scripts
        script_x = x + base_width + 1  # Small space after base
        script_font_size = base.font_size * 0.7  # Scripts are smaller
        
        for i, script in enumerate(box.content[1:]):
            if i == 0:  # Superscript
                script_baseline = baseline_y + base.dimensions.height * 0.5
            else:  # Subscript
                script_baseline = baseline_y - base.dimensions.depth * 0.5
            
            # Temporarily adjust font size for script
            original_size = script.font_size
            script.font_size = script_font_size
            script_width = self._render_box(script, script_x, script_baseline)
            script.font_size = original_size
            
            script_x += script_width + 1
        
        return base_width + (script_x - x - base_width)
    
    def _render_large_operator(self, box: MathBox, x: float, baseline_y: float) -> float:
        """Render large operators (∫, ∑, ∏) with proper sizing."""
        # Large operators are rendered at a larger size
        return self._render_atom(box, x, baseline_y)
    
    def _render_delimiter(self, box: MathBox, x: float, baseline_y: float) -> float:
        """Render opening/closing delimiters."""
        return self._render_atom(box, x, baseline_y)
    
    def _render_punctuation(self, box: MathBox, x: float, baseline_y: float) -> float:
        """Render punctuation marks."""
        return self._render_atom(box, x, baseline_y)
    
    def _render_accent(self, box: MathBox, x: float, baseline_y: float) -> float:
        """Render math accents (hats, bars, dots, etc.)."""
        if not isinstance(box.content, list) or len(box.content) == 0:
            return 0.0
        
        # Render the base content
        content = box.content[0]
        width = self._render_box(content, x, baseline_y)
        
        # Draw accent above the content
        # This is simplified - real accents would use proper glyphs
        accent_y = baseline_y + content.dimensions.height + 1
        self._draw_line(x, accent_y, x + width, accent_y, 0.3)
        
        return width
    
    def _draw_line(self, x1: float, y1: float, x2: float, y2: float, 
                   thickness: float = 0.5):
        """
        Draw a line in PDF.
        
        Args:
            x1, y1: Starting point
            x2, y2: Ending point
            thickness: Line thickness in points
        """
        self.commands.extend([
            "q",  # Save graphics state
            f"{thickness} w",  # Set line width
            "0 0 0 RG",  # Set stroke color to black
            f"{x1} {y1} m",  # Move to start point
            f"{x2} {y2} l",  # Line to end point
            "S",  # Stroke the path
            "Q"  # Restore graphics state
        ])
    
    def _get_font_name(self, font_style: str) -> str:
        """Get PDF font name based on style."""
        style_map = {
            "normal": "Helvetica",
            "italic": "Helvetica-Oblique",
            "bold": "Helvetica-Bold",
            "bold_italic": "Helvetica-BoldOblique",
        }
        return style_map.get(font_style, "Helvetica")
    
    def _to_pdf_literal(self, text: str) -> str:
        """Convert text to PDF string literal format."""
        # Escape special characters
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        return f"({escaped})"
