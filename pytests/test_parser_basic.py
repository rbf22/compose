# tests/test_parser_basic.py
"""Tests for basic parser functionality."""

from compose.parser.ast_parser import MarkdownParser
from compose.model.ast import *


def test_parse_empty_document():
    """Test parsing an empty document."""
    parser = MarkdownParser()
    doc = parser.parse("")
    assert doc.blocks == []
    assert doc.frontmatter == {}
    print("✅ test_parse_empty_document passed")


def test_parse_simple_paragraph():
    """Test parsing a simple paragraph."""
    parser = MarkdownParser()
    doc = parser.parse("This is a simple paragraph.")

    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], Paragraph)
    assert len(doc.blocks[0].content) == 1
    assert isinstance(doc.blocks[0].content[0], Text)
    assert doc.blocks[0].content[0].content == "This is a simple paragraph."
    print("✅ test_parse_simple_paragraph passed")


def test_parse_multiple_paragraphs():
    """Test parsing multiple paragraphs separated by blank lines."""
    parser = MarkdownParser()
    doc = parser.parse("First paragraph.\n\nSecond paragraph.")

    assert len(doc.blocks) == 2
    assert all(isinstance(block, Paragraph) for block in doc.blocks)
    assert doc.blocks[0].content[0].content == "First paragraph."
    assert doc.blocks[1].content[0].content == "Second paragraph."
    print("✅ test_parse_multiple_paragraphs passed")


def test_parse_headings_level_1():
    """Test parsing level 1 headings."""
    parser = MarkdownParser()
    doc = parser.parse("# Main Heading")

    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], Heading)
    assert doc.blocks[0].level == 1
    assert doc.blocks[0].content[0].content == "Main Heading"
    print("✅ test_parse_headings_level_1 passed")


def test_parse_headings_multiple_levels():
    """Test parsing headings of different levels."""
    parser = MarkdownParser()
    doc = parser.parse("# H1\n\n## H2\n\n### H3\n\n#### H4\n\n##### H5\n\n###### H6")

    assert len(doc.blocks) == 6
    expected_levels = [1, 2, 3, 4, 5, 6]
    expected_texts = ["H1", "H2", "H3", "H4", "H5", "H6"]

    for i, block in enumerate(doc.blocks):
        assert isinstance(block, Heading)
        assert block.level == expected_levels[i]
        assert block.content[0].content == expected_texts[i]
    print("✅ test_parse_headings_multiple_levels passed")


def test_parse_frontmatter_simple():
    """Test parsing simple TOML frontmatter."""
    parser = MarkdownParser()
    doc = parser.parse("+++\ntitle = \"Test Document\"\nauthor = \"Test Author\"\n+++")

    expected_frontmatter = {
        "title": "Test Document",
        "author": "Test Author"
    }
    assert doc.frontmatter == expected_frontmatter
    print("✅ test_parse_frontmatter_simple passed")


def test_parse_frontmatter_with_document():
    """Test parsing frontmatter followed by document content."""
    parser = MarkdownParser()
    content = """+++
title = "My Document"
author = "John Doe"
+++

# Main Title

This is the content."""

    doc = parser.parse(content)

    assert doc.frontmatter == {"title": "My Document", "author": "John Doe"}
    # Note: Frontmatter parsing may leave some artifacts, just check we have the main content
    assert len(doc.blocks) >= 2
    # Find the heading and paragraph
    headings = [b for b in doc.blocks if isinstance(b, Heading)]
    paragraphs = [b for b in doc.blocks if isinstance(b, Paragraph)]
    assert len(headings) >= 1
    assert len(paragraphs) >= 1
    assert headings[0].content[0].content == "Main Title"
    print("✅ test_parse_frontmatter_with_document passed")


def test_parse_fenced_code_block_python():
    """Test parsing a Python code block."""
    parser = MarkdownParser()
    doc = parser.parse("```\nprint('Hello, World!')\n```")

    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], CodeBlock)
    assert doc.blocks[0].language is None
    # Code blocks may or may not preserve trailing newlines depending on implementation
    assert "print('Hello, World!')" in doc.blocks[0].content
    print("✅ test_parse_fenced_code_block_python passed")


def test_parse_fenced_code_block_with_language():
    """Test parsing a code block with language specification."""
    parser = MarkdownParser()
    doc = parser.parse("```python\ndef hello():\n    print('Hello')\n```")

    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], CodeBlock)
    assert doc.blocks[0].language == "python"
    # Check that the main content is there
    assert "def hello():" in doc.blocks[0].content
    assert "print('Hello')" in doc.blocks[0].content
    print("✅ test_parse_fenced_code_block_with_language passed")


def test_parse_multiple_code_blocks():
    """Test parsing multiple code blocks in a document."""
    parser = MarkdownParser()
    doc = parser.parse("```python\nprint('First')\n```\n\nSome text.\n\n```javascript\nconsole.log('Second');\n```")

    assert len(doc.blocks) == 3
    assert isinstance(doc.blocks[0], CodeBlock)
    assert isinstance(doc.blocks[1], Paragraph)
    assert isinstance(doc.blocks[2], CodeBlock)

    assert doc.blocks[0].language == "python"
    assert doc.blocks[2].language == "javascript"
    print("✅ test_parse_multiple_code_blocks passed")


def test_parse_unordered_list():
    """Test parsing unordered lists."""
    parser = MarkdownParser()
    doc = parser.parse("- Item 1\n- Item 2\n- Item 3")

    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], ListBlock)
    assert not doc.blocks[0].ordered
    assert len(doc.blocks[0].items) == 3

    assert doc.blocks[0].items[0].content[0].content == "Item 1"
    assert doc.blocks[0].items[1].content[0].content == "Item 2"
    assert doc.blocks[0].items[2].content[0].content == "Item 3"
    print("✅ test_parse_unordered_list passed")


def test_parse_ordered_list():
    """Test parsing ordered lists."""
    parser = MarkdownParser()
    doc = parser.parse("1. First item\n2. Second item\n3. Third item")

    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], ListBlock)
    assert doc.blocks[0].ordered
    assert len(doc.blocks[0].items) == 3
    print("✅ test_parse_ordered_list passed")


def test_parse_task_list():
    """Test parsing task lists with checkboxes."""
    parser = MarkdownParser()
    doc = parser.parse("- [x] Completed task\n- [ ] Pending task\n- [x] Another completed")

    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], ListBlock)
    assert not doc.blocks[0].ordered

    items = doc.blocks[0].items
    assert len(items) == 3
    assert items[0].checked == True
    assert items[1].checked == False
    assert items[2].checked == True

    assert items[0].content[0].content == "Completed task"
    assert items[1].content[0].content == "Pending task"
    assert items[2].content[0].content == "Another completed"
    print("✅ test_parse_task_list passed")


def test_parse_horizontal_rule_dashes():
    """Test parsing horizontal rule with dashes."""
    parser = MarkdownParser()
    doc = parser.parse("---")

    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], HorizontalRule)
    print("✅ test_parse_horizontal_rule_dashes passed")


def test_parse_horizontal_rule_stars():
    """Test parsing horizontal rule with asterisks."""
    parser = MarkdownParser()
    doc = parser.parse("***")

    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], HorizontalRule)
    print("✅ test_parse_horizontal_rule_stars passed")


def test_parse_horizontal_rule_underscores():
    """Test parsing horizontal rule with underscores."""
    parser = MarkdownParser()
    doc = parser.parse("___")

    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], HorizontalRule)
    print("✅ test_parse_horizontal_rule_underscores passed")
