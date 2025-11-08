# pytests/test_linter.py
"""Tests for the Compose markdown linter"""

import pytest
import tempfile
from pathlib import Path
from compose.lint.config import LintConfig
from compose.lint.linter import MarkdownLinter, resolve_rule_id
from compose.lint.rules import RuleViolation


def test_lint_config_creation():
    """Test creating a lint configuration"""
    config = LintConfig()
    assert config.rules == {}
    assert config.disabled_rules == []
    assert config.config_file is None


def test_default_config():
    """Test default configuration"""
    config = LintConfig.create_default()
    assert config.is_rule_enabled("MD001")  # line-length
    assert config.is_rule_enabled("MD002")  # trailing-whitespace
    assert config.get_rule_config("MD001") == {"max_length": 80}


def test_rule_resolution():
    """Test rule ID resolution"""
    assert resolve_rule_id("MD001") == "MD001"
    assert resolve_rule_id("line-length") == "MD001"
    assert resolve_rule_id("unknown") == "unknown"


def test_max_line_length_rule():
    """Test max line length rule"""
    from compose.lint.rules import MaxLineLengthRule

    rule = MaxLineLengthRule({"max_length": 10})
    violation = rule.validate_line("This is a very long line that exceeds the limit", 1)
    assert violation is not None
    assert violation.rule_id == "MD001"
    assert "exceeds maximum length" in violation.message

    # Test line within limit
    violation = rule.validate_line("Short line", 1)
    assert violation is None


def test_trailing_whitespace_rule():
    """Test trailing whitespace rule"""
    from compose.lint.rules import TrailingWhitespaceRule

    rule = TrailingWhitespaceRule()
    violation = rule.validate_line("Line with trailing spaces   ", 1)
    assert violation is not None
    assert violation.rule_id == "MD002"

    # Test line without trailing whitespace
    violation = rule.validate_line("Clean line", 1)
    assert violation is None


def test_hard_tab_rule():
    """Test hard tab rule"""
    from compose.lint.rules import HardTabRule

    rule = HardTabRule()
    violation = rule.validate_line("Line with\ttab", 1)
    assert violation is not None
    assert violation.rule_id == "MD003"

    # Test line without tabs
    violation = rule.validate_line("Clean line", 1)
    assert violation is None


def test_missing_alt_text_rule():
    """Test missing alt text rule"""
    from compose.lint.rules import MissingAltTextRule

    rule = MissingAltTextRule()
    violation = rule.validate_line("![](/path/to/image.png)", 1)
    assert violation is not None
    assert violation.rule_id == "MD007"

    # Test image with alt text
    violation = rule.validate_line("![Alt text](/path/to/image.png)", 1)
    assert violation is None


def test_markdown_linter():
    """Test the main linter class"""
    config = LintConfig.create_default()
    linter = MarkdownLinter(config)

    # Test linting content with violations
    content = "This line is way too long and should trigger a violation because it exceeds the maximum allowed length\n"
    content += "This line has trailing spaces   \n"
    content += "This line has\ttabs\n"

    violations = linter.lint_content(content)
    assert len(violations) >= 2  # Should catch at least line length and trailing spaces

    # Check that violations have correct structure
    for violation in violations:
        assert isinstance(violation, RuleViolation)
        assert violation.rule_id in ["MD001", "MD002", "MD003"]
        assert violation.line_nr > 0


def test_linter_file_processing():
    """Test linting actual files"""
    config = LintConfig.create_default()
    linter = MarkdownLinter(config)

    # Create a temporary markdown file with issues
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Test Document\n\n")
        f.write("This is a very long line that exceeds the maximum allowed length for testing purposes and should trigger a line length violation.\n")
        f.write("Line with trailing spaces   \n")
        f.write("\n\n")  # Multiple blank lines
        temp_path = f.name

    try:
        violations = linter.lint_file(temp_path)
        assert len(violations) > 0

        # Should have line length violation
        line_length_violations = [v for v in violations if v.rule_id == "MD001"]
        assert len(line_length_violations) > 0

    finally:
        Path(temp_path).unlink()


def test_config_file_loading():
    """Test loading configuration from file"""
    # Create a temporary config file
    config_content = """
[general]
ignore = "MD003"

[rules]
MD001.max_length = 50
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write(config_content)
        temp_config = f.name

    try:
        config = LintConfig.load_from_file(temp_config)
        assert config.is_rule_enabled("MD001")
        assert not config.is_rule_enabled("MD003")  # Should be disabled
        assert config.get_rule_config("MD001")["max_length"] == 50

    finally:
        Path(temp_config).unlink()


def test_file_finder():
    """Test the Markdown file finder"""
    from compose.lint.filefinder import MarkdownFileFinder

    # Create temporary directory with markdown files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some markdown files
        Path(temp_dir, "test.md").write_text("# Test")
        Path(temp_dir, "subdir").mkdir()
        Path(temp_dir, "subdir", "nested.md").write_text("# Nested")
        Path(temp_dir, "not_md.txt").write_text("Not markdown")

        files = MarkdownFileFinder.find_files(temp_dir)
        assert len(files) == 2
        assert any("test.md" in f for f in files)
        assert any("nested.md" in f for f in files)
        assert not any("not_md.txt" in f for f in files)


def test_violation_formatting():
    """Test violation formatting"""
    from compose.lint.linter import format_violations

    violation = RuleViolation("MD001", "Test message", 5, 10, "warning")

    results = {"test.md": [violation]}
    output = format_violations(results, "standard")

    assert "test.md:" in output
    assert "5: WARNING: MD001 Test message" in output

    # Test compact format
    compact = format_violations(results, "compact")
    assert "test.md:5: MD001 Test message" in compact
