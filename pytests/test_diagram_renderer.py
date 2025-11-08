# tests/test_diagram_renderer.py
"""Tests for diagram rendering system"""

import pytest
from compose.render.diagram_renderer import DiagramRenderer, DiagramBox, render_mermaid_block
from compose.layout.tex_boxes import Box


class TestDiagramRenderer:
    """Test diagram rendering functionality"""

    def test_renderer_initialization(self):
        """Test creating diagram renderer"""
        renderer = DiagramRenderer()
        assert renderer.node_width == 12
        assert renderer.node_height == 3
        assert renderer.spacing_x == 4
        assert renderer.spacing_y == 2

    def test_empty_diagram(self):
        """Test rendering empty diagram"""
        renderer = DiagramRenderer()
        result = renderer.render_diagram("")
        assert result == ""

    def test_simple_flowchart_ascii(self):
        """Test rendering simple flowchart as ASCII"""
        renderer = DiagramRenderer()

        code = """
        graph TD
            A[Start] --> B[Process]
            B --> C[End]
        """

        result = renderer.render_diagram(code, 'ascii')

        # Should contain the node labels
        assert 'Start' in result
        assert 'Process' in result
        assert 'End' in result
        assert '[Start]' in result or '(Start)' in result

    def test_flowchart_with_connections(self):
        """Test flowchart with connection arrows"""
        renderer = DiagramRenderer()

        code = """
        graph TD
            A[Start] --> B[Process]
            B --> C[Decision]
            C --> D[End]
        """

        result = renderer.render_diagram(code, 'ascii')

        # Should show connections
        assert 'Start' in result
        assert 'Process' in result
        assert 'Decision' in result
        assert 'End' in result

    def test_flowchart_svg_rendering(self):
        """Test rendering flowchart as SVG"""
        renderer = DiagramRenderer()

        code = """
        graph TD
            A[Start] --> B[End]
        """

        result = renderer.render_diagram(code, 'svg')

        # Should be valid SVG
        assert result.startswith('<svg')
        assert '</svg>' in result
        assert 'xmlns="http://www.w3.org/2000/svg"' in result
        assert 'Start' in result
        assert 'End' in result

    def test_different_node_shapes(self):
        """Test different node shapes in flowcharts"""
        renderer = DiagramRenderer()

        code = """
        graph TD
            A[Rectangle]
            B(Round)
            C{{Hexagon}}
        """

        result = renderer.render_diagram(code, 'ascii')

        # Should contain different shape representations
        assert 'Rectangle' in result
        assert 'Round' in result
        assert 'Hexagon' in result

    def test_sequence_diagram_placeholder(self):
        """Test sequence diagram"""
        renderer = DiagramRenderer()

        code = """
        sequenceDiagram
            participant Alice
            participant Bob
            Alice->>Bob: Hello
        """

        result = renderer.render_diagram(code, 'ascii')

        # Should contain sequence diagram elements
        assert 'Sequence Diagram' in result
        assert 'Alice' in result
        assert 'Bob' in result
        assert 'Hello' in result

    def test_gantt_diagram_placeholder(self):
        """Test Gantt chart"""
        renderer = DiagramRenderer()

        code = """
        gantt
            title Project Timeline
            task1: done, 2023-01-01, 2023-01-05
        """

        result = renderer.render_diagram(code, 'ascii')

        # Should contain Gantt chart elements
        assert 'Gantt Chart' in result
        assert 'task1' in result
        assert '[✓]' in result  # done task marker

    def test_mermaid_block_rendering(self):
        """Test rendering mermaid block for HTML integration"""
        code = """
        graph TD
            A[Hello] --> B[World]
        """

        result = render_mermaid_block(code)

        # Should be wrapped in HTML div
        assert result.startswith('<div class="mermaid-diagram">')
        assert result.endswith('</div>')
        assert '<svg' in result  # Should contain SVG

    def test_flowchart_box_creation(self):
        """Test creating diagram box for typesetting integration"""
        renderer = DiagramRenderer()

        code = """
        graph TD
            A[Node A] --> B[Node B]
        """

        result = renderer.render_diagram(code, 'box')

        # Should return DiagramBox
        assert isinstance(result, DiagramBox)
        assert result.diagram_type == 'flowchart'
        assert len(result.elements) == 2  # Two nodes
        assert len(result.connections) == 1  # One connection

    def test_sequence_diagram_ascii(self):
        """Test rendering sequence diagram as ASCII"""
        renderer = DiagramRenderer()

        code = """
        sequenceDiagram
            participant Alice
            participant Bob
            Alice->>Bob: Hello
            Bob->>Alice: Hi there
        """

        result = renderer.render_diagram(code, 'ascii')

        # Should contain sequence diagram elements
        assert 'Sequence Diagram' in result
        assert 'Alice' in result
        assert 'Bob' in result
        assert 'Hello' in result
        assert 'Hi there' in result

    def test_sequence_diagram_svg(self):
        """Test rendering sequence diagram as SVG"""
        renderer = DiagramRenderer()

        code = """
        sequenceDiagram
            participant Alice
            participant Bob
            Alice->>Bob: Hello
        """

        result = renderer.render_diagram(code, 'svg')

        # Should be valid SVG
        assert result.startswith('<svg')
        assert '</svg>' in result
        assert 'Alice' in result
        assert 'Bob' in result
        assert 'Hello' in result

    def test_gantt_chart_ascii(self):
        """Test rendering Gantt chart as ASCII"""
        renderer = DiagramRenderer()

        code = """
        gantt
            title Project Timeline
            task1: done, 2023-01-01, 2023-01-05
            task2: active, 2023-01-06, 2023-01-10
        """

        result = renderer.render_diagram(code, 'ascii')

        # Should contain Gantt chart elements
        assert 'Gantt Chart' in result
        assert 'task1' in result
        assert 'task2' in result
        assert '[✓]' in result  # done task
        assert '[ ]' in result  # active task

    def test_gantt_chart_svg(self):
        """Test rendering Gantt chart as SVG"""
        renderer = DiagramRenderer()

        code = """
        gantt
            title Project Timeline
            task1: done, 2023-01-01, 2023-01-05
        """

        result = renderer.render_diagram(code, 'svg')

        # Should be valid SVG
        assert result.startswith('<svg')
        assert '</svg>' in result
        assert 'Gantt Chart' in result
        assert 'task1' in result

    def test_diagram_caching(self):
        """Test that diagrams are cached properly"""
        renderer = DiagramRenderer()

        code = """
        graph TD
            A[Start] --> B[End]
        """

        # First render
        result1 = renderer.render_diagram(code, 'ascii')

        # Second render (should use cache)
        result2 = renderer.render_diagram(code, 'ascii')

        # Results should be identical
        assert result1 == result2

        # Should contain the diagram content
        assert 'Start' in result1
        assert 'End' in result1


class TestDiagramBox:
    """Test DiagramBox functionality"""

    def test_diagram_box_creation(self):
        """Test creating diagram box"""
        elements = [
            {'id': 'A', 'label': 'Start', 'shape': 'rectangle'},
            {'id': 'B', 'label': 'End', 'shape': 'rectangle'}
        ]
        connections = [
            {'from': 'A', 'to': 'B', 'directed': True}
        ]

        box = DiagramBox('flowchart', elements, connections)

        assert box.diagram_type == 'flowchart'
        assert len(box.elements) == 2
        assert len(box.connections) == 1
        assert box.box_type == 'diagram'

    def test_diagram_box_empty(self):
        """Test creating empty diagram box"""
        box = DiagramBox('empty')

        assert box.diagram_type == 'empty'
        assert box.elements == []
        assert box.connections == []
