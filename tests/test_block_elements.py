# tests/test_block_elements.py
"""Tests for block-level element parsing."""

from compose.parser.ast_parser import MarkdownParser
from compose.model.ast import *


def test_parse_simple_table():
    """Test parsing a simple table."""
    parser = MarkdownParser()
    doc = parser.parse("| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1 | Cell 2 |")

    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], Table)
    table = doc.blocks[0]

    assert len(table.headers) == 2
    assert len(table.rows) == 1
    assert len(table.rows[0]) == 2
    print("✅ test_parse_simple_table passed")


def test_parse_blockquote():
    """Test parsing blockquotes."""
    parser = MarkdownParser()
    doc = parser.parse("> This is a blockquote")

    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], Blockquote)
    blockquote = doc.blocks[0]

    assert len(blockquote.content) == 1
    assert isinstance(blockquote.content[0], Paragraph)
    print("✅ test_parse_blockquote passed")


def test_parse_math_block():
    """Test parsing mathematical blocks."""
    parser = MarkdownParser()
    doc = parser.parse("$$\nx^2 + y^2 = z^2\n$$")

    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], MathBlock)
    assert "x^2 + y^2 = z^2" in doc.blocks[0].content
    print("✅ test_parse_math_block passed")


def test_parse_inline_vs_block_math():
    """Test distinguishing between inline and block math."""
    parser = MarkdownParser()
    doc = parser.parse("Inline $x^2$ and block:\n$$\ny^2\n$$")

    assert len(doc.blocks) == 2
    assert isinstance(doc.blocks[0], Paragraph)  # Contains inline math
    assert isinstance(doc.blocks[1], MathBlock)  # Block math

    # Check inline math in paragraph
    inline_math = [el for el in doc.blocks[0].content if isinstance(el, MathInline)]
    assert len(inline_math) == 1
    print("✅ test_parse_inline_vs_block_math passed")
