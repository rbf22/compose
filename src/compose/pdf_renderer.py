"""Minimal PDF renderer over a mistletoe Document using fpdf.

This is an early prototype that focuses on headings, paragraphs, and
simple bullet lists. Inline math is recognized via the shared MathSpan
 token and rendered as plain text derived from pytex/KaTeX (with a very
naive tag strip). The layout model can be refined over time.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

from mistletoe import block_token, span_token
from mistletoe.base_renderer import BaseRenderer

from .config import Rules
from .html_renderer import MathSpan
from .math_pdf_layout import (
    BoxMetrics,
    SymbolBox,
    draw_math_box,
    measure_math_box,
    parse_latex_to_box,
)


def _import_fpdf():
    """Import the FPDF class, supporting the local sub-repo layout.

    We first try a normal import (for environments where `fpdf` is
    installed). If that fails, we fall back to adding the local fpdf
    project root (../fpdf) to sys.path and importing from there.
    """

    try:
        from fpdf import FPDF as _FPDF  # type: ignore[import]
        return _FPDF
    except Exception:  # pragma: no cover - best-effort fallback
        root = Path(__file__).resolve().parent.parent
        fpdf_root = root / "fpdf"
        if fpdf_root.is_dir() and str(fpdf_root) not in sys.path:
            sys.path.append(str(fpdf_root))
        from fpdf import FPDF as _FPDF  # type: ignore[import]
        return _FPDF


def _import_katex_render():
    """Import pytex's KaTeX renderer for math text, with local fallback.

    For PDF we only use this to derive a plain-text representation of the
    math expression, falling back to the original LaTeX if needed.
    """

    try:
        from pytex.katex import render_to_string as _render_to_string  # type: ignore[import]
        return _render_to_string
    except Exception:  # pragma: no cover - best-effort fallback
        root = Path(__file__).resolve().parent.parent
        pytex_root = root / "pytex"
        if pytex_root.is_dir() and str(pytex_root) not in sys.path:
            sys.path.append(str(pytex_root))
        from pytex.katex import render_to_string as _render_to_string  # type: ignore[import]
        return _render_to_string


FPDF = _import_fpdf()
katex_render = _import_katex_render()


class PdfRenderer(BaseRenderer):
    """Minimal PDF renderer using fpdf.

    This renderer walks a mistletoe Document AST and emits text into an
    FPDF document. It is intentionally small and can be extended as the
    PDF layout model matures.
    """

    def __init__(self, rules: Rules, *extras, **kwargs) -> None:
        self.rules = rules

        # Basic FPDF setup.
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
        self.pdf.add_page()

        self._base_font_family = "Helvetica"
        self._base_font_size = 12
        self.pdf.set_font(self._base_font_family, size=self._base_font_size)

        # Register MathSpan so inline math is parsed as a dedicated token.
        super().__init__(MathSpan, *extras, **kwargs)

    # ------------------------------------------------------------------
    # Span-level rendering
    # ------------------------------------------------------------------

    def render_raw_text(self, token: span_token.RawText) -> str:  # type: ignore[override]
        return token.content

    def render_math_span(self, token: MathSpan) -> str:
        """Return a plain-text representation of inline math.

        For now this is derived from pytex's HTML output with a naive tag
        strip. If anything goes wrong, we fall back to the original
        LaTeX source wrapped in `$...$`.
        """

        try:
            html_snippet = katex_render(token.latex, display_mode=False)
        except Exception:
            return f"${token.latex}$"

        # Naive text extraction: strip tags, collapse whitespace, and
        # unescape HTML entities. This is only a placeholder until we
        # design a proper math→PDF layout path.
        text = re.sub(r"<[^>]+>", " ", html_snippet)
        text = re.sub(r"\s+", " ", text)
        text = html.unescape(text).strip()
        return text or token.latex

    # ------------------------------------------------------------------
    # Block-level rendering
    # ------------------------------------------------------------------

    def _write_paragraph(self, text: str) -> None:
        if not text:
            return
        # Full-width cell (0) with a modest line height.
        self.pdf.multi_cell(0, 5, txt=text)
        self.pdf.ln(3)

    def render_paragraph(self, token: block_token.Paragraph) -> str:  # type: ignore[override]
        children = getattr(token, "children", None)

        if self.rules.pdf_vector_math_enabled and children:
            # First, special case: paragraph that is a single MathSpan
            # becomes display-style math.
            if len(children) == 1 and isinstance(children[0], MathSpan):
                box = parse_latex_to_box(children[0].latex)
                if box is not None:
                    x = self.pdf.l_margin
                    y = self.pdf.get_y() + self._base_font_size
                    draw_math_box(
                        self.pdf,
                        box,
                        x,
                        y,
                        self._base_font_family,
                        self._base_font_size,
                    )
                    self.pdf.ln(self._base_font_size * 1.8)
                    return ""

            # Inline flow: convert children into a sequence of text
            # segments and MathBox instances, then draw them at a shared
            # baseline with basic word-level line breaking.
            items: list[tuple[str, object]] = []  # ("text"|"box", value)

            for child in children:
                if isinstance(child, MathSpan):
                    box = parse_latex_to_box(child.latex)
                    if box is not None:
                        items.append(("box", box))
                        continue

                    # Fallback: render math as plain text.
                    seg = self.render_math_span(child)
                    if seg:
                        items.append(("text", seg))
                else:
                    seg = self.render(child)
                    if seg:
                        items.append(("text", seg))

            if items:
                max_x = self.pdf.w - self.pdf.r_margin
                x = self.pdf.l_margin
                baseline_y = self.pdf.get_y() + self._base_font_size
                line_height_above = 0.0
                line_height_below = 0.0

                def _new_line() -> None:
                    nonlocal x, baseline_y, line_height_above, line_height_below
                    total = line_height_above + line_height_below
                    if total <= 0:
                        total = self._base_font_size * 1.2
                    self.pdf.ln(total)
                    x = self.pdf.l_margin
                    baseline_y = self.pdf.get_y() + self._base_font_size
                    line_height_above = 0.0
                    line_height_below = 0.0

                for kind, value in items:
                    if kind == "box":
                        box_metrics: BoxMetrics = measure_math_box(
                            self.pdf,
                            value,
                            self._base_font_family,
                            self._base_font_size,
                        )
                        # Line break if this box would overflow.
                        if x > self.pdf.l_margin and x + box_metrics.width > max_x:
                            _new_line()
                        draw_math_box(
                            self.pdf,
                            value,
                            x,
                            baseline_y,
                            self._base_font_family,
                            self._base_font_size,
                        )
                        x += box_metrics.width + 1.0
                        line_height_above = max(line_height_above, box_metrics.height)
                        line_height_below = max(line_height_below, box_metrics.depth)
                    else:
                        seg = value
                        # Split text into word+space chunks so we can wrap.
                        import re

                        for part in re.findall(r"\S+\s*", seg):
                            if not part:
                                continue
                            word_box = SymbolBox(text=part)
                            word_metrics = measure_math_box(
                                self.pdf,
                                word_box,
                                self._base_font_family,
                                self._base_font_size,
                            )
                            if x > self.pdf.l_margin and x + word_metrics.width > max_x:
                                _new_line()
                            self.pdf.set_font(self._base_font_family, size=self._base_font_size)
                            self.pdf.text(x, baseline_y, part)
                            x += word_metrics.width
                            line_height_above = max(line_height_above, word_metrics.height)
                            line_height_below = max(line_height_below, word_metrics.depth)

                _new_line()
                return ""

        text = self.render_inner(token)
        self._write_paragraph(text)
        return ""

    def render_heading(self, token: block_token.Heading) -> str:  # type: ignore[override]
        level = getattr(token, "level", 1)
        text = self.render_inner(token)
        if not text:
            return ""

        size_map = {1: 18, 2: 16, 3: 14}
        size = size_map.get(level, self._base_font_size)

        self.pdf.set_font(self._base_font_family, "B", size=size)
        self.pdf.multi_cell(0, 6, txt=text)
        self.pdf.ln(4)
        self.pdf.set_font(self._base_font_family, size=self._base_font_size)

        return ""

    def render_list(self, token: block_token.List) -> str:  # type: ignore[override]
        for child in token.children:
            self.render(child)
        self.pdf.ln(2)
        return ""

    def render_list_item(self, token: block_token.ListItem) -> str:  # type: ignore[override]
        text = self.render_inner(token)
        if not text:
            return ""
        # Simple bullet list.
        self.pdf.cell(5, 5, txt="- ")
        self.pdf.multi_cell(0, 5, txt=text)
        return ""

    def render_block_code(self, token: block_token.BlockCode) -> str:  # type: ignore[override]
        text = self.render_inner(token)
        if not text:
            return ""

        # Use a monospace font for code blocks.
        self.pdf.set_font("Courier", size=self._base_font_size)
        self.pdf.multi_cell(0, 5, txt=text)
        self.pdf.ln(3)
        self.pdf.set_font(self._base_font_family, size=self._base_font_size)
        return ""

    def render_quote(self, token: block_token.Quote) -> str:  # type: ignore[override]
        text = self.render_inner(token)
        if not text:
            return ""

        # Indent and italicize block quotes slightly.
        original_margin = self.pdf.l_margin
        self.pdf.set_left_margin(original_margin + 5)
        self.pdf.set_x(original_margin + 5)
        self.pdf.set_font(self._base_font_family, "I", size=self._base_font_size)
        self.pdf.multi_cell(0, 5, txt=text)
        self.pdf.ln(2)
        self.pdf.set_left_margin(original_margin)
        self.pdf.set_font(self._base_font_family, size=self._base_font_size)
        return ""

    def render_table(self, token: block_token.Table) -> str:  # type: ignore[override]
        for child in token.children:
            self.render(child)
        self.pdf.ln(3)
        return ""

    def render_table_row(self, token: block_token.TableRow) -> str:  # type: ignore[override]
        cells = [self.render(cell) for cell in token.children]
        line = " | ".join(cells)
        self._write_paragraph(line)
        return ""

    def render_table_cell(self, token: block_token.TableCell) -> str:  # type: ignore[override]
        return self.render_inner(token)

    def render_document(self, token: block_token.Document):
        """Walk the AST, then return the generated PDF bytes.

        Most child renderers return an empty string and write directly to
        `self.pdf`.
        """

        for child in token.children:
            self.render(child)

        result = self.pdf.output(dest="S")
        if isinstance(result, str):
            return result.encode("latin1")
        return result
