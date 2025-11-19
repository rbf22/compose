import io
from pathlib import Path

import compose_app
from compose_app import (
    typeset_markdown_to_html,
    typeset_markdown_to_pdf,
    default_rules,
    load_rules_from_toml,
)
from compose_app.cli import main as cli_main


def test_typeset_plain_text(tmp_path: Path) -> None:
    html = typeset_markdown_to_html("Hello, world!", rules=default_rules())
    assert "Hello, world!" in html
    # Should at least look like HTML, not raw Markdown.
    assert "<" in html and ">" in html


def test_typeset_inline_math() -> None:
    text = "This is inline math: $x^2 + 1$."
    html = typeset_markdown_to_html(text, rules=default_rules())
    # Math should be rendered via KaTeX and wrapped with the configured class.
    assert "math-inline" in html
    # The original $...$ should not appear verbatim if rendering succeeded.
    assert "$x^2 + 1$" not in html


def test_typeset_display_math_paragraph() -> None:
    text = "Before.\n\n$x^2 + 1$\n\nAfter."
    html = typeset_markdown_to_html(text, rules=default_rules())
    # Paragraph that is only $...$ should become display math.
    assert "math-display" in html
    assert "$x^2 + 1$" not in html


def test_cli_basic(tmp_path: Path, monkeypatch) -> None:
    input_path = tmp_path / "doc.md"
    input_path.write_text("Hello CLI with $x^2$", encoding="utf-8")
    output_path = tmp_path / "doc.html"

    # Run the CLI entrypoint programmatically.
    cli_main([str(input_path), "-o", str(output_path)])

    assert output_path.exists()
    html = output_path.read_text(encoding="utf-8")
    assert "Hello CLI" in html
    assert "math-inline" in html


def test_load_rules_from_toml_and_typeset(tmp_path: Path) -> None:
    # Write a minimal TOML config that changes the math_inline_class.
    config_path = tmp_path / "config.toml"
    config_path.write_text('math_inline_class = "my-inline-math"\n', encoding="utf-8")

    rules = load_rules_from_toml(config_path)
    assert rules.math_inline_class == "my-inline-math"

    text = "Inline math: $x^2$."
    html = typeset_markdown_to_html(text, rules=rules)
    assert "my-inline-math" in html


def test_section_from_level_groups_h2() -> None:
    rules = default_rules()
    rules.section_from_level = 2

    md = "\n".join(
        [
            "# Title",
            "",
            "Subtitle",
            "",
            "## First section",
            "",
            "Body",
            "",
            "## Second section",
            "",
            "More",
        ]
    )

    html = typeset_markdown_to_html(md, rules=rules)

    # Two H2s should open two <section> blocks, with matching close tags.
    assert html.count("<section>") == 2
    assert html.count("</section>") == 2
    assert "<h2>First section</h2>" in html
    assert "<h2>Second section</h2>" in html


def test_typeset_markdown_to_pdf_basic() -> None:
    text = "Hello PDF with $x^2$."

    pdf_bytes = typeset_markdown_to_pdf(text, rules=default_rules())

    assert isinstance(pdf_bytes, (bytes, bytearray))
    # FPDF should produce a valid PDF header.
    assert pdf_bytes.startswith(b"%PDF")


def test_html_integration_headings_lists_tables_math_and_ids() -> None:
    rules = default_rules()
    rules.heading_base_class = "heading"
    rules.auto_heading_ids = True
    rules.heading_id_prefix = "sec-"

    md = "\n".join(
        [
            "# My Title",
            "",
            "Intro paragraph with inline $x^2$.",
            "",
            "## Section One",
            "",
            "- Item 1",
            "- Item 2",
            "",
            "| Col1 | Col2 |",
            "| ---- | ---- |",
            "| a    | b    |",
            "",
            "$y^2 + 1$",
        ]
    )

    html = typeset_markdown_to_html(md, rules=rules)

    # Headings should have classes and IDs derived from Rules and text.
    assert '<h1 class="heading" id="sec-my-title">' in html
    assert '<h2 class="heading" id="sec-section-one">' in html

    # Inline and display math should be present.
    assert "math-inline" in html
    assert "math-display" in html

    # Lists should render with list and list-item elements.
    assert "<ul>" in html
    assert "<li>Item 1</li>" in html

    # Tables should render with a <table> wrapper.
    assert "<table>" in html
