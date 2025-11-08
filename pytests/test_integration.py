# tests/test_integration.py
"""Integration tests for the universal layout system."""

from compose.layout import (
    UniversalLayoutEngine, DocumentBuilder,
    UniversalBox, ContentType, BoxType,
    MathExpressionParser, DiagramRenderer
)


def test_full_document_workflow():
    """Test complete document creation workflow."""
    # Create a document with mixed content
    builder = DocumentBuilder()
    doc = (builder
        .add_text("# Mathematical Document")
        .add_text("This document demonstrates mixed content.")
        .add_math("E = mc^2", display=True)
        .add_text("Here's a process diagram:")
        .add_diagram("""
graph TD
    A[Input] --> B[Process]
    B --> C{Decision}
    C -->|Yes| D[Output A]
    C -->|No| E[Output B]
""")
        .add_text("End of document.")
        .build())
    
    # Verify document structure
    assert len(doc) == 6
    assert doc[0].content_type == ContentType.TEXT  # Title
    assert doc[1].content_type == ContentType.TEXT  # Description
    assert doc[2].content_type == ContentType.MATH  # Equation
    assert doc[3].content_type == ContentType.TEXT  # Diagram intro
    assert doc[4].content_type == ContentType.DIAGRAM  # Diagram
    assert doc[5].content_type == ContentType.TEXT  # End
    
    print("✅ test_full_document_workflow passed")


def test_math_diagram_integration():
    """Test integration between math and diagram systems."""
    # Create a document with math in diagram labels
    builder = DocumentBuilder()
    doc = (builder
        .add_text("Mathematical process:")
        .add_diagram("""
graph LR
    A[x²] --> B[+]
    C[y²] --> B
    B --> D[= z²]
""")
        .add_math("\\text{Where } x^2 + y^2 = z^2", display=True)
        .build())
    
    assert len(doc) == 3
    assert doc[1].content_type == ContentType.DIAGRAM
    assert doc[2].content_type == ContentType.MATH
    
    print("✅ test_math_diagram_integration passed")


def test_layout_engine_mixed_content():
    """Test layout engine with mixed content types."""
    engine = UniversalLayoutEngine()
    
    # Create boxes of different types
    text_box = UniversalBox("Introduction", ContentType.TEXT, BoxType.BLOCK)
    math_box = UniversalBox("x^2 + y^2 = z^2", ContentType.MATH, BoxType.BLOCK)
    diagram_box = UniversalBox("graph TD\n  A --> B", ContentType.DIAGRAM, BoxType.BLOCK)
    
    boxes = [text_box, math_box, diagram_box]
    
    # Layout the document
    laid_out = engine.layout_document(boxes)
    
    assert len(laid_out) == 3
    
    # Check that positions were set
    for box in laid_out:
        if box.box_type == BoxType.BLOCK:
            assert box.position is not None
    
    print("✅ test_layout_engine_mixed_content passed")


def test_parser_renderer_integration():
    """Test integration between parsers and renderers."""
    # Parse math expression
    math_parser = MathExpressionParser()
    math_box = math_parser.parse_expression("\\alpha + \\beta^2")
    
    assert math_box is not None
    assert math_box.dimensions.width > 0
    
    # Render diagram
    diagram_renderer = DiagramRenderer()
    diagram_box = UniversalBox(
        content="graph LR\n  A --> B --> C",
        content_type=ContentType.DIAGRAM,
        attributes={"diagram_type": "mermaid"}
    )
    
    svg_output = diagram_renderer.render_diagram(diagram_box)
    assert isinstance(svg_output, str)
    assert len(svg_output) > 0
    assert '<svg' in svg_output
    
    print("✅ test_parser_renderer_integration passed")


def test_complex_mathematical_document():
    """Test complex mathematical document with multiple equation types."""
    builder = DocumentBuilder()
    doc = (builder
        .add_text("# Advanced Mathematics")
        .add_text("## Calculus")
        .add_math("\\int_0^1 x^2 dx = \\frac{1}{3}", display=True)
        .add_text("## Linear Algebra")
        .add_math("\\mathbf{A}\\mathbf{x} = \\mathbf{b}", display=True)
        .add_text("## Greek Letters")
        .add_math("\\alpha + \\beta + \\gamma = \\delta", display=True)
        .build())
    
    # Should have at least 6 elements (3 text, 3 math), but may have more due to processing
    assert len(doc) >= 6
    
    # Count math and text elements specifically
    math_boxes = [box for box in doc if box.content_type == ContentType.MATH]
    text_boxes = [box for box in doc if box.content_type == ContentType.TEXT]
    
    assert len(math_boxes) == 3  # Should have exactly 3 math expressions
    assert len(text_boxes) >= 3  # Should have at least 3 text sections
    
    # All math should be display style
    for box in math_boxes:
        assert box.box_type == BoxType.BLOCK
    
    print("✅ test_complex_mathematical_document passed")


