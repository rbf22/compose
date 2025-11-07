# compose/parser/markdown.py
from ..model.document import Node

def parse_markdown(path: str) -> list[Node]:
    nodes = []
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            text = line[level:].strip()
            nodes.append(Node('heading', text=text, level=level))
        elif line.startswith('- '):
            nodes.append(Node('list_item', text=line[2:].strip()))
        elif line.strip() == '---':
            nodes.append(Node('hr'))
        elif line.strip():
            nodes.append(Node('paragraph', text=line.strip()))

    return nodes
