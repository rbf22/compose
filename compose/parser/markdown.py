# compose/parser/markdown.py
import re
from ..model.document import Node

try:
    from . import _tokenizer
    USE_C = True
except ImportError:
    USE_C = False

def parse_markdown(path: str) -> tuple[list[Node], dict]:
    """Parse markdown file and return nodes and frontmatter metadata"""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract frontmatter if present
    frontmatter, content = _extract_frontmatter(content)

    if USE_C:
        nodes = _parse_markdown_c(content)
    else:
        nodes = _parse_markdown_py(content)

    return nodes, frontmatter

def _extract_frontmatter(content: str) -> tuple[dict, str]:
    """Extract TOML frontmatter from markdown content"""
    lines = content.split('\n')
    frontmatter = {}

    # Check for frontmatter (starts and ends with +++ for TOML)
    if len(lines) >= 3 and lines[0].strip() == '+++':
        # Find the closing +++
        end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == '+++':
                end_idx = i
                break

        if end_idx > 0:
            # Parse the frontmatter content
            frontmatter_lines = lines[1:end_idx]
            frontmatter_content = '\n'.join(frontmatter_lines)
            frontmatter = _parse_toml_simple(frontmatter_content)

            # Remove frontmatter from content
            content = '\n'.join(lines[end_idx + 1:])

    return frontmatter, content

def _parse_toml_simple(content: str) -> dict:
    """Simple TOML parser for basic key-value pairs (no dependencies)"""
    result = {}
    lines = content.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            # Remove quotes if present
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]

            # Try to convert to appropriate type
            if value.lower() in ('true', 'false'):
                value = value.lower() == 'true'
            elif value.isdigit():
                value = int(value)
            elif value.replace('.', '').isdigit() and '.' in value:
                value = float(value)

            result[key] = value

    return result

def _parse_markdown_py(content: str) -> list[Node]:
    """Pure Python Markdown parser"""
    nodes = []
    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        # Code blocks (fenced)
        if line.startswith('```'):
            code_block, i = _parse_code_block(lines, i)
            nodes.append(code_block)
            continue

        # Block math ($$...$$)
        if line.strip().startswith('$$'):
            math_block, i = _parse_math_block(lines, i)
            nodes.append(math_block)
            continue

        # Mermaid diagrams
        if line.strip() == '```mermaid':
            mermaid_block, i = _parse_mermaid_block(lines, i)
            nodes.append(mermaid_block)
            continue

        # Blockquotes (> text)
        if line.strip().startswith('>'):
            blockquote, i = _parse_blockquote(lines, i)
            nodes.append(blockquote)
            continue

        # Tables
        if _is_table_row(line) and i + 1 < len(lines) and _is_table_separator(lines[i + 1]):
            table, i = _parse_table(lines, i)
            nodes.append(table)
            continue

        # Headings
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            text = line[level:].strip()
            if text:
                node = Node('heading', text=_parse_inline(text), level=level)
                nodes.append(node)
            i += 1
            continue

        # Lists
        if line.startswith('- ') or line.startswith('* '):
            list_items, i = _parse_list(lines, i)
            nodes.extend(list_items)
            continue

        # Horizontal rule
        if line.strip() in ['---', '***', '___']:
            nodes.append(Node('hr'))
            i += 1
            continue

        # Paragraphs (collect consecutive non-empty lines)
        if line.strip():
            paragraph_lines = []
            while i < len(lines) and lines[i].strip():
                paragraph_lines.append(lines[i])
                i += 1

            if paragraph_lines:
                text = ' '.join(paragraph_lines)
                node = Node('paragraph', text=_parse_inline(text))
                nodes.append(node)
            continue

        i += 1

    return nodes

