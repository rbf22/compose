# pytests/test_advanced_features.py
"""Tests for advanced Compose features: macros, microtypography, TeX compatibility"""

import pytest
from compose.macro_system import MacroProcessor, expand_macros, MacroError
from compose.microtypography import MicroTypographyEngine
from compose.tex_compatibility import TexCompatibilityEngine


class TestMacroSystem:
    """Test the LaTeX-style macro system"""

    def test_basic_macro_definition(self):
        """Test defining and using a simple macro"""
        processor = MacroProcessor()

        # Define a simple macro
        processor.define_macro("hello", 1, "Hello, #1!")

        # Test expansion
        result = processor.expand_macros(r"\hello{World}")
        assert result.expanded == "Hello, World!"
        assert "hello" in result.macros_used

    def test_newcommand_parsing(self):
        """Test parsing \newcommand directives"""
        processor = MacroProcessor()

        # Test newcommand parsing
        processor.process_newcommand(r"\newcommand{\hello}[1]{Hello, #1!}")

        result = processor.expand_macros(r"\hello{World}")
        assert result.expanded == "Hello, World!"

    def test_parameter_substitution(self):
        """Test parameter substitution with multiple parameters"""
        processor = MacroProcessor()

        processor.define_macro("vector", 2, "(#1, #2)")

        result = processor.expand_macros(r"\vector{x}{y}")
        assert result.expanded == "(x, y)"

    def test_recursive_expansion(self):
        """Test recursive macro expansion"""
        processor = MacroProcessor()

        # Define macros that reference each other
        processor.define_macro("bold", 1, "\\textbf{#1}")
        processor.define_macro("important", 1, "\\bold{IMPORTANT: #1}")

        result = processor.expand_macros(r"\important{Test}")
        assert result.expanded == "\\textbf{IMPORTANT: Test}"
        assert set(result.macros_used) == {"bold", "important"}

    def test_builtin_macros(self):
        """Test built-in macro definitions"""
        processor = MacroProcessor()

        # Test built-in text formatting macros
        result = processor.expand_macros(r"\textbf{test}")
        assert result.expanded == "\\mathbf{test}"

        # Test math operators
        result = processor.expand_macros(r"\sin x")
        assert result.expanded == "\\mathop{\\mathrm{sin}}\\nolimits x"

    def test_macro_scoping(self):
        """Test macro scoping"""
        processor = MacroProcessor()

        # Global macro
        processor.define_macro("global", 1, "GLOBAL: #1")

        # Push local scope
        processor.push_scope()
        processor.define_macro("local", 1, "LOCAL: #1")

        # Test scoping
        result = processor.expand_macros(r"\global{test} \local{test}")
        assert result.expanded == "GLOBAL: test LOCAL: test"

        # Pop scope
        processor.pop_scope()

        # Local macro should no longer exist
        result = processor.expand_macros(r"\local{test}")
        assert result.expanded == r"\local{test}"  # Unchanged

    def test_macro_errors(self):
        """Test macro error handling"""
        processor = MacroProcessor()

        # Test undefined macro
        result = processor.expand_macros(r"\undefined{test}")
        assert result.expanded == r"\undefined{test}"

        # Test wrong parameter count
        processor.define_macro("test", 2, "#1 and #2")
        with pytest.raises(MacroError):
            processor.expand_macros(r"\test{one}")  # Missing parameter

    def test_protected_macros(self):
        """Test protected macro behavior"""
        processor = MacroProcessor()

        # Define protected macro
        processor.define_macro("protected", 1, "PROTECTED: #1", protected=True)

        # Should not be able to redefine
        with pytest.raises(MacroError):
            processor.define_macro("protected", 1, "NEW: #1")


class TestMicroTypography:
    """Test micro-typography features"""

    def test_character_protrusion(self):
        """Test character protrusion calculations"""
        engine = MicroTypographyEngine()

        # Test line with punctuation that can protrude
        line = '"Hello, world!"'
        left_protrusion, right_protrusion = engine._calculate_protrusion(line, 12.0)

        # Should have right protrusion for closing quote
        assert right_protrusion > 0

    def test_line_adjustments(self):
        """Test line adjustment calculations"""
        engine = MicroTypographyEngine()

        # Short line that needs expansion
        line = "Hello world"
        adjustment = engine.adjust_line(line, len(line), 80.0)

        # Should recommend some expansion
        assert adjustment.expansion_ratio > 1.0

    def test_paragraph_enhancement(self):
        """Test paragraph-level micro-typography"""
        engine = MicroTypographyEngine()

        paragraph = "This is a test.\nAnother line here."
        enhanced = engine.enhance_paragraph(paragraph)

        # Should contain adjustment comments
        assert "expansion:" in enhanced or "protrusion:" in enhanced


class TestTexCompatibility:
    """Test TeX compatibility features"""

    def test_box_operations(self):
        """Test TeX-style box operations"""
        engine = TexCompatibilityEngine()

        box = engine.create_box(10.0, 5.0, 2.0)
        assert box.width == 10.0
        assert box.height == 5.0
        assert box.depth == 2.0

    def test_glue_operations(self):
        """Test TeX-style glue operations"""
        engine = TexCompatibilityEngine()

        glue = engine.create_glue(5.0, stretch=3.0, shrink=1.0)
        assert glue.width == 5.0
        assert glue.stretch == 3.0
        assert glue.shrink == 1.0

    def test_badness_calculation(self):
        """Test badness calculation for line adjustments"""
        engine = TexCompatibilityEngine()

        # Small adjustment should have low badness
        badness_small = engine.calculate_badness(0.1)
        assert badness_small < 1.0

        # Large adjustment should have high badness
        badness_large = engine.calculate_badness(1.5)
        assert badness_large > 1000000  # Very bad

    def test_trip_test_subset(self):
        """Test TeX compatibility test suite"""
        engine = TexCompatibilityEngine()

        results = engine.run_trip_test_subset()

        # Should have summary with score
        assert 'summary' in results
        assert 'score' in results['summary']
        assert 0.0 <= results['summary']['score'] <= 1.0

    def test_tex_style_line_breaking(self):
        """Test TeX-style line breaking"""
        engine = TexCompatibilityEngine()

        text = "This is a sample paragraph for testing TeX-style line breaking algorithms."
        lines = engine.typeset_paragraph_tex_style(text, 50.0)

        # Should break into multiple lines
        assert len(lines) > 1
        assert all(len(line) <= 60 for line in lines)  # Approximate limit


class TestIntegration:
    """Test integration of advanced features"""

    def test_macro_expansion_in_build(self):
        """Test that macros are expanded during document building"""
        from compose.macro_system import macro_processor

        # Define a test macro
        macro_processor.define_macro("testmacro", 1, "EXPANDED: #1")

        # Test expansion
        result = macro_processor.expand_macros(r"Before \testmacro{content} after")
        assert "EXPANDED: content" in result.expanded

    def test_microtypography_integration(self):
        """Test microtypography can be applied to text"""
        from compose.microtypography import microtypography_engine

        # Test basic functionality
        adjustment = microtypography_engine.adjust_line("Test line", 9, 50.0)
        assert isinstance(adjustment.expansion_ratio, float)
        assert adjustment.expansion_ratio >= 0.95  # Within bounds

    def test_tex_compatibility_demonstration(self):
        """Test TeX compatibility demonstration"""
        from compose.tex_compatibility import tex_compatibility_engine

        demo = tex_compatibility_engine.demonstrate_tex_compatibility()

        # Should contain key information
        assert "TeX Compatibility" in demo
        assert "Trip Test" in demo
        assert "Box-and-glue" in demo
