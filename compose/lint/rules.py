# compose/lint/rules.py
"""
Markdown linting rules for Compose.

This module defines the core rule system and built-in rules for validating
Markdown documents according to common style guidelines.
"""

import re
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod


class RuleViolation:
    """Represents a single rule violation"""
    def __init__(self, rule_id: str, message: str, line_nr: Optional[int] = None,
                 column: Optional[int] = None, severity: str = "warning"):
        self.rule_id = rule_id
        self.message = message
        self.line_nr = line_nr
        self.column = column
        self.severity = severity  # "error", "warning", "info"

    def __str__(self):
        location = f"{self.line_nr}" if self.line_nr else "?"
        if self.column:
            location += f":{self.column}"
        return f"{location}: {self.severity.upper()}: {self.rule_id} {self.message}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if not isinstance(other, RuleViolation):
            return False
        return (self.rule_id == other.rule_id and
                self.message == other.message and
                self.line_nr == other.line_nr and
                self.column == other.column and
                self.severity == other.severity)


class RuleOption:
    """Represents a configurable option for a rule"""
    def __init__(self, name: str, default_value: Any, description: str):
        self.name = name
        self.value = default_value
        self.default_value = default_value
        self.description = description

    def set_value(self, value: Any):
        """Set the option value"""
        self.value = value

    def reset(self):
        """Reset to default value"""
        self.value = self.default_value


class Rule(ABC):
    """Base class for all linting rules"""
    rule_id: str = ""
    name: str = ""
    description: str = ""
    severity: str = "warning"

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        self.options: Dict[str, RuleOption] = {}
        self._initialize_options()
        if options:
            self.configure(options)

    def _initialize_options(self):
        """Initialize rule options - override in subclasses"""
        pass

    def configure(self, options: Dict[str, Any]):
        """Configure rule options"""
        for key, value in options.items():
            if key in self.options:
                self.options[key].set_value(value)

    @abstractmethod
    def validate(self, content: str, line_nr: Optional[int] = None) -> Optional[RuleViolation]:
        """Validate content and return violation if any"""
        pass

    def validate_line(self, line: str, line_nr: int) -> Optional[RuleViolation]:
        """Validate a single line - default implementation"""
        return self.validate(line, line_nr)

    def validate_file(self, content: str) -> List[RuleViolation]:
        """Validate entire file - default implementation applies line-by-line"""
        violations = []
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            violation = self.validate_line(line, i)
            if violation:
                violations.append(violation)
        return violations


class LineRule(Rule):
    """Rule that operates on individual lines"""

    def validate(self, content: str, line_nr: Optional[int] = None) -> Optional[RuleViolation]:
        """For line rules, content should be a single line"""
        if line_nr is None:
            return None
        return self.validate_line(content, line_nr)


class FileRule(Rule):
    """Rule that operates on entire files"""

    def validate_line(self, line: str, line_nr: int) -> Optional[RuleViolation]:
        """File rules don't validate individual lines"""
        return None

    def validate_file(self, content: str) -> List[RuleViolation]:
        """File rules validate the entire content"""
        violation = self.validate(content)
        return [violation] if violation else []


# Built-in Rules

class MaxLineLengthRule(LineRule):
    """Check for lines exceeding maximum length"""
    rule_id = "MD001"
    name = "line-length"
    description = "Line length should not exceed maximum"

    def _initialize_options(self):
        self.options["max_length"] = RuleOption("max_length", 80, "Maximum line length")

    def validate_line(self, line: str, line_nr: int) -> Optional[RuleViolation]:
        max_length = self.options["max_length"].value
        if len(line.rstrip()) > max_length:
            return RuleViolation(
                self.rule_id,
                f"Line exceeds maximum length ({len(line.rstrip())} > {max_length})",
                line_nr,
                severity=self.severity
            )
        return None


