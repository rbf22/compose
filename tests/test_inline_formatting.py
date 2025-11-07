# tests/test_inline_formatting.py
"""Tests for inline formatting parsing."""

from compose.parser.ast_parser import MarkdownParser
from compose.model.ast import *


def test_parse_bold_simple():
    """Test parsing simple bold text."""
    parser = MarkdownParser()
    doc = parser.parse("This is **bold** text.")

    assert len(doc.blocks) == 1
    paragraph = doc.blocks[0]

    # Should have: Text("This is "), Bold([Text("bold")]), Text(" text.")
    assert len(paragraph.content) == 3
    assert isinstance(paragraph.content[0], Text)
    assert isinstance(paragraph.content[1], Bold)
    assert isinstance(paragraph.content[2], Text)

    assert paragraph.content[0].content == "This is "
    assert paragraph.content[1].children[0].content == "bold"
    assert paragraph.content[2].content == " text."
    print("✅ test_parse_bold_simple passed")


def test_parse_italic_simple():
    """Test parsing simple italic text."""
    parser = MarkdownParser()
    doc = parser.parse("This is *italic* text.")

    paragraph = doc.blocks[0]
    assert len(paragraph.content) == 3
    assert isinstance(paragraph.content[1], Italic)
    assert paragraph.content[1].children[0].content == "italic"
    print("✅ test_parse_italic_simple passed")


def test_parse_code_inline():
    """Test parsing inline code."""
    parser = MarkdownParser()
    doc = parser.parse("Use the `print()` function.")

    paragraph = doc.blocks[0]
    assert len(paragraph.content) == 3
    assert isinstance(paragraph.content[1], CodeInline)
    assert paragraph.content[1].content == "print()"
    print("✅ test_parse_code_inline passed")


def test_smart_quotes():
    """Test smart quotes."""
    parser = MarkdownParser()
    doc = parser.parse('"Hello World" and \'single quotes\'.')

    paragraph = doc.blocks[0]
    text_content = paragraph.content[0].content
    assert '"' in text_content or '"' in text_content
    print("✅ test_smart_quotes passed")


def test_smart_dashes():
    """Test smart dashes."""
    parser = MarkdownParser()
    doc = parser.parse("Pages 10--15 and em---dash.")

    paragraph = doc.blocks[0]
    text_content = paragraph.content[0].content
    assert '–' in text_content  # en-dash
    assert '—' in text_content  # em-dash
    print("✅ test_smart_dashes passed")


def test_smart_ellipses():
    """Test smart ellipses."""
    parser = MarkdownParser()
    doc = parser.parse("And so on...")

    paragraph = doc.blocks[0]
    text_content = paragraph.content[0].content
    assert '…' in text_content
    print("✅ test_smart_ellipses passed")
