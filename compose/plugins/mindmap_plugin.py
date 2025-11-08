# Example Content Plugin: Mind Map Diagrams
"""
Example implementation of a ContentPlugin for mind map diagrams.

This demonstrates how developers can extend Compose with custom content types
that integrate seamlessly with the UniversalBox system.
"""

from typing import Dict, List, Any, Optional
from compose.plugin_system import ContentPlugin
from compose.layout.universal_box import UniversalBox, ContentType, BoxType


class MindMapPlugin(ContentPlugin):
    """
    Plugin for rendering mind map diagrams.

    Supports syntax like:
    ```
    mindmap
    Central Idea
      Branch 1
        Sub-branch 1.1
        Sub-branch 1.2
      Branch 2
        Sub-branch 2.1
    ```
    """

    @property
    def name(self) -> str:
        return "mindmap"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def content_type(self) -> str:
        return "mindmap"

    def can_handle(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Check if content looks like a mind map"""
        lines = content.strip().split('\n')
        if not lines:
            return False

        # Check if it starts with mindmap keyword or has indented structure
        first_line = lines[0].strip().lower()
        if first_line == 'mindmap':
            return True

        # Check for indented structure (at least 3 indented lines)
        indented_lines = [line for line in lines if line.startswith(' ') or line.startswith('\t')]
        return len(indented_lines) >= 3

    def parse_to_box(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> UniversalBox:
        """Parse mind map content into UniversalBox"""
        lines = content.strip().split('\n')

        # Remove 'mindmap' keyword if present
        if lines and lines[0].strip().lower() == 'mindmap':
            lines = lines[1:]

        # Parse hierarchical structure
        nodes = []
        stack = []  # (node, level)

        for line in lines:
            line = line.rstrip()
            if not line:
                continue

            # Count leading spaces/tabs to determine level
            level = 0
            for char in line:
                if char in ' \t':
                    level += 1
                else:
                    break

            # Remove leading whitespace
            text = line[level:].strip()

            # Create node
            node = {
                'text': text,
                'level': level,
                'children': []
            }

            # Add to appropriate parent
            while stack and stack[-1]['level'] >= level:
                stack.pop()

            if stack:
                stack[-1]['children'].append(node)
            else:
                nodes.append(node)

            stack.append(node)

        # Create UniversalBox
        mindmap_box = UniversalBox(
            content={
                'nodes': nodes,
                'type': 'mindmap',
                'metadata': metadata or {}
            },
            content_type=ContentType.DIAGRAM,
            box_type=BoxType.BLOCK,
            attributes={
                'plugin': 'mindmap',
                'source': content
            }
        )

        return mindmap_box

    def enhance_box(self, box: UniversalBox) -> UniversalBox:
        """Enhance the mind map box with layout information"""
        if box.content.get('type') == 'mindmap':
            # Calculate dimensions based on content
            nodes = box.content.get('nodes', [])
            if nodes:
                # Estimate dimensions (this would be more sophisticated in practice)
                estimated_width = 400
                estimated_height = len(nodes) * 50 + 100
                box.dimensions.width = estimated_width
                box.dimensions.height = estimated_height

        return box

    def get_dependencies(self) -> List[str]:
        """No external dependencies required"""
        return []


# Automatic registration when module is imported
def _register_plugin():
    """Register this plugin automatically"""
    from compose.plugin_system import plugin_manager
    plugin_manager.register_plugin(MindMapPlugin)

# Register on import
_register_plugin()
