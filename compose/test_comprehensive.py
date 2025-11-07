# compose/test_comprehensive.py
"""
Comprehensive test suite for the Compose markdown typesetting system.
This file contains tests for all major features and examples we've developed.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from compose.parser.ast_parser import MarkdownParser
from compose.render.ast_renderer import HTMLRenderer, TextRenderer
from compose.model.ast import *

def test_basic_markdown_features():
    """Test basic markdown features: headings, paragraphs, lists"""
    print("🧪 Testing Basic Markdown Features...")

    md = """# Main Heading

This is a paragraph with some text.

## Subheading

Another paragraph here.

### Lists

- Item 1
- Item 2
  - Nested item
  - Another nested

1. Numbered item
2. Another numbered item

#### More Content

Regular paragraph text."""

    parser = MarkdownParser()
    doc = parser.parse(md)

    # Verify structure
    assert len(doc.blocks) == 9  # 4 headings + 5 content blocks

    # Check headings
    assert isinstance(doc.blocks[0], Heading)
    assert doc.blocks[0].level == 1
    assert doc.blocks[0].content[0].content == "Main Heading"

    assert isinstance(doc.blocks[1], Paragraph)
    assert isinstance(doc.blocks[2], Heading)
    assert doc.blocks[2].level == 2

    print("✅ Basic markdown features test passed")

def test_inline_formatting():
    """Test comprehensive inline formatting"""
    print("🧪 Testing Inline Formatting...")

    md = """# Inline Formatting Examples

This paragraph has **bold text**, *italic text*, and ~~strikethrough text~~.

It also has `inline code` and [links](https://example.com).

Math expressions: $E = mc^2$ and more complex ones.

Images: ![Alt text](image.png)

Combined: ***bold italic*** and **bold with `code` inside**."""

    parser = MarkdownParser()
    doc = parser.parse(md)

    assert len(doc.blocks) >= 2  # Heading + at least one paragraph

    # Find paragraphs in the document
    paragraphs = [b for b in doc.blocks if isinstance(b, Paragraph)]
    assert len(paragraphs) >= 1

    # Check that at least one paragraph has the expected formatting
    found_formatting = False
    for paragraph in paragraphs:
        content = paragraph.content
        has_bold = any(isinstance(el, Bold) for el in content)
        has_italic = any(isinstance(el, Italic) for el in content)
        has_strike = any(isinstance(el, Strikethrough) for el in content)
        has_code = any(isinstance(el, CodeInline) for el in content)
        has_link = any(isinstance(el, Link) for el in content)
        has_math = any(isinstance(el, MathInline) for el in content)

        if has_bold or has_italic or has_strike or has_code or has_link or has_math:
            found_formatting = True
            break

    assert found_formatting, "No inline formatting found in any paragraph"

    print("✅ Inline formatting test passed")

def test_code_blocks_and_syntax_highlighting():
    """Test code blocks with syntax highlighting"""
    print("🧪 Testing Code Blocks and Syntax Highlighting...")

    md = """# Code Examples

## Python Code

```python
def compose_document(content: str, config: dict) -> str:
    \"\"\"Process markdown content into beautiful output.\"\"\"
    # Parse the markdown
    nodes = parse_markdown(content)

    # Apply configuration
    mode = config.get('mode', 'document')
    output_format = config.get('output', 'html')

    # Render to desired format
    if output_format == 'html':
        return render_html(nodes, config)
    elif output_format == 'pdf':
        return render_pdf(nodes, config)
    else:
        return render_text(nodes, config)

# Usage
result = compose_document("# Hello World", {"output": "html"})
print(result)
```

## JavaScript Code

```javascript
const compose = {
    features: [
        'markdown',
        'syntax-highlighting',
        'math-support',
        'task-lists'
    ],
    version: '1.0.0'
};

// Process document
function processDocument(markdown) {
    return compose.process(markdown, {
        output: 'html',
        syntaxHighlight: true
    });
}

console.log('Compose is ready!');
```"""

    parser = MarkdownParser()
    doc = parser.parse(md)

    # Should have: heading, subheading, code block, subheading, code block
    assert len(doc.blocks) == 5

    # Check code blocks
    assert isinstance(doc.blocks[2], CodeBlock)
    assert isinstance(doc.blocks[4], CodeBlock)

    python_block = doc.blocks[2]
    js_block = doc.blocks[4]

    assert python_block.language == 'python'
    assert js_block.language == 'javascript'

    # Check that code contains expected content
    assert 'def compose_document' in python_block.content
    assert 'const compose' in js_block.content

    print("✅ Code blocks and syntax highlighting test passed")

def test_tables():
    """Test table parsing and rendering"""
    print("🧪 Testing Tables...")

    md = """# Data Tables

| Feature | Status | Priority |
|---------|--------|----------|
| Markdown Parsing | ✅ Complete | High |
| Rich Text Formatting | ✅ Complete | High |
| Code Syntax Highlighting | ✅ Complete | Medium |
| Mathematical Expressions | ✅ Complete | High |

## Complex Table

| **Bold Header** | *Italic Header* | `Code Header` |
|----------------|-----------------|---------------|
| Normal cell | **Bold cell** | *Italic cell* |
| Cell with `code` | ~~Strike~~ | [Link](url) |
| Math: $E=mc^2$ | Image: ![img](pic.png) | Combined **bold** and *italic* |"""

    parser = MarkdownParser()
    doc = parser.parse(md)

    # Should have: heading, table, heading, table
    assert len(doc.blocks) == 4

    assert isinstance(doc.blocks[1], Table)
    assert isinstance(doc.blocks[3], Table)

    # Check first table structure
    table1 = doc.blocks[1]
    assert len(table1.headers) == 3
    assert len(table1.rows) == 4

    # Check that headers are parsed as inline elements
    assert len(table1.headers[0]) == 1  # "Feature"
    assert len(table1.headers[1]) == 1  # "Status"

    print("✅ Tables test passed")

def test_blockquotes_with_formatting():
    """Test complex blockquotes with nested formatting"""
    print("🧪 Testing Blockquotes with Formatting...")

    md = """> # Blockquote with Heading
>
> This blockquote demonstrates how **rich formatting** works within quotes.
> You can include *italic text*, `code snippets`, and even ~~strikethrough~~ elements.
>
> ## Nested Heading
>
> It supports multiple paragraphs and **complex formatting** with:
> - **Bold items**
> - *Italic items*
> - `Code items`
>
> > You can even nest blockquotes for complex document structures.
> > With **bold** and *italic* formatting in nested quotes.
>
> Math expressions work too: $E = mc^2$ and $\\int f(x) dx$.
>
> And here's a code block inside a blockquote:
>
> ```python
> def example():
>     print("Hello from blockquote!")
> ```"""

    parser = MarkdownParser()
    doc = parser.parse(md)

    assert len(doc.blocks) == 1
    assert isinstance(doc.blocks[0], Blockquote)

    blockquote = doc.blocks[0]
    # Should contain multiple blocks: headings, paragraphs, nested blockquote, math, code
    assert len(blockquote.content) >= 5

    print("✅ Blockquotes with formatting test passed")

def test_math_rendering():
    """Test mathematical expressions rendering"""
    print("🧪 Testing Math Rendering...")

    md = """# Mathematical Expressions

## Inline Math

The famous equation $E = mc^2$ relates energy $E$ to mass $m$ and the speed of light $c$.

## Block Math

For more complex expressions:

$$
\\int_{-\\infty}^{\\infty} e^{-x^2} dx = \\sqrt{\\pi}
$$

This is the Gaussian integral, fundamental in probability and statistics.

## More Math

Euler's formula: $e^{i\\pi} + 1 = 0$

Matrix notation: $\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}$

