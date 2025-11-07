# compose/engine.py
import json
from .parser.ast_parser import MarkdownParser
from .parser.config import parse_config
from .render.ast_renderer import HTMLRenderer, TextRenderer
from .render.math_images import HTMLMathProcessor
from .render.pdf_renderer import PDFRenderer

def build(md_path, cfg_path):
    config = parse_config(cfg_path)
    
    # Parse markdown using new AST parser
    parser = MarkdownParser()
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    doc = parser.parse(content)
    
    # Merge frontmatter with config
    if doc.frontmatter:
        config = _deep_merge_frontmatter(config, doc.frontmatter)

    mode = config.get('mode', 'document')
    output = config.get('output', 'text')

    # Handle slides mode (placeholder for now)
    if mode == 'slides':
        # For now, use text renderer for slides
        renderer = TextRenderer()
        result = renderer.render(doc, config)
        print(result)
        return

    # Handle document modes
    if output == 'pdf':
        renderer = PDFRenderer()
        pdf_data = renderer.render(doc, config)
        print(f"Generated {len(pdf_data)} bytes of PDF data")
        print(f"First 20 bytes: {pdf_data[:20]}")
        
        # Write to temporary file first
        temp_file = 'output.pdf.tmp'
        with open(temp_file, 'wb') as f:
            f.write(pdf_data)
        
        # Rename to final file
        import os
        os.rename(temp_file, 'output.pdf')
        print("PDF output written to output.pdf")
    elif output == 'html':
        renderer = HTMLRenderer()
        html_content = renderer.render(doc, config)

        # Process math expressions into images
        math_processor = HTMLMathProcessor()
        html_content = math_processor.process_html(html_content)

        with open('output.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("HTML output written to output.html")
    elif output == 'json':
        # Output the AST as JSON
        ast_dict = {
            'frontmatter': doc.frontmatter,
            'blocks': [{'type': type(block).__name__, **vars(block)} for block in doc.blocks]
        }
        with open('output.json', 'w', encoding='utf-8') as f:
            json.dump(ast_dict, f, indent=2, default=str)
        print("JSON AST written to output.json")
    elif output == 'plain':
        # Plain text without markdown formatting
        renderer = TextRenderer()
        plain_content = renderer.render(doc, config)
        # Simple plain text extraction (remove markdown syntax)
        import re
        plain_content = re.sub(r'\*\*(.*?)\*\*', r'\1', plain_content)  # Remove bold
        plain_content = re.sub(r'\*(.*?)\*', r'\1', plain_content)      # Remove italic
        plain_content = re.sub(r'~~(.*?)~~', r'\1', plain_content)     # Remove strikethrough
        plain_content = re.sub(r'`([^`]*)`', r'\1', plain_content)      # Remove inline code
        with open('output.txt', 'w', encoding='utf-8') as f:
            f.write(plain_content)
        print("Plain text written to output.txt")
    else:
        renderer = TextRenderer()
        print(renderer.render(doc, config))

def _deep_merge_frontmatter(config: dict, frontmatter: dict) -> dict:
    """Merge frontmatter into config, with frontmatter taking precedence for document settings"""
    result = config.copy()

    # Frontmatter fields that should override config
    override_fields = ['title', 'author', 'date', 'description', 'mode']

    for key, value in frontmatter.items():
        if key in override_fields or key not in result:
            result[key] = value
        elif isinstance(result.get(key), dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)

    return result

def render_json(nodes):
    """Render nodes to JSON AST representation"""
    def node_to_dict(node):
        if hasattr(node, 'type'):
            result = {
                'type': node.type,
                'text': node.text if hasattr(node, 'text') else None,
            }
            # Add optional attributes
            for attr in ['level', 'language', 'checked', 'rows', 'headers']:
                if hasattr(node, attr) and getattr(node, attr) is not None:
                    result[attr] = getattr(node, attr)
            # Add children recursively
            if hasattr(node, 'children') and node.children:
                result['children'] = [node_to_dict(child) for child in node.children]
            return result
        else:
            return str(node)

    return json.dumps([node_to_dict(node) for node in nodes], indent=2, ensure_ascii=False)

def render_plain(nodes):
    """Render nodes to plain text (no markdown formatting)"""
    output = []

    def extract_text(node):
        if hasattr(node, 'type'):
            if node.type in ['text', 'code_inline']:
                return node.text or ''
            elif hasattr(node, 'children') and node.children:
                return ''.join(extract_text(child) for child in node.children)
            elif hasattr(node, 'text'):
                return node.text or ''
        return str(node)

    for node in nodes:
        if node.type == 'heading':
            output.append(f"{extract_text(node.text)}\n")
        elif node.type == 'paragraph':
            output.append(f"{extract_text(node.text)}\n\n")
        elif node.type == 'list_item':
            output.append(f"• {extract_text(node.text)}\n")
        elif node.type == 'task_item':
            checkbox = '[x]' if node.checked else '[ ]'
            output.append(f"{checkbox} {extract_text(node.text)}\n")
        elif node.type == 'code_block':
            output.append(f"{node.text}\n\n")
        elif node.type == 'blockquote':
            lines = extract_text(node.text).split('\n')
            for line in lines:
                if line.strip():
                    output.append(f"{line}\n")
            output.append('\n')
        elif node.type == 'table':
            if node.headers:
                output.append(' | '.join(node.headers) + '\n')
            for row in node.rows:
                output.append(' | '.join(row) + '\n')
            output.append('\n')
        elif node.type in ['hr', 'mermaid_diagram', 'math_block']:
            output.append('\n')

    return ''.join(output)
