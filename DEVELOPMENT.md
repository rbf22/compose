
# 🧱 PROJECT OVERVIEW

**Project Name:** Compose
**Goal:** Build a dependency-light, deterministic, and opinionated Markdown→Document/Slide/PDF generator that offers the *aesthetic and density of LaTeX* with *the simplicity of Markdown*.

---

## 🔭 CORE VALUE PROPOSITION

> *Compose* allows technical writers, researchers, and developers to produce dense, beautiful, publication-ready documents (and slides) from Markdown — reproducibly and offline.

---

# 🧩 FUNCTIONAL REQUIREMENTS

Each requirement is annotated with `P` (Priority) and a proposed implementation phase.

| #      | Feature                                       | Description                                                                                                             | P     | Phase |
| ------ | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ----- | ----- |
| **1**  | **Markdown Parsing**                          | Full CommonMark subset (headings, bold, italics, lists, tables, code blocks, horizontal rules).                         | ★★★★★ | 1     |
| **2**  | **LaTeX-style Math Syntax**                   | Inline `$x^2$` and block `$$E=mc^2$$` support. Minimal parser → render as text (Phase 1), as proper glyph layout later. | ★★★★☆ | 2     |
| **3**  | **Mermaid-like Diagrams**                     | Recognize code blocks tagged `mermaid`, and render as ASCII box diagrams in Phase 1, or SVG/PDF vector graphics later.  | ★★★☆☆ | 3     |
| **4**  | **Image Embedding**                           | Support `![alt](path "caption")`. Inline raster in PDF, link in slides.                                                 | ★★★★★ | 2     |
| **5**  | **Code Blocks**                               | Fenced blocks `lang`. Syntax highlighting optional (Phase 3).                                                           | ★★★★★ | 1     |
| **6**  | **Markdown Linting / Validation**             | Basic static checks: heading hierarchy, trailing spaces, line length, missing alt text, etc.                            | ★★★☆☆ | 2     |
| **7**  | **Typographic Rules (Tuffty Style)**          | Compact layouts with minimal whitespace; no widows/orphans; avoid single words on new lines.                            | ★★★★☆ | 3     |
| **8**  | **Opinionated Typesetting (LaTeX Influence)** | Consistent margins, spacing, figure placement, and font choice. Layout policies rather than manual control.             | ★★★★★ | 3     |
| **9**  | **Page Layout System**                        | "Modes" like `document`, `slides`, `poster`. Each with default template and layout grid.                                | ★★★★★ | 1     |
| **10** | **Output Targets**                            | Text, HTML, and minimalist PDF. Later: native PDF and slides with animation layers.                                     | ★★★★★ | 1     |
| **11** | **Configuration System**                      | Lightweight YAML/TOML for global settings: fonts, colors, modes, metadata.                                              | ★★★★★ | 1     |
| **12** | **Build Engine & CLI**                        | `compose build file.md --config config.yml`. Reproducible outputs.                                                      | ★★★★★ | 1     |
| **13** | **Extensible Plugin API**                     | Allow custom renderers/parsers.                                                                                         | ★★★☆☆ | 3     |

---

# 🏗️ UNIVERSAL LAYOUT ENGINE ROADMAP

## 🎯 Vision: Professional Typesetting for All Content Types

The box-and-glue layout system we're building isn't just for mathematics - it's the **universal foundation** for all advanced layout in Compose. This includes mathematical expressions, diagrams, slides, tables, and any content requiring precise positioning and professional typography.

## 🧩 **Unified Layout Architecture**

### **Core Philosophy: Everything is a Box**
Following TeX's revolutionary insight, we treat all document elements as **boxes with dimensions and spacing rules**:

- **Text boxes**: Characters, words, paragraphs
- **Math boxes**: Symbols, operators, expressions  
- **Diagram boxes**: Shapes, connectors, labels
- **Media boxes**: Images, videos, interactive elements
- **Layout boxes**: Columns, grids, slide frames

### **Universal Box Model**
```python
class UniversalBox:
    content: Union[str, List[Box], DiagramElement, MediaElement]
    box_type: BoxType  # TEXT, MATH, DIAGRAM, MEDIA, LAYOUT
    dimensions: Dimensions
    spacing: GlueSpace
    style: RenderingStyle
```

---

## 🚀 **Phase 4: Universal Layout Foundation (6-12 months)**

### **Expanded Core Architecture**
- **Universal Box Model**: Extend math boxes to handle all content types
- **Multi-Modal Parser**: Parse math, diagrams, and layout structures
- **Rendering Pipeline**: Unified output to HTML, PDF, SVG
- **Style System**: Typography, colors, spacing for all content types

