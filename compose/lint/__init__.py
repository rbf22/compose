# compose/lint/__init__.py
"""
Compose Markdown Linter

A comprehensive linting system for Markdown documents that checks for
style violations, formatting issues, and best practices.
"""

from .rules import BUILTIN_RULES, RULE_ALIASES, RuleViolation
from .config import LintConfig, find_config_file
from .linter import MarkdownLinter, format_violations
from .filefinder import MarkdownFileFinder

__version__ = "1.0.0"

__all__ = [
    'LintConfig',
    'MarkdownLinter',
    'MarkdownFileFinder',
    'RuleViolation',
    'BUILTIN_RULES',
    'RULE_ALIASES',
    'find_config_file',
    'format_violations'
]
