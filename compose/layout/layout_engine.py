# compose/layout/layout_engine.py
"""
Universal Layout Engine - Main coordinator for all content types.

This module provides the main interface for laying out documents
with mixed content types: text, math, diagrams, slides, etc.
"""

from typing import List, Dict, Any, Optional, Union, Tuple
from ..cache_system import performance_monitor
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
        
        # Multi-column layout settings
        self.columns = 1  # Number of columns
        self.column_gap = 18.0  # Gap between columns in points
        
        # Performance optimization: layout cache
        self._layout_cache = {}
        self._cache_enabled = True
        
        # Style and configuration
        self.default_font_size = 12.0
        self.line_height = 1.2
        self.paragraph_spacing = 12.0

    @performance_monitor.time_operation("document_layout")
    def layout_document(self, boxes: List[UniversalBox]) -> List[UniversalBox]:
        """
        Layout a complete document with mixed content types.
        
        This is the main entry point for document layout.
        """
        if not boxes:
            return []
        
        # Create cache key from box content (simplified)
        cache_key = None
        if self._cache_enabled:
            cache_key = self._create_cache_key(boxes)
            if cache_key in self._layout_cache:
                return self._layout_cache[cache_key].copy()
        
        # Process each box according to its content type
        processed_boxes = []
        
        for box in boxes:
            processed_box = self._process_box(box)
            processed_boxes.append(processed_box)
        
        # Apply document-level layout (page breaks, flow, etc.)
        result = self._apply_document_layout(processed_boxes)
        
        # Cache the result
        if self._cache_enabled and cache_key:
            self._layout_cache[cache_key] = result.copy()
        
        return result
    
    def _create_cache_key(self, boxes: List[UniversalBox]) -> str:
        """Create a cache key from box content."""
        # Simplified cache key based on content types and dimensions
        key_parts = []
        for box in boxes:
            key_parts.append(f"{box.content_type.value}:{box.box_type.value}:{box.dimensions.width:.1f}")
        return "|".join(key_parts)[:200]  # Limit key length
    
    def clear_cache(self):
        """Clear the layout cache."""
        self._layout_cache.clear()
    
    def enable_cache(self, enabled: bool = True):
        """Enable or disable layout caching."""
        self._cache_enabled = enabled
        if not enabled:
            self.clear_cache()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            'cache_size': len(self._layout_cache),
            'cache_enabled': self._cache_enabled
        }
    
    @performance_monitor.time_operation("math_box_processing")
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
    
    @performance_monitor.time_operation("diagram_box_processing")
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
            # Check if a content plugin can handle this content type
            from ..plugin_system import plugin_manager
            content_plugin = plugin_manager.get_content_plugin_for_type(box.content_type.value)
            if content_plugin:
                try:
                    # If we have a plugin, let it enhance the box
                    return content_plugin.enhance_box(box)
                except Exception as e:
                    print(f"❌ Error enhancing box with plugin {content_plugin.name}: {e}")
                    return box
            else:
                # Default processing for unknown content types
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
        
        # Separate floats from regular content
        floats, regular_boxes = self._separate_floats(boxes)
        
        if self.columns == 1:
            # Single column layout
            laid_out_boxes = self._apply_single_column_layout(regular_boxes)
            # Add floats with placement
            return self._place_floats(floats, laid_out_boxes)
        else:
            # Multi-column layout
            laid_out_boxes = self._apply_multi_column_layout(regular_boxes)
            # Add floats with placement
            return self._place_floats(floats, laid_out_boxes)
    
    def _separate_floats(self, boxes: List[UniversalBox]) -> Tuple[List[UniversalBox], List[UniversalBox]]:
        """Separate floating boxes from regular content."""
        floats = []
        regular = []
        
        for box in boxes:
            if box.box_type == BoxType.FLOAT and box.float_placement:
                floats.append(box)
            else:
                regular.append(box)
        
        return floats, regular
    
    def _place_floats(self, floats: List[UniversalBox], regular_boxes: List[UniversalBox]) -> List[UniversalBox]:
        """Place floating boxes according to their placement rules."""
        result = regular_boxes.copy()
        
        for float_box in floats:
            placement = float_box.float_placement
            
            if placement == FloatPlacement.HERE:
                # Insert at current position in flow
                # For now, just append (could be improved with better positioning)
                result.append(float_box)
            
            elif placement == FloatPlacement.TOP:
                # Place at top of current page/column
                # Find first block box and insert before it
                insert_pos = 0
                for i, box in enumerate(result):
                    if box.box_type == BoxType.BLOCK:
                        insert_pos = i
                        break
                result.insert(insert_pos, float_box)
            
            elif placement == FloatPlacement.BOTTOM:
                # Place at bottom of current page/column
                # For now, append to end (could be improved)
                result.append(float_box)
            
            elif placement == FloatPlacement.PAGE:
                # Place on separate page
                # For now, treat as HERE (would need page break logic)
                result.append(float_box)
        
        return result
    
    def _apply_single_column_layout(self, boxes: List[UniversalBox]) -> List[UniversalBox]:
        """Apply single column document layout."""
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
    
    def _apply_multi_column_layout(self, boxes: List[UniversalBox]) -> List[UniversalBox]:
        """Apply multi-column document layout."""
        # Calculate column dimensions
        available_width = (self.current_page_width - 
                          self.margins['left'] - self.margins['right'])
        total_gap_width = (self.columns - 1) * self.column_gap
        column_width = (available_width - total_gap_width) / self.columns
        
        # Group boxes into columns
        columns = self._balance_boxes_into_columns(boxes, column_width)
        
        # Position columns horizontally
        current_x = self.margins['left']
        for column_boxes in columns:
            # Position boxes in this column vertically
            y_position = self.margins['top']
            
            for box in column_boxes:
                if box.box_type == BoxType.BLOCK:
                    box.position.width = current_x  # x position
                    box.position.height = y_position  # y position
                    y_position += box.total_height()
                elif box.box_type == BoxType.INLINE:
                    # Inline boxes flow with text
                    pass
            
            # Move to next column
            current_x += column_width + self.column_gap
        
        return boxes
    
    def _balance_boxes_into_columns(self, boxes: List[UniversalBox], column_width: float) -> List[List[UniversalBox]]:
        """Balance boxes across columns, preserving heading hierarchy."""
        columns = [[] for _ in range(self.columns)]
        column_heights = [0.0] * self.columns
        
        # Keep track of current column
        current_column = 0
        
        i = 0
        while i < len(boxes):
            box = boxes[i]
            
            # Special handling for headings - don't split them across columns
            if (hasattr(box, 'content_type') and box.content_type == ContentType.TEXT and 
                isinstance(box.content, str) and box.content.startswith('#')):
                # Find the best column for this heading
                min_height_column = column_heights.index(min(column_heights))
                columns[min_height_column].append(box)
                column_heights[min_height_column] += box.total_height()
                current_column = min_height_column
                i += 1
                continue
            
            # Add box to current column
            columns[current_column].append(box)
            column_heights[current_column] += box.total_height()
            
            # Move to next column (simple round-robin for now)
            current_column = (current_column + 1) % self.columns
            i += 1
        
        return columns
    
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
    
    def set_columns(self, columns: int, gap: Optional[float] = None):
        """Set the number of columns for multi-column layout."""
        self.columns = max(1, columns)  # Ensure at least 1 column
        if gap is not None:
            self.column_gap = gap
    
    def set_column_gap(self, gap: float):
        """Set the gap between columns."""
        self.column_gap = gap
    
    def get_column_width(self) -> float:
        """Get the width of each column."""
        if self.columns == 1:
            return self.get_content_width()
        
        available_width = self.get_content_width()
        total_gap_width = (self.columns - 1) * self.column_gap
        return (available_width - total_gap_width) / self.columns


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
    
    def add_figure(self, image_path: str, caption: str = "", label: str = "", 
                  float_placement: str = "here") -> 'DocumentBuilder':
        """Add a figure with caption."""
        from .universal_box import FloatPlacement, create_figure_box
        
        placement = getattr(FloatPlacement, float_placement.upper(), FloatPlacement.HERE)
        figure_box = create_figure_box(image_path, caption, label, placement)
        self.boxes.append(figure_box)
        return self
    
    def add_table(self, data: List[List[str]], headers: Optional[List[str]] = None,
                 caption: str = "", label: str = "", float_placement: str = "here") -> 'DocumentBuilder':
        """Add a table with caption."""
        from .universal_box import FloatPlacement, create_table_box
        
        placement = getattr(FloatPlacement, float_placement.upper(), FloatPlacement.HERE)
        table_box = create_table_box(data, headers, caption, label, placement)
        self.boxes.append(table_box)
        return self
    
    def build(self) -> List[UniversalBox]:
        """Build the document and return laid out boxes."""
        # Clear cache after layout to ensure clean state
        self.engine.clear_cache()

        return self.engine.layout_document(self.boxes)
    
    def set_columns(self, columns: int, gap: Optional[float] = None) -> 'DocumentBuilder':
        """Set multi-column layout."""
        self.engine.set_columns(columns, gap)
        return self
    
    def set_column_gap(self, gap: float) -> 'DocumentBuilder':
        """Set gap between columns."""
        self.engine.set_column_gap(gap)
        return self


