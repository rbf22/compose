# Compose Typesetting Roadmap

This document describes how the two repositories in this root directory — `mistletoe` and `pytex` — will be used to build a flexible typesetting application for Markdown → HTML and **direct AST → PDF**.

The plan is structured into phases with checklists so we can track what is implemented vs. what is still missing.

---

## 0. Current Capabilities (Upstream Repos)

### 0.1 `mistletoe` – Markdown Front-End

- [x] CommonMark-compliant Markdown parser
  - `mistletoe.Document` parses Markdown into a block/span **AST**.
  - Supports paragraphs, headings, lists, tables, code blocks, HTML blocks, footnotes, etc.
- [x] Pluggable renderer architecture
  - Core renderers: HTML, LaTeX, AST, Markdown.
  - Contrib renderers: MathJax HTML, Pygments code highlighting, Jira/XWiki/TOC, etc.
- [x] Extensible token system
  - Ability to add custom block/span tokens.
  - Ability to write new renderers by subclassing `BaseRenderer`.
- [x] Comprehensive test suite
  - 330+ tests passing under Poetry in our local copy.

### 0.2 `pytex` – LaTeX Math Engine

- [x] KaTeX-compatible math rendering in pure Python
  - `pytex.katex.render_to_string(r"...")` → HTML snippet (KaTeX-like markup).
  - Supports inline and display math.
- [x] Rich LaTeX math feature set
  - Fractions, roots, sums/products/integrals, accents, matrices, text commands, colors, macros, etc.
- [x] Multiple output formats
  - HTML and MathML (via the internal renderer abstraction).
- [x] Independent library with its own tests and documentation.

These are **building blocks**. The Compose project will sit on top of them and provide a higher-level document/typesetting pipeline.

---

## 1. Project Goal (High-Level)

We want a flexible application that:

1. **Parses Markdown** documents into a structured AST.
2. **Applies configurable typesetting rules** (spacing, hierarchy, semantics) to that AST.
3. **Renders to HTML** for on-screen viewing and web use.
4. **Later**: Renders **directly from AST to PDF** using a PDF library, with the same rules.
5. Uses `pytex` to render **LaTeX math** embedded in Markdown (both HTML and PDF paths).

Key architectural principle: **One AST, shared rules, multiple backends (HTML, PDF).**

---

## 2. Phase 1 – Rule-Aware HTML Typesetting

Goal: Markdown → `mistletoe.Document` → **RuleAwareHtmlRenderer** → HTML (with math via `pytex`).

### 2.1 Configuration & Rule Model

Define a central configuration that describes layout and styling rules, not hard-coded in renderers.

- [x] Create a `config` module (`compose_app/config.py`) that:
  - [x] Loads a TOML file describing rules.
    - [ ] Global document options (base font size, max line width, etc.).
    - [ ] Block spacing rules (spacing between headings, paragraphs, lists, etc.).
    - [ ] Mapping from token types → HTML tags + CSS classes (e.g. `Heading(level=1)` → `h1.chapter-title`).
    - [ ] Rules for tables, code blocks, and block quotes.
    - [x] Math and theming options (inline/display CSS classes, stylesheets, HTML document/body/article flags, macros for `pytex`).
  - [x] Exposes a typed `Rules` object used by all renderers.

### 2.2 Markdown + Math Parsing Wrapper

Build a wrapper around `mistletoe` that gives us a `Document` AST with explicit math tokens.

- [x] Create a `markdown_parser` module (`compose_app/markdown_parser.py`):
  - [x] Provide a function `parse_markdown(text: str) -> Document`.
  - [x] Enable/define custom math span tokens for `$...$` (via renderer extras for now).
  - [x] Ensure math tokens carry enough metadata (inline vs display, original source) for renderers.
  - [x] Ensure this wrapper is **pure** and has no HTML/PDF concerns.

### 2.3 Rule-Aware HTML Renderer

Implement a renderer that applies rules and calls `pytex` for math.

- [x] Create `html_renderer.py` (`compose_app/html_renderer.py`):
  - [x] Subclass `mistletoe.html_renderer.HtmlRenderer`.
  - [x] Accept a `Rules` object from the config module.
  - [ ] Implement/override methods for key tokens:
    - [x] `render_document` (supports full HTML document output and stylesheet links).
    - [ ] `render_heading`
    - [ ] `render_paragraph`
    - [ ] `render_list`, `render_list_item`
    - [ ] `render_table`, `render_table_row`, `render_table_cell`
    - [ ] `render_block_code`, `render_code_span`
    - [ ] `render_quote`, `render_thematic_break`
    - [x] `render_math_span`.
  - [x] For math rendering:
    - [x] Inline math: call `pytex.katex.render_to_string(latex, display_mode=False)`.
    - [ ] Display math: call `render_to_string(..., display_mode=True)`.
    - [x] Wrap KaTeX HTML into your chosen container (`<span class="math-inline">`, `<div class="math-display">`, etc.) according to `Rules`.
  - [ ] Add hooks for optional features:
    - [ ] Heading IDs and slug generation for linking.
    - [ ] Table-of-contents support (collect headings as you render).

### 2.4 CLI / Application Entry Point (HTML)

Expose a simple command-line interface to run the pipeline.

- [x] Create `cli.py` at a shared app level (`compose_app/cli.py`).
  - [x] Provide a `main()` entrypoint.
  - [x] Commands such as:
    - [x] `typeset-md INPUT.md -o OUTPUT.html --config CONFIG.toml`
  - [x] Pipeline:
    1. [x] Load config → `Rules`.
    2. [x] Read Markdown file.
    3. [x] `doc = parse_markdown(text)`.
    4. [x] Render with `RuleAwareHtmlRenderer`.
    5. [x] Write HTML output.
  - [ ] Optionally add a console script entry in one of the `pyproject.toml` files.