def _parse_inline(text: str) -> Node:
    """Parse inline formatting within text - now with proper bold/italic support"""
    # Create a root paragraph node to hold inline elements
    root = Node('paragraph')

    # Apply smart typography first
    text = _apply_smart_typography(text)

    # Handle bold and italic first (can contain code)
    text = _parse_bold_italic(text, root)

    # Handle inline code (within formatted text)
    text = _parse_inline_code(text, root)

    # Handle inline math
    text = _parse_inline_math(text, root)

    # Handle image references
    text = _parse_images(text, root)

    # Add remaining plain text
    if text.strip():
        root.add_child(Node('text', text=text.strip()))

    return root

def _apply_smart_typography(text: str) -> str:
    """Apply smart typography transformations"""
    # Smart quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace("'", "'").replace("'", "'")

    # Smart dashes
    text = text.replace('--', '–')  # en dash
    text = text.replace('---', '—')  # em dash

    # Smart ellipses
    text = text.replace('...', '…')

    return text

def _parse_inline_code(text: str, root: Node) -> str:
    """Parse inline code (`code`) and return remaining text"""
    while '`' in text:
        start = text.find('`')
        if start == -1:
            break

        # Add text before backtick
        if start > 0:
            root.add_child(Node('text', text=text[:start]))

        # Find closing backtick
        end = text.find('`', start + 1)
        if end == -1:
            # Unclosed backtick, treat as regular text
            root.add_child(Node('text', text=text[start:]))
            return ""

        # Extract code content
        code_content = text[start + 1:end]
        root.add_child(Node('code_inline', text=code_content))

        # Continue with remaining text
        text = text[end + 1:]

    return text

def _parse_bold_italic(text: str, root: Node) -> str:
    """Parse bold (**text**), italic (*text*), and strikethrough (~~text~~) formatting"""
    # Use regex to find bold, italic, and strikethrough patterns
    # Order matters: check longer patterns first
    patterns = [
        (r'~~([^*~]+)~~', 'strikethrough'),  # ~~strikethrough~~
        (r'\*\*\*([^*]+)\*\*\*', 'bold_italic'),  # ***both***
        (r'\*\*([^*]+)\*\*', 'bold'),           # **bold**
        (r'\*([^*]+)\*', 'italic'),             # *italic*
    ]

    for pattern, node_type in patterns:
        match = re.search(pattern, text)
        if match:
            # Add text before the match
            if match.start() > 0:
                root.add_child(Node('text', text=text[:match.start()]))

            # Parse the inner content recursively for nested formatting
            content = match.group(1)
            inner_node = _parse_inline(content)
            
            # Create the formatted node with children
            formatted_node = Node(node_type, children=inner_node.children)
            root.add_child(formatted_node)

            # Continue with remaining text
            remaining = text[match.end():]
            if remaining:
                remaining = _parse_bold_italic(remaining, root)

            return ""  # We've consumed all text

    return text

def _parse_inline_math(text: str, root: Node) -> str:
    """Parse inline math ($math$) with basic ASCII rendering"""
    while '$' in text:
        start = text.find('$')
        if start == -1:
            break

        # Add text before dollar sign
        if start > 0:
            root.add_child(Node('text', text=text[:start]))

        # Find closing dollar sign (but not $$)
        end = text.find('$', start + 1)
        if end == -1 or text[end:end+2] == '$$':
            # No closing $ or it's actually $$, skip
            root.add_child(Node('text', text=text[start]))
            text = text[start + 1:]
            continue

        # Extract math content
        math_content = text[start + 1:end]

        # Try basic ASCII rendering for simple expressions
        ascii_math = _render_simple_math_ascii(math_content)
        if ascii_math != math_content:
            # Use ASCII rendering
            root.add_child(Node('math_inline', text=ascii_math))
        else:
            # Keep original LaTeX
            root.add_child(Node('math_inline', text=math_content))

        # Continue with remaining text
        text = text[end + 1:]

    return text

