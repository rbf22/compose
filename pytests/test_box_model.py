# tests/test_box_model.py
"""Tests for the universal box model system."""

from compose.layout.box_model import (
    MathBox, BoxType, Dimensions, GlueSpace, MathSpacing,
    create_atom_box, create_operator_box, create_fraction_box
)
from compose.layout.universal_box import (
    UniversalBox, ContentType, BoxType as UBoxType, RenderingStyle,
    create_text_box, create_paragraph_box, create_diagram_box
)


def test_dimensions_creation():
    """Test creating dimensions."""
    dim = Dimensions(10.0, 5.0, 2.0)
    assert dim.width == 10.0
    assert dim.height == 5.0
    assert dim.depth == 2.0
    assert dim.total_height == 7.0  # height + depth
    print("✅ test_dimensions_creation passed")


def test_glue_space_creation():
    """Test creating glue space."""
    glue = GlueSpace(natural_width=5.0, stretch=2.0, shrink=1.0)
    assert glue.natural_width == 5.0
    assert glue.stretch == 2.0
    assert glue.shrink == 1.0
    
    # Test width computation
    stretched = glue.compute_width(0.5)  # 50% stretch
    assert stretched == 6.0  # 5.0 + 0.5 * 2.0
    
    shrunk = glue.compute_width(-0.5)  # 50% shrink
    assert shrunk == 4.5  # 5.0 + (-0.5) * 1.0
    print("✅ test_glue_space_creation passed")


def test_math_box_creation():
    """Test creating math boxes."""
    box = MathBox(
        content="x",
        box_type=BoxType.ATOM,
        dimensions=Dimensions(5.0, 4.0, 1.0)
    )
    
    assert box.content == "x"
    assert box.box_type == BoxType.ATOM
    assert box.dimensions.width == 5.0
    assert box.is_atomic()
    assert not box.is_composite()
    print("✅ test_math_box_creation passed")


def test_math_box_spacing():
    """Test math box automatic spacing."""
    op_box = MathBox(
        content="+",
        box_type=BoxType.OPERATOR,
        dimensions=Dimensions(7.0, 5.0, 1.0)
    )
    
    # Operator should get automatic spacing
    assert op_box.left_glue is not None
    assert op_box.right_glue is not None
    assert op_box.left_glue.natural_width > 0
    print("✅ test_math_box_spacing passed")


def test_create_atom_box():
    """Test atom box factory function."""
    box = create_atom_box("x", font_size=12.0)
    
    assert box.content == "x"
    assert box.box_type == BoxType.ATOM
    assert box.font_size == 12.0
    assert box.dimensions.width > 0
    print("✅ test_create_atom_box passed")


def test_create_operator_box():
    """Test operator box factory function."""
    box = create_operator_box("+", font_size=10.0)
    
    assert box.content == "+"
    assert box.box_type == BoxType.OPERATOR
    assert box.font_size == 10.0
    assert box.dimensions.width > 0
    print("✅ test_create_operator_box passed")


def test_create_fraction_box():
    """Test fraction box factory function."""
    num = create_atom_box("a")
    den = create_atom_box("b")
    
    frac = create_fraction_box(num, den, rule_thickness=0.4)
    
    assert frac.box_type == BoxType.FRACTION
    assert frac.is_composite()
    assert len(frac.content) == 2
    assert frac.dimensions.height > num.dimensions.height
    assert frac.dimensions.depth > den.dimensions.depth
    print("✅ test_create_fraction_box passed")


def test_universal_box_creation():
    """Test creating universal boxes."""
    box = UniversalBox(
        content="Hello",
        content_type=ContentType.TEXT,
        box_type=UBoxType.INLINE
    )
    
    assert box.content == "Hello"
    assert box.content_type == ContentType.TEXT
    assert box.box_type == UBoxType.INLINE
    assert box.is_atomic()
    print("✅ test_universal_box_creation passed")


def test_universal_box_container():
    """Test universal box as container."""
    child1 = UniversalBox("Child 1", ContentType.TEXT)
    child2 = UniversalBox("Child 2", ContentType.TEXT)
    
    container = UniversalBox(
        content=[child1, child2],
        content_type=ContentType.TEXT,
        box_type=UBoxType.BLOCK
    )
    
    assert container.is_container()
    assert len(container.get_children()) == 2
    
    # Test adding children
    child3 = UniversalBox("Child 3", ContentType.TEXT)
    container.add_child(child3)
    assert len(container.get_children()) == 3
    print("✅ test_universal_box_container passed")


