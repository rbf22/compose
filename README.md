# Compose: Professional Typesetting from Markdown

> **Compose** transforms Markdown into publication-quality documents with LaTeX-like mathematical typesetting, while maintaining Markdown's simplicity.

[![Tests](https://img.shields.io/badge/tests-404%20passing-brightgreen)](https://github.com/compose/compose)
[![Python](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## ✨ Features

### 📐 Mathematical Typesetting
- **LaTeX-quality equations** with proper spacing and alignment
- **Advanced math layout**: matrices, integrals, radicals, fractions
- **Macro system** with `\newcommand` support
- **Knuth-Plass line breaking** for optimal paragraph layout

### 🎨 Professional Typography
- **Micro-typography**: character protrusion, optical margins
- **Font embedding** and high-DPI rendering
- **Cross-references** with automatic numbering
- **Bibliography management** with multiple citation styles

### 🔧 Extensible Architecture
- **Plugin system** for custom content types
- **Advanced animations** for slide presentations
- **Multiple output formats**: HTML, PDF, slides
- **Comprehensive linting** with configurable rules

### 📊 Content Types
- **Diagrams**: Flowcharts, sequence diagrams, Gantt charts, ER diagrams, network diagrams
- **Slides**: Interactive presentations with animations
- **Tables**: Professional table rendering with captions
- **Code blocks**: Syntax highlighting and formatting

## 🚀 Quick Start

### Installation
```bash
# Clone the repository
git clone https://github.com/compose/compose.git
cd compose

# Install with Poetry
poetry install

# Or install manually
pip install -e .
```

### Basic Usage
```bash
# Build a document
compose build document.md --config config.toml

# Lint markdown files
compose lint document.md

# Create slides
compose build slides.md --mode slides
```

### Example Document
```markdown
# My Research Paper

## Abstract
This paper presents groundbreaking results in mathematics.

## Mathematical Foundations

Consider the equation:
$$E = mc^2$$

For more complex expressions:
$$\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}$$

## Matrix Operations

Consider the following matrix:
$$\begin{pmatrix}
a & b \\
c & d
\end{pmatrix}$$

## References

See Figure \ref{fig:results} for the experimental results.

![Experimental Results](results.png){#fig:results}

## Bibliography

According to @smith2023, this approach is effective.

@article{smith2023,
  title={An Effective Approach},
  author={John Smith},
  journal={Journal},
  year={2023}
}
```

## 📖 Documentation

### Core Concepts

#### Mathematical Expressions
Compose supports both inline `$x^2$` and display `$$E = mc^2$$` math expressions with full LaTeX compatibility.

#### Macros and Definitions
```latex
\newcommand{\R}{\mathbb{R}}
\newcommand{\vector}[1]{\mathbf{#1}}
\newcommand{\norm}[1]{\left\| #1 \right\|}

Let $\vector{v} \in \R^n$ such that $\norm{\vector{v}} = 1$.
```

#### Cross-References
```markdown
See Figure \ref{fig:results} for the experimental results.

![Experimental Results](results.png){#fig:results}
```

#### Bibliography
```markdown
According to @smith2023, this approach is effective.

@article{smith2023,
  title={An Effective Approach},
  author={John Smith},
  journal={Journal},
  year={2023}
}
```

### Configuration
```toml
[output]
format = "pdf"

[math]
quality = "high"

[typography]
font_family = "Times"
font_size = 11

[features]
macros = true
cross_references = true
bibliography = true
microtypography = true
```

### Advanced Features

#### Plugin System
Create custom content types:
```python
from compose.plugin_system import ContentPlugin

class MindMapPlugin(ContentPlugin):
    @property
    def content_type(self) -> str:
        return "mindmap"

    def parse_to_box(self, content: str, metadata=None):
        # Custom parsing logic
        return UniversalBox(content=parsed_data, content_type=ContentType.DIAGRAM)
```

#### Slide Animations
```python
slide = engine.create_content_slide("Title", content_blocks)
engine.create_fade_in_animation(slide, ".slide-content")
engine.create_sequential_reveal(slide, [".bullet-1", ".bullet-2"])
```

#### Micro-typography
Automatic character protrusion and font expansion for professional typography.

## 🏗️ Architecture

```
compose/
├── cli.py              # Command-line interface
├── engine.py           # Main build engine
├── parser/             # Markdown parsing
├── layout/             # Layout engines
│   ├── math_layout.py      # Advanced math typesetting
│   ├── knuth_plass.py      # Line breaking algorithm
│   ├── macro_system.py     # LaTeX macro expansion
│   └── microtypography.py  # Professional typography
├── render/             # Output renderers
│   ├── html.py
│   ├── pdf.py
│   └── slide.py
├── lint/               # Markdown linting system
├── plugin_system.py    # Extensible plugin architecture
└── tex_compatibility.py # TeX compatibility layer
```

## 🧪 Testing

Run the comprehensive test suite:
```bash
poetry run pytest
```

The system includes 404+ tests covering:
- Mathematical layout algorithms
- Macro expansion and scoping
- Typography and micro-typography
- Plugin system functionality
- Cross-reference management
- Bibliography formatting
- Markdown linting rules

## 📈 Performance

- **Sub-second rendering** for typical documents
- **Incremental layout** for large documents
- **Memory-efficient** font handling
- **Parallel processing** capabilities

## 🤝 Contributing

We welcome contributions! Areas of particular interest:

1. **Performance Optimization**
2. **Additional Output Formats**
3. **New Content Types**
4. **Internationalization**
5. **Accessibility Features**

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **Donald Knuth** for TeX and the box-and-glue model
- **John Gruber** for Markdown
- **The LaTeX community** for mathematical typesetting standards
- **Typography experts** worldwide for the science of beautiful text

---

**Compose**: Where Markdown meets Mathematics meets Professional Publishing 🎯
