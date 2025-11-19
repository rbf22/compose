# KaTeX Python 

**Fast math typesetting for Python** - A complete Python port of [KaTeX](https://katex.org/), the fastest math rendering library for the web.

[![PyPI version](https://badge.fury.io/py/pytex-katex.svg)](https://pypi.org/project/pytex-katex/)
[![Python versions](https://img.shields.io/pypi/pyversions/pytex-katex.svg)](https://pypi.org/project/pytex-katex/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Blazing Fast** - Optimized for performance
- **100% LaTeX Compatible** - Supports all standard LaTeX math commands
- **Zero Dependencies** - Pure Python implementation
- **Multiple Output Formats** - HTML, MathML, and more
- **Extensible** - Easy to add custom commands and macros
- **Comprehensive** - 46+ mathematical functions implemented

## Installation

```bash
pip install pytex-katex
```

## Quick Start

```python
from pytex.katex import render_to_string

# Render LaTeX to HTML
html = render_to_string(r"\sum_{i=1}^{n} \frac{\partial f}{\partial x_i}")
print(html)
# Output: <span class="katex">...</span>

# Render with display mode
html = render_to_string(r"\int_{-\infty}^{\infty} e^{-x^2} \, dx = \sqrt{\pi}", display_mode=True)
```

## Usage Examples

### Basic Mathematics
```python
from pytex.katex import render_to_string

# Fractions and integrals
result = render_to_string(r"\frac{a}{b} + \int_0^1 f(x) \, dx")

# Superscripts and subscripts
result = render_to_string(r"x^2 + a_{ij} + \sum_{n=1}^{\infty} \frac{1}{n^2}")

# Greek letters and symbols
result = render_to_string(r"\alpha + \beta + \gamma + \Delta + \infty")
```

### Advanced Features
```python
# Matrices and arrays
matrix = render_to_string(r"""
\begin{pmatrix}
a & b & c \\
d & e & f \\
g & h & i
\end{pmatrix}
""")

# Custom macros
from pytex.katex import define_macro
define_macro(r"\R", r"\mathbb{R}")
result = render_to_string(r"f: \R \to \R")

# Color and styling
colored = render_to_string(r"\color{red}{\int_0^1 x^2 \, dx} = \frac{1}{3}")
```

## Supported LaTeX Commands

### Core Mathematics
- **Arithmetic**: `+`, `-`, `\times`, `\div`, `\pm`, `\mp`
- **Relations**: `=`, `<`, `>`, `\leq`, `\geq`, `\neq`
- **Operators**: `\sum`, `\prod`, `\int`, `\lim`, `\sin`, `\cos`, `\log`

### Advanced Features
- **Fractions**: `\frac{a}{b}`, `\dfrac{a}{b}`, `\binom{n}{k}`
- **Roots**: `\sqrt{x}`, `\sqrt[n]{x}`
- **Accents**: `\hat{x}`, `\tilde{y}`, `\bar{z}`, `\vec{v}`
- **Arrays**: `\begin{matrix}`, `\begin{pmatrix}`, `\begin{bmatrix}`
- **Text**: `\text{normal text}`, `\mathrm{roman}`, `\mathbf{bold}`

### Extensions
- **Colors**: `\color{red}{text}`, `\textcolor{blue}{text}`
- **Macros**: `\def\mycommand{...}`, `\let`, `\futurelet`
- **Boxes**: `\fbox{content}`, `\colorbox{color}{content}`
- **Spacing**: `\kern{1em}`, `\phantom{text}`

## Architecture

```
pytex/
├── python/           # Complete Python KaTeX implementation
│   ├── katex/        # Main KaTeX implementation
│   │   ├── __init__.py  # Public API
│   │   ├── parser.py    # LaTeX parsing engine
│   │   ├── renderer.py  # Output generation
│   │   └── functions/   # Mathematical functions (46+ files)
│   ├── environments/    # Array/matrix environments
│   └── utils/          # Supporting utilities
├── archive/          # Original JavaScript code (archived)
├── setup.py          # Python packaging
├── requirements.txt  # Dependencies
└── README.md         # This file
```

## Development

### Setup
```bash
git clone https://github.com/robertfenwick/pytex-katex.git
cd pytex-katex
pip install -e .
```

### Testing
```bash
pytest tests/
```

### Type Checking
```bash
mypy python/
```

## Documentation

- [API Reference](docs/api.md)
- [Supported Commands](docs/commands.md)
- [Integration Guide](docs/integration.md)
- [Contributing](docs/contributing.md)

## Contributing

We welcome contributions! Please see our [Contributing Guide](docs/contributing.md) for details.

### Areas for Contribution
- Additional LaTeX command support
- Performance optimizations
- PDF rendering integration
- Documentation improvements

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Original KaTeX**: This is a Python port of [KaTeX](https://katex.org/)
- **Inspiration**: Based on the excellent work of the KaTeX team
- **Community**: Thanks to all contributors and users

## Support

- **Issues**: [GitHub Issues](https://github.com/robertfenwick/pytex-katex/issues)
- **Discussions**: [GitHub Discussions](https://github.com/robertfenwick/pytex-katex/discussions)
- **Documentation**: [Read the Docs](https://pytex-katex.readthedocs.io/)

---

**KaTeX Python** - Bringing beautiful mathematical typesetting to Python! 
