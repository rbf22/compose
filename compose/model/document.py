# compose/model/document.py
class Node:
    def __init__(self, type, text=None, level=None):
        self.type = type
        self.text = text
        self.level = level
        self.children = []

    def __repr__(self):
        return f"<Node {self.type} '{self.text or ''}'>"
