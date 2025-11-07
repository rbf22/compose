# compose/parser/markdown.py
from ..model.document import Node

try:
    from . import _tokenizer
    USE_C = True
except ImportError:
    USE_C = False

def parse_markdown(path: str) -> list[Node]:
    if USE_C:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        tokens = _tokenizer.tokenize(text)
        nodes = []
        for token in tokens:
            if isinstance(token, str):
                if token == "HR":
                    nodes.append(Node('hr'))
            elif isinstance(token, tuple):
                ttype = token[0]
                if ttype == "HEADING":
                    nodes.append(Node('heading', text=token[2], level=token[1]))
                elif ttype == "LIST_ITEM":
                    nodes.append(Node('list_item', text=token[1]))
                elif ttype == "PARAGRAPH":
                    nodes.append(Node('paragraph', text=token[1]))
        return nodes
    else:
        # Fallback to pure Python
        nodes = []
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            line = line.rstrip('\n')
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                text = line[level:].strip()
                nodes.append(Node('heading', text=text, level=level))
            elif line.startswith('- '):
                nodes.append(Node('list_item', text=line[2:]))
            elif line.strip() == '---':
                nodes.append(Node('hr'))
            elif line.strip():
                nodes.append(Node('paragraph', text=line.strip()))

        return nodes
