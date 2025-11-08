# compose/lint/config.py
"""
Configuration system for the Compose linter.

Supports loading configuration from files and command-line options.
"""

import os
from typing import Dict, Any, List, Optional
from pathlib import Path


class LintConfigError(Exception):
    """Configuration error"""
    pass


class LintConfig:
    """Configuration for the markdown linter"""

    def __init__(self):
        self.rules: Dict[str, Dict[str, Any]] = {}
        self.disabled_rules: List[str] = []
        self.config_file: Optional[str] = None

    def enable_rule(self, rule_id: str, options: Optional[Dict[str, Any]] = None):
        """Enable a rule with optional configuration"""
        if rule_id in self.disabled_rules:
            self.disabled_rules.remove(rule_id)

        if options:
            if rule_id not in self.rules:
                self.rules[rule_id] = {}
            self.rules[rule_id].update(options)

    def disable_rule(self, rule_id: str):
        """Disable a rule"""
        if rule_id not in self.disabled_rules:
            self.disabled_rules.append(rule_id)

        # Remove any configuration for this rule
        if rule_id in self.rules:
            del self.rules[rule_id]

    def is_rule_enabled(self, rule_id: str) -> bool:
        """Check if a rule is enabled"""
        return rule_id not in self.disabled_rules

    def get_rule_config(self, rule_id: str) -> Dict[str, Any]:
        """Get configuration for a specific rule"""
        return self.rules.get(rule_id, {})

    @classmethod
    def load_from_file(cls, filepath: str) -> 'LintConfig':
        """Load configuration from a TOML file.

        Supports two formats:
        1) Dedicated linter file (legacy): top-level [general] and [rules]
        2) Project config: nested under [lint], e.g. [lint.general], [lint.rules]
        """
        config = cls()
        config.config_file = filepath

        try:
            path = Path(filepath)
            if not path.exists():
                raise LintConfigError(f"Configuration file not found: {filepath}")

            content = path.read_text()

            # First try proper TOML parsing to detect [lint] section in project files
            try:
                try:
                    import tomllib  # Python 3.11+
                except ImportError:  # pragma: no cover
                    tomllib = None  # We won't import external deps

                if tomllib is not None:
                    with open(filepath, 'rb') as f:
                        data = tomllib.load(f)
                    if isinstance(data, dict) and 'lint' in data and isinstance(data['lint'], dict):
                        return cls._from_project_lint_dict(data['lint'], filepath)
            except Exception:
                # Fall back to legacy parser below
                pass

            # Legacy/simple parser expecting top-level [general] and [rules]
            config._parse_config_content(content)

        except Exception as e:
            raise LintConfigError(f"Failed to load config from {filepath}: {e}")

        return config

    @classmethod
    def _from_project_lint_dict(cls, lint_dict: Dict[str, Any], source: Optional[str] = None) -> 'LintConfig':
        """Create LintConfig from a project TOML [lint] dictionary."""
        cfg = cls()
        cfg.config_file = source

        # General disables (comma-separated string or list)
        general = lint_dict.get('general', {}) if isinstance(lint_dict.get('general'), dict) else {}
        ignore_val = general.get('ignore')
        if isinstance(ignore_val, str):
            for rule in [r.strip() for r in ignore_val.split(',') if r.strip()]:
                cfg.disable_rule(rule)
        elif isinstance(ignore_val, list):
            for rule in ignore_val:
                cfg.disable_rule(str(rule))

        # Rules section
        rules = lint_dict.get('rules', {})
        if isinstance(rules, dict):
            for rule_id, options in rules.items():
                if isinstance(options, dict) and options:
                    cfg.enable_rule(rule_id, options)
                else:
                    # Treat bare true/false as enable/disable
                    if isinstance(options, bool):
                        if options:
                            cfg.enable_rule(rule_id)
                        else:
                            cfg.disable_rule(rule_id)

        return cfg

    def _parse_config_content(self, content: str):
        """Parse simple TOML-like configuration"""
        lines = content.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Section headers
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1].strip()
                continue

            # Key-value pairs
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]

                self._parse_config_line(current_section, key, value)

    def _parse_config_line(self, section: Optional[str], key: str, value: str):
        """Parse a single configuration line"""
        if section == "rules":
            # Rule configuration: rule_id.option = value
            if '.' in key:
                rule_id, option = key.split('.', 1)
                if rule_id not in self.rules:
                    self.rules[rule_id] = {}
                self.rules[rule_id][option] = self._parse_value(value)
            else:
                # Rule enable/disable
                if value.lower() in ('true', '1', 'yes', 'on'):
                    self.enable_rule(key)
                elif value.lower() in ('false', '0', 'no', 'off'):
                    self.disable_rule(key)

        elif section == "general":
            if key == "ignore":
                # Comma-separated list of rules to ignore
                rules_to_ignore = [r.strip() for r in value.split(',')]
                for rule in rules_to_ignore:
                    self.disable_rule(rule)

    def _parse_value(self, value: str) -> Any:
        """Parse a configuration value"""
        # Try to parse as number
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Try to parse as boolean
        if value.lower() in ('true', 'yes', 'on'):
            return True
        elif value.lower() in ('false', 'no', 'off'):
            return False

        # Return as string
        return value

    def save_to_file(self, filepath: str):
        """Save configuration to a file"""
        content = "# Compose Markdown Linter Configuration\n\n"

        # General section
        if self.disabled_rules:
            content += "[general]\n"
            content += f"ignore = \"{', '.join(self.disabled_rules)}\"\n\n"

        # Rules section
        if self.rules:
            content += "[rules]\n"
            for rule_id, options in self.rules.items():
                for option_key, option_value in options.items():
                    content += f"{rule_id}.{option_key} = {repr(option_value)}\n"
                content += "\n"

        Path(filepath).write_text(content)

    @classmethod
    def create_default(cls) -> 'LintConfig':
        """Create a default configuration"""
        config = cls()

        # Default rule configurations
        config.enable_rule("MD001", {"max_length": 80})
        config.enable_rule("MD002")  # trailing whitespace
        config.enable_rule("MD003")  # hard tabs
        config.enable_rule("MD004", {"max_blank_lines": 1})
        config.enable_rule("MD005", {"style": "atx"})
        config.enable_rule("MD006")  # heading level
        config.enable_rule("MD007")  # missing alt text
        config.enable_rule("MD008", {"style": "fenced"})

        return config


def find_config_file(start_path: Optional[str] = None) -> Optional[str]:
    """Find configuration file in current or parent directories"""
    if start_path is None:
        start_path = os.getcwd()

    current_path = Path(start_path)

    # Look for .compose-lint.toml in current and parent directories
    for path in [current_path] + list(current_path.parents):
        config_file = path / ".compose-lint.toml"
        if config_file.exists():
            return str(config_file)

    return None


def find_project_config_with_lint(start_path: Optional[str] = None) -> Optional[str]:
    """Find a project TOML file that contains a [lint] section.

    Scans current directory for *.toml and returns the first with a [lint] table.
    """
    if start_path is None:
        start_path = os.getcwd()
    base = Path(start_path)

    try:
        try:
            import tomllib  # Python 3.11+
        except ImportError:  # pragma: no cover
            tomllib = None

        if tomllib is None:
            return None

        for candidate in base.glob('*.toml'):
            try:
                with open(candidate, 'rb') as f:
                    data = tomllib.load(f)
                if isinstance(data, dict) and 'lint' in data:
                    return str(candidate)
            except Exception:
                continue
    except Exception:
        return None

    return None