### 2.5 Basic Theming / CSS

- [x] Provide at least one default CSS file for the generated HTML that:
  - [x] Styles headings, paragraphs, lists, code, tables (via `tufte-css/tufte.css`).
  - [x] Styles math output from `pytex` (via KaTeX classes plus theme CSS).
  - [ ] Handles basic print-friendly rules (margins, fonts, etc.).
- [x] Decide how CSS is attached:
  - [x] Linked stylesheet(s) via the `stylesheets` field in `Rules`.
- [ ] Add additional themes and examples:
  - [x] Wire in Tufte CSS as an optional theme (by pointing `stylesheets` at `tufte-css/tufte.css`, enabling `html_document`, and wrapping content in `<article>`).
  - [ ] Provide example configs and Markdown documents demonstrating Tufte and non-Tufte themes.

---

## 3. Phase 2 – Rules & Structure Refinement

After basic HTML typesetting works, refine the semantics and rules with an eye towards reuse in the PDF pipeline.

### 3.1 Structural Semantics

- [ ] Add optional structural wrappers in the HTML renderer:
  - [ ] Group blocks into `<section>`, `<article>`, etc., based on heading levels.
  - [ ] Add data attributes or IDs for cross-references.
- [ ] Define label / cross-reference scheme (to reuse in PDF):
  - [ ] Syntax for user labels in Markdown (e.g. `{#label}` after headings).
  - [ ] Data structure that maps labels → AST nodes.

### 3.2 Spacing & Layout Rules (HTML)

- [ ] Encode spacing rules in the `Rules` model:
  - [ ] Spacing before/after headings of each level.
  - [ ] Spacing between paragraphs and lists.
  - [ ] Rules for code blocks and figures/tables.
- [ ] Ensure these rules are **backend-agnostic** (no HTML-specific assumptions), so the same values can inform PDF layout later.

### 3.3 Testing & Examples

- [ ] Add integration tests for the HTML pipeline:
  - [ ] Simple document with headings, paragraphs, lists, tables, code, and math.
  - [ ] Edge cases (nested lists, long code blocks, tables with wide cells).
- [ ] Add example Markdown and their rendered HTML outputs under a `examples/` directory.

---

## 4. Phase 3 – Direct AST → PDF (Long-Term Plan)

**Explicit Long-Term Direction:**

> We will implement **direct AST → PDF via a PDF library**, *not* HTML→PDF.

### 4.1 PDF Backend Selection

- [ ] Choose a PDF library compatible with the project’s constraints (ideally pure Python):
  - Candidates: `reportlab`, or a minimal custom PDF writer if you want no external deps.
- [ ] Decide how strict the “no external dependencies” policy should be for the PDF feature:
  - [ ] Core app stays pure-stdlib.
  - [ ] PDF backend could be an optional extra group in `pyproject.toml` (e.g. `[tool.poetry.group.pdf]`).

### 4.2 Layout Model for PDF

- [ ] Define a layout model that reuses the AST and `Rules`:
  - [ ] Page size and margins.
  - [ ] Fonts and line heights.
  - [ ] Block spacing (reuse from HTML rules where possible).
  - [ ] Widows/orphans/page-break rules (even if simplified initially).
- [ ] Decide on a layout pipeline:
  - [ ] **Measure → Layout → Render** pattern, or a simpler single-pass layout for v1.

### 4.3 `PdfRenderer` Over `mistletoe.Document`

- [ ] Create `pdf_renderer.py` (e.g. `compose_app/pdf_renderer.py`):
  - [ ] Accepts `Document` AST and `Rules`.
  - [ ] Walks the AST and:
    - [ ] Lays out headings, paragraphs, lists, tables, code, and math.
    - [ ] Maintains current page, cursor position, and handles page breaks.
  - [ ] For math:
    - [ ] Either interpret `pytex` output (e.g. a box model) into PDF drawing commands, or
    - [ ] Use a separate math layout layer that shares logic with HTML.

### 4.4 CLI Support for PDF

- [ ] Extend the CLI to support PDF output:
  - [ ] `typeset-md INPUT.md -o OUTPUT.pdf --config CONFIG.toml --format pdf`
  - [ ] Share the same `parse_markdown` and `Rules`.

### 4.5 PDF-Specific Tests

- [ ] Add tests that:
  - [ ] Generate PDFs in a temporary directory.
  - [ ] Inspect metadata (page count, maybe text extraction) to verify structure.
  - [ ] Compare layout for simple cases (e.g. known page-break points).

---

## 5. Cross-Cutting Concerns

- [ ] Error handling and diagnostics
  - [ ] Friendly error messages when math fails to parse.
  - [ ] Warnings for unsupported Markdown constructs.
- [ ] Performance
  - [ ] Benchmark parsing and rendering on large documents.
  - [ ] Optimize only where needed.
- [ ] Documentation
  - [ ] High-level architecture overview.
  - [ ] Usage docs for the CLI.
  - [ ] Config schema docs (what rules exist and how to tweak them).

---

## 6. Status Summary (High-Level)

- **Upstream libs**
  - [x] `mistletoe` Markdown engine is working and fully tested locally.
  - [x] `pytex` KaTeX-like math engine is available and tested.
- **Compose glue app**
  - [x] Config + rules model (TOML-based, with theming knobs and math options).
  - [x] Markdown + math wrapper around `mistletoe` (including structural `MathSpan` tokens).
  - [x] Rule-aware HTML renderer using `pytex` (inline math + optional full HTML document output).
  - [x] CLI / entrypoint (`python -m compose_app.cli ...`).
  - [ ] PDF layout engine and renderer

This file should be kept up to date as pieces are implemented.
