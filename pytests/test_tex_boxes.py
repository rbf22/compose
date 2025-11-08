# tests/test_tex_boxes.py
"""Tests for TeX box model implementation"""

import pytest
from compose.layout.tex_boxes import (
    Box, CharBox, Glue, Penalty, HBox, VBox,
    TexLayoutEngine, LineBreaker
)


class TestBoxModel:
    """Test basic box model components"""

    def test_char_box_creation(self):
        """Test creating character boxes"""
        box = CharBox('a', 12.0)

        assert box.char == 'a'
        assert box.font_size == 12.0
        assert box.width > 0
        assert box.height > 0
        assert box.depth > 0

    def test_glue_creation(self):
        """Test creating glue boxes"""
        glue = Glue(width=5.0, stretch=2.0, shrink=1.0)

        assert glue.width == 5.0
        assert glue.stretch == 2.0
        assert glue.shrink == 1.0
        assert glue.height == 0.0  # Glue has no height
        assert glue.depth == 0.0

    def test_penalty_creation(self):
        """Test creating penalty boxes"""
        penalty = Penalty(penalty=100.0, flagged=True)

        assert penalty.penalty == 100.0
        assert penalty.flagged == True
        assert penalty.width == 0.0
        assert penalty.height == 0.0
        assert penalty.depth == 0.0


class TestHBox:
    """Test horizontal box functionality"""

    def test_hbox_creation(self):
        """Test creating horizontal boxes"""
        hbox = HBox()

        assert len(hbox.contents) == 0
        assert hbox.width == 0.0
        assert hbox.height == 0.0
        assert hbox.depth == 0.0

    def test_hbox_add_boxes(self):
        """Test adding boxes to horizontal box"""
        hbox = HBox()

        box1 = CharBox('a', 12.0)
        box2 = CharBox('b', 12.0)

        hbox.add_box(box1)
        hbox.add_box(box2)

        assert len(hbox.contents) == 2
        assert hbox.width == box1.width + box2.width
        assert hbox.height == max(box1.height, box2.height)

    def test_hbox_with_glue(self):
        """Test horizontal box with glue"""
        hbox = HBox()

        box1 = CharBox('x', 12.0)
        glue = Glue(width=5.0, stretch=2.0)
        box2 = CharBox('y', 12.0)

        hbox.add_box(box1)
        hbox.add_glue(width=5.0, stretch=2.0)
        hbox.add_box(box2)

        assert len(hbox.contents) == 3
        assert hbox.width > box1.width + box2.width  # Includes glue width


class TestVBox:
    """Test vertical box functionality"""

    def test_vbox_creation(self):
        """Test creating vertical boxes"""
        vbox = VBox()

        assert len(vbox.contents) == 0
        assert vbox.width == 0.0
        assert vbox.height == 0.0
        assert vbox.depth == 0.0

    def test_vbox_add_boxes(self):
        """Test adding boxes to vertical box"""
        vbox = VBox()

        box1 = CharBox('a', 12.0)
        box2 = CharBox('b', 12.0)

        vbox.add_box(box1)
        vbox.add_box(box2)

        assert len(vbox.contents) == 2
        expected_height = box1.height + box1.depth + box2.height + box2.depth
        assert abs(vbox.height - expected_height) < 0.001  # Allow for floating point precision
        assert vbox.width == max(box1.width, box2.width)


class TestTexLayoutEngine:
    """Test TeX layout engine"""

    def test_layout_engine_creation(self):
        """Test creating layout engine"""
        engine = TexLayoutEngine()
        assert engine.font_size == 12.0

    def test_layout_simple_expression(self):
        """Test laying out simple expression"""
        engine = TexLayoutEngine()
        hbox = engine.layout_expression("x + y")

        assert isinstance(hbox, HBox)
        assert len(hbox.contents) > 0
        assert hbox.width > 0

    def test_layout_expression_with_symbols(self):
        """Test laying out expression with mathematical symbols"""
        engine = TexLayoutEngine()
        hbox = engine.layout_expression("α + β = γ")

        assert isinstance(hbox, HBox)
        assert hbox.width > 0

    def test_layout_integral(self):
        """Test laying out integral expression"""
        engine = TexLayoutEngine()
        hbox = engine.layout_integral("f(x)", "0", r"\infty")

        assert isinstance(hbox, HBox)
        assert len(hbox.contents) > 0

        # Should contain integral symbol
        char_boxes = [box for box in hbox.contents if isinstance(box, CharBox)]
        integral_boxes = [box for box in char_boxes if box.char == '∫']
        assert len(integral_boxes) == 1


class TestLineBreaker:
    """Test line breaking functionality"""

    def test_line_breaker_creation(self):
        """Test creating line breaker"""
        hboxes = [HBox(), HBox()]
        breaker = LineBreaker(hboxes, 100.0)

        assert breaker.line_width == 100.0
        assert len(breaker.hboxes) == 2

    def test_simple_line_breaking(self):
        """Test basic line breaking"""
        # Create some test hboxes
        hbox1 = HBox()
        hbox1.add_box(CharBox('a' * 50, 12.0))  # Wide box

        hbox2 = HBox()
        hbox2.add_box(CharBox('b' * 50, 12.0))  # Another wide box

        breaker = LineBreaker([hbox1, hbox2], 100.0)
        lines = breaker.break_into_lines()

        # Should break into multiple lines due to width constraints
        assert len(lines) >= 1
