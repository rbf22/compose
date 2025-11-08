# tests/test_diagram_engine.py
"""Tests for the diagram rendering engine."""

from compose.layout.engines.diagram_engine import DiagramRenderer, MermaidRenderer
from compose.layout import UniversalBox, ContentType, BoxType


def test_mermaid_renderer_creation():
    """Test creating a Mermaid renderer."""
    renderer = MermaidRenderer()
    assert renderer is not None
    assert renderer.node_spacing == 100.0
    assert renderer.level_spacing == 80.0
    print("✅ test_mermaid_renderer_creation passed")


def test_flowchart_parsing():
    """Test parsing a simple flowchart."""
    renderer = MermaidRenderer()
    code = """
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action]
    B -->|No| D[End]
"""
    
    layout = renderer.parse_flowchart(code.strip())
    
    assert layout.diagram_type == "flowchart"
    assert len(layout.nodes) >= 4  # A, B, C, D
    assert len(layout.edges) >= 3  # A->B, B->C, B->D
    assert layout.width > 0
    assert layout.height > 0
    print("✅ test_flowchart_parsing passed")


def test_sequence_diagram_parsing():
    """Test parsing a sequence diagram."""
    renderer = MermaidRenderer()
    code = """
sequenceDiagram
    participant A as Alice
    participant B as Bob
    A->>B: Hello
    B->>A: Hi there
"""
    
    layout = renderer.parse_sequence_diagram(code.strip())
    
    assert layout.diagram_type == "sequence"
    assert len(layout.nodes) == 2  # Alice, Bob
    assert len(layout.edges) == 2  # Two messages
    assert layout.width > 0
    assert layout.height > 0
    print("✅ test_sequence_diagram_parsing passed")


def test_gantt_chart_parsing():
    """Test parsing a Gantt chart."""
    renderer = MermaidRenderer()
    code = """
gantt
    title Project Timeline
    section Phase 1
    Task 1 : 2024-01-01, 30d
    Task 2 : 2024-01-15, 20d
"""
    
    layout = renderer.parse_gantt_chart(code.strip())
    
    assert layout.diagram_type == "gantt"
    assert layout.title == "Project Timeline"
    assert len(layout.nodes) >= 2  # Tasks
    assert layout.width == 600  # Fixed Gantt width
    print("✅ test_gantt_chart_parsing passed")


def test_svg_rendering():
    """Test SVG output generation."""
    renderer = MermaidRenderer()
    code = """
graph LR
    A[Input] --> B[Process] --> C[Output]
"""
    
    layout = renderer.parse_flowchart(code.strip())
    svg = renderer.render_to_svg(layout)
    
    assert svg.startswith('<svg')
    assert svg.endswith('</svg>')
    assert 'xmlns="http://www.w3.org/2000/svg"' in svg
    assert 'marker id="arrowhead"' in svg  # Should have arrow markers
    assert 'polygon' in svg  # Should have arrow polygons
    
    # Check that we have a valid SVG structure
    assert svg.count('<svg') == 1
    assert svg.count('</svg>') == 1
    
    print("✅ test_svg_rendering passed")


def test_diagram_renderer_integration():
    """Test the main diagram renderer interface."""
    renderer = DiagramRenderer()
    
    # Create a diagram box
    diagram_box = UniversalBox(
        content="graph TD\n  A[Start] --> B[End]",
        content_type=ContentType.DIAGRAM,
        attributes={"diagram_type": "mermaid"}
    )
    
    # Render to SVG
    svg = renderer.render_diagram(diagram_box)
    
    assert isinstance(svg, str)
    assert len(svg) > 0
    assert '<svg' in svg
    assert diagram_box.dimensions.width > 0
    assert diagram_box.dimensions.height > 0
    print("✅ test_diagram_renderer_integration passed")


def test_node_level_computation():
    """Test hierarchical node level computation."""
    renderer = MermaidRenderer()
    
    # Create test nodes and edges
    from compose.layout.engines.diagram_engine import DiagramNode, DiagramEdge
    
    nodes = [
        DiagramNode("A", "Start"),
        DiagramNode("B", "Middle"),
        DiagramNode("C", "End")
    ]
    
    edges = [
        DiagramEdge("A", "B"),
        DiagramEdge("B", "C")
    ]
    
    levels = renderer._compute_node_levels(nodes, edges)
    
    assert levels["A"] == 0  # Root level
    assert levels["B"] == 1  # Second level
    assert levels["C"] == 2  # Third level
    print("✅ test_node_level_computation passed")


def test_diagram_error_handling():
    """Test diagram rendering error handling."""
    renderer = DiagramRenderer()
    
    # Create invalid diagram box
    invalid_box = UniversalBox(
        content="invalid diagram syntax",
        content_type=ContentType.DIAGRAM,
        attributes={"diagram_type": "unknown"}
    )
    
    try:
        renderer.render_diagram(invalid_box)
        assert False, "Should have raised an error"
    except ValueError as e:
        assert "Unsupported diagram type" in str(e)
        print("✅ test_diagram_error_handling passed")


def test_create_diagram_box():
    """Test diagram box creation helper."""
    renderer = DiagramRenderer()
    
    code = "graph TD\n  A --> B"
    box = renderer.create_diagram_box(code, "mermaid")
    
    assert box.content_type == ContentType.DIAGRAM
    assert box.box_type == BoxType.BLOCK
    assert box.content == code
    assert box.attributes["diagram_type"] == "mermaid"
    print("✅ test_create_diagram_box passed")