### **Key Components**
| Component | Description | Scope | Priority |
|-----------|-------------|-------|----------|
| `UniversalBox` | Base class for ALL document elements | Text, Math, Diagrams, Media | ★★★★★ |
| `LayoutEngine` | Unified layout system with specialized handlers | All content types | ★★★★★ |
| `DiagramRenderer` | Mermaid, flowcharts, technical diagrams | Diagrams | ★★★★☆ |
| `SlideLayoutEngine` | Presentation-specific layout rules | Slides | ★★★★☆ |
| `StyleSystem` | Unified styling across all content types | Visual consistency | ★★★★★ |

### **Content Type Support**

#### **📊 Diagrams & Visualizations**
- **Mermaid diagrams**: Flowcharts, sequence diagrams, Gantt charts
- **Technical diagrams**: Circuit diagrams, network topologies
- **Data visualizations**: Charts, graphs, plots
- **ASCII art**: Box drawings, simple illustrations

#### **🎯 Slide Presentations**  
- **Layout grids**: Title slides, content slides, comparison layouts
- **Animation timing**: Reveal sequences, transitions
- **Interactive elements**: Clickable areas, navigation
- **Speaker notes**: Hidden content for presentation mode

#### **📐 Mathematical Content**
- **Expressions**: Inline and display math
- **Equations**: Numbered, aligned, multi-line
- **Proofs**: Structured mathematical arguments
- **Chemical formulas**: Molecular structures, reactions

#### **📄 Document Structures**
- **Multi-column layouts**: Academic papers, newsletters
- **Figure placement**: Floating elements with captions
- **Cross-references**: Automatic numbering and linking
- **Bibliography**: Citation formatting and management

---

## 🛠️ **Implementation Strategy**

### **Phase 4A: Core Layout Engine (Months 1-4)**
1. **Generalize box model** from math-specific to universal
2. **Implement basic diagram rendering** (simple Mermaid subset)
3. **Create slide layout templates** (title, content, comparison)
4. **Unified styling system** for consistent appearance

### **Phase 4B: Content Integration (Months 5-8)**
1. **Advanced diagram support** (sequence diagrams, Gantt charts)
2. **Interactive slide features** (animations, navigation)
3. **Multi-column document layouts** 
4. **Figure and table positioning**

### **Phase 4C: Polish & Performance (Months 9-12)**
1. **Performance optimization** for complex layouts
2. **Accessibility features** across all content types
3. **Export quality** matching professional tools
4. **Developer API** for custom content types

---

## 🎨 **Unified Rendering Pipeline**

### **Content Type Handlers**
```python
class ContentRenderer:
    def render_math(self, box: MathBox) -> RenderOutput
    def render_diagram(self, box: DiagramBox) -> RenderOutput  
    def render_slide(self, box: SlideBox) -> RenderOutput
    def render_table(self, box: TableBox) -> RenderOutput
```

### **Output Targets**
- **HTML**: Interactive diagrams, responsive slides
- **PDF**: Print-quality documents and presentations
- **SVG**: Scalable diagrams and illustrations
- **PNG/WebP**: Raster exports for sharing

---

## 📊 **Diagram System Architecture**

### **Mermaid Integration**
```python
class MermaidRenderer:
    def parse_flowchart(self, code: str) -> DiagramBox
    def parse_sequence(self, code: str) -> DiagramBox
    def parse_gantt(self, code: str) -> DiagramBox
    def render_to_svg(self, diagram: DiagramBox) -> str
```

### **Diagram Types Supported**
- ✅ **Flowcharts**: Decision trees, process flows
- ✅ **Sequence diagrams**: API interactions, protocols  
- ✅ **Gantt charts**: Project timelines, schedules
- 🔄 **Network diagrams**: System architectures
- 🔄 **Entity-relationship**: Database schemas
- 🔄 **Mind maps**: Concept relationships

---

## 🎭 **Slide System Architecture**

### **Slide Layout Engine**
```python
class SlideLayoutEngine:
    def create_title_slide(self, title: str, subtitle: str) -> SlideBox
    def create_content_slide(self, title: str, content: List[Box]) -> SlideBox
    def create_comparison_slide(self, left: Box, right: Box) -> SlideBox
    def add_animation(self, slide: SlideBox, timing: AnimationTiming) -> SlideBox
```

### **Presentation Features**
- **Layout templates**: Professional slide designs
- **Animation system**: Reveal sequences, transitions
- **Speaker notes**: Hidden presenter information
- **Navigation**: Slide numbering, progress indicators
- **Export formats**: PDF slides, HTML presentations

