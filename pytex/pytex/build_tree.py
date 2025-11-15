"""Python port of KaTeX's buildTree.js - tree building dispatcher."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .build_common import make_span
from .options import Options
from .settings import Settings
from .style import Style

if TYPE_CHECKING:
    pass  # type: ignore


def options_from_settings(settings: Settings) -> Options:
    """Create Options from Settings."""
    return Options({
        "style": Style.DISPLAY if settings.display_mode else Style.TEXT,
        "maxSize": settings.max_size,
        "minRuleThickness": settings.min_rule_thickness,
    })


def display_wrap(node, settings: Settings):
    """Wrap node for display mode."""
    if settings.display_mode:
        classes = ["katex-display"]
        if settings.leqno:
            classes.append("leqno")
        if settings.fleqn:
            classes.append("fleqn")
        node = make_span(classes, [node])
    return node


def build_tree(tree, expression: str, settings: Settings):
    """Build tree with appropriate output format."""
    options = options_from_settings(settings)

    if settings.output == "mathml":
        from .build_mathml import build_mathml
        return build_mathml(tree, expression, options, settings.display_mode, True)
    elif settings.output == "html":
        from .build_html import build_html
        html_node = build_html(tree, options)
        katex_node = make_span(["katex"], [html_node])
        return display_wrap(katex_node, settings)
    else:
        # Both HTML and MathML
        from .build_mathml import build_mathml
        from .build_html import build_html
        mathml_node = build_mathml(tree, expression, options, settings.display_mode, False)
        html_node = build_html(tree, options)
        katex_node = make_span(["katex"], [mathml_node, html_node])
        return display_wrap(katex_node, settings)


def build_html_tree(tree, expression: str, settings: Settings):
    """Build HTML tree."""
    options = options_from_settings(settings)
    from .build_html import build_html
    html_node = build_html(tree, options)
    katex_node = make_span(["katex"], [html_node])
    return display_wrap(katex_node, settings)


__all__ = ["build_tree", "build_html_tree", "options_from_settings", "display_wrap"]
