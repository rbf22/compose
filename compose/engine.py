# compose/engine.py
from .parser.markdown import parse_markdown
from .parser.config import parse_config
from .render.text import render_text
from .render.pdf import render_pdf

def build(md_path, cfg_path):
    config = parse_config(cfg_path)
    nodes = parse_markdown(md_path)
    mode = config.get('mode', 'document')
    output = config.get('output', 'text')

    if output == 'pdf':
        render_pdf(nodes, config, 'output.pdf')
    else:
        print(render_text(nodes, config))
