"""HTML renderer that applies simple rules and integrates pytex for math.

This builds on mistletoe's HtmlRenderer but overrides raw text rendering
so that LaTeX math enclosed in ``$...$`` is rendered via pytex/KaTeX.
The goal is to keep this minimal and safe while providing a concrete
end-to-end pipeline.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List

from mistletoe import span_token
from mistletoe.html_renderer import HtmlRenderer

from .config import Rules


def _import_katex_render():
    """Import pytex's KaTeX renderer, supporting the local sub-repo layout.

    We first try a normal import (for environments where pytex-katex is
    installed). If that fails, we fall back to adding the local pytex
    project root (../pytex) to sys.path and importing from there.
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


katex_render = _import_katex_render()


class MathSpan(span_token.SpanToken):
    pattern = re.compile(r"(?<!\\)(?:\\\\)*\$(.+?)\$", re.DOTALL)
    parse_inner = False
    parse_group = 1

    def __init__(self, match):
        super().__init__(match)
        latex = match.group(self.parse_group)
        self.latex = latex
        self.children = (span_token.RawText(latex),)


class RuleAwareHtmlRenderer(HtmlRenderer):
    """HTML renderer with basic rule support and inline math.

    Currently, the only rule we use is the CSS class for inline math.
    More layout and spacing rules can be added over time and reused in a
    future PDF renderer.
    """

    def __init__(self, rules: Rules, *extras, **kwargs) -> None:
        self.rules = rules
        # Track heading/subtitle state for optional Tufte semantics.
        self._seen_h1 = False
        self._expect_subtitle = False
        # Track an open <section> started by a heading, if any.
        self._open_section_level: int | None = None
        super().__init__(MathSpan, *extras, **kwargs)

    def _slugify(self, text: str) -> str:
        s = text.lower()
        s = re.sub(r"[^a-z0-9]+", "-", s)
        return s.strip("-")

    def render_raw_text(self, token: span_token.RawText) -> str:  # type: ignore[override]
        return self.escape_html_text(token.content)

    def render_math_span(self, token: MathSpan) -> str:
        try:
            math_html = katex_render(token.latex, display_mode=False)
        except Exception:
            return self.escape_html_text(f"${token.latex}$")
        return f'<span class="{self.rules.math_inline_class}">{math_html}</span>'

    # ----- Block-level overrides -------------------------------------------------

    def render_heading(self, token) -> str:  # type: ignore[override]
        # Standard HtmlRenderer heading behavior.
        level = getattr(token, "level", 1)
        inner = self.render_inner(token)

        cls_attr = ""
        if self.rules.heading_base_class:
            cls_val = self.escape_html_text(self.rules.heading_base_class)
            cls_attr = f' class="{cls_val}"'

        id_attr = ""
        if getattr(self.rules, "auto_heading_ids", False):
            plain = re.sub(r"<[^>]+>", "", inner)
            slug = self._slugify(plain)
            if slug:
                prefix = getattr(self.rules, "heading_id_prefix", "") or ""
                id_val = self.escape_html_text(prefix + slug)
                id_attr = f' id="{id_val}"'

        rendered = f"<h{level}{cls_attr}{id_attr}>{inner}</h{level}>"

        if self.rules.subtitle_after_h1 and level == 1 and not self._seen_h1:
            # After the first H1, treat the next paragraph as a subtitle.
            self._seen_h1 = True
            self._expect_subtitle = True

        # Optionally wrap sections starting at a configured heading level.
        section_level = self.rules.section_from_level
        if section_level is not None and level == section_level:
            parts = []
            if self._open_section_level is not None:
                parts.append("</section>")
            parts.append("<section>")
            parts.append(rendered)
            self._open_section_level = level
            return "\n".join(parts)

        return rendered

    def render_paragraph(self, token) -> str:  # type: ignore[override]
        if self.rules.subtitle_after_h1 and self._expect_subtitle:
            # Only apply subtitle styling to the very next paragraph.
            self._expect_subtitle = False
            inner = self.render_inner(token)
            cls = self.escape_html_text(self.rules.subtitle_class)
            return f'<p class="{cls}">{inner}</p>'

        children = getattr(token, "children", None)
        if children and len(children) == 1 and isinstance(children[0], MathSpan):
            math_token = children[0]
            try:
                math_html = katex_render(math_token.latex, display_mode=True)
            except Exception:
                escaped = self.escape_html_text(f"${math_token.latex}$")
                return f"<p>{escaped}</p>"
            cls = self.escape_html_text(self.rules.math_display_class)
            return f'<div class="{cls}">{math_html}</div>'

        # Fallback to HtmlRenderer behavior, including list-related
        # paragraph suppression logic.
        html = super().render_paragraph(token)
        para_cls = getattr(self.rules, "paragraph_base_class", None)
        if para_cls and html.startswith("<p>"):
            cls_val = self.escape_html_text(para_cls)
            html = html.replace("<p>", f'<p class="{cls_val}">', 1)
        return html

    def render_document(self, token) -> str:  # type: ignore[override]
        # Base behavior: render children and collect footnotes.
        self.footnotes.update(getattr(token, "footnotes", {}))
        inner_parts: List[str] = [self.render(child) for child in token.children]
        inner = "\n".join(inner_parts)

        # Close any trailing <section> opened by headings.
        if self.rules.section_from_level is not None and self._open_section_level is not None:
            inner = f"{inner}\n</section>"
            self._open_section_level = None

        if not self.rules.html_document:
            return f"{inner}\n" if inner else ""

        # Build <head> with meta tags and any configured stylesheets.
        head_lines: List[str] = [
            "<meta charset=\"utf-8\">",
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
        ]
        for href in self.rules.stylesheets:
            escaped_href = self.escape_html_text(href)
            head_lines.append(f'<link rel="stylesheet" href="{escaped_href}">')
        head = "\n    ".join(head_lines)

        body_class_attr = ""
        if self.rules.body_class:
            body_class_attr = f' class="{self.escape_html_text(self.rules.body_class)}"'

        body_inner = inner
        if self.rules.article_wrapper:
            body_inner = f"<article>\n{inner}\n</article>"

        return (
            "<!DOCTYPE html>\n"
            "<html lang=\"en\">\n"
            "  <head>\n"
            f"    {head}\n"
            "  </head>\n"
            f"  <body{body_class_attr}>\n"
            f"{body_inner}\n"
            "  </body>\n"
            "</html>\n"
        )
