"""
Layout Measurement System

Measures component heights before rendering to enable proper page break handling.

This is the foundation of the Measure → Update → Render → Check pipeline.
"""

from dataclasses import dataclass
from typing import Tuple, Optional, List as ListType
from compose.model.ast import (
    BlockElement, Paragraph, Heading, CodeBlock, ListBlock, ListItem,
    Text, CodeInline, Link, MathInline, Bold, Italic
)


@dataclass
class MeasurementResult:
    """Result of measuring a component."""
    height: float  # Total height needed (including spacing after)
    content_height: float  # Height of just the content (without spacing)
    can_split: bool  # Whether this component can be split across pages
    spacing_after: float  # Spacing that should follow this component
    
    def __repr__(self):
        return (f"MeasurementResult(height={self.height:.1f}, "
                f"content={self.content_height:.1f}, "
                f"can_split={self.can_split}, spacing={self.spacing_after:.1f})")


class LayoutMeasurer:
    """
    Measures component heights for layout planning.
    
    This measurer calculates how much vertical space each component needs,
    enabling the renderer to make informed decisions about page breaks
    BEFORE rendering.
    """
    
    def __init__(self, page_width: float, page_height: float,
                 margin_left: float, margin_right: float,
                 margin_top: float, margin_bottom: float,
                 font_metrics: dict, current_font_size: float = 12):
        """
        Initialize the measurer.
        
        Args:
            page_width: PDF page width
            page_height: PDF page height
            margin_left: Left margin
            margin_right: Right margin
            margin_top: Top margin
            margin_bottom: Bottom margin
            font_metrics: Font metrics dictionary
            current_font_size: Current font size in points
        """
        self.page_width = page_width
        self.page_height = page_height
        self.margin_left = margin_left
        self.margin_right = margin_right
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom
        self.font_metrics = font_metrics
        self.current_font_size = current_font_size
        
        # Content area dimensions
        self.content_width = page_width - margin_left - margin_right
        self.content_height = page_height - margin_top - margin_bottom
    
    def measure(self, element: BlockElement, spacing_after: Optional[float] = None) -> MeasurementResult:
        """
        Measure a block element.
        
        Args:
            element: The block element to measure
            spacing_after: Optional spacing to add after (if None, uses default for element type)
        
        Returns:
            MeasurementResult with height and properties
        """
        if isinstance(element, Heading):
            return self._measure_heading(element, spacing_after)
        elif isinstance(element, Paragraph):
            return self._measure_paragraph(element, spacing_after)
        elif isinstance(element, CodeBlock):
            return self._measure_code_block(element, spacing_after)
        elif isinstance(element, ListBlock):
            return self._measure_list(element, spacing_after)
        else:
            # Unknown element type - estimate
            return MeasurementResult(
                height=24,
                content_height=12,
                can_split=False,
                spacing_after=spacing_after or 6
            )
    
    def _measure_heading(self, heading: Heading, spacing_after: Optional[float] = None) -> MeasurementResult:
        """Measure a heading element."""
        # Heading sizes by level
        font_sizes = {1: 24, 2: 18, 3: 14, 4: 12, 5: 12, 6: 12}
        font_size = font_sizes.get(heading.level, 12)
        
        # Get font metrics
        font_name = "Helvetica-Bold"
        font_metrics = self.font_metrics.get(font_name, {})
        ascender = font_metrics.get('ascent', font_size * 0.8) / 1000.0 * font_size
        descender = abs(font_metrics.get('descent', font_size * 0.2)) / 1000.0 * font_size
        
        # Heading height
        heading_height = ascender + descender
        
        # Default spacing after heading
        spacing_map = {1: 18, 2: 12, 3: 9, 4: 6, 5: 6, 6: 6}
        default_spacing = spacing_map.get(heading.level, 6)
        spacing = spacing_after if spacing_after is not None else default_spacing
        
        return MeasurementResult(
            height=heading_height + spacing,
            content_height=heading_height,
            can_split=False,  # Headings cannot be split
            spacing_after=spacing
        )
    
    def _measure_paragraph(self, paragraph: Paragraph, spacing_after: Optional[float] = None) -> MeasurementResult:
        """Measure a paragraph element."""
        # Estimate paragraph height based on text content
        # This is a simplified measurement - actual wrapping would be more complex
        
        # Extract text content
        text_content = self._extract_text(paragraph.content)
        
        # Estimate number of lines
        # Average characters per line at current font size
        chars_per_line = int(self.content_width / (self.current_font_size * 0.5))
        
        if chars_per_line <= 0:
            chars_per_line = 40  # Fallback
        
        num_lines = max(1, len(text_content) // chars_per_line + 1)
        
        # Line height
        font_metrics = self.font_metrics.get("Helvetica", {})
        ascender = font_metrics.get('ascent', self.current_font_size * 0.8) / 1000.0 * self.current_font_size
        descender = abs(font_metrics.get('descent', self.current_font_size * 0.2)) / 1000.0 * self.current_font_size
        line_height = (ascender + descender) * 1.2  # 1.2x line height factor
        
        content_height = num_lines * line_height
        
        # Default spacing after paragraph
        default_spacing = 6
        spacing = spacing_after if spacing_after is not None else default_spacing
        
        return MeasurementResult(
            height=content_height + spacing,
            content_height=content_height,
            can_split=True,  # Paragraphs can be split
            spacing_after=spacing
        )
    
    def _measure_code_block(self, code_block: CodeBlock, spacing_after: Optional[float] = None) -> MeasurementResult:
        """Measure a code block element."""
        # Count lines in code
        lines = code_block.content.split('\n')
        num_lines = len(lines)
        
        # Code block line height (typically smaller font)
        code_font_size = 10
        font_metrics = self.font_metrics.get("Courier", {})
        ascender = font_metrics.get('ascent', code_font_size * 0.8) / 1000.0 * code_font_size
        descender = abs(font_metrics.get('descent', code_font_size * 0.2)) / 1000.0 * code_font_size
        line_height = ascender + descender
        
        # Add padding for code block
        padding = 6
        content_height = (num_lines * line_height) + (padding * 2)
        
        # Default spacing after code block
        default_spacing = 12
        spacing = spacing_after if spacing_after is not None else default_spacing
        
        return MeasurementResult(
            height=content_height + spacing,
            content_height=content_height,
            can_split=True,  # Code blocks can be split (though not ideal)
            spacing_after=spacing
        )
    
    def _measure_list(self, list_element: ListBlock, spacing_after: Optional[float] = None) -> MeasurementResult:
        """Measure a list element."""
        # Measure each list item
        item_height = 0
        for item in list_element.items:
            if isinstance(item, ListItem):
                # Each list item is roughly one line
                font_metrics = self.font_metrics.get("Helvetica", {})
                ascender = font_metrics.get('ascent', self.current_font_size * 0.8) / 1000.0 * self.current_font_size
                descender = abs(font_metrics.get('descent', self.current_font_size * 0.2)) / 1000.0 * self.current_font_size
                line_height = (ascender + descender) * 1.2
                item_height += line_height
        
        # Default spacing after list
        default_spacing = 12
        spacing = spacing_after if spacing_after is not None else default_spacing
        
        return MeasurementResult(
            height=item_height + spacing,
            content_height=item_height,
            can_split=True,  # Lists can be split
            spacing_after=spacing
        )
    
    def _extract_text(self, elements) -> str:
        """Extract plain text from inline elements."""
        result = []
        for element in elements:
            if isinstance(element, Text):
                result.append(element.content)
            elif isinstance(element, (CodeInline, Link, MathInline)):
                result.append(element.content if hasattr(element, 'content') else str(element))
            elif isinstance(element, (Bold, Italic)):
                result.append(self._extract_text(element.children))
        return ''.join(result)
    
    def fits_on_page(self, measurement: MeasurementResult, available_height: float) -> bool:
        """
        Check if a measured component fits in available space.
        
        Args:
            measurement: The measurement result
            available_height: Available vertical space on page
        
        Returns:
            True if component fits, False otherwise
        """
        return measurement.height <= available_height
    
    def get_available_height(self, current_y: float) -> float:
        """
        Get available height from current position to bottom margin.
        
        Args:
            current_y: Current Y position (baseline)
        
        Returns:
            Available height in points
        """
        return current_y - self.margin_bottom