class TrailingWhitespaceRule(LineRule):
    """Check for trailing whitespace"""
    rule_id = "MD002"
    name = "trailing-whitespace"
    description = "Lines should not have trailing whitespace"

    def validate_line(self, line: str, line_nr: int) -> Optional[RuleViolation]:
        if line != line.rstrip(' \t'):
            return RuleViolation(
                self.rule_id,
                "Line has trailing whitespace",
                line_nr,
                severity=self.severity
            )
        return None


class HardTabRule(LineRule):
    """Check for hard tab characters"""
    rule_id = "MD003"
    name = "hard-tabs"
    description = "Lines should not contain hard tab characters"

    def validate_line(self, line: str, line_nr: int) -> Optional[RuleViolation]:
        if '\t' in line:
            return RuleViolation(
                self.rule_id,
                "Line contains hard tab characters",
                line_nr,
                severity=self.severity
            )
        return None


class MultipleBlankLinesRule(LineRule):
    """Check for multiple consecutive blank lines"""
    rule_id = "MD004"
    name = "multiple-blank-lines"
    description = "Multiple consecutive blank lines should be avoided"

    def _initialize_options(self):
        self.options["max_blank_lines"] = RuleOption("max_blank_lines", 1, "Maximum consecutive blank lines")

    def validate_line(self, line: str, line_nr: int) -> Optional[RuleViolation]:
        # This rule needs context of previous lines, so it's implemented as a file rule
        return None

    def validate_file(self, content: str) -> List[RuleViolation]:
        violations = []
        lines = content.split('\n')
        consecutive_blanks = 0
        max_blanks = self.options["max_blank_lines"].value

        for i, line in enumerate(lines, 1):
            if line.strip() == "":
                consecutive_blanks += 1
                if consecutive_blanks > max_blanks:
                    violations.append(RuleViolation(
                        self.rule_id,
                        f"Multiple consecutive blank lines ({consecutive_blanks} > {max_blanks})",
                        i,
                        severity=self.severity
                    ))
            else:
                consecutive_blanks = 0

        return violations


class HeadingStyleRule(LineRule):
    """Check heading style consistency"""
    rule_id = "MD005"
    name = "heading-style"
    description = "Headings should use consistent style"

    def _initialize_options(self):
        self.options["style"] = RuleOption("style", "atx", "Heading style: 'atx' (#) or 'setext' (===)")

    def validate_line(self, line: str, line_nr: int) -> Optional[RuleViolation]:
        style = self.options["style"].value

        # Line-level ATX check: flag when setext is expected
        if line.startswith('#') and style == "setext":
            return RuleViolation(
                self.rule_id,
                "ATX heading style used, but setext style expected",
                line_nr,
                severity=self.severity
            )

        # Setext detection requires previous-line context; handled in validate_file
        return None

    def validate_file(self, content: str) -> List[RuleViolation]:
        # Use file-level context to detect setext headings correctly
        violations: List[RuleViolation] = []
        style = self.options["style"].value

        lines = content.split('\n')
        for i in range(1, len(lines)):
            prev_line = lines[i - 1]
            line = lines[i]

            # Detect setext underline (=== or ---). Only consider it a setext
            # heading if the previous line contains non-whitespace text and is
            # not already an ATX heading.
            if re.match(r'^\s*[-=]+\s*$', line):
                if prev_line.strip() and not prev_line.lstrip().startswith('#'):
                    if style == "atx":
                        violations.append(RuleViolation(
                            self.rule_id,
                            "Setext heading style used, but ATX style expected",
                            i + 1,
                            severity=self.severity
                        ))

        return violations


