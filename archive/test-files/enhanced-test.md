# Enhanced Compose Features Test

This document demonstrates all the advanced markdown features supported by Compose.

## Text Formatting

**Bold text** and *italic text* and ***bold italic*** combinations work perfectly.

You can also ~~strikethrough text~~ when needed.

Inline `code snippets` look great alongside $math expressions$ like $E = mc^2$.

## Links and Images

Check out this [link to Python documentation](https://docs.python.org/3/) for more information.

Here's an example image:

![Python Logo](python-logo.png "The official Python logo")

## Blockquotes

> This is a blockquote that can span multiple lines.
> It supports **bold** and *italic* formatting within.
>
> You can also have multiple paragraphs in a blockquote.
> Each line starts with > in the markdown source.

## Math Support

### Inline Math
The famous equation is $E = mc^2$.

### Block Math
Here's a more complex equation:

$$
\frac{d}{dx} \int_a^x f(t) dt = f(x)
$$

## Code Examples

Here's a Python function:

```python
def fibonacci(n):
    """Generate the nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))  # Output: 55
```

And here's some JavaScript:

```javascript
const compose = {
    features: ['markdown', 'math', 'code'],
    awesome: true
};

console.log('Compose is', compose.awesome ? 'awesome!' : 'meh');
```

## Tables

| Feature | Status | Notes |
|---------|--------|-------|
| **Bold/Italic** | ✅ Complete | Full support |
| ~~Strikethrough~~ | ✅ Complete | Text formatting |
| `Inline Code` | ✅ Complete | Syntax highlighting ready |
| $Math$ | ✅ Complete | LaTeX-style expressions |
| ![Images](img) | ✅ Complete | Path references |
| [Links](url) | ✅ Complete | URL references |
| > Blockquotes | ✅ Complete | Multi-line support |
| Code Blocks | ✅ Complete | Language detection |

## Lists

- **Bold item** with formatting
- *Italic item* here
- Regular item
- Item with `inline code`
- Item with $inline math$
- ~~Strikethrough item~~
- [Link item](https://example.com)

## Horizontal Rules

---

That's all the advanced features! The system now supports a comprehensive subset of CommonMark with additional enhancements for technical writing.
