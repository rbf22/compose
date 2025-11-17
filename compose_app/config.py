"""Configuration and rules for the Compose typesetting application.

This module defines a minimal ruleset focused on math rendering and
utilities to load those rules from a TOML configuration file. The same
Rules object is intended to be shared between HTML and future PDF
renderers.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import tomllib


@dataclass
class Rules:
    """Minimal rendering rules.

    Attributes:
        math_inline_class: CSS class applied to inline math wrappers.
        math_display_class: CSS class applied to display math wrappers.
        html_document: whether to wrap output in a full HTML document
            (<!DOCTYPE html> + <html><head>...</head><body>...</body></html>).
        stylesheets: list of stylesheet HREFs to include in the <head>.
        body_class: optional CSS class for the <body> element.
        article_wrapper: whether to wrap the rendered content in an
            <article> tag inside <body>.
    """

    math_inline_class: str = "math-inline"
    math_display_class: str = "math-display"
    html_document: bool = False
    stylesheets: list[str] = field(default_factory=list)
    body_class: str | None = None
    article_wrapper: bool = False


def default_rules() -> Rules:
    """Return the default rules used by the application."""

    return Rules()


def _rules_from_mapping(data: Mapping[str, Any]) -> Rules:
    """Construct Rules from a mapping loaded from TOML.

    We look for a top-level [rules] table. If it does not exist, we fall
    back to reading keys from the top level, which keeps small configs
    convenient to write.
    """

    rules_section = data.get("rules", data)

    stylesheets_value = rules_section.get("stylesheets", [])
    if isinstance(stylesheets_value, list):
        stylesheets = [str(item) for item in stylesheets_value]
    elif stylesheets_value is None:
        stylesheets = []
    else:
        stylesheets = [str(stylesheets_value)]

    body_class_value = rules_section.get("body_class")
    body_class = str(body_class_value) if body_class_value is not None else None

    return Rules(
        math_inline_class=str(rules_section.get("math_inline_class", "math-inline")),
        math_display_class=str(rules_section.get("math_display_class", "math-display")),
        html_document=bool(rules_section.get("html_document", False)),
        stylesheets=stylesheets,
        body_class=body_class,
        article_wrapper=bool(rules_section.get("article_wrapper", False)),
    )


def load_rules_from_toml(path: str | Path) -> Rules:
    """Load Rules from a TOML configuration file.

    Args:
        path: Path to a TOML file containing either a [rules] table or
            top-level keys matching the fields of Rules.
    """

    config_path = Path(path)
    with config_path.open("rb") as f:
        data = tomllib.load(f)
    return _rules_from_mapping(data)