class HeadingLevelRule(LineRule):
    """Check heading level hierarchy"""
    rule_id = "MD006"
    name = "heading-level"
    description = "Headings should not skip levels"

    def __init__(self, options: Optional[Dict[str, Any]] = None):
        super().__init__(options)
        self.last_level = 0

    def validate_line(self, line: str, line_nr: int) -> Optional[RuleViolation]:
        # Use file-level context to avoid counting headings inside fenced code
        return None

    def validate_file(self, content: str) -> List[RuleViolation]:
        violations: List[RuleViolation] = []
        self.last_level = 0

        lines = content.split('\n')
        in_fenced = False
        fence_marker = None

        for i, raw in enumerate(lines, 1):
            line = raw.rstrip('\n')
            stripped = line.strip()

            # Toggle fenced block state
            if stripped.startswith('```') or stripped.startswith('~~~'):
                marker = '```' if stripped.startswith('```') else '~~~'
                if not in_fenced:
                    in_fenced = True
                    fence_marker = marker
                else:
                    if fence_marker == marker:
                        in_fenced = False
                        fence_marker = None
                continue

            if in_fenced:
                continue

            # Extract heading level (start of line only)
            match = re.match(r'^(#+)', line)
            if match:
                level = len(match.group(1))

                # Reset on level 1 headings
                if level == 1:
                    self.last_level = 1
                    continue

                # Check for skipped levels
                if self.last_level and level > self.last_level + 1:
                    violations.append(RuleViolation(
                        self.rule_id,
                        f"Heading level skips from {self.last_level} to {level}",
                        i,
                        severity=self.severity
                    ))

                self.last_level = level

        return violations


class MissingAltTextRule(LineRule):
    """Check for images without alt text"""
    rule_id = "MD007"
    name = "missing-alt-text"
    description = "Images should have alt text"

    def validate_line(self, line: str, line_nr: int) -> Optional[RuleViolation]:
        # Match Markdown image syntax: ![alt](url)
        # This regex finds images with empty or missing alt text
        pattern = r'!\[\s*\]\([^)]+\)'
        if re.search(pattern, line):
            return RuleViolation(
                self.rule_id,
                "Image is missing alt text",
                line_nr,
                severity=self.severity
            )
        return None


class CodeBlockStyleRule(LineRule):
    """Check code block style consistency"""
    rule_id = "MD008"
    name = "code-block-style"
    description = "Code blocks should use consistent fence style"

    def _initialize_options(self):
        self.options["style"] = RuleOption("style", "fenced", "Code block style: 'fenced' or 'indented'")

    def validate_line(self, line: str, line_nr: int) -> Optional[RuleViolation]:
        # Use file-level context to avoid false positives inside fenced blocks
        return None

    def validate_file(self, content: str) -> List[RuleViolation]:
        violations: List[RuleViolation] = []
        style = self.options["style"].value

        lines = content.split('\n')
        in_fenced = False
        fence_marker = None  # ``` or ~~~

        for i, raw in enumerate(lines, 1):
            line = raw.rstrip('\n')
            stripped = line.strip()

            # Detect fenced block start/end
            if stripped.startswith('```') or stripped.startswith('~~~'):
                marker = '```' if stripped.startswith('```') else '~~~'
                if not in_fenced:
                    in_fenced = True
                    fence_marker = marker
                else:
                    # Only close if matching opener
                    if fence_marker == marker:
                        in_fenced = False
                        fence_marker = None

                # Style check: fenced used while expecting indented
                if style == 'indented':
                    violations.append(RuleViolation(
                        self.rule_id,
                        "Fenced code block used, but indented style expected",
                        i,
                        severity=self.severity
                    ))
                continue

            # When inside fenced block, do not flag indentation
            if in_fenced:
                continue

            # Indented code detection (four leading spaces by CommonMark)
            if line.startswith('    '):
                # Heuristic: ignore list continuations (e.g., '    - item')? We still treat as code by CommonMark
                if style == 'fenced':
                    violations.append(RuleViolation(
                        self.rule_id,
                        "Indented code block used, but fenced style expected",
                        i,
                        severity=self.severity
                    ))

        return violations


