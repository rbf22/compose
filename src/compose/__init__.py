"""Top-level API for the Compose typesetting application.

This package glues together mistletoe (Markdown) and pytex (math) to
produce HTML and (prototype) PDF output from Markdown source.
"""

from .config import Rules, default_rules, load_rules_from_toml
from .html_renderer import RuleAwareHtmlRenderer
from .markdown_parser import parse_markdown
from .pdf_renderer import PdfRenderer


def typeset_markdown_to_html(text: str, rules: Rules | None = None) -> str:
    """Typeset a Markdown string to HTML using the configured rules.

    This is the primary programmatic entrypoint for the HTML pipeline.
    """
    if rules is None:
        rules = default_rules()

    # Important: instantiate the renderer (which registers any extra
    # span/block tokens) before we construct the Document AST. The
    # mistletoe.Document constructor consults the global token lists, so
    # extras must already be installed when parsing happens.
    with RuleAwareHtmlRenderer(rules=rules) as renderer:
        document = parse_markdown(text)
        return renderer.render(document)


def typeset_markdown_to_pdf(text: str, rules: Rules | None = None) -> bytes:
    """Typeset a Markdown string to PDF bytes using the configured rules.

    This uses the same mistletoe AST and Rules model as the HTML
    pipeline, but renders with ``PdfRenderer`` on top of ``fpdf``.
    """

    if rules is None:
        rules = default_rules()

    with PdfRenderer(rules=rules) as renderer:
        document = parse_markdown(text)
        result = renderer.render(document)

    if isinstance(result, (bytes, bytearray)):
        return bytes(result)
    if isinstance(result, str):
        # FPDF may return a latin-1 string for PDF bytes.
        return result.encode("latin1")
    raise TypeError(f"PdfRenderer.render() returned unsupported type: {type(result)!r}")
