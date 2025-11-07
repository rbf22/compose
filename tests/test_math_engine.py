# tests/test_math_engine.py
"""Tests for the mathematical layout engine."""

from compose.layout.engines.math_engine import MathLayoutEngine, ExpressionLayout
from compose.layout.content.math_parser import MathExpressionParser
from compose.layout import MathBox, Dimensions
from compose.layout.box_model import BoxType  # Import the math BoxType


def test_math_layout_engine_creation():
    """Test creating a math layout engine."""
    engine = MathLayoutEngine()
    assert engine is not None
    assert engine.font_metrics is not None
    assert not engine.display_style  # Default is inline
    print("✅ test_math_layout_engine_creation passed")


def test_expression_layout_creation():
    """Test creating an expression layout."""
    layout = ExpressionLayout(display_style=True)
    assert layout is not None
    assert layout.engine.display_style == True
    print("✅ test_expression_layout_creation passed")


def test_math_parser_creation():
    """Test creating a math expression parser."""
    parser = MathExpressionParser()
    assert parser is not None
    assert parser.font_metrics is not None
    assert len(parser.greek_letters) > 0
    assert len(parser.operators) > 0
    print("✅ test_math_parser_creation passed")


def test_parse_simple_expression():
    """Test parsing a simple mathematical expression."""
    parser = MathExpressionParser()
    box = parser.parse_expression("x + y")
    
    assert isinstance(box, MathBox)
    assert box.dimensions.width > 0
    print("✅ test_parse_simple_expression passed")


def test_parse_greek_letters():
    """Test parsing Greek letters."""
    parser = MathExpressionParser()
    box = parser.parse_expression("\\alpha + \\beta")
    
    assert isinstance(box, MathBox)
    # Should contain Greek symbols
    print("✅ test_parse_greek_letters passed")


def test_parse_superscript():
    """Test parsing superscripts."""
    parser = MathExpressionParser()
    box = parser.parse_expression("x^2")
    
    assert isinstance(box, MathBox)
    assert box.box_type == BoxType.SCRIPT
    print("✅ test_parse_superscript passed")


def test_parse_subscript():
    """Test parsing subscripts."""
    parser = MathExpressionParser()
    box = parser.parse_expression("x_i")
    
    assert isinstance(box, MathBox)
    assert box.box_type == BoxType.SCRIPT
    print("✅ test_parse_subscript passed")


def test_parse_complex_expression():
    """Test parsing a complex mathematical expression."""
    parser = MathExpressionParser()
    box = parser.parse_expression("x^2 + y^2 = z^2")
    
    assert isinstance(box, MathBox)
    assert box.dimensions.width > 0
    print("✅ test_parse_complex_expression passed")


def test_layout_fraction():
    """Test fraction layout."""
    engine = MathLayoutEngine()
    
    # Create simple boxes for numerator and denominator
    from compose.layout.box_model import create_atom_box
    num = create_atom_box("a")
    den = create_atom_box("b")
    
    fraction = engine.layout_fraction(num, den)
    
    assert isinstance(fraction, MathBox)
    assert fraction.box_type == BoxType.FRACTION
    assert fraction.dimensions.width > 0
    assert fraction.dimensions.height > 0
    print("✅ test_layout_fraction passed")


def test_layout_superscript():
    """Test superscript layout."""
    engine = MathLayoutEngine()
    
    from compose.layout.box_model import create_atom_box
    base = create_atom_box("x")
    sup = create_atom_box("2")
    
    script = engine.layout_superscript(base, sup)
    
    assert isinstance(script, MathBox)
    assert script.box_type == BoxType.SCRIPT
    assert script.dimensions.width > base.dimensions.width
    print("✅ test_layout_superscript passed")


def test_layout_subscript():
    """Test subscript layout."""
    engine = MathLayoutEngine()
    
    from compose.layout.box_model import create_atom_box
    base = create_atom_box("x")
    sub = create_atom_box("i")
    
    script = engine.layout_subscript(base, sub)
    
    assert isinstance(script, MathBox)
    assert script.box_type == BoxType.SCRIPT
    assert script.dimensions.depth > base.dimensions.depth
    print("✅ test_layout_subscript passed")


def test_layout_subsuperscript():
    """Test combined subscript and superscript layout."""
    engine = MathLayoutEngine()
    
    from compose.layout.box_model import create_atom_box
    base = create_atom_box("x")
    sub = create_atom_box("i")
    sup = create_atom_box("2")
    
    script = engine.layout_subsuperscript(base, sub, sup)
    
    assert isinstance(script, MathBox)
    assert script.box_type == BoxType.SCRIPT
    assert len(script.content) == 3  # base, sup, sub
    print("✅ test_layout_subsuperscript passed")


def test_expression_layout_simple():
    """Test simple expression layout."""
    layout = ExpressionLayout()
    box = layout.layout_simple_expression(["x", "+", "y"])
    
    assert isinstance(box, MathBox)
    assert box.dimensions.width > 0
    print("✅ test_expression_layout_simple passed")


def test_expression_layout_fraction():
    """Test fraction layout through expression layout."""
    layout = ExpressionLayout()
    box = layout.layout_fraction("a + b", "c + d")
    
    assert isinstance(box, MathBox)
    assert box.box_type == BoxType.FRACTION
    print("✅ test_expression_layout_fraction passed")


def test_expression_layout_power():
    """Test power layout through expression layout."""
    layout = ExpressionLayout()
    box = layout.layout_power("x", "2")
    
    assert isinstance(box, MathBox)
    assert box.box_type == BoxType.SCRIPT
    print("✅ test_expression_layout_power passed")


def test_math_spacing_rules():
    """Test mathematical spacing rules."""
    engine = MathLayoutEngine()
    
    from compose.layout.box_model import create_atom_box, create_operator_box
    atom = create_atom_box("x")
    op = create_operator_box("+")
    
    boxes = [atom, op, atom]
    spaced = engine._apply_spacing_rules(boxes)
    
    assert len(spaced) == 3
    # Operator should have spacing
    assert spaced[1].left_glue is not None
    print("✅ test_math_spacing_rules passed")


def test_font_metrics_integration():
    """Test font metrics integration."""
    parser = MathExpressionParser()
    
    # Test character metrics lookup
    metrics = parser.font_metrics.get_char_metrics('x')
    assert metrics is not None
    assert metrics.width > 0
    assert metrics.height > 0
    
    # Test font parameters
    params = parser.font_metrics.get_font_parameters()
    assert params.x_height > 0
    assert params.sup_shift_up > 0
    print("✅ test_font_metrics_integration passed")
