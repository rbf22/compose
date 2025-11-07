# compose/model/ast.py
"""Abstract Syntax Tree model for Compose documents"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class InlineElement:
    """Base class for inline elements"""
    pass

@dataclass
class Text(InlineElement):
    """Plain text"""
    content: str

@dataclass
class Bold(InlineElement):
    """Bold text"""
    children: List[InlineElement]

@dataclass
class Italic(InlineElement):
    """Italic text"""
    children: List[InlineElement]

@dataclass
class Strikethrough(InlineElement):
    """Strikethrough text"""
    children: List[InlineElement]

@dataclass
class CodeInline(InlineElement):
    """Inline code"""
    content: str

@dataclass
class MathInline(InlineElement):
    """Inline math"""
    content: str

@dataclass
class Link(InlineElement):
    """Link"""
    text: str
    url: str

@dataclass
class Image(InlineElement):
    """Image"""
    alt: str
    url: str

@dataclass
class BlockElement:
    """Base class for block elements"""
    pass

@dataclass
class Heading(BlockElement):
    """Heading"""
    level: int
    content: List[InlineElement]

@dataclass
class Paragraph(BlockElement):
    """Paragraph"""
    content: List[InlineElement]

@dataclass
class CodeBlock(BlockElement):
    """Code block"""
    content: str
    language: Optional[str] = None

@dataclass
class MathBlock(BlockElement):
    """Math block"""
    content: str

@dataclass
class Blockquote(BlockElement):
    """Blockquote"""
    content: List[BlockElement]

@dataclass
class ListItem(BlockElement):
    """List item"""
    content: List[InlineElement]
    checked: Optional[bool] = None  # For task lists

@dataclass
class ListBlock(BlockElement):
    """List (ordered or unordered)"""
    items: List[ListItem]
    ordered: bool = False

@dataclass
class Table(BlockElement):
    """Table"""
    headers: List[List[InlineElement]]
    rows: List[List[InlineElement]]

@dataclass
class HorizontalRule(BlockElement):
    """Horizontal rule"""
    pass

@dataclass
class MermaidDiagram(BlockElement):
    """Mermaid diagram"""
    content: str

@dataclass
class Document:
    """Complete document"""
    blocks: List[BlockElement]
    frontmatter: Dict[str, Any]
