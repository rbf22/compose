# compose/render/slides.py

def render_slides(nodes, config):
    """Render nodes in slides mode - simple text-based slides"""
    slides = []
    current_slide = []

    for node in nodes:
        if node.type == 'heading' and node.level == 1:
            # New slide
            if current_slide:
                slides.append(current_slide)
            current_slide = [node]
        else:
            current_slide.append(node)

    if current_slide:
        slides.append(current_slide)

    # Render slides
    output = []
    for i, slide in enumerate(slides, 1):
        output.append(f"\n{'='*50}")
        output.append(f"Slide {i}")
        output.append('='*50)

        for node in slide:
            if node.type == 'heading':
                output.append(f"\n{node.text}\n")
            elif node.type == 'paragraph':
                output.append(f"{node.text}\n\n")
            elif node.type == 'list_item':
                output.append(f"• {node.text}\n")
            elif node.type == 'code_block':
                output.append("```\n")
                output.append(f"{node.text}\n")
                output.append("```\n\n")
            elif node.type == 'table':
                # Simple table rendering for slides
                if node.headers:
                    output.append('| ' + ' | '.join(node.headers) + ' |\n')
                    output.append('| ' + ' | '.join('-' * len(h) for h in node.headers) + ' |\n')
                for row in node.rows:
                    output.append('| ' + ' | '.join(row) + ' |\n')
                output.append('\n')
            elif node.type == 'hr':
                output.append('-'*30 + '\n')

    return ''.join(output)
