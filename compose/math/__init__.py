# compose/math/__init__.py
"""
Mathematical typesetting compatibility layer.

This module provides backward compatibility and convenience imports
for mathematical typesetting. The actual implementation has moved
to the universal layout system in compose.layout.
"""

# Import from the new layout system
from ..layout.box_model import MathBox, GlueSpace, BoxType
from ..layout.font_metrics import MathFontMetrics, FontStyle
from ..layout.engines.math_engine import ExpressionLayout, MathLayoutEngine
from ..layout.content.math_parser import MathExpressionParser

__all__ = [
    'MathBox', 'GlueSpace', 'BoxType',
    'MathFontMetrics', 'FontStyle', 
    'ExpressionLayout', 'MathLayoutEngine',
    'MathExpressionParser'
]
