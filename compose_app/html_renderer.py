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
        super().__init__(MathSpan, *extras, **kwargs)

    def render_raw_text(self, token: span_token.RawText) -> str:  # type: ignore[override]
        return self.escape_html_text(token.content)

    def render_math_span(self, token: MathSpan) -> str:
        try:
            math_html = katex_render(token.latex, display_mode=False)
        except Exception:
            return self.escape_html_text(f"${token.latex}$")
        return f'<span class="{self.rules.math_inline_class}">{math_html}</span>'

    def render_document(self, token) -> str:  # type: ignore[override]
        # Base behavior: render children and collect footnotes.
        self.footnotes.update(getattr(token, "footnotes", {}))
        inner = "\n".join([self.render(child) for child in token.children])

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
