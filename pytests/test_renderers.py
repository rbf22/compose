# tests/test_renderers.py
"""Tests for HTML and text renderers."""

from compose.parser.ast_parser import MarkdownParser
from compose.render.ast_renderer import HTMLRenderer, TextRenderer
from compose.model.ast import *


def test_html_renderer_heading():
    """Test rendering headings to HTML."""
    doc = Document(blocks=[
        Heading(level=1, content=[Text(content="Main Title")]),
        Heading(level=2, content=[Text(content="Subtitle")])
    ], frontmatter={})

    renderer = HTMLRenderer()
    html = renderer.render(doc, {})

    assert '<h1>Main Title</h1>' in html
    assert '<h2>Subtitle</h2>' in html
    print("✅ test_html_renderer_heading passed")


def test_html_renderer_bold():
    """Test rendering bold text to HTML."""
    doc = Document(blocks=[
        Paragraph(content=[
            Text(content="This is "),
            Bold(children=[Text(content="bold")]),
            Text(content=" text.")
        ])
    ], frontmatter={})

    renderer = HTMLRenderer()
    html = renderer.render(doc, {})
    assert '<strong>bold</strong>' in html
    print("✅ test_html_renderer_bold passed")


def test_html_renderer_code_block():
    """Test rendering code blocks to HTML."""
    doc = Document(blocks=[
        CodeBlock(content='print("Hello")\nreturn True', language='python')
    ], frontmatter={})

    renderer = HTMLRenderer()
    html = renderer.render(doc, {})
    assert '<pre><code language-python>' in html
    assert '<span class="syntax-keyword">print</span>' in html
    assert '<span class="syntax-keyword">return</span>' in html
    print("✅ test_html_renderer_code_block passed")


def test_text_renderer_heading():
    """Test rendering headings to text."""
    doc = Document(blocks=[
        Heading(level=1, content=[Text(content="Main Title")])
    ], frontmatter={})

    renderer = TextRenderer()
    text = renderer.render(doc, {})
    assert "# Main Title" in text
    print("✅ test_text_renderer_heading passed")


def test_text_renderer_bold():
    """Test rendering bold text to markdown format."""
    doc = Document(blocks=[
        Paragraph(content=[
            Text(content="This is "),
            Bold(children=[Text(content="bold")]),
            Text(content=" text.")
        ])
    ], frontmatter={})

    renderer = TextRenderer()
    text = renderer.render(doc, {})
    assert "**bold**" in text
    print("✅ test_text_renderer_bold passed")


def test_text_renderer_code_block():
    """Test rendering code blocks to text."""
    doc = Document(blocks=[
        CodeBlock(content='print("Hello")\nreturn True', language='python')
    ], frontmatter={})

    renderer = TextRenderer()
    text = renderer.render(doc, {})
    assert "```" in text
    assert 'print("Hello")' in text
    print("✅ test_text_renderer_code_block passed")


def test_renderer_integration():
    """Test that parsing and rendering works together."""
    md = """# Test Document

This is a **bold** paragraph with `code`.

```python
def hello():
    return "world"
```"""

    parser = MarkdownParser()
    doc = parser.parse(md)

    # Test HTML rendering
    html_renderer = HTMLRenderer()
    html = html_renderer.render(doc, {})
    assert '<h1>Test Document</h1>' in html
    assert '<strong>bold</strong>' in html
    assert '<code>' in html

    # Test text rendering
    text_renderer = TextRenderer()
    text = text_renderer.render(doc, {})
    assert '# Test Document' in text
    assert '**bold**' in text
    assert '`code`' in text
    assert '```' in text

    print("✅ test_renderer_integration passed")
