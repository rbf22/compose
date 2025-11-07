# compose/linter.py
import re

def lint_markdown(content: str) -> list[str]:
    """Lint markdown content and return a list of issues"""
    issues = []
    lines = content.split('\n')

    # Track headings for hierarchy checking
    heading_levels = []

    for i, line in enumerate(lines, 1):
        # Check for trailing whitespace
        if line.rstrip() != line:
            issues.append(f"Line {i}: Trailing whitespace")

        # Check for lines longer than 100 characters (configurable)
        if len(line) > 100:
            issues.append(f"Line {i}: Line too long ({len(line)} characters)")

        # Check for headings without proper spacing
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            heading_levels.append(level)

            if i > 1 and lines[i-2].strip():  # Previous line should be empty
                issues.append(f"Line {i}: Heading should be preceded by empty line")

            # Check heading hierarchy (shouldn't skip levels)
            if len(heading_levels) > 1:
                prev_level = heading_levels[-2]
                if level > prev_level + 1:
                    issues.append(f"Line {i}: Heading hierarchy violation (skipped level)")

        # Check for inconsistent list markers in consecutive lines
        if re.match(r'^[-*]\s', line):
            # Look ahead to check for mixed list types
            if i < len(lines) - 1:
                next_line = lines[i]
                if re.match(r'^[-*]\s', next_line):
                    current_marker = line[0]
                    next_marker = next_line[0]
                    if current_marker != next_marker:
                        issues.append(f"Line {i}: Mixed list markers (use consistent - or *)")

        # Check for empty list items
        if re.match(r'^[-*]\s*$', line):
            issues.append(f"Line {i}: Empty list item")

        # Check for broken image references (missing alt text)
        if re.search(r'!\[\]\([^)]+\)', line):
            issues.append(f"Line {i}: Image missing alt text")

        # Check for broken links (empty link text)
        if re.search(r'\[\]\([^)]+\)', line):
            issues.append(f"Line {i}: Link missing text")

        # Check for unbalanced brackets in links/images
        bracket_count = line.count('[') - line.count(']')
        if bracket_count != 0:
            issues.append(f"Line {i}: Unbalanced brackets")

        paren_count = line.count('(') - line.count(')')
        if paren_count != 0:
            issues.append(f"Line {i}: Unbalanced parentheses")

        # Check for code blocks without language specification
        if line.strip() == '```' and i < len(lines) - 1:
            next_line = lines[i]
            if not next_line.strip() or next_line.strip().startswith('```'):
                issues.append(f"Line {i}: Code block without language specification")

    # Check for broken table formatting
    table_issues = _lint_tables(content)
    issues.extend(table_issues)

    return issues

def _lint_tables(content: str) -> list[str]:
    """Check for table formatting issues"""
    issues = []
    lines = content.split('\n')

    in_table = False
    table_start = 0

    for i, line in enumerate(lines, 1):
        if '|' in line and not in_table:
            # Potential table start
            if i < len(lines) - 1 and '|' in lines[i]:
                in_table = True
                table_start = i
        elif in_table and line.strip() == '':
            # Table ended
            table_lines = lines[table_start-1:i]
            if len(table_lines) >= 2:
                # Check if second line is a separator
                separator_line = table_lines[1] if len(table_lines) > 1 else ""
                if not re.match(r'^\s*\|[\s\-\|:]+\|\s*$', separator_line):
                    issues.append(f"Line {table_start + 1}: Invalid table separator")
            in_table = False

    return issues

def lint_file(file_path: str) -> list[str]:
    """Lint a markdown file and return issues"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return lint_markdown(content)
    except FileNotFoundError:
        return [f"File not found: {file_path}"]
    except Exception as e:
        return [f"Error reading file: {e}"]
