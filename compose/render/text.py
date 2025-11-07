# compose/render/text.py

def render_text(nodes, config):
    output = []
    for n in nodes:
        if n.type == 'heading':
            output.append(f"{'#' * n.level} {_render_inline(n.text)}\n")
        elif n.type == 'paragraph':
            output.append(f"{_render_inline(n.text)}\n\n")
        elif n.type == 'list_item':
            output.append(f"• {_render_inline(n.text)}\n")
        elif n.type == 'task_item':
            checkbox = '[x]' if n.checked else '[ ]'
            output.append(f"{checkbox} {_render_inline(n.text)}\n")
        elif n.type == 'hr':
            output.append('-' * 40 + '\n')
        elif n.type == 'code_block':
            _render_code_block(output, n)
        elif n.type == 'table':
            _render_table(output, n)
        elif n.type == 'math_block':
            _render_math_block(output, n)
        elif n.type == 'blockquote':
            _render_blockquote(output, n)
        elif n.type == 'mermaid_diagram':
            _render_mermaid_diagram(output, n)
    return ''.join(output)

def _render_inline(node):
    """Render inline formatted text"""
    if isinstance(node, str):
        return node
    elif hasattr(node, 'children') and node.children:
        parts = []
        for child in node.children:
            if child.type == 'text':
                parts.append(child.text)
            elif child.type == 'bold':
                parts.append(f"**{child.text}**")
            elif child.type == 'italic':
                parts.append(f"*{child.text}*")
            elif child.type == 'strikethrough':
                parts.append(f"~~{child.text}~~")
            elif child.type == 'bold_italic':
                parts.append(f"***{child.text}***")
            elif child.type == 'code_inline':
                parts.append(f"`{child.text}`")
            elif child.type == 'math_inline':
                # Remove $ delimiters for cleaner display
                math_content = child.text.strip('$')
                parts.append(f"[{math_content}]")
            elif child.type == 'image':
                parts.append(f"[Image: {child.text}]")
            elif child.type == 'link':
                parts.append(f"[{child.text}]")
            else:
                parts.append(str(child))
        return ''.join(parts)
    else:
        return str(node)

def _render_code_block(output, node):
    """Render a code block"""
    output.append("```\n")
    if node.language:
        output.append(f"{node.language}\n")
    output.append(f"{node.text}\n")
    output.append("```\n\n")

def _render_table(output, node):
    """Render a table in text format"""
    if not node.headers and not node.rows:
        return

    # Calculate column widths
    all_rows = [node.headers] + node.rows if node.headers else node.rows
    col_widths = []

    for col_idx in range(len(all_rows[0])):
        max_width = 0
        for row in all_rows:
            if col_idx < len(row):
                cell_text = _render_inline(row[col_idx])
                max_width = max(max_width, len(cell_text))
        col_widths.append(max_width)

    # Render header
    if node.headers:
        output.append('| ' + ' | '.join(_render_inline(header).ljust(col_widths[i]) for i, header in enumerate(node.headers)) + ' |\n')
        output.append('| ' + ' | '.join('-' * col_widths[i] for i in range(len(node.headers))) + ' |\n')

    # Render rows
    for row in node.rows:
        output.append('| ' + ' | '.join(_render_inline(cell).ljust(col_widths[i]) if i < len(col_widths) else _render_inline(cell)
                                       for i, cell in enumerate(row)) + ' |\n')

    output.append('\n')

def _render_math_block(output, node):
    """Render a math block with improved formatting"""
    # Remove $$ delimiters and clean up
    math_content = node.text.strip()
    if math_content.startswith('$$') and math_content.endswith('$$'):
        math_content = math_content[2:-2].strip()
    elif math_content.startswith('$') and math_content.endswith('$'):
        math_content = math_content[1:-1].strip()

    output.append("┌─ Math Block ─┐\n")
    for line in math_content.split('\n'):
        if line.strip():
            output.append(f"│ {line} │\n")
    output.append("└─────────────┘\n\n")

def _render_blockquote(output, node):
    """Render a blockquote, handling nested content"""
    if hasattr(node.text, 'type') and node.text.type == 'blockquote':
        # Nested blockquote - render with extra > markers
        inner_lines = []
        _render_nested_blockquote(inner_lines, node.text, 1)
        output.extend(inner_lines)
        output.append('\n')
    else:
        # Regular blockquote content
        lines = _render_inline(node.text).split('\n')
        for line in lines:
            if line.strip():
                output.append(f"> {line}\n")
            else:
                output.append(">\n")
        output.append('\n')

def _render_nested_blockquote(output, node, depth):
    """Render nested blockquotes with appropriate markers"""
    marker = '>' * (depth + 1)  # > for depth 1, >> for depth 2, etc.

    if hasattr(node.text, 'type') and node.text.type == 'blockquote':
        # Another level of nesting
        _render_nested_blockquote(output, node.text, depth + 1)
    else:
        # Content at this level
        lines = _render_inline(node.text).split('\n')
        for line in lines:
            if line.strip():
                output.append(f"{marker} {line}\n")
            else:
                output.append(f"{marker}\n")

def _render_mermaid_diagram(output, node):
    """Render a Mermaid diagram (ASCII art)"""
    output.append("Mermaid Diagram:\n")
    output.append(f"{node.text}\n\n")
