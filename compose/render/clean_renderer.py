"""
Clean Rendering Implementation

Implements the Measure → Update → Render → Check pipeline.
This is the new rendering system that replaces the old layout methods.

Key principle: Each render method is simple - take a Y position, render, return new Y.
No spacing logic, no page break logic in render methods.
"""

from typing import Tuple
from compose.model.ast import (
    Heading, Paragraph, CodeBlock, ListBlock, MathBlock, Image, Table, Text
)


class CleanRenderer:
    """
    Clean rendering implementation using Measure → Update → Render → Check pipeline.
    
    This class provides rendering methods that work with the measurement system.
    Each method:
    - Takes a Y position
    - Renders content at that position
    - Returns the new Y position
    - Does NOT handle spacing or page breaks
    """
    
    def __init__(self, pdf_renderer):
        """
        Initialize with reference to main PDF renderer.
        
        Args:
            pdf_renderer: The ProfessionalPDFRenderer instance
        """
        self.renderer = pdf_renderer
    
    def render_heading(self, heading: Heading, y: float) -> float:
        """
        Render a heading at position y.
        
        Args:
            heading: Heading element to render
            y: Y position (baseline) for rendering
        
        Returns:
            New Y position after heading
        """
        level = heading.level
        text_content = self.renderer._extract_text_content(heading.content)
        
        # Font sizes by level
        font_sizes = {1: 24, 2: 18, 3: 14, 4: 12, 5: 12, 6: 12}
        font_size = font_sizes.get(level, 12)
        font_name = "Helvetica-Bold"
        
        # Get font metrics
        font_metrics = self.renderer.font_metrics.get(font_name, {})
        ascender = font_metrics.get('ascent', font_size * 0.8) / 1000.0 * font_size
        descender = abs(font_metrics.get('descent', font_size * 0.2)) / 1000.0 * font_size
        
        # Render heading
        commands = [
            "BT",
            "0 0 0 rg",
            f"/{font_name} {font_size} Tf",
            f"1 0 0 1 {self.renderer.margin_left} {y} Tm",
            f"{self.renderer._to_pdf_literal(text_content)} Tj",
            "ET"
        ]
        self.renderer._add_to_current_page(commands)
        
        # Record to tracker
        text_width = self.renderer._measure_text_width(text_content, font_name, font_size)
        self.renderer.tracker.record_text(
            x=self.renderer.margin_left,
            y=y + ascender,
            width=text_width,
            height=ascender + descender,
            page=self.renderer.current_page,
            label=f"heading:{text_content.strip()}"
        )
        
        # Update content bottom
        self.renderer._update_content_bottom(y, descender)
        
        # Return new Y (move down by font size)
        return y - font_size
    
    def render_paragraph(self, paragraph: Paragraph, y: float) -> float:
        """
        Render a paragraph at position y.
        
        Args:
            paragraph: Paragraph element to render
            y: Y position (baseline) for rendering
        
        Returns:
            New Y position after paragraph
        """
        # Extract text content
        text_content = self.renderer._extract_text_content(paragraph.content)
        
        font_size = self.renderer.current_font_size
        font_name = "Helvetica"
        
        # Get font metrics
        font_metrics = self.renderer.font_metrics.get(font_name, {})
        ascender = font_metrics.get('ascent', font_size * 0.8) / 1000.0 * font_size
        descender = abs(font_metrics.get('descent', font_size * 0.2)) / 1000.0 * font_size
        
        # Wrap text to page width
        max_width = self.renderer.page_width - self.renderer.margin_left - self.renderer.margin_right
        lines = self.renderer._wrap_text(text_content, max_width)
        
        current_y = y
        
        # Render each line
        for line in lines:
            commands = [
                "BT",
                "0 0 0 rg",
                f"/{font_name} {font_size} Tf",
                f"1 0 0 1 {self.renderer.margin_left} {current_y} Tm",
                f"{self.renderer._to_pdf_literal(line)} Tj",
                "ET"
            ]
            self.renderer._add_to_current_page(commands)
            
            # Record to tracker
            text_width = self.renderer._measure_text_width(line, font_name, font_size)
            self.renderer.tracker.record_text(
                x=self.renderer.margin_left,
                y=current_y + ascender,
                width=text_width,
                height=ascender + descender,
                page=self.renderer.current_page,
                label=f"text:{line[:30]}"
            )
            
            # Update content bottom
            self.renderer._update_content_bottom(current_y, descender)
            
            # Move down for next line
            current_y -= (font_size * self.renderer.line_height_factor)
        
        return current_y
    
    def render_code_block(self, code_block: CodeBlock, y: float) -> float:
        """
        Render a code block at position y.
        
        Args:
            code_block: CodeBlock element to render
            y: Y position (baseline) for rendering
        
        Returns:
            New Y position after code block
        """
        lines = code_block.content.split('\n')
        font_size = 10
        font_name = "Helvetica"
        
        # Get font metrics
        font_metrics = self.renderer.font_metrics.get(font_name, {})
        ascender = font_metrics.get('ascent', font_size * 0.8) / 1000.0 * font_size
        descender = abs(font_metrics.get('descent', font_size * 0.2)) / 1000.0 * font_size
        
        current_y = y
        
        for line in lines:
            if line.strip():
                # Render line
                commands = [
                    "BT",
                    "0 0 0 rg",
                    f"/{font_name} {font_size} Tf",
                    f"1 0 0 1 {self.renderer.margin_left} {current_y} Tm",
                    f"{self.renderer._to_pdf_literal(line)} Tj",
                    "ET"
                ]
                self.renderer._add_to_current_page(commands)
                
                # Record to tracker
                line_width = self.renderer._measure_text_width(line, font_name, font_size)
                self.renderer.tracker.record_text(
                    x=self.renderer.margin_left,
                    y=current_y + ascender,
                    width=line_width,
                    height=ascender + descender,
                    page=self.renderer.current_page,
                    label=f"code:{line[:30]}"
                )
                
                # Update content bottom
                self.renderer._update_content_bottom(current_y, descender)
                
                # Move down for next line
                current_y -= (font_size * self.renderer.line_height_factor)
        
        return current_y
    
    def render_list_block(self, list_block: ListBlock, y: float) -> float:
        """
        Render a list block at position y.
        
        Args:
            list_block: ListBlock element to render
            y: Y position (baseline) for rendering
        
        Returns:
            New Y position after list
        """
        font_size = self.renderer.current_font_size
        current_y = y
        
        # Get font metrics
        font_metrics = self.renderer.font_metrics.get("Helvetica", {})
        descender = abs(font_metrics.get('descent', font_size * 0.2)) / 1000.0 * font_size
        
        for item in list_block.items:
            # Render list item
            item_text = self.renderer._extract_text_content(item.content)
            
            # Add bullet
            bullet = "• "
            full_text = bullet + item_text
            
            commands = [
                "BT",
                "0 0 0 rg",
                f"/Helvetica {font_size} Tf",
                f"1 0 0 1 {self.renderer.margin_left + 10} {current_y} Tm",
                f"{self.renderer._to_pdf_literal(full_text)} Tj",
                "ET"
            ]
            self.renderer._add_to_current_page(commands)
            
            # Record to tracker
            text_width = self.renderer._measure_text_width(full_text, "Helvetica", font_size)
            ascender = font_metrics.get('ascent', font_size * 0.8) / 1000.0 * font_size
            self.renderer.tracker.record_text(
                x=self.renderer.margin_left + 10,
                y=current_y + ascender,
                width=text_width,
                height=ascender + descender,
                page=self.renderer.current_page,
                label=f"list_item:{item_text[:30]}"
            )
            
            # Update content bottom
            self.renderer._update_content_bottom(current_y, descender)
            
            # Move down for next item
            current_y -= (font_size * self.renderer.line_height_factor)
        
        return current_y
    
    def render_math_block(self, math_block: MathBlock, y: float) -> float:
        """
        Render a math block at position y.
        
        Args:
            math_block: MathBlock element to render
            y: Y position (baseline) for rendering
        
        Returns:
            New Y position after math block
        """
        # For now, render as placeholder text
        font_size = self.renderer.current_font_size
        content = math_block.content
        
        # Get font metrics
        font_metrics = self.renderer.font_metrics.get("Helvetica", {})
        ascender = font_metrics.get('ascent', font_size * 0.8) / 1000.0 * font_size
        descender = abs(font_metrics.get('descent', font_size * 0.2)) / 1000.0 * font_size
        
        # Render as text
        commands = [
            "BT",
            "0 0 0 rg",
            f"/Helvetica {font_size} Tf",
            f"1 0 0 1 {self.renderer.margin_left} {y} Tm",
            f"{self.renderer._to_pdf_literal(content)} Tj",
            "ET"
        ]
        self.renderer._add_to_current_page(commands)
        
        # Record to tracker
        text_width = self.renderer._measure_text_width(content, "Helvetica", font_size)
        self.renderer.tracker.record_text(
            x=self.renderer.margin_left,
            y=y + ascender,
            width=text_width,
            height=ascender + descender,
            page=self.renderer.current_page,
            label=f"math_block:{content[:30]}"
        )
        
        # Update content bottom
        self.renderer._update_content_bottom(y, descender)
        
        # Move down
        return y - font_size