---

## 🎯 **Success Metrics**

### **Phase 4A Success Criteria**
- [ ] Render basic Mermaid flowcharts correctly
- [ ] Create professional slide layouts
- [ ] Unified styling across math, text, and diagrams
- [ ] Performance: <200ms for typical mixed content

### **Phase 4B Success Criteria**  
- [ ] Complex diagram support (sequence, Gantt)
- [ ] Interactive slide presentations
- [ ] Multi-column document layouts
- [ ] Figure positioning matching LaTeX quality

### **Phase 4C Success Criteria**
- [ ] Export quality matching professional tools
- [ ] Real-time preview for complex documents
- [ ] Accessibility compliance (WCAG 2.1)
- [ ] Plugin API for custom content types

---

## 🔬 **Research Priorities**

### **Layout Algorithms**
1. **Constraint-based layout**: Automatic element positioning
2. **Responsive design**: Adaptive layouts for different outputs
3. **Performance optimization**: Incremental rendering, caching
4. **Accessibility**: Screen reader support, keyboard navigation

### **Content Integration**
1. **Diagram parsing**: Advanced Mermaid features, custom syntaxes
2. **Animation systems**: Smooth transitions, timing controls
3. **Interactive elements**: Clickable diagrams, form inputs
4. **Data binding**: Dynamic content from external sources

---

*This expanded vision transforms Compose from a Markdown processor into a **universal document creation platform** capable of producing professional-quality content across all media types while maintaining the simplicity that makes Markdown accessible.*

### 🚀 **Phase 5: Advanced Math Layout (12-18 months)**

#### **Knuth-Plass Integration**
- **Line Breaking**: Adapt Knuth-Plass algorithm for mathematical expressions
- **Penalty System**: Implement break penalties for math expressions
- **Optimal Spacing**: Dynamic spacing optimization based on content

#### **Advanced Features**
| Feature | Description | Complexity |
|---------|-------------|------------|
| **Matrix Layout** | `\begin{matrix}...\end{matrix}` with alignment | High |
| **Large Operators** | Integrals, sums with proper limits positioning | High |
| **Radical Layout** | Square roots with proper vinculum drawing | Medium |
| **Accent Handling** | Math accents with proper positioning | Medium |
| **Delimiter Sizing** | Auto-sizing parentheses, brackets, braces | High |

#### **Font System Enhancement**
- OpenType Math font support (STIX, Latin Modern Math)
- Glyph variant selection for different sizes
- Math italic correction and kerning
- Extensible character construction

### 🎨 **Phase 6: Professional Typesetting (18-24 months)**

#### **Advanced Typography**
- **Micro-typography**: Character protrusion, font expansion
- **Math Style Contexts**: Display vs inline vs script vs scriptscript
- **Baseline Alignment**: Proper alignment across mixed content
- **Color and Styling**: Math expression styling and highlighting

#### **Macro System**
| Component | Description | Scope |
|-----------|-------------|-------|
| **Macro Parser** | Basic `\newcommand` support | Limited TeX compatibility |
| **Expansion Engine** | Recursive macro expansion with proper scoping | Core functionality |
| **Package System** | Support for essential LaTeX packages (amsmath, amssymb) | Ecosystem integration |

#### **Output Quality**
- PDF output with proper font embedding
- SVG output for web with font fallbacks  
- High-DPI rendering support
- Accessibility features (MathML generation)

### 🧪 **Phase 7: Compatibility & Optimization (24+ months)**

#### **TeX Compatibility**
- **Trip Test**: Pass Knuth's canonical TeX compatibility test
- **LaTeX Subset**: Support core LaTeX math environments
- **Package Ecosystem**: Integration with popular math packages
- **Error Handling**: Graceful degradation for unsupported features

#### **Performance Optimization**
- Incremental layout for large documents
- Caching of complex expression layouts
- Memory-efficient font handling
- Parallel processing for independent expressions

---

## 🛣️ **Implementation Strategy**

### **Incremental Development Approach**

#### **Year 1: Foundations**
1. **Q1-Q2**: Extend current math renderer with box model
2. **Q3**: Implement basic fraction and script layouts  
3. **Q4**: Add font metrics system and operator spacing

#### **Year 2: Core Features**
1. **Q1-Q2**: Advanced layout algorithms (matrices, radicals)
2. **Q3**: Line breaking integration for math expressions
3. **Q4**: OpenType math font support

#### **Year 3+: Professional Grade**
1. **Macro system development**
2. **LaTeX compatibility layer**
3. **Performance optimization**
4. **Ecosystem integration**

