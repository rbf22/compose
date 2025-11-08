# tests/test_universal_layout.py
"""Tests for the universal layout engine."""

from compose.layout.layout_engine import UniversalLayoutEngine, DocumentBuilder
from compose.layout.universal_box import UniversalBox, ContentType, BoxType, RenderingStyle
from compose.layout.box_model import MathBox, Dimensions


def test_universal_layout_engine_creation():
    """Test creating a universal layout engine."""
    engine = UniversalLayoutEngine()
    assert engine is not None
    assert engine.math_engine is not None
    assert engine.diagram_engine is not None
    print("✅ test_universal_layout_engine_creation passed")


def test_document_builder_text():
    """Test document builder with text content."""
    builder = DocumentBuilder()
    doc = builder.add_text("Hello, World!").build()
    
    assert len(doc) == 1
    assert doc[0].content_type == ContentType.TEXT
    assert doc[0].content == "Hello, World!"
    print("✅ test_document_builder_text passed")


def test_document_builder_math():
    """Test document builder with math content."""
    builder = DocumentBuilder()
    doc = builder.add_math("x^2 + y^2 = z^2", display=True).build()
    
    assert len(doc) == 1
    assert doc[0].content_type == ContentType.MATH
    assert doc[0].box_type == BoxType.BLOCK
    print("✅ test_document_builder_math passed")


def test_document_builder_diagram():
    """Test document builder with diagram content."""
    builder = DocumentBuilder()
    diagram_code = """
graph TD
    A[Start] --> B[End]
"""
    doc = builder.add_diagram(diagram_code.strip()).build()
    
    assert len(doc) == 1
    assert doc[0].content_type == ContentType.DIAGRAM
    assert doc[0].box_type == BoxType.BLOCK
    print("✅ test_document_builder_diagram passed")


def test_mixed_content_document():
    """Test document with mixed content types."""
    builder = DocumentBuilder()
    doc = (builder
        .add_text("Introduction")
        .add_math("E = mc^2", display=True)
        .add_diagram("graph LR\n  A --> B")
        .build())
    
    assert len(doc) == 3
    assert doc[0].content_type == ContentType.TEXT
    assert doc[1].content_type == ContentType.MATH
    assert doc[2].content_type == ContentType.DIAGRAM
    print("✅ test_mixed_content_document passed")


def test_universal_box_creation():
    """Test creating universal boxes."""
    text_box = UniversalBox(
        content="Hello",
        content_type=ContentType.TEXT,
        box_type=BoxType.INLINE
    )
    
    assert text_box.content == "Hello"
    assert text_box.content_type == ContentType.TEXT
    assert text_box.box_type == BoxType.INLINE
    assert text_box.is_atomic()
    assert not text_box.is_container()
    print("✅ test_universal_box_creation passed")


def test_universal_box_container():
    """Test universal box as container."""
    child1 = UniversalBox("Child 1", ContentType.TEXT)
    child2 = UniversalBox("Child 2", ContentType.TEXT)
    
    container = UniversalBox(
        content=[child1, child2],
        content_type=ContentType.TEXT,
        box_type=BoxType.BLOCK
    )
    
    assert container.is_container()
    assert not container.is_atomic()
    assert len(container.get_children()) == 2
    print("✅ test_universal_box_container passed")


def test_layout_engine_page_settings():
    """Test layout engine page configuration."""
    engine = UniversalLayoutEngine()
    
    # Test default settings
    assert engine.current_page_width == 612.0
    assert engine.current_page_height == 792.0
    
    # Test setting custom page size
    engine.set_page_size(800, 600)
    assert engine.current_page_width == 800
    assert engine.current_page_height == 600
    
    # Test margins
    engine.set_margins(50, 40, 50, 40)
    assert engine.margins['top'] == 50
    assert engine.margins['right'] == 40
    
    # Test content dimensions
    content_width = engine.get_content_width()
    assert content_width == 800 - 40 - 40  # width - left - right
    print("✅ test_layout_engine_page_settings passed")


def test_typography_processing():
    """Test typography improvements in text processing."""
    engine = UniversalLayoutEngine()
    
    text_box = UniversalBox(
        content='This has "quotes" and -- dashes and ... ellipses',
        content_type=ContentType.TEXT
    )
    
    processed = engine._process_text_box(text_box)
    content = processed.content
    
    # Check smart typography
    assert '"' in content or '"' in content  # Smart quotes
    assert '–' in content  # En dash
    assert '…' in content  # Ellipsis
    print("✅ test_typography_processing passed")
