"""Command-line interface for the Compose typesetting application.

Usage (from the /compose root directory):

    python -m compose_app.cli input.md -o output.html

This currently supports only Markdown → HTML. The same parsing layer
and rules will later be reused for a PDF renderer.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from . import typeset_markdown_to_html, default_rules, load_rules_from_toml


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Typeset Markdown to HTML using mistletoe + pytex.")
    parser.add_argument("input", help="Path to the input Markdown file")
    parser.add_argument(
        "-o",
        "--output",
        help="Path to the output HTML file (defaults to INPUT with .html extension)",
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

    html = typeset_markdown_to_html(text, rules=rules)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_suffix(".html")

    output_path.write_text(html, encoding="utf-8")


if __name__ == "__main__":  # pragma: no cover
    main()