### **Risk Mitigation**

#### **Technical Risks**
- **Complexity**: Start with subset of TeX features, expand gradually
- **Performance**: Profile early, optimize incrementally
- **Compatibility**: Focus on modern LaTeX subset, not full TeX

#### **Resource Risks**  
- **Expertise**: Collaborate with typography/TeX experts
- **Time**: Allow for 3-5 year development timeline
- **Scope**: Maintain clear feature boundaries per phase

### **Success Metrics**

#### **Phase 4 Success Criteria**
- [ ] Render complex fractions correctly
- [ ] Proper superscript/subscript positioning
- [ ] Basic integral notation support
- [ ] Performance: <100ms for typical math expressions

#### **Phase 5 Success Criteria**
- [ ] Matrix layout matching LaTeX output
- [ ] Auto-sizing delimiters
- [ ] OpenType math font rendering
- [ ] Performance: <500ms for complex expressions

#### **Phase 6+ Success Criteria**
- [ ] Pass 90% of common LaTeX math test cases
- [ ] Support amsmath package subset
- [ ] Professional-quality PDF output
- [ ] Performance: Real-time preview for documents <100 pages

---

## 🔬 **Research & Development Priorities**

### **Immediate Research Needs**
1. **Font Metrics Analysis**: Study OpenType Math table specifications
2. **Layout Algorithm Study**: Deep dive into TeX's math layout rules
3. **Performance Benchmarking**: Profile existing math rendering solutions
4. **Compatibility Analysis**: Survey most-used LaTeX math features

### **Prototype Development**
1. **Math Box Prototype**: Simple box-and-glue implementation
2. **Font Metrics Reader**: Basic OpenType Math table parser  
3. **Layout Engine Core**: Recursive expression layout
4. **Rendering Pipeline**: Integration with existing HTML/PDF output

### **Community Engagement**
- **TeX Community**: Engage with TeX developers and typography experts
- **Academic Users**: Gather requirements from research document authors
- **Tool Integration**: Plan integration with existing LaTeX workflows

---

## 📚 **Technical References**

### **Essential Reading**
- **"The TeXbook"** by Donald Knuth - Foundational TeX algorithms
- **"TeX by Topic"** by Victor Eijkhout - Implementation details
- **"Digital Typography"** by Donald Knuth - Mathematical typesetting theory
- **OpenType Math Specification** - Modern math font standards

### **Key Algorithms**
- **Knuth-Plass Line Breaking** - Optimal line breaking with penalties
- **TeX Math Layout Rules** - Hundreds of spacing and positioning rules
- **Font Metric Interpretation** - TFM and OpenType Math table processing
- **Box-and-Glue Model** - Fundamental layout abstraction

### **Reference Implementations**
- **TeX Engine Source** - Original Knuth implementation
- **LuaTeX** - Modern TeX engine with Lua scripting
- **KaTeX** - Fast math rendering for web
- **MathJax** - Comprehensive math display system

---

*This roadmap represents a significant evolution of Compose from a Markdown processor to a full mathematical typesetting system. The phased approach ensures steady progress while maintaining the project's core values of simplicity and reliability.*

---

# 👤 USER STORIES

## A. Technical Author

> *As a technical author, I want to write my documentation in Markdown, but get publication-quality PDFs with LaTeX-like typesetting without learning LaTeX.*

**Acceptance:**

* Headings, bold/italics, code blocks render properly.
* Math inline looks consistent with body text.
* Paragraphs wrap without typographic artifacts.

---

## B. Researcher

> *As a researcher, I want to include equations, images, and tables seamlessly, with reliable references.*

**Acceptance:**

* `$E=mc^2$` and `$$...$$` render as math blocks.
* `![caption](figure.png)` includes an image with caption and consistent spacing.
* Tables align correctly even with mixed text/math.

---

## C. Developer / Presenter

> *As a developer, I want to produce slide decks and documentation from the same Markdown sources.*

**Acceptance:**

* `mode: slides` config switches layout to wide aspect ratio.
* Headings become slide titles.
* Lists and code blocks auto-scale to fit.

---

## D. Editor / QA

> *As an editor, I want to lint documents before build to catch formatting errors.*

**Acceptance:**

* CLI option `compose lint file.md` reports violations.
* Configurable rules (e.g., line length, heading order).
* Returns non-zero exit code on error.

---

# 🪜 DEVELOPMENT PHASES

## **Phase 1 — Core Parser & Rendering (MVP)**

Goal: Minimal viable document pipeline.

**Features:**

