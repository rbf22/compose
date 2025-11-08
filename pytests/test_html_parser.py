# tests/test_html_parser.py
"""Tests for HTML math expression parsing"""

import pytest
from compose.render.html_parser import HTMLMathProcessor


class TestHTMLMathProcessor:
    """Test HTML math expression processing"""

    def test_extract_inline_math(self):
        """Test extracting inline math expressions"""
        html = '<p>Here is <span class="math" style="font-style: italic; color: #c92c2c;">[E = mc^2]</span> and more text.</p>'
        processor = HTMLMathProcessor()

        expressions = processor._extract_math_expressions(html)
        assert len(expressions) == 1
        assert expressions[0] == ("E = mc^2", False)  # inline

    def test_extract_block_math(self):
        """Test extracting block math expressions"""
        html = '''
        <div class="math-block">
            <div class="math-placeholder">
                ∫_{-∞}^{∞} e^{-x²} dx = √{π}
            </div>
        </div>
        '''
        processor = HTMLMathProcessor()

        expressions = processor._extract_math_expressions(html)
        assert len(expressions) == 1
        content, is_display = expressions[0]
        assert is_display == True  # block math
        assert r"\int" in content  # Should contain LaTeX integral command
        assert r"\infty" in content  # Should contain LaTeX infinity command

    def test_extract_mixed_math(self):
        """Test extracting both inline and block math"""
        html = '''
        <p>Inline: <span class="math" style="font-style: italic; color: #c92c2c;">[x^2]</span></p>
        <div class="math-block">
            <div class="math-placeholder">
                ∑_{i=1}^{n} x_i
            </div>
        </div>
        '''
        processor = HTMLMathProcessor()

        expressions = processor._extract_math_expressions(html)
        assert len(expressions) == 2

        # First should be inline
        assert expressions[0] == ("x^2", False)

        # Second should be block
        content, is_display = expressions[1]
        assert is_display == True
        assert r"\sum" in content  # Should contain LaTeX sum command

    def test_replace_inline_math(self):
        """Test replacing inline math with images"""
        html = '<p>Formula: <span class="math" style="font-style: italic; color: #c92c2c;">[E=mc^2]</span> here.</p>'
        processor = HTMLMathProcessor()

        # Mock the image generator to return a test URL
        processor.image_generator.get_all_math_images = lambda exprs: {
            expr: f"data:image/svg+xml;base64,test_{i}" for i, (expr, _) in enumerate(exprs)
        }

        result = processor.process_html(html)

        # Should contain image tag instead of span
        assert '<img src="data:image/svg+xml;base64,test_0"' in result
        assert 'class="math-image math-inline"' in result
        assert '[E=mc^2]' not in result  # Original should be gone

    def test_replace_block_math(self):
        """Test replacing block math with images"""
        html = '''
        <div class="math-block">
            <div class="math-placeholder">
                ∫ x dx
            </div>
        </div>
        '''
        processor = HTMLMathProcessor()

        # Mock the image generator
        processor.image_generator.get_all_math_images = lambda exprs: {
            expr[0]: f"data:image/svg+xml;base64,test_{i}" for i, expr in enumerate(exprs)
        }

        result = processor.process_html(html)

        # Should contain image container
        assert 'math-image-container' in result
        assert 'math-image math-block' in result
        assert '∫ x dx' not in result  # Original should be gone

    def test_no_math_content(self):
        """Test processing HTML with no math content"""
        html = '<p>This is just regular text with no math.</p>'
        processor = HTMLMathProcessor()

        expressions = processor._extract_math_expressions(html)
        assert len(expressions) == 0

        result = processor.process_html(html)
        assert result == html  # Should be unchanged

    def test_unicode_to_latex_conversion(self):
        """Test that Unicode symbols in HTML are converted back to LaTeX"""
        html = '''
        <div class="math-block">
            <div class="math-placeholder">
                ∫_{-∞}^{∞} e^{-x²} dx = √{π}
            </div>
        </div>
        '''
        processor = HTMLMathProcessor()

        expressions = processor._extract_math_expressions(html)
        assert len(expressions) == 1

        latex_content, _ = expressions[0]
        # Should have been converted back to LaTeX commands
        assert r'\int' in latex_content
        assert r'\infty' in latex_content
        assert r'\sqrt' in latex_content
        assert r'\pi' in latex_content
