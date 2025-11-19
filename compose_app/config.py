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
        subtitle_after_h1: whether to treat the first paragraph after the
            first H1 as a subtitle.
        subtitle_class: CSS class to apply to the subtitle paragraph.
        section_from_level: heading level at which <section> wrappers are
            started (for example, 2 to start sections at H2). If None, no
            section elements are emitted.
        pdf_vector_math_enabled: whether to attempt vector-like math
            layout in the PDF backend for simple expressions (currently
            a tiny PoC subset only).
    """

    math_inline_class: str = "math-inline"
    math_display_class: str = "math-display"
    html_document: bool = False
    stylesheets: list[str] = field(default_factory=list)
    body_class: str | None = None
    article_wrapper: bool = False
    subtitle_after_h1: bool = False
    subtitle_class: str = "subtitle"
    section_from_level: int | None = None
    pdf_vector_math_enabled: bool = False
    heading_base_class: str | None = None
    paragraph_base_class: str | None = None
    auto_heading_ids: bool = False
    heading_id_prefix: str = ""


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

    section_from_level_value = rules_section.get("section_from_level")
    if section_from_level_value is None:
        section_from_level: int | None = None
    else:
        try:
            section_from_level = int(section_from_level_value)
        except (TypeError, ValueError):
            section_from_level = None

    heading_base_class_value = rules_section.get("heading_base_class")
    heading_base_class = (
        str(heading_base_class_value) if heading_base_class_value is not None else None
    )

    paragraph_base_class_value = rules_section.get("paragraph_base_class")
    paragraph_base_class = (
        str(paragraph_base_class_value) if paragraph_base_class_value is not None else None
    )

    heading_id_prefix = str(rules_section.get("heading_id_prefix", ""))

    return Rules(
        math_inline_class=str(rules_section.get("math_inline_class", "math-inline")),
        math_display_class=str(rules_section.get("math_display_class", "math-display")),
        html_document=bool(rules_section.get("html_document", False)),
        stylesheets=stylesheets,
        body_class=body_class,
        article_wrapper=bool(rules_section.get("article_wrapper", False)),
        subtitle_after_h1=bool(rules_section.get("subtitle_after_h1", False)),
        subtitle_class=str(rules_section.get("subtitle_class", "subtitle")),
        section_from_level=section_from_level,
        pdf_vector_math_enabled=bool(rules_section.get("pdf_vector_math_enabled", False)),
        heading_base_class=heading_base_class,
        paragraph_base_class=paragraph_base_class,
        auto_heading_ids=bool(rules_section.get("auto_heading_ids", False)),
        heading_id_prefix=heading_id_prefix,
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
