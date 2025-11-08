# compose/render/fractions.py
"""
Fraction layout engine for mathematical expressions.
Handles proper fraction bars, nested fractions, and complex fraction layouts.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from ..layout.tex_boxes import HBox, VBox, CharBox, Glue, Box
from ..cache_system import math_cache


class FractionLayoutEngine:
    """
    Layout engine for mathematical fractions with proper alignment and sizing.
    Handles nested fractions, mixed numbers, and complex fraction expressions.
    """

    def __init__(self):
        self.fraction_bar_thickness = 1  # pixels
        self.fraction_rule_width = 0.05  # relative to font size
        self.numerator_gap = 3  # pixels between numerator and fraction bar
        self.denominator_gap = 3  # pixels between fraction bar and denominator

    @performance_monitor.time_operation("fraction_layout")
    def layout_fraction(self, numerator: str, denominator: str,
                       display_style: bool = True) -> Box:
        """
        Layout a fraction with proper alignment and spacing.

        Args:
            numerator: Numerator content
            denominator: Denominator content
            display_style: Whether to use display style (larger, more spacing)

        Returns:
            Box containing the laid out fraction
        """
        # Create numerator and denominator boxes
        num_box = self._create_fraction_component(numerator, display_style, "numerator")
        den_box = self._create_fraction_component(denominator, display_style, "denominator")

        # Calculate fraction dimensions
        width = max(num_box.width, den_box.width)
        height = num_box.height + den_box.height + self.fraction_bar_thickness
        height += self.numerator_gap + self.denominator_gap

        # Create fraction container
        fraction_box = VBox()
        fraction_box.width = width
        fraction_box.height = height

        # Add numerator
        num_x = (width - num_box.width) // 2  # Center numerator
        num_box._x_offset = num_x
        fraction_box.add_box(num_box)

        # Add gap above fraction bar
        if self.numerator_gap > 0:
            fraction_box.add_box(Glue(height=self.numerator_gap))

        # Add fraction bar
        bar_box = self._create_fraction_bar(width)
        fraction_box.add_box(bar_box)

        # Add gap below fraction bar
        if self.denominator_gap > 0:
            fraction_box.add_box(Glue(height=self.denominator_gap))

        # Add denominator
        den_x = (width - den_box.width) // 2  # Center denominator
        den_box._x_offset = den_x
        fraction_box.add_box(den_box)

        return fraction_box

    def _create_fraction_component(self, content: str, display_style: bool,
                                 component_type: str) -> Box:
        """
        Create a fraction component (numerator or denominator).

        Args:
            content: Component content
            display_style: Whether using display style
            component_type: "numerator" or "denominator"

        Returns:
            Box for the component
        """
        if not content:
            content = "1"  # Default for empty components

        # Estimate size (simplified - would use font metrics in full implementation)
        width = max(20, len(content) * 8)
        height = 18 if display_style else 14

        box = Box(width=width, height=height, box_type=f"fraction_{component_type}")
        box._content = content
        box._display_style = display_style

        return box

    def _create_fraction_bar(self, width: int) -> Box:
        """Create the fraction bar (horizontal rule)."""
        bar_box = Box(width=width, height=self.fraction_bar_thickness, box_type="fraction_bar")
        bar_box._color = "#000000"  # Black bar
        return bar_box


class SubSuperscriptLayoutEngine:
    """
    Layout engine for subscripts and superscripts with proper positioning.
    Handles complex nested scripts and mathematical notation.
    """

    def __init__(self):
        self.subscript_offset = 0.3  # Baseline offset for subscripts (relative)
        self.superscript_offset = 0.6  # Baseline offset for superscripts (relative)
        self.script_scale = 0.7  # Size scale for scripts
        self.script_gap = 1  # Gap between base and scripts

    @performance_monitor.time_operation("script_layout")
    def layout_with_scripts(self, base: str, subscript: str = None,
                          superscript: str = None, display_style: bool = True) -> Box:
        """
        Layout an expression with subscripts and superscripts.

        Args:
            base: Base expression
            subscript: Subscript content (optional)
            superscript: Superscript content (optional)
            display_style: Whether to use display style

        Returns:
            Box containing the laid out expression
        """
        # Create base box
        base_box = self._create_base_box(base, display_style)

        # Create script boxes
        sub_box = self._create_script_box(subscript, display_style, "sub") if subscript else None
        sup_box = self._create_script_box(superscript, display_style, "super") if superscript else None

        # Calculate total dimensions
        width = base_box.width
        height = base_box.height

        if sub_box:
            width += sub_box.width + self.script_gap
            # Subscript extends below baseline
            height = max(height, base_box.height + sub_box.height - base_box.height * self.subscript_offset)

        if sup_box:
            width += sup_box.width + self.script_gap
            # Superscript extends above
            height = max(height, sup_box.height + base_box.height * self.superscript_offset)

        # Create horizontal layout
        hbox = HBox()
        hbox.width = width
        hbox.height = height

        # Add base
        base_box._baseline_offset = 0
        hbox.add_box(base_box)

        # Add scripts
        if sup_box:
            sup_box._baseline_offset = base_box.height * self.superscript_offset
            hbox.add_box(sup_box)

        if sub_box:
            sub_box._baseline_offset = -base_box.height * self.subscript_offset
            hbox.add_box(sub_box)

        return hbox

    def _create_base_box(self, content: str, display_style: bool) -> Box:
        """Create the base expression box."""
        width = max(15, len(content) * 9)
        height = 20 if display_style else 16

        box = Box(width=width, height=height, box_type="script_base")
        box._content = content
        box._display_style = display_style

        return box

    def _create_script_box(self, content: str, display_style: bool, script_type: str) -> Box:
        """Create a subscript or superscript box."""
        width = max(10, len(content) * 7)  # Smaller than base
        height = int((16 if display_style else 12) * self.script_scale)

        box = Box(width=width, height=height, box_type=f"script_{script_type}")
        box._content = content
        box._display_style = display_style
        box._script_type = script_type

        return box


class ComplexExpressionLayoutEngine:
    """
    Layout engine for complex mathematical expressions combining fractions,
    scripts, operators, and other elements.
    """

    def __init__(self):
        self.fraction_engine = FractionLayoutEngine()
        self.script_engine = SubSuperscriptLayoutEngine()

    def layout_complex_expression(self, expression: str) -> Box:
        """
        Layout a complex mathematical expression with fractions, scripts, etc.

        Args:
            expression: LaTeX expression

        Returns:
            Box containing the laid out expression
        """
        # Parse expression into components (simplified)
        components = self._parse_expression_components(expression)

        # Layout components (simplified - would be more complex in full implementation)
        if len(components) == 1:
            return self._create_simple_box(components[0])
        else:
            return self._layout_component_list(components)

    def _parse_expression_components(self, expression: str) -> List[str]:
        """
        Parse expression into components (simplified tokenization).

        Args:
            expression: LaTeX expression

        Returns:
            List of expression components
        """
        # Simple parsing - split by operators and spaces
        # In a full implementation, this would use proper LaTeX parsing
        components = re.findall(r'\S+', expression)
        return components

    def _create_simple_box(self, content: str) -> Box:
        """Create a simple expression box."""
        width = max(15, len(content) * 8)
        height = 20

        box = Box(width=width, height=height, box_type="expression")
        box._content = content

        return box

    def _layout_component_list(self, components: List[str]) -> Box:
        """Layout a list of expression components."""
        if not components:
            return self._create_simple_box("")

        # Create horizontal layout for components
        hbox = HBox()
        total_width = 0
        max_height = 0

        for component in components:
            comp_box = self._create_simple_box(component)
            hbox.add_box(comp_box)
            total_width += comp_box.width
            max_height = max(max_height, comp_box.height)

            # Add spacing between components
            if component != components[-1]:
                hbox.add_box(Glue(width=3))

        hbox.width = total_width + (len(components) - 1) * 3
        hbox.height = max_height

        return hbox


# Global instances
fraction_engine = FractionLayoutEngine()
script_engine = SubSuperscriptLayoutEngine()
complex_expression_engine = ComplexExpressionLayoutEngine()


def render_fraction(numerator: str, denominator: str, display_style: bool = True) -> Optional[str]:
    """
    Render a fraction to SVG.

    Args:
        numerator: Numerator content
        denominator: Denominator content
        display_style: Whether to use display style

    Returns:
        SVG data URL if successful
    """
    # Check cache first
    cache_key = f"fraction:{numerator}:{denominator}:{display_style}"
    cached_result = math_cache.get_rendered_math(cache_key)
    if cached_result:
        return cached_result

    # Generate layout
    box = fraction_engine.layout_fraction(numerator, denominator, display_style)

    # Convert to SVG
    svg = _box_to_svg(box)

    # Cache result
    math_cache.set_rendered_math(cache_key, display_style, svg)

    return svg


def render_with_scripts(base: str, subscript: str = None,
                       superscript: str = None, display_style: bool = True) -> Optional[str]:
    """
    Render an expression with sub/superscripts to SVG.

    Args:
        base: Base expression
        subscript: Subscript content
        superscript: Superscript content
        display_style: Whether to use display style

    Returns:
        SVG data URL if successful
    """
    # Check cache first
    cache_key = f"scripts:{base}:{subscript}:{superscript}:{display_style}"
    cached_result = math_cache.get_rendered_math(cache_key)
    if cached_result:
        return cached_result

    # Generate layout
    box = script_engine.layout_with_scripts(base, subscript, superscript, display_style)

    # Convert to SVG
    svg = _box_to_svg(box)

    # Cache result
    math_cache.set_rendered_math(cache_key, display_style, svg)

    return svg


def _box_to_svg(box: Box) -> str:
    """
    Convert a box layout to SVG (simplified implementation).
    """
    width = box.width + 20
    height = box.height + 20

    svg_parts = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']

    # Background
    svg_parts.append(f'<rect width="100%" height="100%" fill="#ffffff"/>')

    # Render box content based on type
    if hasattr(box, '_content'):
        svg_parts.append(f'<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-size="16px">{box._content}</text>')
    elif box.box_type == "fraction_bar":
        svg_parts.append(f'<line x1="10" y1="50%" x2="{width-10}" y2="50%" stroke="#000000" stroke-width="1"/>')

    svg_parts.append('</svg>')

    svg_content = '\n'.join(svg_parts)

    # Convert to data URL
    import base64
    svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{svg_base64}"
