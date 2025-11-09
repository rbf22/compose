"""
Text layout engine for calculating text positions and wrapping.

This module provides pure functions for text measurement and layout,
completely separated from PDF rendering. All functions are stateless
and can be cached/memoized for performance.
"""

from functools import lru_cache
from typing import List, Dict, Tuple, Optional
from .layout_primitives import TextRun, LineLayout, TextMeasurement


class TextLayoutEngine:
    """
    Pure text layout calculations without any rendering.
    
    This class is stateless and all methods are deterministic based on inputs.
    Results can be safely cached.
    """
    
    def __init__(self, font_metrics: Dict[str, Dict]):
        """
        Initialize with font metrics.
        
        Args:
            font_metrics: Dictionary mapping font names to their metrics
                         (ascent, descent, glyph_widths, etc.)
        """
        self.font_metrics = font_metrics
        # Create cache key from font metrics for cache invalidation
        self._metrics_hash = hash(str(sorted(font_metrics.items())))
    
    @lru_cache(maxsize=2000)
    def measure_text(self, text: str, font: str, size: float) -> TextMeasurement:
        """
        Measure text dimensions.
        
        This is a pure function - same inputs always produce same output.
        Results are cached for performance.
        
        Args:
            text: Text to measure
            font: Font name (e.g., "Helvetica", "Times-Roman")
            size: Font size in points
            
        Returns:
            TextMeasurement with width, height, ascent, descent
        """
        if font not in self.font_metrics:
            # Fallback estimation
            width = len(text) * size * 0.5
            return TextMeasurement(
                text=text,
                font=font,
                size=size,
                width=width,
                height=size * 1.2,
                ascent=size,
                descent=size * 0.2
            )
        
        metrics = self.font_metrics[font]
        glyph_widths = metrics['glyph_widths']
        
        # Calculate width from glyph metrics
        total_width = 0.0
        for char in text:
            if char in glyph_widths:
                total_width += glyph_widths[char]
            else:
                # Fallback for unknown characters
                total_width += glyph_widths.get('a', 4.4)
        
        # Convert from font units to points
        units_per_em = metrics.get('units_per_em', 1000)
        width = total_width * (size / units_per_em)
        
        # Calculate height metrics
        ascent = metrics['ascent'] * (size / units_per_em)
        descent = abs(metrics['descent']) * (size / units_per_em)
        height = ascent + descent
        
        return TextMeasurement(
            text=text,
            font=font,
            size=size,
            width=width,
            height=height,
            ascent=ascent,
            descent=descent
        )
    
    def measure_text_width(self, text: str, font: str, size: float) -> float:
        """
        Quick width measurement (cached).
        
        Args:
            text: Text to measure
            font: Font name
            size: Font size in points
            
        Returns:
            Width in points
        """
        return self.measure_text(text, font, size).width
    
    def wrap_text(
        self,
        text: str,
        max_width: float,
        font: str,
        size: float,
        word_spacing: float = 0.0
    ) -> List[str]:
        """
        Wrap text to fit within max_width.
        
        This is a pure function - no state mutation.
        
        Args:
            text: Text to wrap
            max_width: Maximum line width in points
            font: Font name
            size: Font size in points
            word_spacing: Additional spacing between words
            
        Returns:
            List of wrapped lines
        """
        if not text:
            return []
        
        words = text.split()
        if not words:
            return [text]
        
        lines = []
        current_line = []
        current_width = 0.0
        
        space_width = self.measure_text_width(' ', font, size) + word_spacing
        
        for word in words:
            word_width = self.measure_text_width(word, font, size)
            
            # Check if word fits on current line
            if current_line:
                # Need to account for space before word
                needed_width = current_width + space_width + word_width
            else:
                # First word on line
                needed_width = word_width
            
            if needed_width <= max_width:
                # Word fits
                current_line.append(word)
                current_width = needed_width
            else:
                # Word doesn't fit
                if current_line:
                    # Save current line and start new one
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_width = word_width
                else:
                    # Word is too long for line - force it
                    lines.append(word)
                    current_line = []
                    current_width = 0.0
        
        # Add remaining words
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def layout_text_line(
        self,
        text: str,
        x: float,
        y: float,
        font: str,
        size: float,
        color: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        underline: bool = False,
        strikethrough: bool = False
    ) -> LineLayout:
        """
        Create layout for a single line of text.
        
        Args:
            text: Text content
            x: X position (left edge)
            y: Y position (baseline)
            font: Font name
            size: Font size
            color: RGB color tuple (0-1 range)
            underline: Whether to underline
            strikethrough: Whether to strikethrough
            
        Returns:
            LineLayout with single TextRun
        """
        measurement = self.measure_text(text, font, size)
        
        text_run = TextRun(
            text=text,
            font=font,
            size=size,
            x=x,
            y=y,
            width=measurement.width,
            color=color,
            underline=underline,
            strikethrough=strikethrough
        )
        
        return LineLayout(
            runs=[text_run],
            x=x,
            y=y,
            width=measurement.width,
            height=measurement.height,
            baseline_offset=measurement.ascent
        )
    
    def layout_wrapped_text(
        self,
        text: str,
        x: float,
        y: float,
        max_width: float,
        font: str,
        size: float,
        line_height_factor: float = 1.2,
        color: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        alignment: str = "left"
    ) -> List[LineLayout]:
        """
        Layout multi-line wrapped text.
        
        Args:
            text: Text to layout
            x: Left edge X position
            y: Top Y position (will be adjusted to baseline)
            max_width: Maximum line width
            font: Font name
            size: Font size
            line_height_factor: Line height multiplier
            color: RGB color tuple
            alignment: Text alignment (left, center, right)
            
        Returns:
            List of LineLayout objects, one per line
        """
        # Wrap text into lines
        wrapped_lines = self.wrap_text(text, max_width, font, size)
        
        if not wrapped_lines:
            return []
        
        # Calculate line height
        measurement = self.measure_text("Ay", font, size)  # Use chars with ascent/descent
        line_height = measurement.height * line_height_factor
        
        # Layout each line
        layouts = []
        current_y = y - measurement.ascent  # Adjust to baseline
        
        for line_text in wrapped_lines:
            line_measurement = self.measure_text(line_text, font, size)
            
            # Calculate X position based on alignment
            if alignment == "center":
                line_x = x + (max_width - line_measurement.width) / 2
            elif alignment == "right":
                line_x = x + max_width - line_measurement.width
            else:  # left
                line_x = x
            
            text_run = TextRun(
                text=line_text,
                font=font,
                size=size,
                x=line_x,
                y=current_y,
                width=line_measurement.width,
                color=color
            )
            
            line_layout = LineLayout(
                runs=[text_run],
                x=line_x,
                y=current_y,
                width=line_measurement.width,
                height=line_height,
                baseline_offset=measurement.ascent
            )
            
            layouts.append(line_layout)
            current_y -= line_height
        
        return layouts
    
    def calculate_line_height(self, font: str, size: float, factor: float = 1.2) -> float:
        """
        Calculate line height for a font.
        
        Args:
            font: Font name
            size: Font size
            factor: Line height multiplier
            
        Returns:
            Line height in points
        """
        measurement = self.measure_text("Ay", font, size)
        return measurement.height * factor
    
    def clear_cache(self):
        """Clear the measurement cache"""
        self.measure_text.cache_clear()


# Convenience functions for common operations

def create_text_layout_engine(font_metrics: Dict[str, Dict]) -> TextLayoutEngine:
    """
    Factory function to create a text layout engine.
    
    Args:
        font_metrics: Font metrics dictionary
        
    Returns:
        TextLayoutEngine instance
    """
    return TextLayoutEngine(font_metrics)
