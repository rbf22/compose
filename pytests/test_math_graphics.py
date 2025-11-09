"""
Tests for TeX-style PDF math graphics rendering.

Tests the MathGraphicsRenderer that converts MathBox structures
to PDF graphics commands for proper mathematical typesetting.
"""

import pytest
from compose.render.math_graphics import MathGraphicsRenderer
from compose.layout.box_model import (
    MathBox, BoxType, create_atom_box, create_operator_box,
    create_fraction_box, Dimensions
)


class TestMathGraphicsRenderer:
    """Test suite for MathGraphicsRenderer."""
    
    def test_render_simple_atom(self):
        """Test rendering a simple atomic box."""
        renderer = MathGraphicsRenderer()
        
        # Create a simple atom box
        atom = create_atom_box("x", font_size=12.0)
        
        # Render it
        commands, width = renderer.render_math_box(atom, x=100, y=200, baseline_y=200)
        
        # Should produce PDF commands
        assert len(commands) > 0
        assert any("BT" in cmd for cmd in commands)  # Begin text
        assert any("ET" in cmd for cmd in commands)  # End text
        assert width > 0
    
    def test_render_operator(self):
        """Test rendering an operator."""
        renderer = MathGraphicsRenderer()
        
        # Create operator box
        op = create_operator_box("+", font_size=12.0)
        
        # Render it
        commands, width = renderer.render_math_box(op, x=100, y=200, baseline_y=200)
        
        # Should produce PDF commands
        assert len(commands) > 0
        assert width > 0
    
    def test_render_fraction(self):
        """Test rendering a fraction with horizontal bar."""
        renderer = MathGraphicsRenderer()
        
        # Create fraction: x / y
        numerator = create_atom_box("x", font_size=12.0)
        denominator = create_atom_box("y", font_size=12.0)
        fraction = create_fraction_box(numerator, denominator)
        
        # Render it
        commands, width = renderer.render_math_box(fraction, x=100, y=200, baseline_y=200)
        
        # Should produce PDF commands including line drawing
        assert len(commands) > 0
        # Should contain line drawing commands (q, w, RG, m, l, S, Q)
        assert any("q" in cmd for cmd in commands)  # Save graphics state
        assert any("S" in cmd for cmd in commands)  # Stroke path
        assert width > 0
    
    def test_render_superscript(self):
        """Test rendering superscript."""
        renderer = MathGraphicsRenderer()
        
        # Create base box
        base = create_atom_box("x", font_size=12.0)
        
        # Create superscript box
        superscript = create_atom_box("2", font_size=12.0)
        
        # Create script box containing base and superscript
        script_box = MathBox(
            content=[base, superscript],
            box_type=BoxType.SCRIPT,
            dimensions=Dimensions(
                width=base.dimensions.width + superscript.dimensions.width,
                height=base.dimensions.height + superscript.dimensions.height,
                depth=base.dimensions.depth
            ),
            font_size=12.0
        )
        
        # Render it
        commands, width = renderer.render_math_box(script_box, x=100, y=200, baseline_y=200)
        
        # Should produce PDF commands
        assert len(commands) > 0
        assert width > 0
    
    def test_render_radical(self):
        """Test rendering a radical (square root)."""
        renderer = MathGraphicsRenderer()
        
        # Create content box
        content = create_atom_box("x", font_size=12.0)
        
        # Create radical box
        radical_box = MathBox(
            content=[content],
            box_type=BoxType.RADICAL,
            dimensions=Dimensions(
                width=content.dimensions.width + 10,
                height=content.dimensions.height + 5,
                depth=content.dimensions.depth
            ),
            font_size=12.0
        )
        
        # Render it
        commands, width = renderer.render_math_box(radical_box, x=100, y=200, baseline_y=200)
        
        # Should produce PDF commands including line drawing
        assert len(commands) > 0
        assert any("q" in cmd for cmd in commands)  # Save graphics state
        assert width > 0
    
    def test_render_with_positioning(self):
        """Test rendering with shift_up and shift_right adjustments."""
        renderer = MathGraphicsRenderer()
        
        # Create atom with positioning
        atom = create_atom_box("x", font_size=12.0)
        atom.shift_up = 5.0
        atom.shift_right = 3.0
        
        # Render it
        commands, width = renderer.render_math_box(atom, x=100, y=200, baseline_y=200)
        
        # Should produce PDF commands with adjusted positioning
        assert len(commands) > 0
        # Check that positioning is applied (should see adjusted coordinates)
        assert any("103" in cmd for cmd in commands)  # x + shift_right
    
    def test_render_complex_expression(self):
        """Test rendering a complex expression."""
        renderer = MathGraphicsRenderer()
        
        # Create a more complex structure
        # (x + y) / (a + b)
        x = create_atom_box("x", font_size=12.0)
        plus1 = create_operator_box("+", font_size=12.0)
        y = create_atom_box("y", font_size=12.0)
        
        a = create_atom_box("a", font_size=12.0)
        plus2 = create_operator_box("+", font_size=12.0)
        b = create_atom_box("b", font_size=12.0)
        
        # Create numerator and denominator as composite boxes
        numerator = MathBox(
            content=[x, plus1, y],
            box_type=BoxType.ATOM,
            dimensions=Dimensions(
                width=x.dimensions.width + plus1.dimensions.width + y.dimensions.width,
                height=max(x.dimensions.height, plus1.dimensions.height, y.dimensions.height),
                depth=max(x.dimensions.depth, plus1.dimensions.depth, y.dimensions.depth)
            ),
            font_size=12.0
        )
        
        denominator = MathBox(
            content=[a, plus2, b],
            box_type=BoxType.ATOM,
            dimensions=Dimensions(
                width=a.dimensions.width + plus2.dimensions.width + b.dimensions.width,
                height=max(a.dimensions.height, plus2.dimensions.height, b.dimensions.height),
                depth=max(a.dimensions.depth, plus2.dimensions.depth, b.dimensions.depth)
            ),
            font_size=12.0
        )
        
        fraction = create_fraction_box(numerator, denominator)
        
        # Render it
        commands, width = renderer.render_math_box(fraction, x=100, y=200, baseline_y=200)
        
        # Should produce PDF commands
        assert len(commands) > 0
        assert width > 0
    
    def test_pdf_literal_escaping(self):
        """Test that special characters are properly escaped in PDF literals."""
        renderer = MathGraphicsRenderer()
        
        # Create atom with special characters
        atom = create_atom_box("(test)", font_size=12.0)
        
        # Render it
        commands, width = renderer.render_math_box(atom, x=100, y=200, baseline_y=200)
        
        # Should escape parentheses
        assert any("\\(" in cmd or "\\)" in cmd for cmd in commands)
    
    def test_font_style_mapping(self):
        """Test that font styles are correctly mapped."""
        renderer = MathGraphicsRenderer()
        
        # Test different font styles
        styles = ["normal", "italic", "bold", "bold_italic"]
        
        for style in styles:
            atom = create_atom_box("x", font_size=12.0)
            atom.font_style = style
            
            commands, width = renderer.render_math_box(atom, x=100, y=200, baseline_y=200)
            
            # Should produce PDF commands with appropriate font
            assert len(commands) > 0
            assert width > 0


class TestMathGraphicsIntegration:
    """Integration tests with PDF renderer."""
    
    def test_math_graphics_with_pdf_renderer(self):
        """Test that math graphics renderer integrates with PDF renderer."""
        # This test would require a full PDF renderer instance
        # For now, just verify the renderer can be instantiated
        from compose.render.pdf_renderer import ProfessionalPDFRenderer
        
        renderer = ProfessionalPDFRenderer()
        graphics = MathGraphicsRenderer(renderer)
        
        assert graphics.pdf_renderer is renderer


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
