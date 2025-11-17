"""Top-level API for the Compose typesetting application.

This package glues together mistletoe (Markdown) and pytex (math) to
produce HTML output from Markdown source.
"""

from .config import Rules, default_rules, load_rules_from_toml
from .markdown_parser import parse_markdown
from .html_renderer import RuleAwareHtmlRenderer


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
