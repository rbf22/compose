# compose/layout/content/__init__.py
"""
Content parsers for different markup formats.

These parsers convert various input formats into the universal box model:
- MathParser: LaTeX mathematical expressions
- DiagramParser: Mermaid diagram syntax
- MarkdownParser: Enhanced Markdown with extensions
- SlideParser: Presentation-specific markup
"""

from .math_parser import MathExpressionParser

__all__ = [
    'MathExpressionParser',
]
