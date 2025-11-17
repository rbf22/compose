"""Command-line interface for the Compose typesetting application.

Usage (from the /compose root directory):

    # HTML output (default)
    python -m compose_app.cli input.md -o output.html

    # PDF output
    python -m compose_app.cli input.md --format pdf --output-pdf output.pdf

The CLI shares the same parsing layer and rules for both HTML and PDF
renderers.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from . import (
    typeset_markdown_to_html,
    typeset_markdown_to_pdf,
    default_rules,
    load_rules_from_toml,
)


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Typeset Markdown to HTML or PDF using mistletoe + pytex + fpdf.",
    )
    parser.add_argument("input", help="Path to the input Markdown file")
    parser.add_argument(
        "-o",
        "--output",
        help="Path to the output file (defaults to INPUT with extension based on --format)",
    )
    parser.add_argument(
        "--output-pdf",
        help="Path to the output PDF file (used when --format=pdf; overrides --output if set)",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["html", "pdf"],
        default="html",
        help="Output format: html (default) or pdf",
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Path to a TOML configuration file defining rendering rules",
    )

    args = parser.parse_args(argv)

    input_path = Path(args.input)
    text = input_path.read_text(encoding="utf-8")

    if args.config:
        rules = load_rules_from_toml(args.config)
    else:
        rules = default_rules()

    if args.format == "pdf":
        pdf_bytes = typeset_markdown_to_pdf(text, rules=rules)

        if args.output_pdf:
            output_path = Path(args.output_pdf)
        elif args.output:
            output_path = Path(args.output)
        else:
            output_path = input_path.with_suffix(".pdf")

        output_path.write_bytes(pdf_bytes)
    else:
        html = typeset_markdown_to_html(text, rules=rules)

        if args.output:
            output_path = Path(args.output)
        else:
            output_path = input_path.with_suffix(".html")

        output_path.write_text(html, encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    main()
