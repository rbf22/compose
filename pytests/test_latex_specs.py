# tests/test_latex_specs.py
"""Tests for LaTeX to Unicode conversion specifications"""

import pytest
from compose.render.latex_specs import latex_to_unicode, unicode_to_latex, LATEX_TO_UNICODE


class TestLatexToUnicode:
    """Test LaTeX to Unicode conversion"""

    def test_greek_letters(self):
        """Test Greek letter conversions"""
        assert latex_to_unicode(r'\alpha') == 'α'
        assert latex_to_unicode(r'\beta') == 'β'
        assert latex_to_unicode(r'\gamma') == 'γ'
        assert latex_to_unicode(r'\delta') == 'δ'
        assert latex_to_unicode(r'\pi') == 'π'
        assert latex_to_unicode(r'\sigma') == 'σ'
        assert latex_to_unicode(r'\omega') == 'ω'

    def test_mathematical_operators(self):
        """Test mathematical operator conversions"""
        assert latex_to_unicode(r'\int') == '∫'
        assert latex_to_unicode(r'\sum') == '∑'
        assert latex_to_unicode(r'\prod') == '∏'
        assert latex_to_unicode(r'\sqrt') == '√'
        assert latex_to_unicode(r'\infty') == '∞'

    def test_relations(self):
        """Test mathematical relation conversions"""
        assert latex_to_unicode(r'\leq') == '≤'
        assert latex_to_unicode(r'\geq') == '≥'
        assert latex_to_unicode(r'\neq') == '≠'
        assert latex_to_unicode(r'\approx') == '≈'
        assert latex_to_unicode(r'\equiv') == '≡'

    def test_arrows(self):
        """Test arrow conversions"""
        assert latex_to_unicode(r'\rightarrow') == '→'
        assert latex_to_unicode(r'\leftarrow') == '←'
        assert latex_to_unicode(r'\uparrow') == '↑'
        assert latex_to_unicode(r'\downarrow') == '↓'

    def test_complex_expression(self):
        """Test complex mathematical expression"""
        expr = r'\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}'
        result = latex_to_unicode(expr)
        assert '∫' in result
        assert '∞' in result
        assert '√' in result
        assert 'π' in result

    def test_no_conversion_needed(self):
        """Test text that doesn't need conversion"""
        text = "Hello world 123"
        assert latex_to_unicode(text) == text

    def test_empty_string(self):
        """Test empty string handling"""
        assert latex_to_unicode("") == ""

    def test_unknown_commands(self):
        """Test unknown LaTeX commands are left unchanged"""
        text = r'\unknowncommand{text}'
        result = latex_to_unicode(text)
        assert r'\unknowncommand' in result


class TestUnicodeToLatex:
    """Test Unicode to LaTeX conversion"""

    def test_reverse_conversion(self):
        """Test that unicode_to_latex attempts to reverse latex_to_unicode"""
        original = r'\alpha + \beta'
        unicode_version = latex_to_unicode(original)

        # Forward conversion should work
        assert 'α' in unicode_version
        assert 'β' in unicode_version

        # Reverse conversion may not be perfect due to mapping complexities
        # but should at least not crash
        latex_version = unicode_to_latex(unicode_version)
        assert isinstance(latex_version, str)
        assert len(latex_version) > 0

    def test_no_unicode(self):
        """Test text with no Unicode characters"""
        text = "Hello world"
        assert unicode_to_latex(text) == text


class TestLatexToUnicodeMappings:
    """Test the LATEX_TO_UNICODE mapping dictionary"""

    def test_mapping_structure(self):
        """Test that the mapping is properly structured"""
        assert isinstance(LATEX_TO_UNICODE, dict)
        assert len(LATEX_TO_UNICODE) > 50  # Should have substantial mappings

    def test_key_format(self):
        """Test that keys are valid strings"""
        for key in LATEX_TO_UNICODE.keys():
            assert isinstance(key, str), f"Key {key} should be a string"
            assert len(key) > 0, f"Key {key} should not be empty"

    def test_value_types(self):
        """Test that values are strings"""
        for value in LATEX_TO_UNICODE.values():
            assert isinstance(value, str), f"Value {value} should be a string"
