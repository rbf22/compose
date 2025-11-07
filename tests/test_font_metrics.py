# tests/test_font_metrics.py
"""Tests for the font metrics system."""

from compose.layout.font_metrics import (
    MathFontMetrics, FontStyle, FontParameters, CharacterMetrics,
    default_math_font
)


def test_font_parameters_creation():
    """Test creating font parameters."""
    params = FontParameters(
        x_height=4.3,
        quad_width=10.0,
        sup_shift_up=4.2,
        sub_shift_down=1.5,
        sup_drop=3.8,
        sub_drop=0.5,
        num_shift_up=6.8,
        denom_shift_down=2.7,
        rule_thickness=0.4,
        radical_rule_thickness=0.4,
        radical_extra_ascender=1.0,
        thin_mu_skip=3.0,
        med_mu_skip=4.0,
        thick_mu_skip=5.0,
        display_op_min_height=8.5
    )
    
    assert params.x_height == 4.3
    assert params.quad_width == 10.0
    assert params.sup_shift_up == 4.2
    assert params.sub_shift_down == 1.5
    assert params.rule_thickness == 0.4
    print("✅ test_font_parameters_creation passed")


def test_character_metrics_creation():
    """Test creating character metrics."""
    metrics = CharacterMetrics(
        width=5.5,
        height=4.3,
        depth=0.0,
        italic_correction=0.5
    )
    
    assert metrics.width == 5.5
    assert metrics.height == 4.3
    assert metrics.depth == 0.0
    assert metrics.italic_correction == 0.5
    print("✅ test_character_metrics_creation passed")


def test_math_font_metrics_creation():
    """Test creating math font metrics."""
    font = MathFontMetrics("Test Font")
    
    assert font.font_name == "Test Font"
    assert font._font_params is not None
    assert len(font._char_metrics) > 0
    print("✅ test_math_font_metrics_creation passed")


def test_character_metrics_lookup():
    """Test looking up character metrics."""
    font = MathFontMetrics()
    
    # Test basic Latin letters
    a_metrics = font.get_char_metrics('a')
    assert a_metrics is not None
    assert a_metrics.width > 0
    assert a_metrics.height > 0
    
    # Test uppercase letters
    A_metrics = font.get_char_metrics('A')
    assert A_metrics is not None
    assert A_metrics.width > a_metrics.width  # Uppercase should be wider
    
    # Test digits
    digit_metrics = font.get_char_metrics('5')
    assert digit_metrics is not None
    assert digit_metrics.width > 0
    print("✅ test_character_metrics_lookup passed")


def test_operator_metrics():
    """Test operator character metrics."""
    font = MathFontMetrics()
    
    plus_metrics = font.get_char_metrics('+')
    assert plus_metrics is not None
    assert plus_metrics.width > 0
    
    equals_metrics = font.get_char_metrics('=')
    assert equals_metrics is not None
    assert equals_metrics.width > 0
    
    # Relations should be wider than operators
    assert equals_metrics.width >= plus_metrics.width
    print("✅ test_operator_metrics passed")


def test_greek_letter_metrics():
    """Test Greek letter metrics."""
    font = MathFontMetrics()
    
    alpha_metrics = font.get_char_metrics('α')
    assert alpha_metrics is not None
    assert alpha_metrics.width > 0
    assert alpha_metrics.italic_correction > 0  # Greek letters are italic
    
    pi_metrics = font.get_char_metrics('π')
    assert pi_metrics is not None
    assert pi_metrics.width > 0
    print("✅ test_greek_letter_metrics passed")


def test_font_parameters_access():
    """Test accessing font parameters."""
    font = MathFontMetrics()
    params = font.get_font_parameters()
    
    assert params.x_height > 0
    assert params.quad_width > 0
    assert params.sup_shift_up > 0
    assert params.sub_shift_down > 0
    assert params.rule_thickness > 0
    print("✅ test_font_parameters_access passed")


