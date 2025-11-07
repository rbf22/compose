# compose/test_parser.py
"""Unit tests for the markdown parser"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from compose.parser.ast_parser import MarkdownParser
from compose.model.ast import *

def test_basic_paragraph():
    """Test parsing a simple paragraph"""
    test_md = "This is a simple paragraph."
    nodes, _ = parse_markdown_string(test_md)

    assert len(nodes) == 1
    assert isinstance(nodes[0], Paragraph)
    assert len(nodes[0].content) == 1
    assert isinstance(nodes[0].content[0], Text)
    assert nodes[0].content[0].content == "This is a simple paragraph."
    print("✅ test_basic_paragraph passed")

def test_headings():
    """Test parsing headings"""
    test_md = "# Heading 1\n\n## Heading 2\n\n### Heading 3"
    nodes, _ = parse_markdown_string(test_md)

    assert len(nodes) == 3
    assert isinstance(nodes[0], Heading)
    assert nodes[0].level == 1
    assert len(nodes[0].content) == 1
    assert isinstance(nodes[0].content[0], Text)
    assert nodes[0].content[0].content == "Heading 1"

    assert isinstance(nodes[1], Heading)
    assert nodes[1].level == 2
    assert nodes[1].content[0].content == "Heading 2"

    assert isinstance(nodes[2], Heading)
    assert nodes[2].level == 3
    assert nodes[2].content[0].content == "Heading 3"
    print("✅ test_headings passed")

def test_bold_formatting():
    """Test parsing bold text"""
    test_md = "This is **bold** text."
    nodes, _ = parse_markdown_string(test_md)

    assert len(nodes) == 1
    paragraph = nodes[0]
    assert isinstance(paragraph, Paragraph)

    # Check that we have multiple inline elements: Text, Bold, Text
    assert len(paragraph.content) >= 3
    assert isinstance(paragraph.content[0], Text)
    assert paragraph.content[0].content == "This is "

    # Find the bold element
    bold_found = False
    for element in paragraph.content:
        if isinstance(element, Bold):
            bold_found = True
            assert len(element.children) == 1
            assert isinstance(element.children[0], Text)
            assert element.children[0].content == "bold"
            break

    assert bold_found, "Bold element not found"
    print("✅ test_bold_formatting passed")

def test_code_blocks():
    """Test parsing code blocks"""
    test_md = "```\ncode block\n```"
    nodes, _ = parse_markdown_string(test_md)

    assert len(nodes) == 1
    assert isinstance(nodes[0], CodeBlock)
    assert nodes[0].content == "code block"
    assert nodes[0].language is None
    print("✅ test_code_blocks passed")

def test_tables():
    """Test parsing tables"""
    test_md = "| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1 | Cell 2 |"
    nodes, _ = parse_markdown_string(test_md)

    assert len(nodes) == 1
    assert isinstance(nodes[0], Table)
    assert len(nodes[0].headers) == 2
    assert nodes[0].headers[0][0].content == "Header 1"
    assert nodes[0].headers[1][0].content == "Header 2"
    assert len(nodes[0].rows) == 1
    assert nodes[0].rows[0][0][0].content == "Cell 1"
    assert nodes[0].rows[0][1][0].content == "Cell 2"
    print("✅ test_tables passed")

def test_blockquotes():
    """Test parsing blockquotes"""
    test_md = "> This is a blockquote"
    nodes, _ = parse_markdown_string(test_md)

    assert len(nodes) == 1
    assert isinstance(nodes[0], Blockquote)
    assert len(nodes[0].content) == 1
    assert isinstance(nodes[0].content[0], Paragraph)
    print("✅ test_blockquotes passed")

def test_blockquote_bold_formatting():
    """Test bold formatting within blockquotes"""
    test_md = "> This blockquote has **bold text** in it."
    nodes, _ = parse_markdown_string(test_md)

    assert len(nodes) == 1
    blockquote = nodes[0]
    assert isinstance(blockquote, Blockquote)
    assert len(blockquote.content) == 1
    
    paragraph = blockquote.content[0]
    assert isinstance(paragraph, Paragraph)
    
    # Check that bold formatting is parsed
    content = paragraph.content
    assert len(content) >= 3  # Text, Bold, Text
    
    # Find the bold element
    bold_found = False
    for element in content:
        if isinstance(element, Bold):
            bold_found = True
            assert len(element.children) == 1
            assert isinstance(element.children[0], Text)
            assert element.children[0].content == "bold text"
            break
    
    assert bold_found, "Bold element not found in blockquote"
    print("✅ test_blockquote_bold_formatting passed")

def test_blockquote_italic_formatting():
    """Test italic formatting within blockquotes"""
    test_md = "> This blockquote has *italic text* in it."
    nodes, _ = parse_markdown_string(test_md)

    assert len(nodes) == 1
    blockquote = nodes[0]
    assert isinstance(blockquote, Blockquote)
    assert len(blockquote.content) == 1
    
    paragraph = blockquote.content[0]
    assert isinstance(paragraph, Paragraph)
    
    # Check that italic formatting is parsed
    content = paragraph.content
    assert len(content) >= 3  # Text, Italic, Text
    
    # Find the italic element
    italic_found = False
    for element in content:
        if isinstance(element, Italic):
            italic_found = True
            assert len(element.children) == 1
            assert isinstance(element.children[0], Text)
            assert element.children[0].content == "italic text"
            break
    
    assert italic_found, "Italic element not found in blockquote"
    print("✅ test_blockquote_italic_formatting passed")

def test_blockquote_strikethrough_formatting():
    """Test strikethrough formatting within blockquotes"""
    test_md = "> This blockquote has ~~strikethrough text~~ in it."
    nodes, _ = parse_markdown_string(test_md)

    assert len(nodes) == 1
    blockquote = nodes[0]
    assert isinstance(blockquote, Blockquote)
    assert len(blockquote.content) == 1
    
    paragraph = blockquote.content[0]
    assert isinstance(paragraph, Paragraph)
    
    # Check that strikethrough formatting is parsed
    content = paragraph.content
    
    # Find the strikethrough element
    strike_found = False
    for element in content:
        if isinstance(element, Strikethrough):
            strike_found = True
            assert len(element.children) == 1
            assert isinstance(element.children[0], Text)
            assert element.children[0].content == "strikethrough text"
            break
    
    assert strike_found, "Strikethrough element not found in blockquote"
    print("✅ test_blockquote_strikethrough_formatting passed")

def test_blockquote_code_formatting():
    """Test code formatting within blockquotes"""
    test_md = "> This blockquote has `code snippets` in it."
    nodes, _ = parse_markdown_string(test_md)

    assert len(nodes) == 1
    blockquote = nodes[0]
    assert isinstance(blockquote, Blockquote)
    assert len(blockquote.content) == 1
    
    paragraph = blockquote.content[0]
    assert isinstance(paragraph, Paragraph)
    
    # Check that code formatting is parsed
    content = paragraph.content
    
    # Find the code element
    code_found = False
    for element in content:
        if isinstance(element, CodeInline):
            code_found = True
            assert element.content == "code snippets"
            break
    
    assert code_found, "Code element not found in blockquote"
    print("✅ test_blockquote_code_formatting passed")

def test_blockquote_mixed_formatting():
    """Test mixed formatting within blockquotes"""
    test_md = "> This has **bold**, *italic*, `code`, and ~~strikethrough~~ formatting."
    nodes, _ = parse_markdown_string(test_md)

    assert len(nodes) == 1
    blockquote = nodes[0]
    assert isinstance(blockquote, Blockquote)
    assert len(blockquote.content) == 1
    
    paragraph = blockquote.content[0]
    assert isinstance(paragraph, Paragraph)
    
    content = paragraph.content
    
    # Check for all formatting types
    bold_found = any(isinstance(el, Bold) for el in content)
    italic_found = any(isinstance(el, Italic) for el in content)
    code_found = any(isinstance(el, CodeInline) for el in content)
    strike_found = any(isinstance(el, Strikethrough) for el in content)
    
    assert bold_found, "Bold not found in mixed blockquote"
    assert italic_found, "Italic not found in mixed blockquote"
    assert code_found, "Code not found in mixed blockquote"
    assert strike_found, "Strikethrough not found in mixed blockquote"
    print("✅ test_blockquote_mixed_formatting passed")

def test_blockquote_multiline_with_formatting():
    """Test multiline blockquotes with formatting"""
    test_md = """> This blockquote demonstrates how **rich formatting** works within quotes.