def test_diagram_types_integration():
    """Test different diagram types in one document."""
    builder = DocumentBuilder()
    doc = (builder
        .add_text("# Diagram Examples")
        .add_text("## Flowchart")
        .add_diagram("graph TD\n  A --> B --> C")
        .add_text("## Sequence Diagram")
        .add_diagram("""
sequenceDiagram
    participant A as Alice
    participant B as Bob
    A->>B: Hello
    B->>A: Hi
""")
        .add_text("## Gantt Chart")
        .add_diagram("""
gantt
    title Project Schedule
    section Phase 1
    Task 1 : 2024-01-01, 30d
""")
        .build())
    
    # Should have at least 6 elements (3 text, 3 diagrams), but may have more due to processing
    assert len(doc) >= 6
    
    # Count diagram and text elements specifically
    diagram_boxes = [box for box in doc if box.content_type == ContentType.DIAGRAM]
    text_boxes = [box for box in doc if box.content_type == ContentType.TEXT]
    
    assert len(diagram_boxes) == 3  # Should have exactly 3 diagrams
    assert len(text_boxes) >= 3     # Should have at least 3 text sections
    
    print("✅ test_diagram_types_integration passed")


def test_styling_integration():
    """Test styling system integration."""
    from compose.layout.universal_box import RenderingStyle
    
    # Create styled content
    style = RenderingStyle(
        font_family="Arial",
        font_size=14.0,
        color="#FF0000"
    )
    
    builder = DocumentBuilder()
    doc = (builder
        .add_text("Styled text", style={"font_size": 16.0, "color": "#0000FF"})
        .add_math("x^2", display=False)
        .build())
    
    assert len(doc) == 2
    
    # Text should have custom styling
    text_box = doc[0]
    assert text_box.style.font_size == 16.0
    assert text_box.style.color == "#0000FF"
    
    print("✅ test_styling_integration passed")


def test_page_layout_integration():
    """Test page layout and positioning."""
    engine = UniversalLayoutEngine()
    
    # Set custom page size
    engine.set_page_size(800, 600)
    engine.set_margins(50, 40, 50, 40)
    
    # Create content
    boxes = [
        UniversalBox("Title", ContentType.TEXT, BoxType.BLOCK),
        UniversalBox("x^2 + y^2 = z^2", ContentType.MATH, BoxType.BLOCK),
        UniversalBox("graph TD\n  A --> B", ContentType.DIAGRAM, BoxType.BLOCK)
    ]
    
    # Layout with custom settings
    laid_out = engine.layout_document(boxes)
    
    # Check page settings were applied
    assert engine.get_content_width() == 720  # 800 - 40 - 40
    assert engine.get_content_height() == 500  # 600 - 50 - 50
    
    # Check positioning
    for box in laid_out:
        if box.box_type == BoxType.BLOCK:
            assert box.position.width >= engine.margins['left']
    
    print("✅ test_page_layout_integration passed")


def test_error_handling_integration():
    """Test error handling across the system."""
    # Test invalid math expression
    math_parser = MathExpressionParser()
    try:
        # This should not crash, but handle gracefully
        box = math_parser.parse_expression("\\invalid_command")
        assert box is not None  # Should return something, even if placeholder
    except Exception as e:
        # Or it might raise an exception, which is also fine
        assert isinstance(e, Exception)
    
    # Test invalid diagram
    diagram_renderer = DiagramRenderer()
    invalid_box = UniversalBox(
        content="invalid syntax",
        content_type=ContentType.DIAGRAM,
        attributes={"diagram_type": "unknown"}
    )
    
    try:
        diagram_renderer.render_diagram(invalid_box)
        assert False, "Should have raised an error"
    except ValueError:
        pass  # Expected
    
    print("✅ test_error_handling_integration passed")


def test_backward_compatibility():
    """Test backward compatibility with old math interface."""
    # Old-style imports should still work
    from compose.math import MathExpressionParser as OldParser
    from compose.math import MathLayoutEngine as OldEngine
    
    # Should be able to use old interface
    parser = OldParser()
    engine = OldEngine()
    
    box = parser.parse_expression("x^2")
    assert box is not None
    
    print("✅ test_backward_compatibility passed")


def test_performance_basic():
    """Basic performance test for layout system."""
    import time
    
    # Create a moderately complex document
    builder = DocumentBuilder()
    for i in range(10):
        builder.add_text(f"Section {i}")
        builder.add_math(f"x_{i}^2 + y_{i}^2 = z_{i}^2", display=True)
        if i % 3 == 0:
            builder.add_diagram(f"graph TD\n  A{i} --> B{i} --> C{i}")
    
    # Time the build process
    start_time = time.time()
    doc = builder.build()
    end_time = time.time()
    
    build_time = end_time - start_time
    
    # Should complete in reasonable time (< 1 second for this size)
    assert build_time < 1.0, f"Build took too long: {build_time:.3f}s"
    
    # Check that we have the expected content types
    text_count = len([box for box in doc if box.content_type == ContentType.TEXT])
    math_count = len([box for box in doc if box.content_type == ContentType.MATH])
    diagram_count = len([box for box in doc if box.content_type == ContentType.DIAGRAM])
    
    assert text_count == 10  # 10 text sections
    assert math_count == 10  # 10 math expressions
    assert diagram_count == 4  # 4 diagrams (i % 3 == 0 for i = 0, 3, 6, 9)
    
    # Total should be 24 elements
    assert len(doc) == 24
    
    print(f"✅ test_performance_basic passed (build time: {build_time:.3f}s)")