def _render_simple_math_ascii(math_expr: str) -> str:
    """Render simple math expressions to ASCII art"""
    expr = math_expr.strip()

    # Simple fraction rendering: a/b -> a/b
    if '/' in expr and len(expr.split('/')) == 2:
        num, den = expr.split('/')
        if len(num) <= 3 and len(den) <= 3:
            return f"{num}/{den}"

    # Simple square root: sqrt(x) -> √x
    sqrt_match = re.match(r'sqrt\(([^)]+)\)', expr)
    if sqrt_match:
        content = sqrt_match.group(1)
        if len(content) <= 5:
            return f"√{content}"

    # Simple superscripts: x^2 -> x², x^3 -> x³
    if '^' in expr:
        base, exp = expr.split('^', 1)
        if exp in ['2', '3', 'n', '0', '1']:
            superscripts = {'2': '²', '3': '³', 'n': 'ⁿ', '0': '⁰', '1': '¹'}
            return f"{base}{superscripts[exp]}"

    # Simple integrals: int -> ∫
    if expr.startswith('int'):
        return f"∫ {expr[3:].strip()}"

    # Simple infinity: infty -> ∞
    if 'infty' in expr:
        return expr.replace('infty', '∞')

    # Return original if no simple rendering available
    return math_expr

def _parse_images(text: str, root: Node) -> str:
    """Parse image references ![alt](path "caption") and links [text](url)"""
    # Simple regex for image syntax
    import re

    # Check for images first (higher priority)
    image_pattern = r'!\[([^\]]*)\]\(([^)"\s]+)(?:\s*"([^"]*)")?\)'
    image_match = re.search(image_pattern, text)
    if image_match:
        # Add text before image
        if image_match.start() > 0:
            root.add_child(Node('text', text=text[:image_match.start()]))

        alt_text = image_match.group(1)
        path = image_match.group(2)
        caption = image_match.group(3) if image_match.group(3) else ""

        root.add_child(Node('image', text=path, level=0))  # Using level for caption if needed

        # Continue with remaining text
        remaining = text[image_match.end():]
        if remaining:
            remaining = _parse_images(remaining, root)

        return ""

    # Check for links
    link_pattern = r'\[([^\]]+)\]\(([^)"\s]+)(?:\s*"([^"]*)")?\)'
    link_match = re.search(link_pattern, text)
    if link_match:
        # Add text before link
        if link_match.start() > 0:
            root.add_child(Node('text', text=text[:link_match.start()]))

        link_text = link_match.group(1)
        url = link_match.group(2)
        title = link_match.group(3) if link_match.group(3) else ""

        root.add_child(Node('link', text=url))  # Store URL in text, link text as child
        # For now, we'll just store the URL - proper link handling would need the link text

        # Continue with remaining text
        remaining = text[link_match.end():]
        if remaining:
            remaining = _parse_images(remaining, root)

        return ""

    return text

def _parse_code_block(lines: list[str], start_idx: int) -> tuple[Node, int]:
    """Parse fenced code block"""
    # First line is ```
    fence = lines[start_idx]
    language = fence[3:].strip() if len(fence) > 3 else None
    i = start_idx + 1

    code_lines = []
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('```'):
            break
        code_lines.append(line)
        i += 1

    code_text = '\n'.join(code_lines)
    node = Node('code_block', text=code_text, language=language)
    return node, i + 1

def _parse_table(lines: list[str], start_idx: int) -> tuple[Node, int]:
    """Parse Markdown table"""
    headers = _parse_table_row(lines[start_idx])
    separator = lines[start_idx + 1]
    i = start_idx + 2

    rows = []
    while i < len(lines) and _is_table_row(lines[i]):
        rows.append(_parse_table_row(lines[i]))
        i += 1

    node = Node('table', headers=headers, rows=rows)
    return node, i

def _parse_table_row(line: str) -> list[Node]:
    """Parse a single table row with inline formatting support"""
    # Split by | and strip whitespace
    raw_cells = [cell.strip() for cell in line.split('|')[1:-1]]
    # Apply inline parsing to each cell
    parsed_cells = [_parse_inline(cell) for cell in raw_cells]
    return parsed_cells