Greek letters: $\\alpha + \\beta = \\gamma$"""

    parser = MarkdownParser()
    doc = parser.parse(md)

    # Should have: heading, subheading, paragraph, math block, paragraph, paragraph, paragraph
    assert len(doc.blocks) >= 7

    # Find the math block
    math_blocks = [b for b in doc.blocks if isinstance(b, MathBlock)]
    assert len(math_blocks) == 1

    math_block = math_blocks[0]
    assert 'int' in math_block.content
    assert 'infty' in math_block.content
    assert 'sqrt' in math_block.content

    print("✅ Math rendering test passed")

def test_smart_typography():
    """Test smart typography transformations"""
    print("🧪 Testing Smart Typography...")

    md = """# Typography Showcase

Compose includes smart typography features:

Smart quotes: "Hello world" and 'single quotes'.
Smart dashes: en-dash (--) and em-dash (---).
Smart ellipses: ... becomes …

## More Examples

"Double quotes" and 'single quotes' should be curly.

Dashes: en--dash and em---dash.

Ellipses... work correctly."""

    parser = MarkdownParser()
    doc = parser.parse(md)

    # Find the paragraph with typography
    typography_para = None
    for block in doc.blocks:
        if isinstance(block, Paragraph):
            content = ' '.join(el.content if isinstance(el, Text) else '' for el in block.content)
            if 'Smart quotes' in content:
                typography_para = block
                break

    assert typography_para is not None

    # Check for smart typography in the parsed content
    text_elements = [el for el in typography_para.content if isinstance(el, Text)]
    combined_text = ' '.join(el.content for el in text_elements)

    # Should contain smart typography characters
    has_curly_quotes = ('"' in combined_text or '"' in combined_text or
                       "'" in combined_text or "'" in combined_text)
    has_en_dash = '–' in combined_text
    has_em_dash = '—' in combined_text
    has_ellipsis = '…' in combined_text

    assert has_curly_quotes, "Smart quotes not applied"
    assert has_en_dash, "En-dash not applied"
    assert has_em_dash, "Em-dash not applied"
    assert has_ellipsis, "Smart ellipses not applied"

    print("✅ Smart typography test passed")

def test_task_lists():
    """Test task list parsing"""
    print("🧪 Testing Task Lists...")

    md = """# Task Management

## Development Tasks

