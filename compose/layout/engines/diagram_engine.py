# compose/layout/diagram_renderer.py
"""
Diagram rendering system for Compose.

This module handles parsing and rendering of various diagram types,
with primary support for Mermaid syntax and extensibility for
custom diagram formats.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from ..universal_box import UniversalBox, ContentType, BoxType, RenderingStyle
from ..box_model import Dimensions


@dataclass
class DiagramNode:
    """A node in a diagram (box, decision, etc.)."""
    id: str
    label: str
    shape: str = "box"  # box, diamond, circle, etc.
    position: Tuple[float, float] = (0, 0)
    style: Optional[RenderingStyle] = None


@dataclass 
class DiagramEdge:
    """An edge/connection between diagram nodes."""
    from_node: str
    to_node: str
    label: str = ""
    style: str = "solid"  # solid, dashed, dotted
    arrow: str = "normal"  # normal, none, both


@dataclass
class DiagramLayout:
    """Layout information for a complete diagram."""
    nodes: List[DiagramNode]
    edges: List[DiagramEdge]
    width: float
    height: float
    diagram_type: str
    title: Optional[str] = None


class MermaidRenderer:
    """
    Renderer for Mermaid diagram syntax.
    
    Supports flowcharts, sequence diagrams, and Gantt charts
    with conversion to SVG output.
    """
    
    def __init__(self):
        self.node_spacing = 100.0
        self.level_spacing = 80.0
        self.default_node_size = (80.0, 40.0)
    
    def parse_flowchart(self, code: str) -> DiagramLayout:
        """Parse Mermaid flowchart syntax."""
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        
        # Extract diagram type
        if not lines or not lines[0].startswith('graph') and not lines[0].startswith('flowchart'):
            raise ValueError("Invalid flowchart syntax")
        
        direction = "TD"  # Top-Down default
        if len(lines[0].split()) > 1:
            direction = lines[0].split()[1]
        
        nodes = {}
        edges = []
        
        # Parse nodes and edges
        for line in lines[1:]:
            if '-->' in line or '---' in line:
                # Edge definition
                edge = self._parse_edge(line)
                if edge:
                    edges.append(edge)
                    # Ensure nodes exist
                    if edge.from_node not in nodes:
                        nodes[edge.from_node] = DiagramNode(edge.from_node, edge.from_node)
                    if edge.to_node not in nodes:
                        nodes[edge.to_node] = DiagramNode(edge.to_node, edge.to_node)
            else:
                # Node definition
                node = self._parse_node(line)
                if node:
                    nodes[node.id] = node
        
        # Layout nodes based on direction
        positioned_nodes = self._layout_flowchart_nodes(list(nodes.values()), edges, direction)
        
        # Calculate diagram dimensions
        if positioned_nodes:
            max_x = max(node.position[0] + self.default_node_size[0] for node in positioned_nodes)
            max_y = max(node.position[1] + self.default_node_size[1] for node in positioned_nodes)
            width, height = max_x + 20, max_y + 20
        else:
            width, height = 200, 100
        
        return DiagramLayout(
            nodes=positioned_nodes,
            edges=edges,
            width=width,
            height=height,
            diagram_type="flowchart"
        )
    
    def parse_sequence_diagram(self, code: str) -> DiagramLayout:
        """Parse Mermaid sequence diagram syntax."""
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        
        if not lines or not lines[0].startswith('sequenceDiagram'):
            raise ValueError("Invalid sequence diagram syntax")
        
        participants = []
        messages = []
        
        for line in lines[1:]:
            if line.startswith('participant'):
                # participant A as Alice
                parts = line.split(' as ')
                if len(parts) == 2:
                    id_part = parts[0].replace('participant ', '').strip()
                    label = parts[1].strip()
                    participants.append(DiagramNode(id_part, label, shape="participant"))
            elif '->' in line or '->>' in line:
                # A->>B: Hello
                arrow = '->>' if '->>' in line else '->'
                parts = line.split(arrow)
                if len(parts) == 2:
                    from_part = parts[0].strip()
                    to_and_msg = parts[1].split(':', 1)
                    to_part = to_and_msg[0].strip()
                    message = to_and_msg[1].strip() if len(to_and_msg) > 1 else ""
                    
                    messages.append(DiagramEdge(
                        from_node=from_part,
                        to_node=to_part,
                        label=message,
                        style="solid" if arrow == '->' else "dashed"
                    ))
        
        # Layout sequence diagram
        positioned_participants = self._layout_sequence_participants(participants)
        
        # Calculate dimensions
        width = len(participants) * 150 + 100 if participants else 300
        height = len(messages) * 50 + 150 if messages else 200
        
        return DiagramLayout(
            nodes=positioned_participants,
            edges=messages,
            width=width,
            height=height,
            diagram_type="sequence"
        )
    
    def parse_gantt_chart(self, code: str) -> DiagramLayout:
        """Parse Mermaid Gantt chart syntax."""
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        
        if not lines or not lines[0].startswith('gantt'):
            raise ValueError("Invalid Gantt chart syntax")
        
        title = ""
        sections = []
        tasks = []
        
        current_section = ""
        
        for line in lines[1:]:
            if line.startswith('title'):
                title = line.replace('title', '').strip()
            elif line.startswith('section'):
                current_section = line.replace('section', '').strip()
                sections.append(current_section)
            elif ':' in line:
                # Task definition: Task name : status, start, duration
                parts = line.split(':', 1)
                task_name = parts[0].strip()
                task_info = parts[1].strip() if len(parts) > 1 else ""
                
                tasks.append(DiagramNode(
                    id=f"task_{len(tasks)}",
                    label=task_name,
                    shape="task",
                    style=RenderingStyle(color="#4472C4")
                ))
        
        # Layout Gantt chart
        positioned_tasks = self._layout_gantt_tasks(tasks)
        
        # Calculate dimensions
        width = 600  # Fixed width for Gantt charts
        height = len(tasks) * 30 + 100
        
        return DiagramLayout(
            nodes=positioned_tasks,
            edges=[],  # Gantt charts don't have edges
            width=width,
            height=height,
            diagram_type="gantt",
            title=title
        )
    
    def _parse_node(self, line: str) -> Optional[DiagramNode]:
        """Parse a single node definition."""
        # Simple node: A[Label]
        match = re.match(r'(\w+)\[([^\]]+)\]', line)
        if match:
            node_id, label = match.groups()
            return DiagramNode(node_id, label, shape="box")
        
        # Diamond node: A{Label}
        match = re.match(r'(\w+)\{([^}]+)\}', line)
        if match:
            node_id, label = match.groups()
            return DiagramNode(node_id, label, shape="diamond")
        
        # Circle node: A((Label))
        match = re.match(r'(\w+)\(\(([^)]+)\)\)', line)
        if match:
            node_id, label = match.groups()
            return DiagramNode(node_id, label, shape="circle")
        
        return None
    
    def _parse_edge(self, line: str) -> Optional[DiagramEdge]:
        """Parse a single edge definition."""
        # Simple arrow: A --> B
        if '-->' in line:
            parts = line.split('-->')
            if len(parts) == 2:
                from_node = parts[0].strip()
                to_part = parts[1].strip()
                
                # Check for label: A --> |label| B
                label_match = re.match(r'\|([^|]+)\|\s*(\w+)', to_part)
                if label_match:
                    label, to_node = label_match.groups()
                    return DiagramEdge(from_node, to_node, label.strip())
                else:
                    return DiagramEdge(from_node, to_part, "")
        
        # Dashed arrow: A -.-> B
        if '-.->':
            parts = line.split('-.->') 
            if len(parts) == 2:
                return DiagramEdge(parts[0].strip(), parts[1].strip(), "", style="dashed")
        
        return None
    
    def _layout_flowchart_nodes(self, nodes: List[DiagramNode], edges: List[DiagramEdge], 
                               direction: str) -> List[DiagramNode]:
        """Layout nodes in a flowchart based on direction."""
        if not nodes:
            return []
        
        # Simple hierarchical layout
        levels = self._compute_node_levels(nodes, edges)
        
        positioned_nodes = []
        level_counts = {}
        
        for node in nodes:
            level = levels.get(node.id, 0)
            level_counts[level] = level_counts.get(level, 0) + 1
            
            if direction in ['TD', 'TB']:  # Top-Down
                x = (level_counts[level] - 1) * self.node_spacing + 50
                y = level * self.level_spacing + 50
            else:  # Left-Right
                x = level * self.level_spacing + 50
                y = (level_counts[level] - 1) * self.node_spacing + 50
            
            node.position = (x, y)
            positioned_nodes.append(node)
        
        return positioned_nodes
    
    def _layout_sequence_participants(self, participants: List[DiagramNode]) -> List[DiagramNode]:
        """Layout participants in a sequence diagram."""
        positioned = []
        for i, participant in enumerate(participants):
            participant.position = (i * 150 + 50, 50)
            positioned.append(participant)
        return positioned
    
    def _layout_gantt_tasks(self, tasks: List[DiagramNode]) -> List[DiagramNode]:
        """Layout tasks in a Gantt chart."""
        positioned = []
        for i, task in enumerate(tasks):
            task.position = (50, i * 30 + 100)
            positioned.append(task)
        return positioned
    
    def _compute_node_levels(self, nodes: List[DiagramNode], edges: List[DiagramEdge]) -> Dict[str, int]:
        """Compute hierarchical levels for nodes."""
        levels = {}
        node_ids = {node.id for node in nodes}
        
        # Find root nodes (no incoming edges)
        incoming = {node_id: 0 for node_id in node_ids}
        for edge in edges:
            if edge.to_node in incoming:
                incoming[edge.to_node] += 1
        
        roots = [node_id for node_id, count in incoming.items() if count == 0]
        
        # BFS to assign levels
        queue = [(root, 0) for root in roots]
        visited = set()
        
        while queue:
            node_id, level = queue.pop(0)
            if node_id in visited:
                continue
            
            visited.add(node_id)
            levels[node_id] = level
            
            # Add children
            for edge in edges:
                if edge.from_node == node_id and edge.to_node not in visited:
                    queue.append((edge.to_node, level + 1))
        
        # Assign level 0 to any unvisited nodes
        for node_id in node_ids:
            if node_id not in levels:
                levels[node_id] = 0
        
        return levels
    
    def render_to_svg(self, layout: DiagramLayout) -> str:
        """Render diagram layout to SVG."""
        svg_parts = [
            f'<svg width="{layout.width}" height="{layout.height}" xmlns="http://www.w3.org/2000/svg">',
            '<defs>',
            '<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">',
            '<polygon points="0 0, 10 3.5, 0 7" fill="#333" />',
            '</marker>',
            '</defs>'
        ]
        
        # Render edges first (so they appear behind nodes)
        for edge in layout.edges:
            from_node = next((n for n in layout.nodes if n.id == edge.from_node), None)
            to_node = next((n for n in layout.nodes if n.id == edge.to_node), None)
            
            if from_node and to_node:
                x1, y1 = from_node.position[0] + 40, from_node.position[1] + 20
                x2, y2 = to_node.position[0] + 40, to_node.position[1] + 20
                
                stroke_style = "stroke-dasharray: 5,5;" if edge.style == "dashed" else ""
                
                svg_parts.append(
                    f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                    f'stroke="#333" stroke-width="2" marker-end="url(#arrowhead)" {stroke_style}/>'
                )
                
                # Add edge label if present
                if edge.label:
                    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                    svg_parts.append(
                        f'<text x="{mid_x}" y="{mid_y-5}" text-anchor="middle" '
                        f'font-family="Arial" font-size="12" fill="#666">{edge.label}</text>'
                    )
        
        # Render nodes
        for node in layout.nodes:
            x, y = node.position
            
            if node.shape == "box":
                svg_parts.append(
                    f'<rect x="{x}" y="{y}" width="80" height="40" '
                    f'fill="#e1f5fe" stroke="#0277bd" stroke-width="2" rx="5"/>'
                )
            elif node.shape == "diamond":
                cx, cy = x + 40, y + 20
                svg_parts.append(
                    f'<polygon points="{cx},{cy-20} {cx+40},{cy} {cx},{cy+20} {cx-40},{cy}" '
                    f'fill="#fff3e0" stroke="#f57c00" stroke-width="2"/>'
                )
            elif node.shape == "circle":
                cx, cy = x + 40, y + 20
                svg_parts.append(
                    f'<circle cx="{cx}" cy="{cy}" r="25" '
                    f'fill="#f3e5f5" stroke="#7b1fa2" stroke-width="2"/>'
                )
            
            # Add node label
            text_x, text_y = x + 40, y + 25
            svg_parts.append(
                f'<text x="{text_x}" y="{text_y}" text-anchor="middle" '
                f'font-family="Arial" font-size="12" fill="#333">{node.label}</text>'
            )
        
        # Add title if present
        if layout.title:
            svg_parts.append(
                f'<text x="{layout.width/2}" y="25" text-anchor="middle" '
                f'font-family="Arial" font-size="16" font-weight="bold" fill="#333">{layout.title}</text>'
            )
        
        svg_parts.append('</svg>')
        
        return '\n'.join(svg_parts)


class DiagramRenderer:
    """
    Main diagram rendering interface.
    
    Coordinates different diagram parsers and provides
    a unified interface for diagram rendering.
    """
    
    def __init__(self):
        self.mermaid = MermaidRenderer()
        self.renderers = {
            'mermaid': self.mermaid,
            'flowchart': self.mermaid,
            'sequence': self.mermaid,
            'gantt': self.mermaid
        }
    
    def render_diagram(self, box: UniversalBox) -> str:
        """Render a diagram box to SVG."""
        if box.content_type != ContentType.DIAGRAM:
            raise ValueError("Box must be of DIAGRAM content type")
        
        diagram_type = box.attributes.get('diagram_type', 'mermaid')
        code = box.content
        
        if diagram_type not in self.renderers:
            raise ValueError(f"Unsupported diagram type: {diagram_type}")
        
        # Parse the diagram
        if 'flowchart' in code or 'graph' in code:
            layout = self.mermaid.parse_flowchart(code)
        elif 'sequenceDiagram' in code:
            layout = self.mermaid.parse_sequence_diagram(code)
        elif 'gantt' in code:
            layout = self.mermaid.parse_gantt_chart(code)
        else:
            # Default to flowchart
            layout = self.mermaid.parse_flowchart(code)
        
        # Update box dimensions
        box.dimensions = Dimensions(layout.width, layout.height, 0)
        
        # Render to SVG
        return self.mermaid.render_to_svg(layout)
    
    def create_diagram_box(self, code: str, diagram_type: str = "mermaid") -> UniversalBox:
        """Create a diagram box from code."""
        return UniversalBox(
            content=code,
            content_type=ContentType.DIAGRAM,
            box_type=BoxType.BLOCK,
            attributes={"diagram_type": diagram_type}
        )
