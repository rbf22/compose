# compose/layout/layout_engine.py
"""
Universal Layout Engine - Main coordinator for all content types.

This module provides the main interface for laying out documents
with mixed content types: text, math, diagrams, slides, etc.
"""

from typing import List, Dict, Any, Optional, Union
from .universal_box import UniversalBox, ContentType, BoxType
from .engines.math_engine import MathLayoutEngine
from .engines.diagram_engine import DiagramRenderer


class UniversalLayoutEngine:
    """
    Main layout engine that coordinates all content types.
    
    This engine routes different content types to their specialized
    layout engines and combines the results into a unified document.
    """
    
    def __init__(self):
        # Specialized engines for different content types
        self.math_engine = MathLayoutEngine()
        self.diagram_engine = DiagramRenderer()
        
        # Layout state
        self.current_page_width = 612.0  # Default letter width in points
        self.current_page_height = 792.0  # Default letter height in points
        self.margins = {'top': 72, 'bottom': 72, 'left': 72, 'right': 72}
        
        # Style and configuration
        self.default_font_size = 12.0
        self.line_height = 1.2
        self.paragraph_spacing = 12.0
    
    def layout_document(self, boxes: List[UniversalBox]) -> List[UniversalBox]:
        """
        Layout a complete document with mixed content types.
        
        This is the main entry point for document layout.
        """
        if not boxes:
            return []
        
        # Process each box according to its content type
        processed_boxes = []
        
        for box in boxes:
            processed_box = self._process_box(box)
            processed_boxes.append(processed_box)
        
        # Apply document-level layout (page breaks, flow, etc.)
        return self._apply_document_layout(processed_boxes)
    
    def _process_box(self, box: UniversalBox) -> UniversalBox:
        """Process a single box according to its content type."""
        
        if box.content_type == ContentType.MATH:
            return self._process_math_box(box)
        elif box.content_type == ContentType.DIAGRAM:
            return self._process_diagram_box(box)
        elif box.content_type == ContentType.TEXT:
            return self._process_text_box(box)
        elif box.content_type == ContentType.SLIDE:
            return self._process_slide_box(box)
        elif box.content_type == ContentType.TABLE:
            return self._process_table_box(box)
        else:
            # Default processing for unknown content types
            return box
    
    def _process_math_box(self, box: UniversalBox) -> UniversalBox:
        """Process mathematical content."""
        # Convert to math engine format if needed
        if isinstance(box.content, str):
            from .content.math_parser import MathExpressionParser
            parser = MathExpressionParser()
            math_box = parser.parse_expression(box.content)
            
            # Update dimensions from math layout
            box.dimensions = math_box.dimensions
        
        return box
    
    def _process_diagram_box(self, box: UniversalBox) -> UniversalBox:
        """Process diagram content."""
        try:
            # Render diagram and update dimensions
            svg_output = self.diagram_engine.render_diagram(box)
            
            # Store rendered output in attributes for later use
            box.attributes = box.attributes or {}
            box.attributes['rendered_svg'] = svg_output
            
        except Exception as e:
            # Handle diagram rendering errors gracefully
            box.attributes = box.attributes or {}
            box.attributes['render_error'] = str(e)
        
        return box
    
    def _process_text_box(self, box: UniversalBox) -> UniversalBox:
        """Process text content with typography rules."""
        if isinstance(box.content, str):
            # Apply typography improvements
            content = box.content
            
            # Smart quotes
            content = content.replace('"', '"').replace('"', '"')
            content = content.replace("'", "'").replace("'", "'")
            
            # Smart dashes
            content = content.replace('---', '—')  # em dash
            content = content.replace('--', '–')   # en dash
            
            # Smart ellipses
            content = content.replace('...', '…')
            
            box.content = content
        
        return box
    
    def _process_slide_box(self, box: UniversalBox) -> UniversalBox:
        """Process slide content."""
        # Slides have special layout constraints
        box.dimensions.width = 1024  # Standard slide width
        box.dimensions.height = 768  # Standard slide height
        
        return box
    
    def _process_table_box(self, box: UniversalBox) -> UniversalBox:
        """Process table content."""
        # Table layout logic would go here
        return box
    
    def _apply_document_layout(self, boxes: List[UniversalBox]) -> List[UniversalBox]:
        """Apply document-level layout rules."""
        if not boxes:
            return boxes
        
        # Calculate available width
        available_width = (self.current_page_width - 
                          self.margins['left'] - self.margins['right'])
        
        # Position boxes vertically
        y_position = self.margins['top']
        
        for box in boxes:
            # Set horizontal position
            if box.box_type == BoxType.BLOCK:
                box.position.width = self.margins['left']  # x position
                box.position.height = y_position  # y position
                
                # Update y position for next box
                y_position += box.total_height()
            
            elif box.box_type == BoxType.INLINE:
                # Inline boxes flow with text
                pass
        
        return boxes
    
    def set_page_size(self, width: float, height: float):
        """Set the page dimensions."""
        self.current_page_width = width
        self.current_page_height = height
    
    def set_margins(self, top: float, right: float, bottom: float, left: float):
        """Set page margins."""
        self.margins = {
            'top': top,
            'right': right, 
            'bottom': bottom,
            'left': left
        }
    
    def get_content_width(self) -> float:
        """Get available content width."""
        return self.current_page_width - self.margins['left'] - self.margins['right']
    
    def get_content_height(self) -> float:
        """Get available content height."""
        return self.current_page_height - self.margins['top'] - self.margins['bottom']


class DocumentBuilder:
    """
    High-level interface for building documents with mixed content.
    
    This provides a convenient API for creating documents programmatically.
    """
    
    def __init__(self):
        self.engine = UniversalLayoutEngine()
        self.boxes = []
    
    def add_text(self, text: str, style: Optional[Dict[str, Any]] = None) -> 'DocumentBuilder':
        """Add a text element."""
        from .universal_box import create_text_box, RenderingStyle
        
        text_style = RenderingStyle()
        if style:
            # Apply style overrides
            for key, value in style.items():
                if hasattr(text_style, key):
                    setattr(text_style, key, value)
        
        box = create_text_box(text, text_style)
        self.boxes.append(box)
        return self
    
    def add_math(self, expression: str, display: bool = False) -> 'DocumentBuilder':
        """Add a mathematical expression."""
        box = UniversalBox(
            content=expression,
            content_type=ContentType.MATH,
            box_type=BoxType.BLOCK if display else BoxType.INLINE
        )
        self.boxes.append(box)
        return self
    
    def add_diagram(self, code: str, diagram_type: str = "mermaid") -> 'DocumentBuilder':
        """Add a diagram."""
        from .universal_box import create_diagram_box
        box = create_diagram_box(code, diagram_type)
        self.boxes.append(box)
        return self
    
    def add_slide(self, title: str, content: List[str]) -> 'DocumentBuilder':
        """Add a slide."""
        # Convert content strings to boxes
        content_boxes = [
            UniversalBox(
                content=text,
                content_type=ContentType.TEXT,
                box_type=BoxType.BLOCK
            ) for text in content
        ]
        
        from .universal_box import create_slide_box
        box = create_slide_box(title, content_boxes)
        self.boxes.append(box)
        return self
    
    def build(self) -> List[UniversalBox]:
        """Build the document and return laid out boxes."""
        return self.engine.layout_document(self.boxes)
    
    def clear(self) -> 'DocumentBuilder':
        """Clear all content."""
        self.boxes = []
        return self
