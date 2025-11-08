# compose/lint/linter.py
"""
Main linter implementation for Compose.

Coordinates rule application and violation reporting.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from .rules import Rule, RuleViolation, BUILTIN_RULES, RULE_ALIASES
from .config import LintConfig


class MarkdownLinter:
    """Main linter class that applies rules to Markdown files"""

    def __init__(self, config: LintConfig):
        self.config = config
        self.rules: Dict[str, Rule] = {}
        self._load_rules()

    def _load_rules(self):
        """Load and configure rules based on configuration"""
        for rule_id, rule_class in BUILTIN_RULES.items():
            if self.config.is_rule_enabled(rule_id):
                rule_config = self.config.get_rule_config(rule_id)
                rule_instance = rule_class(rule_config)
                self.rules[rule_id] = rule_instance

    def lint_file(self, filepath: str) -> List[RuleViolation]:
        """
        Lint a single file.

        Args:
            filepath: Path to the file to lint

        Returns:
            List of violations found
        """
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except (IOError, OSError) as e:
            return [RuleViolation(
                "IO_ERROR",
                f"Could not read file: {e}",
                severity="error"
            )]

        return self.lint_content(content, filepath)

    def lint_content(self, content: str, filename: str = "<string>") -> List[RuleViolation]:
        """
        Lint content string.

        Args:
            content: Content to lint
            filename: Filename for error reporting

        Returns:
            List of violations found
        """
        all_violations = []

        # Apply file-level rules first, but only for rules that specifically
        # provide a custom file-level validator (to avoid duplicates), or are
        # FileRule subclasses.
        from .rules import FileRule, Rule  # local import to avoid cycles
        rules_with_file_run = set()
        for rule_id, rule in self.rules.items():
            # Detect custom validate_file override
            has_custom_file_validator = type(rule).validate_file is not Rule.validate_file
            if isinstance(rule, FileRule) or has_custom_file_validator:
                violations = rule.validate_file(content)
                for violation in violations:
                    if violation.line_nr is None:
                        violation.line_nr = 1  # Default to line 1 for file-level issues
                all_violations.extend(violations)
                rules_with_file_run.add(rule_id)

        # Apply line-level rules
        lines = content.split('\n')
        for line_nr, line in enumerate(lines, 1):
            for rule_id, rule in self.rules.items():
                # Skip line-level validation if we already ran a custom file-level
                # validation for this rule to prevent duplicate reports.
                if rule_id in rules_with_file_run:
                    continue
                if hasattr(rule, 'validate_line'):
                    violation = rule.validate_line(line, line_nr)
                    if violation:
                        all_violations.append(violation)

        return all_violations

    def lint_files(self, filepaths: List[str]) -> Dict[str, List[RuleViolation]]:
        """
        Lint multiple files.

        Args:
            filepaths: List of file paths to lint

        Returns:
            Dictionary mapping file paths to lists of violations
        """
        results = {}

        for filepath in filepaths:
            violations = self.lint_file(filepath)
            if violations:  # Only include files with violations
                results[filepath] = violations

        return results

    def get_enabled_rules(self) -> List[str]:
        """Get list of enabled rule IDs"""
        return list(self.rules.keys())

    def get_rule_info(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific rule"""
        if rule_id not in self.rules:
            return None

        rule = self.rules[rule_id]
        return {
            'id': rule_id,
            'name': getattr(rule, 'name', ''),
            'description': getattr(rule, 'description', ''),
            'severity': getattr(rule, 'severity', 'warning'),
            'options': {k: v.value for k, v in rule.options.items()}
        }


def resolve_rule_id(rule_identifier: str) -> str:
    """
    Resolve a rule identifier to a rule ID.

    Args:
        rule_identifier: Rule name or ID (e.g., "MD001" or "line-length")

    Returns:
        Canonical rule ID
    """
    # Check if it's already a rule ID
    if rule_identifier in BUILTIN_RULES:
        return rule_identifier

    # Check aliases
    if rule_identifier in RULE_ALIASES:
        return RULE_ALIASES[rule_identifier]

    # Try case-insensitive name matching
    rule_identifier_lower = rule_identifier.lower()
    for rule_id, rule_class in BUILTIN_RULES.items():
        if getattr(rule_class, 'name', '').lower() == rule_identifier_lower:
            return rule_id

    return rule_identifier  # Return as-is if not found


def format_violations(results: Dict[str, List[RuleViolation]],
                     format_type: str = "standard") -> str:
    """
    Format linting results for output.

    Args:
        results: Dictionary of file paths to violations
        format_type: Output format ("standard", "json", "compact")

    Returns:
        Formatted output string
    """
    if format_type == "json":
        return _format_json(results)
    elif format_type == "compact":
        return _format_compact(results)
    else:
        return _format_standard(results)


def _format_standard(results: Dict[str, List[RuleViolation]]) -> str:
    """Format results in standard human-readable format"""
    output_lines = []

    total_files = len(results)
    total_violations = sum(len(violations) for violations in results.values())

    for filepath, violations in results.items():
        output_lines.append(f"\n{filepath}:")
        for violation in violations:
            # Standard format should be: line: SEVERITY: RULE Message (no column)
            line = violation.line_nr if violation.line_nr is not None else "?"
            output_lines.append(
                f"  {line}: {violation.severity.upper()}: {violation.rule_id} {violation.message}"
            )

    if total_violations > 0:
        output_lines.append(f"\nFound {total_violations} violations in {total_files} files.")
    else:
        output_lines.append("\nNo violations found.")

    return "\n".join(output_lines)


def _format_compact(results: Dict[str, List[RuleViolation]]) -> str:
    """Format results in compact format"""
    output_lines = []

    for filepath, violations in results.items():
        for violation in violations:
            output_lines.append(f"{filepath}:{violation.line_nr}: {violation.rule_id} {violation.message}")

    return "\n".join(output_lines)


def _format_json(results: Dict[str, List[RuleViolation]]) -> str:
    """Format results as JSON"""
    import json

    json_data = {}
    for filepath, violations in results.items():
        json_data[filepath] = [
            {
                "rule_id": v.rule_id,
                "message": v.message,
                "line": v.line_nr,
                "column": v.column,
                "severity": v.severity
            }
            for v in violations
        ]

    return json.dumps(json_data, indent=2)
