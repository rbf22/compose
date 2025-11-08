# compose/engine.py
import json
from typing import List, Dict, Any
from .parser.ast_parser import MarkdownParser
from .parser.config import parse_config, _deep_merge
from .plugin_system import initialize_plugin_system
from .plugin_system import plugin_manager
from .render.ast_renderer import HTMLRenderer, TextRenderer
from .render.html_parser import HTMLMathProcessor
from .render.slide_renderer import SlideRenderer
from .render.pdf_renderer import PDFRenderer
from .macro_system import macro_processor, expand_macros
from .microtypography import microtypography_engine
from .tex_compatibility import tex_compatibility_engine
from .render.typography_engine import TypographyEngine
from .render.multi_page import MultiPageRenderer
from .render.cross_references import CrossReferenceProcessor, TableOfContentsGenerator
from .analysis.document_analyzer import DocumentAnalyzer

def build(md_path, cfg_path):
    config = parse_config(cfg_path)
    
    # Initialize plugin system
    initialize_plugin_system(config)
    
    # Parse markdown using new AST parser
    parser = MarkdownParser()
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Process macros if enabled
    if config.get('features', {}).get('macros', True):
        macro_expansion = expand_macros(content)
        content = macro_expansion.expanded
        if macro_expansion.macros_used:
            print(f"Expanded macros: {', '.join(macro_expansion.macros_used)}")

    doc = parser.parse(content)
    
    # Analyze document structure and relationships
    analyzer = DocumentAnalyzer(doc)
    enhanced_doc = analyzer.analyze()

    # Process cross-references if enabled
    if config.get('features', {}).get('cross_references', True):
        xref_processor = CrossReferenceProcessor()
        doc = xref_processor.process_document(doc)

    # Apply advanced typography if enabled
    typography_preset = config.get('typography', {}).get('preset')
    if typography_preset or config.get('features', {}).get('advanced_typography', True):
        typography_engine = TypographyEngine()
        doc = typography_engine.apply_typography(doc, typography_preset)

    # Merge frontmatter with config
    if doc.frontmatter:
        config = _deep_merge_frontmatter(config, doc.frontmatter)

    mode = config.get('mode', 'document')
    output = config.get('output', 'text')
    multi_page = config.get('multi_page', False)

    # Handle slides mode
    if mode == 'slides':
        slide_renderer = SlideRenderer()
        slides_html = slide_renderer.render_slide_deck(doc)
        with open('slides.html', 'w', encoding='utf-8') as f:
            f.write(slides_html)
        print("Interactive slides written to slides.html")
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
        if multi_page:
            # Multi-page HTML rendering
            page_renderer = MultiPageRenderer(
                page_width=config.get('page_width', 800),
                page_height=config.get('page_height', 600),
                margins=config.get('margins', {'top': 50, 'bottom': 50, 'left': 40, 'right': 40})
            )
            pages = page_renderer.render_multi_page(doc, 'html')

            # Combine pages into single HTML document
            full_html = _combine_pages_html(pages, config, analyzer)
            with open('output.html', 'w', encoding='utf-8') as f:
                f.write(full_html)
            print(f"Multi-page HTML output written to output.html ({len(pages)} pages)")
        else:
            # Single-page HTML rendering
            renderer = HTMLRenderer()
            html_content = renderer.render(doc, config)

            # Process math expressions into images
            math_processor = HTMLMathProcessor()
            html_content = math_processor.process_html(html_content)

            with open('output.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("HTML output written to output.html")
    elif output == 'json':
        # Output the AST as JSON with enhanced structure analysis
        ast_dict = {
            'frontmatter': doc.frontmatter,
            'blocks': [{'type': type(block).__name__, **vars(block)} for block in doc.blocks],
            'structure': {
                'headings_by_level': {level: [{'text': analyzer._extract_text_from_inline(h.content), 'id': analyzer.structure._generate_heading_id(h, doc.blocks.index(h))} for h in headings] for level, headings in analyzer.structure.headings_by_level.items()},
                'references': list(analyzer.structure.references.keys()),
                'table_of_contents': analyzer.structure.get_table_of_contents(),
                'validation_warnings': analyzer.validate_document_structure()
            }
        }
        with open('output.json', 'w', encoding='utf-8') as f:
            json.dump(ast_dict, f, indent=2, default=str)
        print("JSON AST with structure analysis written to output.json")
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


def _combine_pages_html(pages: List[Dict[str, Any]], config: Dict[str, Any], analyzer: DocumentAnalyzer) -> str:
    """
    Combine multiple pages into a single HTML document with navigation.
    """
    # Generate table of contents
    toc_generator = TableOfContentsGenerator()
    toc_html = toc_generator.render_toc_html(analyzer.structure.get_table_of_contents())

    # Combine all pages
    pages_html = '\n'.join(page['content'] for page in pages)

    # Add navigation and TOC
    full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config.get('title', 'Document')}</title>
    <style>
        body {{
            font-family: 'Times New Roman', serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .page {{
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .toc-container {{
            position: fixed;
            top: 20px;
            right: 20px;
            width: 250px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            max-height: 80vh;
            overflow-y: auto;
        }}
        .toc-container ul {{
            list-style: none;
            padding-left: 0;
        }}
        .toc-container li {{
            margin: 5px 0;
        }}
        .toc-container a {{
            color: #0066cc;
            text-decoration: none;
        }}
        .toc-container a:hover {{
            text-decoration: underline;
        }}
        @media print {{
            .toc-container {{
                display: none;
            }}
            .page {{
                box-shadow: none;
                margin-bottom: 0;
                page-break-after: always;
            }}
        }}
    </style>
</head>
<body>
    <div class="toc-container">
        {toc_html}
    </div>

    <div class="document-content">
        {pages_html}
    </div>

    <script>
        // Add page navigation
        document.addEventListener('DOMContentLoaded', function() {{
            const pages = document.querySelectorAll('.page');
            let currentPage = 0;

            function updateNavigation() {{
                pages.forEach((page, index) => {{
                    if (index === currentPage) {{
                        page.style.display = 'block';
                    }} else {{
                        page.style.display = 'none';
                    }}
                }});
            }}

            // Keyboard navigation
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'ArrowRight' && currentPage < pages.length - 1) {{
                    currentPage++;
                    updateNavigation();
                }} else if (e.key === 'ArrowLeft' && currentPage > 0) {{
                    currentPage--;
                    updateNavigation();
                }}
            }});

            updateNavigation();
        }});
    </script>
</body>
</html>'''

    return full_html
