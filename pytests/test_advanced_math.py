# pytests/test_advanced_math.py
"""Tests for advanced mathematical layout features"""

import pytest
from compose.layout.math_layout import (
    MathLayoutEngine, MathStyle, MathAtom, MathAtomType,
    layout_matrix, layout_fraction, layout_large_operator, layout_radical
)
from compose.layout.universal_box import UniversalBox, ContentType, Dimensions


def test_matrix_layout():
    """Test matrix layout functionality"""
    engine = MathLayoutEngine()

    # Simple 2x2 matrix
    rows = [
        ["a", "b"],
        ["c", "d"]
    ]

    matrix_box = engine.layout_matrix(rows, MathStyle.DISPLAY)

    assert isinstance(matrix_box, UniversalBox)
    assert matrix_box.content_type == ContentType.MATH
    assert matrix_box.attributes.get("math_type") == "matrix"
    assert len(matrix_box.children) == 2  # 2 rows

    # Check that each row has the right number of cells
    for row in matrix_box.children:
        assert len(row.children) == 2  # 2 columns


def test_large_operator_layout():
    """Test large operator layout with limits"""
    engine = MathLayoutEngine()

    # Sum with limits
    sum_box = engine.layout_large_operator("\\sum", "i=1", "n", MathStyle.DISPLAY)

    assert isinstance(sum_box, UniversalBox)
    assert sum_box.attributes.get("math_type") == "large_operator"
    assert len(sum_box.children) >= 2  # Operator + limits

    # Check limits are positioned correctly
    limit_boxes = [child for child in sum_box.children if child.attributes.get("math_type") == "operator_limit"]
    assert len(limit_boxes) == 2  # Lower and upper limits


def test_radical_layout():
    """Test radical (square root) layout"""
    engine = MathLayoutEngine()

    # Simple square root
    sqrt_box = engine.layout_radical("x^2 + y^2")

    assert isinstance(sqrt_box, UniversalBox)
    assert sqrt_box.attributes.get("math_type") == "radical_symbol"

    # Check radicand is positioned correctly
    radicand_boxes = [child for child in sqrt_box.children if child.attributes.get("math_type") == "radicand"]
    assert len(radicand_boxes) == 1


def test_radical_with_index():
    """Test nth root layout"""
    engine = MathLayoutEngine()

    # Cube root
    cube_root_box = engine.layout_radical("x^3 + y^3", "3")

    assert isinstance(cube_root_box, UniversalBox)

    # Should have radical symbol, radicand, and index
    children_types = [child.attributes.get("math_type") for child in cube_root_box.children]
    assert "radical_symbol" in children_types
    assert "radicand" in children_types
    assert "radical_index" in children_types


def test_fraction_layout():
    """Test fraction layout"""
    engine = MathLayoutEngine()

    fraction_box = engine.layout_fraction("a + b", "c - d", MathStyle.DISPLAY)

    assert isinstance(fraction_box, UniversalBox)
    assert fraction_box.attributes.get("math_type") == "fraction"

    # Should have numerator, denominator, and fraction rule
    children_types = [child.attributes.get("math_type") for child in fraction_box.children]
    assert "numerator" in children_types
    assert "denominator" in children_types
    assert "fraction_rule" in children_types


def test_auto_size_delimiters():
    """Test automatic delimiter sizing"""
    engine = MathLayoutEngine()

    # Create a tall content box
    tall_content = UniversalBox(
        content="\\frac{a}{b} + \\int x dx",
        content_type=ContentType.MATH,
        dimensions=Dimensions(width=5.0, height=3.0, depth=1.0)
    )

    left_delim, right_delim = engine.auto_size_delimiters("(", ")", tall_content)

    assert isinstance(left_delim, UniversalBox)
    assert isinstance(right_delim, UniversalBox)
    assert left_delim.attributes.get("math_type") == "delimiter"
    assert right_delim.attributes.get("math_type") == "delimiter"

    # Delimiters should be sized to match content height
    assert left_delim.dimensions.height >= tall_content.dimensions.height


def test_math_spacing():
    """Test mathematical spacing rules"""
    engine = MathLayoutEngine()

    # Create some atoms
    atoms = [
        MathAtom("a", MathAtomType.ORDINARY),
        MathAtom("+", MathAtomType.OPERATOR),
        MathAtom("b", MathAtomType.ORDINARY),
        MathAtom("=", MathAtomType.RELATION),
        MathAtom("c", MathAtomType.ORDINARY)
    ]

    spaced_atoms = engine.apply_math_spacing(atoms)

    assert len(spaced_atoms) >= len(atoms)  # May have spacing atoms added
    assert spaced_atoms[0].content == "a"  # First atom unchanged


def test_convenience_functions():
    """Test convenience functions for common layouts"""
    # Test matrix convenience function
    rows = [["1", "2"], ["3", "4"]]
    matrix_box = layout_matrix(rows)
    assert isinstance(matrix_box, UniversalBox)

    # Test fraction convenience function
    fraction_box = layout_fraction("x", "y")
    assert isinstance(fraction_box, UniversalBox)

    # Test large operator convenience function
    sum_box = layout_large_operator("\\sum", "i=1", "n")
    assert isinstance(sum_box, UniversalBox)

    # Test radical convenience function
    sqrt_box = layout_radical("a^2 + b^2")
    assert isinstance(sqrt_box, UniversalBox)


def test_math_styles():
    """Test different math styles"""
    engine = MathLayoutEngine()

    # Display style should be larger
    display_fraction = engine.layout_fraction("a", "b", MathStyle.DISPLAY)
    inline_fraction = engine.layout_fraction("a", "b", MathStyle.INLINE)

    # Display fractions typically have different positioning
    assert display_fraction.attributes.get("style") != inline_fraction.attributes.get("style")


def test_matrix_alignment():
    """Test matrix column alignment"""
    engine = MathLayoutEngine()

    # Matrix with different content lengths
    rows = [
        ["a", "very_long_content"],
        ["short", "b"]
    ]

    matrix_box = engine.layout_matrix(rows)

    # Both rows should have the same column widths
    row1, row2 = matrix_box.children
    col1_width = row1.children[0].dimensions.width
    col2_width = row1.children[1].dimensions.width

    # Second row should have same column widths
    assert row2.children[0].dimensions.width == col1_width
    assert row2.children[1].dimensions.width == col2_width

    # Shorter content should be padded to match column width
    assert col2_width > col1_width  # Second column is wider


def test_knuth_plass_integration():
    """Test Knuth-Plass line breaking integration"""
    from compose.layout.engines.math_engine import MathLayoutEngine
    from compose.layout.knuth_plass import MathKnuthPlassBreaker

    engine = MathLayoutEngine()

    # Test that Knuth-Plass breaker can be created
    breaker = MathKnuthPlassBreaker(line_width=80.0)
    assert breaker.line_width == 80.0
    assert breaker.tolerance >= 100.0  # Math expressions tolerate more variation