class HorizontalRuleStyleRule(Rule):
    """MD009: Enforce consistent horizontal rule style."""
    rule_id = "MD009"
    description = "Horizontal rule style should be consistent"
    severity = "warning"
    
    def _initialize_options(self):
        """Initialize rule options."""
        self.options["style"] = RuleOption("style", "---", "Preferred style: '---', '***', or '___'")
    
    def validate(self, content: str, line_nr: Optional[int] = None) -> Optional[RuleViolation]:
        """Validate content - not used for this line-level rule."""
        return None
    
    def validate_line(self, line: str, line_nr: int) -> List[RuleViolation]:
        """Check horizontal rule consistency."""
        violations = []
        stripped = line.strip()
        
        # Check if this is a horizontal rule
        if (len(stripped) >= 3 and 
            (all(c == '-' for c in stripped) or
             all(c == '*' for c in stripped) or
             all(c == '_' for c in stripped))):
            
            preferred_style = self.options['style'].value
            if not stripped.startswith(preferred_style[0]):
                violations.append(RuleViolation(
                    self.rule_id,
                    f"Horizontal rule should use '{preferred_style}' style, found '{stripped}'",
                    line_nr,
                    severity=self.severity
                ))
        
        return violations


class UnnecessaryEscapeRule(Rule):
    """MD010: Warn about unnecessary escape characters."""
    rule_id = "MD010"
    name = "unnecessary-escape"
    description = "Unnecessary escape characters should be avoided"
    severity = "warning"
    
    def validate(self, content: str, line_nr: Optional[int] = None) -> Optional[RuleViolation]:
        """Validate content - not used for this line-level rule."""
        return None
    
    def validate_line(self, line: str, line_nr: int) -> List[RuleViolation]:
        """Check for unnecessary escape characters."""
        violations = []
        
        # Check for escaped periods in headings (e.g., "## 5\. Title")
        # Periods don't need escaping in markdown headings
        if line.strip().startswith('#') and '\\.' in line:
            violations.append(RuleViolation(
                self.rule_id,
                "Unnecessary escape character '\\.' in heading - periods don't need escaping",
                line_nr,
                severity=self.severity
            ))
        
        # Check for other commonly unnecessary escapes
        # Parentheses, brackets, etc. don't need escaping in most contexts
        unnecessary_escapes = [
            ('\\(', '(', 'Parentheses'),
            ('\\)', ')', 'Parentheses'),
            ('\\[', '[', 'Brackets'),
            ('\\]', ']', 'Brackets'),
            ('\\{', '{', 'Braces'),
            ('\\}', '}', 'Braces'),
        ]
        
        for escaped, char, name in unnecessary_escapes:
            if escaped in line and not line.strip().startswith('#'):
                # Only warn if it's not in a code block or special context
                if '`' not in line:  # Simple check - not in inline code
                    violations.append(RuleViolation(
                        self.rule_id,
                        f"Unnecessary escape character '{escaped}' - {name} don't need escaping in most contexts",
                        line_nr,
                        severity=self.severity
                    ))
                    break  # Only report once per line
        
        return violations


# Registry of all built-in rules
BUILTIN_RULES = {
    "MD001": MaxLineLengthRule,
    "MD002": TrailingWhitespaceRule,
    "MD003": HardTabRule,
    "MD004": MultipleBlankLinesRule,
    "MD005": HeadingStyleRule,
    "MD006": HeadingLevelRule,
    "MD007": MissingAltTextRule,
    "MD008": CodeBlockStyleRule,
    "MD009": HorizontalRuleStyleRule,
    "MD010": UnnecessaryEscapeRule,
}

# Rule aliases for convenience
RULE_ALIASES = {
    "line-length": "MD001",
    "trailing-whitespace": "MD002",
    "hard-tabs": "MD003",
    "multiple-blank-lines": "MD004",
    "heading-style": "MD005",
    "heading-level": "MD006",
    "missing-alt-text": "MD007",
    "code-block-style": "MD008",
    "horizontal-rule-style": "MD009",
    "unnecessary-escape": "MD010",
}
