# tests/test_matrix_layout.py
"""Tests for matrix layout and rendering"""

import pytest
from compose.render.matrix_layout import (
    MatrixLayoutEngine, MatrixParser, render_matrix_to_svg
)


class TestMatrixLayoutEngine:
    """Test matrix layout engine functionality"""

    def test_matrix_engine_initialization(self):
        """Test creating matrix layout engine"""
        engine = MatrixLayoutEngine()
        assert engine.default_matrix_spacing == 10
        assert engine.matrix_vspace == 8

    def test_parse_matrix_content_simple(self):
        """Test parsing simple matrix content"""
        engine = MatrixLayoutEngine()

        content = "a & b \\\\ c & d"
        rows = engine._parse_matrix_content(content)

        assert len(rows) == 2
        assert rows[0] == ["a", "b"]
        assert rows[1] == ["c", "d"]

    def test_parse_matrix_content_empty(self):
        """Test parsing empty matrix content"""
        engine = MatrixLayoutEngine()

        content = ""
        rows = engine._parse_matrix_content(content)

        assert rows == []

    def test_parse_matrix_content_single_row(self):
        """Test parsing single row matrix"""
        engine = MatrixLayoutEngine()

        content = "x & y & z"
        rows = engine._parse_matrix_content(content)

        assert len(rows) == 1
        assert rows[0] == ["x", "y", "z"]

    def test_parse_matrix_content_irregular(self):
        """Test parsing irregular matrix (different column counts)"""
        engine = MatrixLayoutEngine()

        content = "a & b \\\\ c"
        rows = engine._parse_matrix_content(content)

        assert len(rows) == 2
        assert rows[0] == ["a", "b"]
        assert rows[1] == ["c"]

    def test_create_matrix_layout_simple(self):
        """Test creating matrix layout"""
        engine = MatrixLayoutEngine()

        rows = [["a", "b"], ["c", "d"]]
        matrix_box = engine._create_matrix_layout(rows, "matrix")

        assert matrix_box is not None
        assert hasattr(matrix_box, 'width')
        assert hasattr(matrix_box, 'height')

    def test_add_matrix_delimiters_pmatrix(self):
        """Test adding parentheses delimiters"""
        engine = MatrixLayoutEngine()

        # Create a simple inner box
        from compose.layout.tex_boxes import Box
        inner_box = Box(width=100, height=50, box_type="test")

        result = engine._add_matrix_delimiters(inner_box, "pmatrix")

        # Should have added delimiters
        assert result.width > inner_box.width  # Should be wider with delimiters

    def test_add_matrix_delimiters_bmatrix(self):
        """Test adding bracket delimiters"""
        engine = MatrixLayoutEngine()

        from compose.layout.tex_boxes import Box
        inner_box = Box(width=100, height=50, box_type="test")

        result = engine._add_matrix_delimiters(inner_box, "bmatrix")

        assert result.width > inner_box.width

    def test_add_matrix_delimiters_matrix(self):
        """Test matrix environment without delimiters"""
        engine = MatrixLayoutEngine()

        from compose.layout.tex_boxes import Box
        inner_box = Box(width=100, height=50, box_type="test")

        result = engine._add_matrix_delimiters(inner_box, "matrix")

        # Should be the same box (no delimiters added)
        assert result is inner_box


class TestMatrixParser:
    """Test matrix parser functionality"""

    def test_parser_initialization(self):
        """Test creating matrix parser"""
        parser = MatrixParser()
        assert hasattr(parser, 'matrix_layout_engine')

    def test_parse_matrix_expression_simple(self):
        """Test parsing simple matrix expression"""
        parser = MatrixParser()

        latex = r'\begin{matrix} a & b \\ c & d \end{matrix}'
        matrix_box = parser.parse_matrix_expression(latex)

        assert matrix_box is not None

    def test_parse_matrix_expression_pmatrix(self):
        """Test parsing pmatrix expression"""
        parser = MatrixParser()

        latex = r'\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}'
        matrix_box = parser.parse_matrix_expression(latex)

        assert matrix_box is not None

    def test_parse_matrix_expression_invalid(self):
        """Test parsing invalid matrix expression"""
        parser = MatrixParser()

        latex = r'\begin{matrix} a & b'  # Missing end
        matrix_box = parser.parse_matrix_expression(latex)

        assert matrix_box is None

    def test_parse_matrix_expression_empty(self):
        """Test parsing empty matrix expression"""
        parser = MatrixParser()

        latex = r'\begin{matrix}\end{matrix}'
        matrix_box = parser.parse_matrix_expression(latex)

        assert matrix_box is not None

    def test_extract_matrix_from_latex(self):
        """Test extracting matrices from LaTeX text"""
        parser = MatrixParser()

        latex = r'Some text \begin{matrix} a & b \end{matrix} more text \begin{pmatrix} 1 & 2 \end{pmatrix}'
        matrices = parser.extract_matrix_from_latex(latex)

        assert len(matrices) == 2
        assert 'matrix' in matrices[0]
        assert 'pmatrix' in matrices[1]


class TestMatrixRendering:
    """Test matrix rendering functionality"""

    def test_render_matrix_to_svg_simple(self):
        """Test rendering simple matrix to SVG"""
        latex = r'\begin{matrix} a & b \\ c & d \end{matrix}'
        svg_data = render_matrix_to_svg(latex)

        assert svg_data is not None
        assert svg_data.startswith('data:image/svg+xml;base64,')

    def test_render_matrix_to_svg_pmatrix(self):
        """Test rendering pmatrix to SVG"""
        latex = r'\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}'
        svg_data = render_matrix_to_svg(latex)

        assert svg_data is not None
        assert 'svg' in svg_data

    def test_render_matrix_to_svg_invalid(self):
        """Test rendering invalid matrix"""
        latex = r'\begin{matrix} invalid'  # No closing tag
        svg_data = render_matrix_to_svg(latex)

        assert svg_data is None

    def test_render_matrix_svg_generation(self):
        """Test SVG generation for matrix box"""
        from compose.layout.tex_boxes import Box

        engine = MatrixLayoutEngine()
        matrix_box = Box(width=100, height=50, box_type="test")

        svg = engine.render_matrix_svg(matrix_box)

        assert svg.startswith('data:image/svg+xml;base64,')
        assert 'svg' in svg


class TestMatrixIntegration:
    """Test matrix integration with math rendering"""

    def test_matrix_in_math_image_generator(self):
        """Test that matrix expressions are handled by math image generator"""
        from compose.render.math_images import MathImageGenerator

        generator = MathImageGenerator()

        # Test matrix detection
        matrix_content = r'\begin{matrix} a & b \\ c & d \end{matrix}'
        has_matrix = generator._contains_matrix(matrix_content)
        assert has_matrix == True

        # Test non-matrix content
        regular_content = r'x + y = z'
        has_matrix = generator._contains_matrix(regular_content)
        assert has_matrix == False