> You can include *italic text*, `code snippets`, and even ~~strikethrough~~ elements.
> 
> Multiple paragraphs are supported."""
    nodes, _ = parse_markdown_string(test_md)

    assert len(nodes) == 1
    blockquote = nodes[0]
    assert isinstance(blockquote, Blockquote)
    assert len(blockquote.content) >= 2  # Multiple paragraphs
    
    # Check formatting in first paragraph
    first_para = blockquote.content[0]
    assert isinstance(first_para, Paragraph)
    
    first_content = first_para.content
    bold_found = any(isinstance(el, Bold) for el in first_content)
    italic_found = any(isinstance(el, Italic) for el in first_content)
    code_found = any(isinstance(el, CodeInline) for el in first_content)
    strike_found = any(isinstance(el, Strikethrough) for el in first_content)
    
    assert bold_found, "Bold not found in multiline blockquote"
    assert italic_found, "Italic not found in multiline blockquote"
    assert code_found, "Code not found in multiline blockquote"
    assert strike_found, "Strikethrough not found in multiline blockquote"
    print("✅ test_blockquote_multiline_with_formatting passed")

def test_smart_typography():
    """Test smart typography transformations"""
    test_md = 'Smart quotes: "Hello world" and \'single quotes\'. Smart dashes: en-dash (--) and em-dash (---). Smart ellipses: ... becomes …'
    nodes, _ = parse_markdown_string(test_md)

    assert len(nodes) == 1
    paragraph = nodes[0]
    assert isinstance(paragraph, Paragraph)
    
    # Find the text element containing the typography
    text_content = None
    for element in paragraph.content:
        if isinstance(element, Text) and 'Smart quotes' in element.content:
            text_content = element.content
            break
    
    assert text_content is not None, "Typography text not found"
    
    # Check for smart typography transformations
    has_curly_quotes = ('"' in text_content or '"' in text_content or 
                       "'" in text_content or "'" in text_content)
    has_en_dash = '–' in text_content
    has_em_dash = '—' in text_content
    has_ellipsis = '…' in text_content
    
    assert has_curly_quotes, f"Curly quotes not found in: {repr(text_content)}"
    assert has_en_dash, f"En-dash not found in: {repr(text_content)}"
    assert has_em_dash, f"Em-dash not found in: {repr(text_content)}"
    assert has_ellipsis, f"Ellipsis not found in: {repr(text_content)}"
    
    print("✅ test_smart_typography passed")

def parse_markdown_string(content: str):
    """Helper function to parse markdown from string"""
    parser = MarkdownParser()
    return parser.parse(content).blocks, parser.parse(content).frontmatter

def run_tests():
    """Run all parser tests"""
    print("🧪 Running Parser Tests...")
    print()

    try:
        test_basic_paragraph()
        test_headings()
        test_bold_formatting()
        test_code_blocks()
        test_tables()
        test_blockquotes()
        test_blockquote_bold_formatting()
        test_blockquote_italic_formatting()
        test_blockquote_strikethrough_formatting()
        test_blockquote_code_formatting()
        test_blockquote_mixed_formatting()
        test_blockquote_multiline_with_formatting()
        test_smart_typography()

        print()
        print("🎉 All parser tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_tests()