- [x] Implement basic markdown parsing
- [x] Add syntax highlighting
- [ ] Write comprehensive tests
- [x] Create documentation
- [ ] Deploy to production

## Future Features

- [ ] Add PDF export
- [ ] Implement themes
- [ ] Add plugin system
- [ ] Create web interface"""

    parser = MarkdownParser()
    doc = parser.parse(md)

    # Find list blocks
    list_blocks = [b for b in doc.blocks if isinstance(b, ListBlock)]
    assert len(list_blocks) >= 2

    # Check first task list
    task_list = list_blocks[0]
    assert len(task_list.items) == 5

    # Check task states
    assert task_list.items[0].checked == True   # [x] Implement basic...
    assert task_list.items[1].checked == True   # [x] Add syntax...
    assert task_list.items[2].checked == False  # [ ] Write comprehensive...
    assert task_list.items[3].checked == True   # [x] Create documentation...
    assert task_list.items[4].checked == False  # [ ] Deploy to production...

    print("✅ Task lists test passed")

def test_renderer_integration():
    """Test that renderers work correctly with the AST"""
    print("🧪 Testing Renderer Integration...")

    md = """# Integration Test

This is a **bold** paragraph with *italic* text and `inline code`.

## Code Example

```python
def hello():
    print("Hello, World!")
```

## Math

Inline: $x^2 + y^2 = z^2$

Block:
$$
\\int_0^1 x^2 dx = \\frac{1}{3}
$$"""

    parser = MarkdownParser()
    doc = parser.parse(md)

    # Test HTML rendering
    html_renderer = HTMLRenderer()
    config = {'typography': {'font_size': 14}, 'colors': {'text': '#333'}}
    html_output = html_renderer.render(doc, config)

    # Basic checks
    assert '<!DOCTYPE html>' in html_output
    assert '<title>Compose Document</title>' in html_output
    assert '<strong>bold</strong>' in html_output
    assert '<em>italic</em>' in html_output
    assert '<code>' in html_output  # Should have inline code
    assert '<div class="math-block"' in html_output

    # Test text rendering
    text_renderer = TextRenderer()
    text_output = text_renderer.render(doc, config)

    assert '# Integration Test' in text_output
    assert '**bold**' in text_output
    assert '*italic*' in text_output
    assert '`inline code`' in text_output
    assert '```' in text_output
    assert 'Math Block' in text_output

    print("✅ Renderer integration test passed")

def test_complex_nested_structures():
    """Test complex nested structures"""
    print("🧪 Testing Complex Nested Structures...")

    md = """# Complex Document

## Section 1

This is a paragraph with **bold**, *italic*, and `code`.

> Blockquote with **bold** and *italic* text.
>
> Nested blockquote:
> > Even deeper with ~~strikethrough~~ and `code`.
>
> Math in blockquote: $\\sum_{i=1}^n x_i$

### Subsection

- Task item with **bold**
- [x] Completed task
- [ ] Pending task

#### Table in Subsection

| Feature | Status | Notes |
|---------|--------|-------|
| **Bold** | ✅ | Working |
| *Italic* | ✅ | Working |
| `Code` | ✅ | Working |

## Math Section

Complex equation:
$$
\\lim_{x \\to 0} \\frac{\\sin x}{x} = 1
$$

## Code Section

```python
def complex_function():
    \"\"\"A complex function with docstring.\"\"\"
    # This is a comment
    x = 42
    y = "string"
    if x > 0:
        return x * 2
    else:
        return "negative"
```"""

    parser = MarkdownParser()
    doc = parser.parse(md)

    # Should parse successfully with complex nesting
    assert len(doc.blocks) > 10

    # Check for various element types
    has_headings = any(isinstance(b, Heading) for b in doc.blocks)
    has_paragraphs = any(isinstance(b, Paragraph) for b in doc.blocks)
    has_blockquotes = any(isinstance(b, Blockquote) for b in doc.blocks)
    has_lists = any(isinstance(b, ListBlock) for b in doc.blocks)
    has_tables = any(isinstance(b, Table) for b in doc.blocks)
    has_math = any(isinstance(b, MathBlock) for b in doc.blocks)
    has_code = any(isinstance(b, CodeBlock) for b in doc.blocks)

    assert has_headings
    assert has_paragraphs
    assert has_blockquotes
    assert has_lists
    assert has_tables
    assert has_math
    assert has_code

    print("✅ Complex nested structures test passed")

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 Running Comprehensive Compose Test Suite")
    print("=" * 50)

    try:
        test_basic_markdown_features()
        test_inline_formatting()
        test_code_blocks_and_syntax_highlighting()
        test_tables()
        test_blockquotes_with_formatting()
        test_math_rendering()
        test_smart_typography()
        test_task_lists()
        test_renderer_integration()
        test_complex_nested_structures()

        print("\n" + "=" * 50)
        print("🎉 ALL COMPREHENSIVE TESTS PASSED!")
        print("✅ The Compose markdown typesetting system is fully functional")
        print("✅ All features are working correctly")
        print("✅ Complex nested structures are supported")
        print("✅ Rendering works across HTML and text formats")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_comprehensive_tests()
