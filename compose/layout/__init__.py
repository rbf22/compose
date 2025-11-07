# compose/layout/__init__.py
"""
Universal Layout Engine for Compose.

This is the core layout system that handles all content types:
- Text and typography
- Mathematical expressions  
- Diagrams and visualizations
- Slides and presentations
- Tables and structured data
- Media and interactive elements

The system is based on TeX's box-and-glue model but extended
for modern content types and output formats.
"""

# Core layout primitives
from .box_model import MathBox, Dimensions, GlueSpace, BoxType as MathBoxType
from .universal_box import UniversalBox, ContentType, BoxType, RenderingStyle
from .font_metrics import MathFontMetrics, FontStyle, FontParameters

# Layout engines for different content types
from .engines.math_engine import MathLayoutEngine, ExpressionLayout
from .engines.diagram_engine import DiagramRenderer, MermaidRenderer
from .engines.slide_engine import SlideLayoutEngine, SlideTemplate

# Content parsers
from .content.math_parser import MathExpressionParser

# Main layout coordinator
from .layout_engine import UniversalLayoutEngine, DocumentBuilder

__all__ = [
    # Core primitives
    'UniversalBox', 'ContentType', 'BoxType', 'RenderingStyle',
    'MathBox', 'Dimensions', 'GlueSpace', 'MathBoxType',
    'MathFontMetrics', 'FontStyle', 'FontParameters',
    
    # Layout engines
    'UniversalLayoutEngine', 'DocumentBuilder',
    'MathLayoutEngine', 'ExpressionLayout',
    'DiagramRenderer', 'MermaidRenderer',
    'SlideLayoutEngine', 'SlideTemplate',
    
    # Content parsers
    'MathExpressionParser',
]
