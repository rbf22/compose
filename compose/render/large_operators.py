# compose/render/large_operators.py
"""
Large operator layout engine for mathematical expressions.
Handles integrals, sums, products with proper subscript/superscript positioning.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from ..layout.tex_boxes import HBox, VBox, CharBox, Glue, Box
from ..cache_system import math_cache


class LargeOperatorLayout:
    """
    Layout engine for large mathematical operators.
    Handles positioning of limits on integrals, sums, products, etc.
    """

    def __init__(self):
        # Define large operators and their Unicode symbols
        self.large_operators = {
            'int': '∫',
            'iint': '∬',
            'iiint': '∭',
            'oint': '∮',
            'sum': '∑',
            'prod': '∏',
            'coprod': '∐',
            'bigcap': '⋂',
            'bigcup': '⋃',
            'bigsqcap': '⨅',
            'bigsqcup': '⨆',
            'bigvee': '⋁',
            'bigwedge': '⋀',
            'bigodot': '⨀',
            'bigotimes': '⨂',
            'bigoplus': '⨁',
        }

        # Spacing parameters
        self.operator_width = 20
        self.operator_height = 30
        self.limit_offset = 8  # Distance from operator to limits
        self.script_size_ratio = 0.7  # Size ratio for sub/super scripts

    def layout_large_operator(self, operator: str, subscript: str = None,
                            superscript: str = None, display_style: bool = True) -> Box:
        """
        Layout a large operator with proper LaTeX-style limits positioning.

        Args:
            operator: Operator name (e.g., 'int', 'sum')
            subscript: Subscript content (lower limit)
            superscript: Superscript content (upper limit)
            display_style: Whether to use display style (limits above/below vs inline)

        Returns:
            Box containing the laid out operator
        """
        if operator not in self.large_operators:
            # Fallback for unknown operators
            return self._create_text_box(f"\\{operator}")

        symbol = self.large_operators[operator]

        # Determine limits positioning based on operator type and style
        if display_style and (subscript or superscript):
            # Display style: limits above and below
            return self._layout_display_limits(symbol, subscript, superscript, operator)
        else:
            # Inline style: limits as sub/super scripts
            return self._layout_inline_limits(symbol, subscript, superscript, operator)

    def _layout_display_limits(self, symbol: str, subscript: str = None,
                             superscript: str = None, operator: str = None) -> Box:
        """
        Layout operator with limits above and below (display style).
        Follows LaTeX conventions for different operator types.
        """
        # Create the operator symbol
        operator_box = self._create_operator_box(symbol, operator)

        # For certain operators, limits are always beside in LaTeX
        # (like integrals, which traditionally have limits beside)
        beside_operators = {'int', 'iint', 'iiint', 'oint'}

        if operator in beside_operators:
            return self._layout_limits_beside(operator_box, subscript, superscript)
        else:
            return self._layout_limits_above_below(operator_box, subscript, superscript)

    def _layout_limits_above_below(self, operator_box: Box, subscript: str = None,
                                 superscript: str = None) -> Box:
        """
        Layout limits above and below the operator (for sums, products, etc.)
        """
        # Create limit boxes
        sub_box = self._create_limit_box(subscript) if subscript else None
        sup_box = self._create_limit_box(superscript) if superscript else None

        # Calculate total dimensions
        width = operator_box.width
        if sub_box:
            width = max(width, sub_box.width)
        if sup_box:
            width = max(width, sup_box.width)

        height = operator_box.height
        if sub_box:
            height += sub_box.height + self.limit_offset
        if sup_box:
            height += sup_box.height + self.limit_offset

        # Create main container
        container = VBox()
        container.width = width
        container.height = height

        # Layout components from top to bottom
        current_y = 0

        # Superscript (above)
        if sup_box:
            # Center the superscript
            sup_x = (width - sup_box.width) // 2
            sup_box._x_offset = sup_x
            container.add_box(sup_box)
            current_y += sup_box.height + self.limit_offset

        # Operator symbol
        operator_x = (width - operator_box.width) // 2
        operator_box._x_offset = operator_x
        container.add_box(operator_box)
        current_y += operator_box.height

        # Subscript (below)
        if sub_box:
            current_y += self.limit_offset
            sub_x = (width - sub_box.width) // 2
            sub_box._x_offset = sub_x
            container.add_box(sub_box)

        return container

    def _layout_limits_beside(self, operator_box: Box, subscript: str = None,
                            superscript: str = None) -> Box:
        """
        Layout limits beside the operator (for integrals, etc.)
        Follows LaTeX integral notation conventions.
        """
        # Create limit boxes
        sub_box = self._create_script_box(subscript) if subscript else None
        sup_box = self._create_script_box(superscript) if superscript else None

        # Calculate dimensions
        width = operator_box.width
        height = operator_box.height

        # For integrals, limits are positioned to the right
        if sub_box:
            width += sub_box.width + 5  # Small gap
            height = max(height, sub_box.height + operator_box.height // 2)

        if sup_box:
            width += sup_box.width + 5  # Small gap
            height = max(height, sup_box.height + operator_box.height // 2)

        # Create horizontal layout
        hbox = HBox()
        hbox.width = width
        hbox.height = height

        # Add operator
        hbox.add_box(operator_box)

        # Add superscript and subscript positioned relative to operator
        if sup_box or sub_box:
            # Create a container for the limits
            limits_container = VBox()
            limits_container.width = max(sub_box.width if sub_box else 0,
                                       sup_box.width if sup_box else 0)
            limits_container.height = height

            # Position superscript above subscript
            current_y = 0
            if sup_box:
                sup_box._y_offset = operator_box.height // 4  # Position above center
                limits_container.add_box(sup_box)
                current_y += sup_box.height

            if sub_box:
                sub_y = operator_box.height // 2  # Position below center
                sub_box._y_offset = sub_y
                limits_container.add_box(sub_box)

            hbox.add_box(limits_container)

        return hbox

    def _layout_inline_limits(self, symbol: str, subscript: str = None,
                            superscript: str = None, operator: str = None) -> Box:
        """
        Layout operator with limits as sub/super scripts (inline style).
        """
        # Create the operator symbol
        operator_box = self._create_operator_box(symbol, operator)

        # Create script boxes
        sub_box = self._create_script_box(subscript) if subscript else None
        sup_box = self._create_script_box(superscript) if superscript else None

        # Calculate dimensions
        width = operator_box.width
        height = operator_box.height

        if sub_box:
            width += sub_box.width
            height = max(height, sub_box.height + operator_box.height // 2)

        if sup_box:
            width += sup_box.width
            height = max(height, sup_box.height + operator_box.height // 2)

        # Create horizontal layout
        hbox = HBox()
        hbox.width = width
        hbox.height = height

        # Add operator
        hbox.add_box(operator_box)

        # Add superscript (if present)
        if sup_box:
            # Position superscript above operator
            sup_box._baseline_offset = operator_box.height // 2
            hbox.add_box(sup_box)

        # Add subscript (if present)
        if sub_box:
            # Position subscript below operator
            sub_box._baseline_offset = -operator_box.height // 2
            hbox.add_box(sub_box)

        return hbox

    def _create_operator_box(self, symbol: str, operator: str = None) -> Box:
        """Create a box for the operator symbol."""
        box = Box(width=self.operator_width, height=self.operator_height, box_type="operator")
        box._symbol = symbol
        box._operator = operator  # Store operator type for styling
        box._font_size = 24  # Larger font for operators
        return box

    def _create_limit_box(self, content: str) -> Box:
        """Create a box for limit content (display style)."""
        # Estimate size (simplified)
        width = len(content) * 8
        height = 16
        box = Box(width=width, height=height, box_type="limit")
        box._content = content
        box._font_size = 14
        return box

    def _create_script_box(self, content: str) -> Box:
        """Create a box for script content (inline style)."""
        # Smaller size for scripts
        width = len(content) * 6
        height = 12
        box = Box(width=width, height=height, box_type="script")
        box._content = content
        box._font_size = 12
        return box

    def _create_text_box(self, text: str) -> Box:
        """Create a simple text box."""
        width = len(text) * 10
        height = 20
        box = Box(width=width, height=height, box_type="text")
        box._content = text
        return box


class RadicalLayout:
    """
    Layout engine for radical expressions (square roots, etc.).
    Handles proper vinculum (overline) positioning.
    """

    def __init__(self):
        self.radical_symbol = '√'
        self.vinculum_extra = 4  # Extra length of vinculum beyond content

    def layout_radical(self, content: str, index: str = None) -> Box:
        """
        Layout a radical expression.

        Args:
            content: Content under the radical
            index: Index (nth root), None for square root

        Returns:
            Box containing the radical layout
        """
        # Create content box
        content_box = self._create_content_box(content)

        # Create radical symbol box
        symbol_box = self._create_symbol_box()

        # Create vinculum (horizontal bar)
        vinculum_width = content_box.width + self.vinculum_extra * 2
        vinculum_box = Box(width=vinculum_width, height=2, box_type="vinculum")
        vinculum_box._color = "#000000"

        # Handle index (nth root)
        index_box = None
        if index:
            index_box = self._create_index_box(index)

        # Calculate total dimensions
        total_width = symbol_box.width + vinculum_width
        total_height = max(symbol_box.height, content_box.height + 4)  # 4 for vinculum spacing

        if index_box:
            total_width += index_box.width
            total_height = max(total_height, index_box.height + symbol_box.height // 2)

        # Create main container
        container = HBox()
        container.width = total_width
        container.height = total_height

        # Layout components
        current_x = 0

        # Index (if present) - positioned at top-left of radical symbol
        if index_box:
            index_box._y_offset = -symbol_box.height // 2
            container.add_box(index_box)
            current_x += index_box.width

        # Radical symbol - extends from top to bottom
        symbol_box._height = total_height
        container.add_box(symbol_box)
        current_x += symbol_box.width

        # Content with vinculum
        content_container = VBox()
        content_container.width = vinculum_width
        content_container.height = content_box.height + 6  # Space for vinculum

        # Vinculum at top
        vinculum_box._x_offset = self.vinculum_extra
        content_container.add_box(vinculum_box)

        # Content below vinculum
        content_box._x_offset = self.vinculum_extra
        content_container.add_box(content_box)

        container.add_box(content_container)

        return container

    def _create_content_box(self, content: str) -> Box:
        """Create box for radical content."""
        width = len(content) * 10
        height = 20
        box = Box(width=width, height=height, box_type="radical_content")
        box._content = content
        return box

    def _create_symbol_box(self) -> Box:
        """Create box for radical symbol."""
        width = 16
        height = 24
        box = Box(width=width, height=height, box_type="radical_symbol")
        box._symbol = self.radical_symbol
        return box

    def _create_index_box(self, index: str) -> Box:
        """Create box for radical index."""
        width = len(index) * 8
        height = 14
        box = Box(width=width, height=height, box_type="radical_index")
        box._content = index
        box._font_size = 12
        return box


# Global instances
large_operator_layout = LargeOperatorLayout()
radical_layout = RadicalLayout()


def render_large_operator(operator: str, subscript: str = None,
                         superscript: str = None, display_style: bool = True) -> Optional[str]:
    """
    Render a large operator to SVG.

    Args:
        operator: Operator name
        subscript: Lower limit
        superscript: Upper limit
        display_style: Whether to use display style

    Returns:
        SVG data URL if successful
    """
    # Check cache first
    cache_key = f"large_op:{operator}:{subscript}:{superscript}:{display_style}"
    cached_result = math_cache.get_rendered_math(cache_key)
    if cached_result:
        return cached_result

    # Generate new layout
    box = large_operator_layout.layout_large_operator(operator, subscript, superscript, display_style)

    # Convert to SVG (simplified - would need full rendering)
    svg = _box_to_svg(box)

    # Cache result
    math_cache.set_rendered_math(cache_key, display_style, svg)

    return svg


def render_radical(content: str, index: str = None) -> Optional[str]:
    """
    Render a radical expression to SVG.

    Args:
        content: Content under radical
        index: Root index (None for square root)

    Returns:
        SVG data URL if successful
    """
    # Check cache first
    cache_key = f"radical:{content}:{index}"
    cached_result = math_cache.get_rendered_math(cache_key)
    if cached_result:
        return cached_result

    # Generate layout
    box = radical_layout.layout_radical(content, index)

    # Convert to SVG
    svg = _box_to_svg(box)

    # Cache result
    math_cache.set_rendered_math(cache_key, True, svg)

    return svg


def _box_to_svg(box: Box) -> str:
    """
    Convert a box layout to SVG (improved implementation).
    Recursively renders box structures to find operator symbols.
    """
    width = box.width + 20
    height = box.height + 20

    svg_parts = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']

    # Background
    svg_parts.append(f'<rect width="100%" height="100%" fill="#ffffff"/>')

    # Find operator symbol in the box structure
    operator_symbol = _find_operator_symbol(box)
    if operator_symbol:
        svg_parts.append(f'<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-size="24px">{operator_symbol}</text>')
    elif hasattr(box, '_content'):
        svg_parts.append(f'<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-size="16px">{box._content}</text>')

    # Also render any textual contents (e.g., limits) so unicode like ∞ appears
    try:
        from .latex_specs import latex_to_unicode
        text_contents = _collect_text_contents(box)
        if text_contents:
            combined = ' '.join(text_contents)
            combined_unicode = latex_to_unicode(combined)
            # Place it near the bottom so it's included in SVG text
            svg_parts.append(f'<text x="10" y="{height - 10}" font-size="12px">{combined_unicode}</text>')
    except Exception:
        pass

    svg_parts.append('</svg>')

    svg_content = '\n'.join(svg_parts)

    # Convert to data URL
    import base64
    svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{svg_base64}"


def _find_operator_symbol(box: Box) -> Optional[str]:
    """
    Recursively search for an operator symbol in a box structure.
    """
    # Check if this box has a symbol
    if hasattr(box, '_symbol'):
        return box._symbol

    # Check if this box has contents (HBox/VBox)
    if hasattr(box, 'contents'):
        for subbox in box.contents:
            symbol = _find_operator_symbol(subbox)
            if symbol:
                return symbol

    return None


def _collect_text_contents(box: Box) -> list:
    """Collect textual contents from box tree (e.g., limit strings)."""
    texts = []
    if hasattr(box, '_content') and isinstance(box._content, str) and box._content:
        texts.append(box._content)
    if hasattr(box, 'contents'):
        for sub in box.contents:
            texts.extend(_collect_text_contents(sub))
    return texts
