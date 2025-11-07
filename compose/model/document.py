# compose/model/document.py
class Node:
    def __init__(self, type, text=None, level=None, language=None, rows=None, headers=None, checked=None):
        self.type = type
        self.text = text
        self.level = level
        self.language = language  # for code blocks
        self.rows = rows  # for tables
        self.headers = headers  # for tables
        self.checked = checked  # for task list items
        self.children = []  # for inline formatting and nested content

    def __repr__(self):
        if self.type == 'code_block':
            return f"<Node {self.type} lang='{self.language or ''}' '{self.text[:20] if self.text else ''}...'>"
        elif self.type == 'table':
            return f"<Node {self.type} {len(self.rows) if self.rows else 0} rows>"
        elif self.type == 'text':
            return f"<Node {self.type} '{self.text[:20] if self.text else ''}...'>"
        else:
            return f"<Node {self.type} '{self.text or ''}'>"

    def add_child(self, child):
        """Add a child node for inline formatting"""
        self.children.append(child)

    def is_inline(self):
        """Check if this node represents inline formatting"""
        return self.type in ['bold', 'italic', 'strikethrough', 'code_inline', 'text']