* Markdown subset (headings, paragraphs, lists, code blocks)
* Config file system
* PDF and text output
* CLI (`compose build file.md --config config.yml`)
* Modular internal structure

**Deliverables:**

* Working `compose/` package
* Output PDF/text
* Basic test suite

**Duration:** ~2 weeks (solo)

---

## **Phase 2 — Math, Images, Linting**

Goal: Richer technical writing features.

**Features:**

* Inline `$math$`, block `$$math$$` (text-mode rendering first)
* Image embedding
* Linter (`compose lint`) with a few basic rules
* Configurable typography (font, size, spacing)

**Deliverables:**

* Math renderer placeholder (text, later replaced)
* Embedded raster image support
* Linting engine integrated into CLI

**Duration:** ~3–4 weeks

---

## **Phase 3 — Opinionated Layout & “Tuffty” Densification**

Goal: Layout polish and content-density aesthetics.

**Features:**

* Widow/orphan control
* Paragraph shaping (no single word lines)
* Smart spacing between elements
* Compact multi-column modes
* Minimal hyphenation rules
* LaTeX-like typography defaults (proportional spacing, kerning simulation)

**Deliverables:**

* Improved PDF layout
* Layout debug mode (`compose layout debug`)
* Style presets: `dense`, `academic`, `poster`

**Duration:** ~4–6 weeks

---

## **Phase 4 — Diagrams, Extended Output, Performance**

Goal: Expand capability & optimize.

**Features:**

* Mermaid-like ASCII and (optionally) vector diagrams
* Slide rendering (`mode: slides`)
* Rust/C optimization for parsing and layout computation
* Plugin architecture

**Deliverables:**

* Mermaid block renderer
* Faster parser (optional compiled module)
* Stable 1.0 spec for config and layout API

**Duration:** ~6–8 weeks

---

# ⚙️ NON-FUNCTIONAL REQUIREMENTS

| Area                   | Requirement                                                             |
| ---------------------- | ----------------------------------------------------------------------- |
| **Performance**        | Process 50 pages of Markdown < 3 s on typical laptop.                   |
| **Portability**        | Works on Python 3.12+ (Windows/macOS/Linux) with zero dependencies.     |
| **Reproducibility**    | Deterministic builds — same Markdown produces same PDF.                 |
| **Extensibility**      | Plugins can extend parsers/renderers cleanly.                           |
| **Error Handling**     | Graceful fallback for unimplemented features (e.g., warn but continue). |
| **Offline Capability** | Fully functional without Internet.                                      |
| **Testing**            | Unit tests for parsing, rendering, and linting subsystems.              |
| **Documentation**      | Markdown-based developer and user docs.                                 |

---

# 🧰 INITIAL TECHNOLOGY CHOICES

| Component           | Implementation                                |
| ------------------- | --------------------------------------------- |
| Core parser         | Hand-rolled line/token parser (Python)        |
| Config              | Lightweight YAML-like parser (Python)         |
| PDF backend         | Raw text-based PDF generator                  |
| Linting             | AST traversal with rule registry              |
| Math syntax         | Regex tokenizer with fallback to plain text   |
| Diagram rendering   | ASCII renderer (later SVG/PDF path generator) |
| Fonts               | Built-in Helvetica / fallback monospace       |
| Optional extensions | Rust for parsing and layout optimization      |

---

# 🧭 EXTENSION PATHS

1. **Advanced Math Rendering**
   Replace placeholder with MathML → PDF text primitives or link to embedded LaTeX via external executable (optional).

2. **Vector Diagrams (Mermaid)**
   Use internal graph layout (DOT-style) or delegate to lightweight Rust module that outputs PDF primitives.

3. **Typography Engine**
   Integrate line-breaking algorithm (Knuth–Plass style) for professional output.

4. **Preview Server**
   Optional local HTML preview (`compose serve`).

---

# 🧠 SPRINT ZERO CHECKLIST

* [x] Initialize repo (`compose/`)
* [x] Add `cli.py`, `engine.py`, `parser/`, `render/`, `model/`
* [x] Implement core Markdown → AST → PDF pipeline
* [x] Define config format
* [x] Create minimal docs (`README.md`, `CONTRIBUTING.md`)
* [x] Establish test harness (`pytest` optional if allowed, otherwise custom test runner)
* [x] Build sample documents

---

# 🧭 NEXT ACTIONS (Immediate)

1. ✅ Finalize architecture (as outlined in previous message)
2. ✅ Scaffold repository & implement **Phase 1** core
3. ✅ Add tests and one sample document (`example.md`)
4. ✅ Write initial user documentation and developer setup guide

---

