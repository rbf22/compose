# compose/render/diagram_renderer.py
"""
Diagram rendering system for Compose.
Supports Mermaid-like diagrams with ASCII and SVG output.
"""

from typing import Dict, List, Any, Tuple
from ..cache_system import diagram_cache, performance_monitor
from ..layout.tex_boxes import Box


class DiagramBox(Box):
    """Box containing diagram elements"""
    diagram_type: str = ""
    elements: List[Dict[str, Any]] = None
    connections: List[Dict[str, Any]] = None

    def __init__(self, diagram_type: str, elements: List[Dict[str, Any]] = None,
                 connections: List[Dict[str, Any]] = None, **kwargs):
        super().__init__(**kwargs)
        self.box_type = "diagram"
        self.diagram_type = diagram_type
        self.elements = elements or []
        self.connections = connections or []


class DiagramRenderer:
    """
    Renders diagrams from Mermaid-like syntax.
    Focuses on flowcharts, sequence diagrams, and basic graph layouts.
    """

    def __init__(self):
        self.node_width = 12
        self.node_height = 3
        self.spacing_x = 4
        self.spacing_y = 2

    @performance_monitor.time_operation("diagram_rendering")
    def render_diagram(self, code: str, format: str = 'ascii') -> str:
        """
        Render diagram from Mermaid code.

        Args:
            code: Mermaid diagram code
            format: 'ascii', 'svg', or 'box'

        Returns:
            Rendered diagram as string
        """
        # Check cache first
        cached_result = diagram_cache.get_rendered_diagram(code, format)
        if cached_result:
            return cached_result

        # Parse diagram type and content
        lines = [line.strip() for line in code.split('\n') if line.strip()]

        if not lines:
            return ""

        # Determine diagram type
        first_line = lines[0].lower()
        if 'graph' in first_line:
            result = self._render_flowchart(lines, format)
        elif 'sequence' in first_line:
            result = self._render_sequence(lines, format)
        elif 'gantt' in first_line:
            result = self._render_gantt(lines, format)
        elif 'network' in first_line or 'topology' in first_line:
            result = self._render_network(lines, format)
        elif 'er' in first_line or 'entity' in first_line:
            result = self._render_er_diagram(lines, format)
        else:
            # Try to parse as flowchart by default
            result = self._render_flowchart(lines, format)

        # Cache the result
        diagram_cache.set_rendered_diagram(code, format, result)

        return result

    def _render_flowchart(self, lines: List[str], format: str) -> str:
        """Render flowchart diagram"""
        try:
            # Parse nodes and connections
            nodes, connections = self._parse_flowchart(lines)

            if format == 'ascii':
                return self._render_flowchart_ascii(nodes, connections)
            elif format == 'svg':
                return self._render_flowchart_svg(nodes, connections)
            else:
                return self._render_flowchart_boxes(nodes, connections)
        except Exception as e:
            return f"Error rendering flowchart: {e}"

    def _parse_flowchart(self, lines: List[str]) -> Tuple[Dict[str, Dict], List[Dict]]:
        """Parse flowchart nodes and connections using robust parser"""
        # Combine lines back into code for the parser
        code = '\n'.join(lines)

        # Check cache first
        cached_result = diagram_cache.get_parsed_diagram(code)
        if cached_result:
            return cached_result

        # Parse using the robust Mermaid parser
        from .mermaid_parser import parse_mermaid_flowchart
        nodes, connections = parse_mermaid_flowchart(code)

        # Cache the parsed result
        diagram_cache.set_parsed_diagram(code, nodes, connections)

        return nodes, connections

    def _detect_shape_from_node(self, node_text: str) -> str:
        """Detect node shape from node text"""
        if '{{' in node_text or '}}' in node_text:
            return 'hexagon'
        elif '(' in node_text and ')' in node_text:
            return 'round'
        else:
            return 'rectangle'

    def _render_flowchart_ascii(self, nodes: Dict, connections: List) -> str:
        """Render flowchart as ASCII art"""
        if not nodes:
            return "No diagram elements found. Check syntax."

        # Simple left-to-right layout
        lines = []

        # Create nodes
        node_lines = []
        max_width = 0

        for node_id, node in nodes.items():
            # Create node box
            label = node['label'][:10]  # Truncate long labels
            if node['shape'] == 'round':
                box = f"({label})"
            elif node['shape'] == 'hexagon':
                box = f"{{{label}}}"
            else:
                box = f"[{label}]"

            node_lines.append(box)
            max_width = max(max_width, len(box))

        # Simple horizontal layout
        result = "    ".join(node_lines)

        # Add connections (simplified)
        if connections:
            result += "\n\nConnections:"
            for conn in connections:
                arrow = " --> " if conn['directed'] else " --- "
                result += f"\n  {conn['from']}{arrow}{conn['to']}"
                if conn['label']:
                    result += f" ({conn['label']})"

        return result

    def _render_flowchart_svg(self, nodes: Dict, connections: List) -> str:
        """Render flowchart as SVG"""
        svg_parts = []
        svg_parts.append('<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">')

        # Simple layout: place nodes in a grid
        node_positions = {}
        cols = min(3, len(nodes))
        rows = (len(nodes) + cols - 1) // cols

        node_list = list(nodes.values())
        for i, node in enumerate(node_list):
            x = (i % cols) * 120 + 20
            y = (i // cols) * 80 + 40
            node_positions[node['id']] = (x, y)

            # Draw node based on shape
            if node['shape'] == 'round':
                svg_parts.append(f'<ellipse cx="{x+50}" cy="{y+20}" rx="50" ry="20" fill="#e1f5fe" stroke="#01579b" stroke-width="2"/>')
                svg_parts.append(f'<text x="{x+50}" y="{y+25}" text-anchor="middle" font-family="Arial" font-size="12">{node["label"]}</text>')
            else:
                svg_parts.append(f'<rect x="{x}" y="{y}" width="100" height="40" fill="#e1f5fe" stroke="#01579b" stroke-width="2" rx="5"/>')
                svg_parts.append(f'<text x="{x+50}" y="{y+25}" text-anchor="middle" font-family="Arial" font-size="12">{node["label"]}</text>')

        # Draw connections
        for conn in connections:
            if conn['from'] in node_positions and conn['to'] in node_positions:
                x1, y1 = node_positions[conn['from']]
                x2, y2 = node_positions[conn['to']]

                # Simple line from center to center
                svg_parts.append(f'<line x1="{x1+50}" y1="{y1+20}" x2="{x2+50}" y2="{y2+20}" stroke="#01579b" stroke-width="2" marker-end="url(#arrowhead)"/>')

        # Add arrow marker
        svg_parts.append('<defs>')
        svg_parts.append('<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">')
        svg_parts.append('<polygon points="0 0, 10 3.5, 0 7" fill="#01579b"/>')
        svg_parts.append('</marker>')
        svg_parts.append('</defs>')

        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    def _render_flowchart_boxes(self, nodes: Dict, connections: List) -> DiagramBox:
        """Render flowchart as box layout for integration with typesetting"""
        # Create diagram box with structured data
        return DiagramBox(
            diagram_type='flowchart',
            elements=list(nodes.values()),
            connections=connections
        )

    def _render_sequence(self, lines: List[str], format: str) -> str:
        """Render sequence diagram"""
        try:
            participants, messages = self._parse_sequence(lines)

            if format == 'ascii':
                return self._render_sequence_ascii(participants, messages)
            elif format == 'svg':
                return self._render_sequence_svg(participants, messages)
            else:
                return self._render_sequence_boxes(participants, messages)
        except Exception as e:
            return f"Error rendering sequence diagram: {e}"

    def _parse_sequence(self, lines: List[str]) -> Tuple[List[str], List[Dict]]:
        """Parse sequence diagram participants and messages"""
        participants = []
        messages = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith('%%'):
                continue

            # Parse participants
            if line.lower().startswith('participant'):
                parts = line.split()
                if len(parts) >= 2:
                    participants.append(parts[1])
            elif '->>' in line or '-->>' in line:
                # Parse message: Alice->>Bob: Hello
                parts = line.split(':', 1)
                if len(parts) == 2:
                    interaction = parts[0].strip()
                    message = parts[1].strip()

                    # Parse interaction: Alice->>Bob
                    arrow_parts = interaction.split('->>')
                    if len(arrow_parts) == 2:
                        from_part = arrow_parts[0].strip()
                        to_part = arrow_parts[1].strip()

                        messages.append({
                            'from': from_part,
                            'to': to_part,
                            'message': message,
                            'type': 'solid'  # ->> is solid arrow
                        })

        return participants, messages

    def _render_sequence_ascii(self, participants: List[str], messages: List[Dict]) -> str:
        """Render sequence diagram as ASCII art"""
        if not participants:
            return "No participants found in sequence diagram."

        result = []

        # Header
        result.append("Sequence Diagram")
        result.append("=" * 50)

        # Participants
        result.append("Participants: " + ", ".join(participants))

        # Messages
        result.append("\nMessages:")
        for msg in messages:
            arrow = "-->>" if msg['type'] == 'solid' else "->>"
            result.append(f"  {msg['from']} {arrow} {msg['to']}: {msg['message']}")

        return "\n".join(result)

    def _render_sequence_svg(self, participants: List[str], messages: List[Dict]) -> str:
        """Render sequence diagram as SVG"""
        if not participants:
            return self._create_error_svg("No participants found")

        width = max(600, len(participants) * 100)
        height = max(400, len(messages) * 60 + 100)

        svg_parts = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']

        # Draw lifelines
        lifeline_x = {}
        for i, participant in enumerate(participants):
            x = 100 + i * 150
            lifeline_x[participant] = x

            # Participant name
            svg_parts.append(f'<text x="{x}" y="30" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold">{participant}</text>')

            # Lifeline
            svg_parts.append(f'<line x1="{x}" y1="40" x2="{x}" y2="{height-20}" stroke="#666" stroke-width="2"/>')

        # Draw messages
        y_offset = 60
        for msg in messages:
            if msg['from'] in lifeline_x and msg['to'] in lifeline_x:
                x1 = lifeline_x[msg['from']]
                x2 = lifeline_x[msg['to']]

                # Message line
                svg_parts.append(f'<line x1="{x1}" y1="{y_offset}" x2="{x2}" y2="{y_offset}" stroke="#000" stroke-width="2" marker-end="url(#arrowhead)"/>')

                # Message text
                text_x = (x1 + x2) / 2
                svg_parts.append(f'<text x="{text_x}" y="{y_offset-5}" text-anchor="middle" font-family="Arial" font-size="10">{msg["message"]}</text>')

                y_offset += 40

        # Add arrow marker
        svg_parts.append('<defs>')
        svg_parts.append('<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">')
        svg_parts.append('<polygon points="0 0, 10 3.5, 0 7" fill="#000"/>')
        svg_parts.append('</marker>')
        svg_parts.append('</defs>')

        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    def _render_sequence_boxes(self, participants: List[str], messages: List[Dict]) -> DiagramBox:
        """Render sequence diagram as box layout for typesetting"""
        # Create diagram box with structured data
        return DiagramBox(
            diagram_type='sequence',
            elements=[{'id': p, 'label': p, 'type': 'participant'} for p in participants],
            connections=messages
        )

    def _render_gantt(self, lines: List[str], format: str) -> str:
        """Render Gantt chart"""
        try:
            tasks = self._parse_gantt(lines)

            if format == 'ascii':
                return self._render_gantt_ascii(tasks)
            elif format == 'svg':
                return self._render_gantt_svg(tasks)
            else:
                return self._render_gantt_boxes(tasks)
        except Exception as e:
            return f"Error rendering Gantt chart: {e}"

    def _parse_gantt(self, lines: List[str]) -> List[Dict]:
        """Parse Gantt chart tasks"""
        tasks = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith('%%'):
                continue

            # Parse title
            if line.lower().startswith('title'):
                # Skip for now
                continue

            # Parse task: task1: done, 2023-01-01, 2023-01-05
            if ':' in line and ',' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    task_name = parts[0].strip()
                    details = parts[1].strip()

                    # Parse details
                    detail_parts = [d.strip() for d in details.split(',')]
                    if len(detail_parts) >= 3:
                        status = detail_parts[0]
                        start_date = detail_parts[1]
                        end_date = detail_parts[2]

                        tasks.append({
                            'name': task_name,
                            'status': status,
                            'start': start_date,
                            'end': end_date
                        })

        return tasks

    def _render_gantt_ascii(self, tasks: List[Dict]) -> str:
        """Render Gantt chart as ASCII art"""
        if not tasks:
            return "No tasks found in Gantt chart."

        result = []
        result.append("Gantt Chart")
        result.append("=" * 40)

        for task in tasks:
            status_marker = "[✓]" if task['status'].lower() == 'done' else "[ ]"
            result.append(f"{status_marker} {task['name']}: {task['start']} - {task['end']}")

        return "\n".join(result)

    def _render_gantt_svg(self, tasks: List[Dict]) -> str:
        """Render Gantt chart as SVG"""
        if not tasks:
            return self._create_error_svg("No tasks found")

        width = 800
        height = max(200, len(tasks) * 40 + 100)

        svg_parts = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']

        # Title
        svg_parts.append('<text x="20" y="30" font-family="Arial" font-size="16" font-weight="bold">Gantt Chart</text>')

        # Draw tasks
        y_offset = 60
        for task in tasks:
            # Task bar
            bar_width = 200  # Simplified
            bar_color = "#4CAF50" if task['status'].lower() == 'done' else "#FFC107"

            svg_parts.append(f'<rect x="150" y="{y_offset-15}" width="{bar_width}" height="20" fill="{bar_color}" stroke="#333" stroke-width="1" rx="3"/>')

            # Task name
            svg_parts.append(f'<text x="20" y="{y_offset+5}" font-family="Arial" font-size="12">{task["name"]}</text>')

            # Date range
            svg_parts.append(f'<text x="370" y="{y_offset+5}" font-family="Arial" font-size="10">{task["start"]} - {task["end"]}</text>')

            y_offset += 35

        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    def _render_network(self, lines: List[str], format: str) -> str:
        """Render network topology diagram"""
        try:
            nodes, connections = self._parse_network(lines)

            if format == 'ascii':
                return self._render_network_ascii(nodes, connections)
            elif format == 'svg':
                return self._render_network_svg(nodes, connections)
            else:
                return self._render_network_boxes(nodes, connections)
        except Exception as e:
            return f"Error rendering network diagram: {e}"

    def _parse_network(self, lines: List[str]) -> Tuple[Dict[str, Dict], List[Dict]]:
        """Parse network topology diagram"""
        nodes = {}
        connections = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith('%%'):
                continue

            # Parse network declaration
            if line.lower().startswith('network'):
                continue

            # Parse node definitions: node1[type]: label
            if '[' in line and ']' in line:
                # Parse node with type: server[web]: Web Server
                parts = line.split(':', 1)
                if len(parts) == 2:
                    node_spec = parts[0].strip()
                    label = parts[1].strip()

                    # Parse node id and type
                    if '[' in node_spec and ']' in node_spec:
                        id_part = node_spec.split('[')[0].strip()
                        type_part = node_spec.split('[')[1].split(']')[0].strip()

                        nodes[id_part] = {
                            'id': id_part,
                            'label': label,
                            'type': type_part,
                            'shape': 'rectangle'
                        }

            # Parse connections: node1 -- node2: label
            elif '--' in line and ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    connection_spec = parts[0].strip()
                    label = parts[1].strip()

                    # Parse connection: node1 -- node2
                    conn_parts = connection_spec.split('--')
                    if len(conn_parts) == 2:
                        from_node = conn_parts[0].strip()
                        to_node = conn_parts[1].strip()

                        connections.append({
                            'from': from_node,
                            'to': to_node,
                            'label': label,
                            'directed': False
                        })

        return nodes, connections

    def _render_network_ascii(self, nodes: Dict, connections: List) -> str:
        """Render network diagram as ASCII art"""
        if not nodes:
            return "No network nodes found."

        result = []
        result.append("Network Topology")
        result.append("=" * 30)

        # List nodes
        result.append("\nNodes:")
        for node_id, node in nodes.items():
            result.append(f"  {node_id} [{node['type']}]")

        # List connections
        result.append("\nConnections:")
        for conn in connections:
            result.append(f"  {conn['from']} -- {conn['to']}: {conn['label']}")

        return "\n".join(result)

    def _render_network_svg(self, nodes: Dict, connections: List) -> str:
        """Render network diagram as SVG"""
        if not nodes:
            return self._create_error_svg("No network nodes found")

        width = 600
        height = 400

        svg_parts = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']

        # Position nodes in a circle
        center_x, center_y = width // 2, height // 2
        radius = min(width, height) // 3
        angle_step = 2 * 3.14159 / len(nodes) if nodes else 0

        node_positions = {}
        node_list = list(nodes.values())

        for i, node in enumerate(node_list):
            angle = i * angle_step
            x = center_x + radius * 0.7 * (1 if len(nodes) == 1 else angle)
            y = center_y + radius * 0.7 * (0 if len(nodes) == 1 else 1)
            node_positions[node['id']] = (x, y)

            # Draw node
            svg_parts.append(f'<circle cx="{x}" cy="{y}" r="30" fill="#e3f2fd" stroke="#1976d2" stroke-width="2"/>')
            svg_parts.append(f'<text x="{x}" y="{y+5}" text-anchor="middle" font-family="Arial" font-size="10" font-weight="bold">{node["label"][:8]}</text>')
            svg_parts.append(f'<text x="{x}" y="{y+18}" text-anchor="middle" font-family="Arial" font-size="8">{node["type"]}</text>')

        # Draw connections
        for conn in connections:
            if conn['from'] in node_positions and conn['to'] in node_positions:
                x1, y1 = node_positions[conn['from']]
                x2, y2 = node_positions[conn['to']]

                svg_parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#666" stroke-width="2"/>')

                # Connection label
                mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                svg_parts.append(f'<text x="{mid_x}" y="{mid_y-5}" text-anchor="middle" font-family="Arial" font-size="8">{conn["label"]}</text>')

        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    def _render_network_boxes(self, nodes: Dict, connections: List) -> DiagramBox:
        """Render network diagram as box layout"""
        return DiagramBox(
            diagram_type='network',
            elements=list(nodes.values()),
            connections=connections
        )

    def _render_er_diagram(self, lines: List[str], format: str) -> str:
        """Render entity-relationship diagram"""
        try:
            entities, relationships = self._parse_er_diagram(lines)

            if format == 'ascii':
                return self._render_er_ascii(entities, relationships)
            elif format == 'svg':
                return self._render_er_svg(entities, relationships)
            else:
                return self._render_er_boxes(entities, relationships)
        except Exception as e:
            return f"Error rendering ER diagram: {e}"

    def _parse_er_diagram(self, lines: List[str]) -> Tuple[Dict[str, Dict], List[Dict]]:
        """Parse entity-relationship diagram"""
        entities = {}
        relationships = []

        current_entity = None

        for line in lines:
            line = line.strip()
            if not line or line.startswith('%%'):
                continue

            # Parse ER declaration
            if line.lower().startswith('er'):
                continue

            # Parse entity definition: entity_name {
            if line.endswith('{') and not line.startswith(' '):
                entity_name = line[:-1].strip()
                current_entity = entity_name
                entities[entity_name] = {
                    'name': entity_name,
                    'attributes': []
                }

            # Parse entity attributes
            elif current_entity and line.startswith('  ') and ':' in line:
                attr_name, attr_type = line.strip().split(':', 1)
                entities[current_entity]['attributes'].append({
                    'name': attr_name.strip(),
                    'type': attr_type.strip()
                })

            # Parse entity end
            elif line == '}' and current_entity:
                current_entity = None

            # Parse relationships: entity1 ||--|| entity2: relationship_name
            elif '||' in line and ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    relationship_spec = parts[0].strip()
                    relationship_name = parts[1].strip()

                    # Parse relationship pattern
                    rel_parts = relationship_spec.split('||')
                    if len(rel_parts) >= 3:
                        entity1 = rel_parts[0].strip()
                        cardinality = '||' + rel_parts[1] + '||'
                        entity2 = rel_parts[2].strip()

                        relationships.append({
                            'entity1': entity1,
                            'entity2': entity2,
                            'cardinality': cardinality,
                            'name': relationship_name
                        })

        return entities, relationships

    def _render_er_ascii(self, entities: Dict, relationships: List) -> str:
        """Render ER diagram as ASCII art"""
        if not entities:
            return "No entities found in ER diagram."

        result = []
        result.append("Entity-Relationship Diagram")
        result.append("=" * 35)

        # Render entities
        for entity_name, entity in entities.items():
            result.append(f"\n{entity_name}")
            result.append("-" * len(entity_name))

            for attr in entity['attributes']:
                result.append(f"  {attr['name']}: {attr['type']}")

        # Render relationships
        if relationships:
            result.append("\nRelationships:")
            for rel in relationships:
                result.append(f"  {rel['entity1']} {rel['cardinality']} {rel['entity2']}: {rel['name']}")

        return "\n".join(result)

    def _render_er_svg(self, entities: Dict, relationships: List) -> str:
        """Render ER diagram as SVG"""
        if not entities:
            return self._create_error_svg("No entities found")

        width = 800
        height = max(400, len(entities) * 120 + 100)

        svg_parts = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']

        # Position entities
        entity_positions = {}
        entity_list = list(entities.values())
        y_offset = 50

        for entity in entity_list:
            x = 50
            entity_positions[entity['name']] = (x, y_offset)

            # Entity box
            box_height = 30 + len(entity['attributes']) * 20
            svg_parts.append(f'<rect x="{x}" y="{y_offset}" width="200" height="{box_height}" fill="#fff" stroke="#333" stroke-width="2" rx="5"/>')

            # Entity name
            svg_parts.append(f'<text x="{x+100}" y="{y_offset+20}" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold">{entity["name"]}</text>')

            # Attributes
            attr_y = y_offset + 40
            for attr in entity['attributes']:
                svg_parts.append(f'<text x="{x+10}" y="{attr_y}" font-family="Arial" font-size="10">{attr["name"]}: {attr["type"]}</text>')
                attr_y += 15

            y_offset += box_height + 40

        # Draw relationships (simplified)
        for rel in relationships:
            if rel['entity1'] in entity_positions and rel['entity2'] in entity_positions:
                x1, y1 = entity_positions[rel['entity1']]
                x2, y2 = entity_positions[rel['entity2']]

                # Simple line between entities
                svg_parts.append(f'<line x1="{x1+200}" y1="{y1+50}" x2="{x2}" y2="{y2+50}" stroke="#666" stroke-width="2"/>')

                # Relationship label
                mid_x, mid_y = (x1 + x2) / 2 + 100, (y1 + y2) / 2 + 50
                svg_parts.append(f'<text x="{mid_x}" y="{mid_y}" text-anchor="middle" font-family="Arial" font-size="10">{rel["name"]}</text>')

        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    def _render_er_boxes(self, entities: Dict, relationships: List) -> DiagramBox:
        """Render ER diagram as box layout"""
        return DiagramBox(
            diagram_type='er',
            elements=list(entities.values()),
            connections=relationships
        )

    def _create_error_svg(self, message: str) -> str:
        """Create an error SVG for rendering failures"""
        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="300" height="100" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="#ffebee" stroke="#f44336" stroke-width="2" rx="5"/>
  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Arial" font-size="12" fill="#c62828">
    Error: {message}
  </text>
</svg>'''

        import base64
        svg_base64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{svg_base64}"


# Integration with markdown parser
def render_mermaid_block(content: str) -> str:
    """
    Render Mermaid code block for HTML output.
    This integrates with the markdown parser.
    """
    renderer = DiagramRenderer()

    # Try to render as SVG first, fall back to ASCII
    try:
        svg_output = renderer.render_diagram(content, 'svg')
        return f'<div class="mermaid-diagram">{svg_output}</div>'
    except Exception:
        # Fallback to ASCII
        ascii_output = renderer.render_diagram(content, 'ascii')
        return f'<pre class="mermaid-ascii">{ascii_output}</pre>'


# Test functions
def test_diagram_rendering():
    """Test diagram rendering functionality"""
    renderer = DiagramRenderer()

    # Test flowchart
    flowchart_code = """
    graph TD
        A[Start] --> B[Process]
        B --> C[Decision]
        C --> D[End]
    """

    print("ASCII Flowchart:")
    print(renderer.render_diagram(flowchart_code, 'ascii'))
    print()

    print("SVG Flowchart (first 200 chars):")
    svg = renderer.render_diagram(flowchart_code, 'svg')
    print(svg[:200] + "...")


if __name__ == "__main__":
    test_diagram_rendering()
