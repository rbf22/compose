# compose/render/text.py
def render_text(nodes, config):
    output = []
    for n in nodes:
        if n.type == 'heading':
            output.append(f"{'#' * n.level} {n.text}\n")
        elif n.type == 'paragraph':
            output.append(f"{n.text}\n\n")
        elif n.type == 'list_item':
            output.append(f"• {n.text}\n")
        elif n.type == 'hr':
            output.append('-' * 40 + '\n')
    return ''.join(output)
