# plugin_highlight.py
"""Syntax highlighting plugin for Compose"""

from compose.plugin_system import TransformerPlugin

class HighlightTransformer(TransformerPlugin):
    """Plugin that adds syntax highlighting to code blocks"""

    @property
    def name(self) -> str:
        return "highlight"

    @property
    def version(self) -> str:
        return "1.0.0"

    def can_transform(self, content_type: str) -> bool:
        return content_type == "code_highlight"

    def transform_content(self, content: str, config: dict) -> str:
        """Add basic syntax highlighting to code"""
        # Simple syntax highlighting for Python
        highlighted = content
        
        # Keywords
        keywords = ['def', 'class', 'if', 'else', 'for', 'while', 'import', 'from', 'return']
        for keyword in keywords:
            highlighted = highlighted.replace(keyword, f'<span class="keyword">{keyword}</span>')
        
        # Strings
        import re
        highlighted = re.sub(r'(".*?")', r'<span class="string">\1</span>', highlighted)
        highlighted = re.sub(r"('.*?')", r'<span class="string">\1</span>', highlighted)
        
        # Comments
        highlighted = re.sub(r'(#.*?)$', r'<span class="comment">\1</span>', highlighted, flags=re.MULTILINE)
        
        return f'<pre class="highlighted-code"><code>{highlighted}</code></pre>'
