import io
from pathlib import Path

import compose_app
from compose_app import typeset_markdown_to_html, default_rules, load_rules_from_toml
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