def test_operator_spacing():
    """Test operator spacing rules."""
    font = MathFontMetrics()
    
    # Test spacing between different element types
    atom_op_spacing = font.get_operator_spacing('atom', 'operator')
    assert atom_op_spacing > 0
    
    atom_rel_spacing = font.get_operator_spacing('atom', 'relation')
    assert atom_rel_spacing > 0
    
    # Relations should have more space than operators
    assert atom_rel_spacing >= atom_op_spacing
    
    # Punctuation should have minimal spacing
    punct_spacing = font.get_operator_spacing('atom', 'punctuation')
    assert punct_spacing == 0
    print("✅ test_operator_spacing passed")


def test_style_scaling():
    """Test font scaling for different styles."""
    font = MathFontMetrics()
    
    base_size = 10.0
    
    # Roman and italic should be same scale
    roman_size = font.scale_for_style(base_size, FontStyle.ROMAN)
    italic_size = font.scale_for_style(base_size, FontStyle.ITALIC)
    assert roman_size == base_size
    assert italic_size == base_size
    
    # Script should be smaller
    script_size = font.scale_for_style(base_size, FontStyle.SCRIPT)
    assert script_size < base_size
    assert script_size == base_size * 0.7
    print("✅ test_style_scaling passed")


def test_large_operator_metrics():
    """Test large operator metrics."""
    font = MathFontMetrics()
    
    # Test inline large operator
    inline_sum = font.get_large_operator_metrics('∑', display_style=False)
    assert inline_sum.width > 0
    assert inline_sum.height > 0
    
    # Test display large operator
    display_sum = font.get_large_operator_metrics('∑', display_style=True)
    assert display_sum.width > inline_sum.width
    assert display_sum.height > inline_sum.height
    
    # Display should be 1.4x larger
    assert abs(display_sum.width - inline_sum.width * 1.4) < 0.1
    print("✅ test_large_operator_metrics passed")


def test_default_math_font():
    """Test the default math font instance."""
    font = default_math_font
    
    assert font is not None
    assert font.font_name == "Computer Modern Math"
    
    # Should have basic character metrics loaded
    x_metrics = font.get_char_metrics('x')
    assert x_metrics is not None
    
    # Should have font parameters
    params = font.get_font_parameters()
    assert params.x_height > 0
    print("✅ test_default_math_font passed")


def test_missing_character_handling():
    """Test handling of missing characters."""
    font = MathFontMetrics()
    
    # Test non-existent character
    missing_metrics = font.get_char_metrics('🦄')  # Unicorn emoji
    assert missing_metrics is None
    
    # Test unknown spacing combination
    unknown_spacing = font.get_operator_spacing('unknown', 'unknown')
    assert unknown_spacing == 0.0
    print("✅ test_missing_character_handling passed")


def test_font_style_enum():
    """Test font style enumeration."""
    assert FontStyle.ROMAN.value == "roman"
    assert FontStyle.ITALIC.value == "italic"
    assert FontStyle.BOLD.value == "bold"
    assert FontStyle.SCRIPT.value == "script"
    assert FontStyle.FRAKTUR.value == "fraktur"
    assert FontStyle.MONOSPACE.value == "monospace"
    assert FontStyle.SANS_SERIF.value == "sans"
    print("✅ test_font_style_enum passed")


def test_comprehensive_character_coverage():
    """Test that font has good character coverage."""
    font = MathFontMetrics()
    
    # Test basic Latin alphabet
    for char in "abcdefghijklmnopqrstuvwxyz":
        metrics = font.get_char_metrics(char)
        assert metrics is not None, f"Missing metrics for '{char}'"
    
    # Test digits
    for char in "0123456789":
        metrics = font.get_char_metrics(char)
        assert metrics is not None, f"Missing metrics for '{char}'"
    
    # Test common operators
    for char in "+-=<>()[]{}":
        metrics = font.get_char_metrics(char)
        assert metrics is not None, f"Missing metrics for '{char}'"
    
    # Test some Greek letters
    for char in "αβγδπθλμσφω":
        metrics = font.get_char_metrics(char)
        assert metrics is not None, f"Missing metrics for '{char}'"
    
    print("✅ test_comprehensive_character_coverage passed")