def benchmark_layout_performance():
    """
    Simple benchmarking function for layout performance testing.
    
    This function can be used to measure layout performance and ensure
    it stays within acceptable thresholds.
    """
    import time
    from .universal_box import create_text_box, create_math_box, create_diagram_box
    
    # Create test data
    test_boxes = [
        create_text_box("This is a test paragraph with some content."),
        create_math_box("E = mc^2"),
        create_diagram_box("graph TD\nA --> B", "flowchart"),
        create_text_box("Another paragraph with more text content for testing purposes."),
    ] * 10  # Repeat for larger test
    
    engine = UniversalLayoutEngine()
    
    # Benchmark layout performance
    start_time = time.time()
    result = engine.layout_document(test_boxes)
    end_time = time.time()
    
    layout_time = end_time - start_time
    cache_stats = engine.get_cache_stats()
    
    # Performance thresholds (adjust as needed)
    max_layout_time = 0.5  # 500ms max for this test
    min_cache_efficiency = 0.8  # 80% cache hit rate desired
    
    print("=== Layout Performance Benchmark ===")
    print(f"Layout time: {layout_time:.3f}s")
    print(f"Cache size: {cache_stats['cache_size']}")
    print(f"Cache enabled: {cache_stats['cache_enabled']}")
    print(f"Boxes processed: {len(result)}")
    
    # Check thresholds
    if layout_time > max_layout_time:
        print(f"⚠️  WARNING: Layout time exceeds threshold ({max_layout_time}s)")
    else:
        print(f"✅ Layout time within acceptable range")
    
    return {
        'layout_time': layout_time,
        'cache_stats': cache_stats,
        'boxes_processed': len(result),
        'within_threshold': layout_time <= max_layout_time
    }


if __name__ == "__main__":
    # Run benchmark when module is executed directly
    benchmark_layout_performance()