def test_rendering_style():
    """Test rendering style system."""
    style = RenderingStyle(
        font_family="Arial",
        font_size=14.0,
        color="#FF0000",
        font_weight="bold"
    )
    
    assert style.font_family == "Arial"
    assert style.font_size == 14.0
    assert style.color == "#FF0000"
    assert style.font_weight == "bold"
    print("✅ test_rendering_style passed")


def test_universal_box_styling():
    """Test applying styles to universal boxes."""
    box = UniversalBox("Styled text", ContentType.TEXT)
    
    new_style = RenderingStyle(
        font_size=16.0,
        color="#0000FF"
    )
    
    box.apply_style(new_style)
    assert box.style.font_size == 16.0
    assert box.style.color == "#0000FF"
    print("✅ test_universal_box_styling passed")


def test_universal_box_spacing():
    """Test universal box spacing rules."""
    # Block element should get vertical spacing
    block_box = UniversalBox(
        content="Block content",
        content_type=ContentType.TEXT,
        box_type=UBoxType.BLOCK
    )
    
    assert block_box.top_glue is not None
    assert block_box.bottom_glue is not None
    assert block_box.top_glue.natural_width > 0
    
    # Inline element should get minimal spacing
    inline_box = UniversalBox(
        content="Inline content",
        content_type=ContentType.TEXT,
        box_type=UBoxType.INLINE
    )
    
    assert inline_box.top_glue.natural_width == 0
    assert inline_box.bottom_glue.natural_width == 0
    print("✅ test_universal_box_spacing passed")


def test_create_text_box():
    """Test text box factory function."""
    box = create_text_box("Hello, World!")
    
    assert box.content == "Hello, World!"
    assert box.content_type == ContentType.TEXT
    assert box.box_type == UBoxType.INLINE
    print("✅ test_create_text_box passed")


def test_create_paragraph_box():
    """Test paragraph box factory function."""
    text1 = create_text_box("First sentence.")
    text2 = create_text_box("Second sentence.")
    
    para = create_paragraph_box([text1, text2])
    
    assert para.content_type == ContentType.TEXT
    assert para.box_type == UBoxType.BLOCK
    assert len(para.content) == 2
    print("✅ test_create_paragraph_box passed")


def test_create_diagram_box():
    """Test diagram box factory function."""
    code = "graph TD\n  A --> B"
    box = create_diagram_box(code, "mermaid")
    
    assert box.content == code
    assert box.content_type == ContentType.DIAGRAM
    assert box.box_type == UBoxType.BLOCK
    assert box.attributes["diagram_type"] == "mermaid"
    print("✅ test_create_diagram_box passed")


def test_math_spacing_constants():
    """Test mathematical spacing constants."""
    assert MathSpacing.THIN_SPACE == 3.0
    assert MathSpacing.MEDIUM_SPACE == 4.0
    assert MathSpacing.THICK_SPACE == 5.0
    assert MathSpacing.NEGATIVE_THIN == -3.0
    assert MathSpacing.QUAD_SPACE == 18.0
    print("✅ test_math_spacing_constants passed")


def test_box_total_dimensions():
    """Test box total dimension calculations."""
    box = UniversalBox(
        content="Test",
        content_type=ContentType.TEXT,
        dimensions=Dimensions(50.0, 10.0, 2.0)
    )
    
    # Add some glue
    box.left_glue = GlueSpace(5.0, 2.0, 1.0)
    box.right_glue = GlueSpace(5.0, 2.0, 1.0)
    box.top_glue = GlueSpace(3.0, 1.0, 0.5)
    box.bottom_glue = GlueSpace(3.0, 1.0, 0.5)
    
    total_width = box.total_width()
    total_height = box.total_height()
    
    assert total_width == 60.0  # 50 + 5 + 5
    assert total_height == 18.0  # (10 + 2) + 3 + 3
    print("✅ test_box_total_dimensions passed")