def _is_table_row(line: str) -> bool:
    """Check if line is a table row"""
    return '|' in line and line.strip().startswith('|') and line.strip().endswith('|')

def _is_table_separator(line: str) -> bool:
    """Check if line is a table separator (---|---)"""
    if not _is_table_row(line):
        return False

    cells = [cell.strip() for cell in line.split('|')[1:-1]]
    return all(cell.replace('-', '').replace(':', '') == '' for cell in cells)

def _parse_list(lines: list[str], start_idx: int) -> tuple[list[Node], int]:
    """Parse a list (simple implementation) with task list support"""
    items = []
    i = start_idx

    while i < len(lines):
        line = lines[i].rstrip()
        if not (line.startswith('- ') or line.startswith('* ')):
            break

        # Check for task list items: - [ ] or - [x] or - [X]
        task_match = re.match(r'^[-*]\s+\[([ xX])\]\s+(.+)$', line)
        if task_match:
            # Task list item
            checkbox_state = task_match.group(1).lower()
            checked = checkbox_state == 'x'
            text = task_match.group(2).strip()
            node = Node('task_item', text=_parse_inline(text), checked=checked)
        else:
            # Regular list item
            text = line[2:].strip()
            node = Node('list_item', text=_parse_inline(text))

        items.append(node)
        i += 1

    return items, i

def _parse_math_block(lines: list[str], start_idx: int) -> tuple[Node, int]:
    """Parse block math ($$...$$)"""
    # First line should start with $$
    line = lines[start_idx]
    if not line.strip().startswith('$$'):
        return None, start_idx

    i = start_idx
    math_lines = []

    # Check if it's a single-line block math
    if '$$' in line[2:]:
        # Single line: $$math$$
        start = line.find('$$')
        end = line.find('$$', start + 2)
        if end != -1:
            math_content = line[start + 2:end]
            node = Node('math_block', text=math_content)
            return node, i + 1

    # Multi-line block math
    # Remove the opening $$
    first_line = line.strip()[2:].strip()
    if first_line:
        math_lines.append(first_line)
    i += 1

    # Collect lines until closing $$
    while i < len(lines):
        line = lines[i]
        if '$$' in line:
            # Found closing $$
            end_pos = line.find('$$')
            if end_pos > 0:
                math_lines.append(line[:end_pos])
            break
        else:
            math_lines.append(line)
        i += 1

    math_content = '\n'.join(math_lines)
    node = Node('math_block', text=math_content)
    return node, i + 1

def _parse_blockquote(lines: list[str], start_idx: int) -> tuple[Node, int]:
    """Parse blockquotes (> text) with proper nested blockquote support"""
    i = start_idx
    quote_lines = []

    # Determine the minimum blockquote level for this block
    min_level = float('inf')
    for check_i in range(start_idx, len(lines)):
        check_line = lines[check_i].rstrip()
        if not check_line.strip().startswith('>'):
            break
        level = len(check_line) - len(check_line.lstrip('>'))
        min_level = min(min_level, level)

    # Collect all lines at this level and deeper
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip().startswith('>'):
            break

        # Count the blockquote level
        level = len(line) - len(line.lstrip('>'))

        if level >= min_level:
            # Keep the blockquote markers for proper parsing
            quote_lines.append(line)
        else:
            break

        i += 1

    # Now parse the blockquote content with proper nesting
    parsed_content = _parse_blockquote_content(quote_lines)
    node = Node('blockquote', text=parsed_content)
    return node, i

