# Complete Compose Feature Showcase

This document demonstrates **all** features of the Compose markdown typesetting system.

## Task Lists

- [x] Complete markdown parsing
- [x] Bold and italic text formatting
- [x] Inline code and code blocks
- [x] Strikethrough text support
- [ ] Links and image embedding
- [ ] Math expressions
- [x] Tables with formatting
- [x] Blockquotes
- [x] Smart typography

## Advanced Text Formatting

You can combine **bold** and *italic* text with `inline code`, ~~strikethrough~~ formatting, and even $math expressions$ like $E = mc^2$.

### Links and References

Check out the [Compose GitHub repository](https://github.com/example/compose) for more information.

Here's an image: ![Compose Logo](logo.png "The Compose logo")

## Code Examples with Syntax Highlighting

### Python Code
```python
def compose_document(content: str, config: dict) -> str:
    """Process markdown content into beautiful output."""
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

### JavaScript Example
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
```

## Mathematical Expressions

### Inline Math
The famous equation $E = mc^2$ relates energy $E$ to mass $m$ and the speed of light $c$.

### Block Math
For more complex expressions:

$$
\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}
$$

This is the Gaussian integral, fundamental in probability and statistics.

## Comprehensive Table

| Feature | Status | Description | Priority |
|---------|--------|-------------|----------|
| **Markdown Parsing** | ✅ Complete | Full CommonMark support | High |
| **Rich Text Formatting** | ✅ Complete | Bold, italic, strikethrough | High |
| **Code Syntax Highlighting** | ✅ Complete | Python, JavaScript support | Medium |
| **Mathematical Expressions** | ✅ Complete | LaTeX-style inline and block math | High |
| **Table Rendering** | ✅ Complete | GitHub-flavored markdown tables | High |
| **Task Lists** | ✅ Complete | Interactive checkboxes | Medium |
| **Link Support** | ✅ Complete | Reference-style and inline links | High |
| **Image Embedding** | ✅ Complete | Alt text and captions | High |
| **Blockquotes** | ✅ Complete | Multi-line quote support | Medium |
| **Smart Typography** | ✅ Complete | Quotes, dashes, ellipses | Low |

## Blockquotes with Rich Content

> This blockquote demonstrates how **rich formatting** works within quotes.
> You can include *italic text*, `code snippets`, and even ~~strikethrough~~ elements.
>
> Multiple paragraphs are supported, and the formatting is preserved throughout.
>
> > You can even nest blockquotes for complex document structures.

## Typography Showcase

Compose includes smart typography features:

- Smart quotes: "Hello world" and 'single quotes'
- Smart dashes: en-dash (--) and em-dash (---)
- Smart ellipses: ... becomes …

## Horizontal Rules

---

That's the complete feature set! The system now provides comprehensive markdown typesetting with professional output quality.