def _parse_blockquote_content(lines: list[str]) -> Node:
    """Parse the content of a blockquote, handling nested blockquotes"""
    if not lines:
        return Node('paragraph')

    # Find all blockquote levels in this content
    content_parts = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if not line.strip().startswith('>'):
            i += 1
            continue

        # Count leading > characters
        level = len(line) - len(line.lstrip('>'))

        if level == 1:
            # This is content at the current level
            # Collect consecutive lines at this level
            current_level_lines = []
            while i < len(lines):
                current_line = lines[i]
                current_level = len(current_line) - len(current_line.lstrip('>')) if current_line.strip().startswith('>') else 0

                if current_level <= 1:  # Current level or regular content
                    if current_level == 1:
                        # Remove one > and add to content
                        content_line = current_line[1:].lstrip()
                        current_level_lines.append(content_line)
                    elif current_line.strip():  # Regular content line
                        current_level_lines.append(current_line)
                    i += 1
                else:
                    # Found deeper nesting, stop here
                    break

            # Parse the collected lines as inline content
            if current_level_lines:
                content_text = '\n'.join(current_level_lines)
                parsed_content = _parse_inline(content_text)
                content_parts.append(parsed_content)

        elif level > 1:
            # This is a nested blockquote
            # Collect all lines at this nesting level
            nested_lines = []
            base_level = level
            while i < len(lines):
                current_line = lines[i]
                current_level = len(current_line) - len(current_line.lstrip('>')) if current_line.strip().startswith('>') else 0

                if current_level >= base_level:
                    nested_lines.append(current_line)
                    i += 1
                else:
                    break

            # Recursively parse the nested blockquote
            nested_content = _parse_blockquote_content(nested_lines)
            content_parts.append(nested_content)

        else:
            i += 1

    # Combine all parts
    if len(content_parts) == 1:
        return content_parts[0]
    elif content_parts:
        # Multiple parts - wrap in a container
        combined = Node('paragraph')
        for part in content_parts:
            if hasattr(combined, 'children'):
                combined.children.append(part)
        return combined
    else:
        return Node('paragraph')

def _parse_mermaid_block(lines: list[str], start_idx: int) -> tuple[Node, int]:
    """Parse Mermaid diagram block and convert to ASCII art"""
    i = start_idx + 1  # Skip the ```mermaid line
    diagram_lines = []

    while i < len(lines):
        line = lines[i].strip()
        if line == '```':
            break
        if line:  # Skip empty lines
            diagram_lines.append(line)
        i += 1

    diagram_text = '\n'.join(diagram_lines)
    ascii_art = _mermaid_to_ascii(diagram_text)

    node = Node('mermaid_diagram', text=ascii_art, diagram_source=diagram_text)
    return node, i + 1

def _mermaid_to_ascii(diagram_text: str) -> str:
    """Convert basic Mermaid syntax to ASCII art (simplified)"""
    lines = diagram_text.strip().split('\n')
    ascii_lines = []

    # Very basic flowchart conversion
    nodes = {}
    connections = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith('graph') or line.startswith('flowchart'):
            continue

        # Simple node definitions: A[Label] or A(Label)
        node_match = re.match(r'(\w+)\[([^\]]+)\]', line) or re.match(r'(\w+)\(([^)]+)\)', line)
        if node_match:
            node_id, label = node_match.groups()
            nodes[node_id] = label
            continue

        # Simple connections: A --> B or A -> B
        conn_match = re.match(r'(\w+)\s*[-=]*>\s*(\w+)', line)
        if conn_match:
            from_node, to_node = conn_match.groups()
            connections.append((from_node, to_node))

    # Generate ASCII art (very basic box diagram)
    if nodes:
        ascii_lines.append("```")
        for node_id, label in nodes.items():
            ascii_lines.append(f"+------------+")
            ascii_lines.append(f"| {label:<10} |")
            ascii_lines.append(f"+------------+")

        for from_node, to_node in connections:
            from_label = nodes.get(from_node, from_node)
            to_label = nodes.get(to_node, to_node)
            ascii_lines.append(f"{from_label} --> {to_label}")

        ascii_lines.append("```")

    return '\n'.join(ascii_lines) if ascii_lines else "```\n[Diagram not supported]\n```"

def _parse_markdown_c(content: str) -> list[Node]:
    """C-accelerated parser (placeholder - would use _tokenizer)"""
    # For now, fall back to Python parser
    # TODO: Integrate C tokenizer results
    return _parse_markdown_py(content)
