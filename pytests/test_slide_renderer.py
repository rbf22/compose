# tests/test_slide_renderer.py
"""Tests for slide presentation system"""

import pytest
from compose.render.slide_renderer import SlideRenderer, SlideLayoutEngine, SlideBox
from compose.model.ast import Document, Heading, Paragraph, ListBlock, ListItem, Text


class TestSlideLayoutEngine:
    """Test slide layout engine functionality"""

    def test_layout_engine_initialization(self):
        """Test creating slide layout engine"""
        engine = SlideLayoutEngine()
        assert engine.slide_width == 1024
        assert engine.slide_height == 768
        assert engine.title_font_size == 48
        assert engine.content_font_size == 24

    def test_create_title_slide(self):
        """Test creating title slide"""
        engine = SlideLayoutEngine()
        slide = engine.create_title_slide("My Presentation", "A great talk", "John Doe")

        assert isinstance(slide, SlideBox)
        assert slide.slide_type == "title"
        assert slide.title == "My Presentation"
        assert len(slide.content_boxes) == 1
        assert slide.width == 1024
        assert slide.height == 768

    def test_create_content_slide(self):
        """Test creating content slide with bullet points"""
        engine = SlideLayoutEngine()

        # Create test content
        content_blocks = [
            ListBlock(items=[
                ListItem(content=[Text(content="First point")]),
                ListItem(content=[Text(content="Second point")])
            ], ordered=False)
        ]

        slide = engine.create_content_slide("Content Slide", content_blocks)

        assert isinstance(slide, SlideBox)
        assert slide.slide_type == "content"
        assert slide.title == "Content Slide"
        assert len(slide.content_boxes) == 1

    def test_create_comparison_slide(self):
        """Test creating comparison slide"""
        engine = SlideLayoutEngine()

        left_content = [Paragraph(content=[Text(content="Left side content")])]
        right_content = [Paragraph(content=[Text(content="Right side content")])]

        slide = engine.create_comparison_slide(
            "Option A", left_content,
            "Option B", right_content
        )

        assert isinstance(slide, SlideBox)
        assert slide.slide_type == "comparison"
        assert "Option A vs Option B" in slide.title


class TestSlideRenderer:
    """Test slide renderer functionality"""

    def test_renderer_initialization(self):
        """Test creating slide renderer"""
        renderer = SlideRenderer()
        assert hasattr(renderer, 'layout_engine')
        assert hasattr(renderer, 'animation_system')

    def test_render_slide_deck_simple(self):
        """Test rendering simple slide deck"""
        # Create test document with headings
        blocks = [
            Heading(level=1, content=[Text(content="Title Slide")]),
            Paragraph(content=[Text(content="Welcome to the presentation")]),
            Heading(level=1, content=[Text(content="Content Slide")]),
            ListBlock(items=[
                ListItem(content=[Text(content="Point 1")]),
                ListItem(content=[Text(content="Point 2")])
            ], ordered=False)
        ]
        doc = Document(blocks=blocks, frontmatter={'title': 'Test Presentation'})

        renderer = SlideRenderer()
        html = renderer.render_slide_deck(doc)

        # Should be valid HTML
        assert html.startswith('<!DOCTYPE html>')
        assert '<html' in html
        assert '</html>' in html
        assert 'Test Presentation' in html

        # Should contain slide elements
        assert 'class="slide"' in html
        assert 'Title Slide' in html
        assert 'Content Slide' in html

        # Should contain navigation script
        assert 'currentSlide' in html
        assert 'nextSlide()' in html

    def test_slide_extraction_from_headings(self):
        """Test that slides are created from level 1 headings"""
        blocks = [
            Heading(level=1, content=[Text(content="Slide 1")]),
            Paragraph(content=[Text(content="Content for slide 1")]),
            Heading(level=1, content=[Text(content="Slide 2")]),
            Paragraph(content=[Text(content="Content for slide 2")]),
            Heading(level=1, content=[Text(content="Slide 3")]),
            ListBlock(items=[ListItem(content=[Text(content="Item 1")])], ordered=False)
        ]
        doc = Document(blocks=blocks, frontmatter={})

        renderer = SlideRenderer()
        html = renderer.render_slide_deck(doc)

        # Should create 3 slides from 3 level 1 headings
        slide_count = html.count('class="slide"')
        assert slide_count == 3

        # Should contain slide titles
        assert 'Slide 1' in html
        assert 'Slide 2' in html
        assert 'Slide 3' in html

    def test_empty_document_slides(self):
        """Test slide rendering for empty document"""
        doc = Document(blocks=[], frontmatter={})

        renderer = SlideRenderer()
        html = renderer.render_slide_deck(doc)

        # Should still produce valid HTML
        assert html.startswith('<!DOCTYPE html>')
        assert 'class="slide"' in html  # At least one slide

    def test_slide_navigation_script(self):
        """Test that navigation script is included"""
        blocks = [Heading(level=1, content=[Text(content="Test Slide")])]
        doc = Document(blocks=blocks, frontmatter={})

        renderer = SlideRenderer()
        html = renderer.render_slide_deck(doc)

        # Should contain JavaScript for navigation
        assert '<script>' in html
        assert 'function nextSlide()' in html
        assert 'function prevSlide()' in html
        assert 'ArrowRight' in html
        assert 'ArrowLeft' in html

    def test_slide_css_styling(self):
        """Test that CSS styling is included"""
        blocks = [Heading(level=1, content=[Text(content="Test Slide")])]
        doc = Document(blocks=blocks, frontmatter={})

        renderer = SlideRenderer()
        html = renderer.render_slide_deck(doc)

        # Should contain CSS
        assert '<style>' in html
        assert '.slide' in html
        assert '.slide-title' in html
        assert '.slide-content' in html

    def test_slide_animations(self):
        """Test that animation classes are included"""
        # Create slide with list content that should get animations
        blocks = [
            Heading(level=1, content=[Text(content="Animated Slide")]),
            ListBlock(items=[
                ListItem(content=[Text(content="Animated item 1")]),
                ListItem(content=[Text(content="Animated item 2")])
            ], ordered=False)
        ]
        doc = Document(blocks=blocks, frontmatter={})

        renderer = SlideRenderer()
        html = renderer.render_slide_deck(doc)

        # Should contain animation CSS
        assert '@keyframes fadeIn' in html or '@keyframes slideUp' in html
        assert '.animated' in html
        assert '.fade-in' in html

    def test_touch_navigation(self):
        """Test that touch navigation is included"""
        blocks = [Heading(level=1, content=[Text(content="Touch Slide")])]
        doc = Document(blocks=blocks, frontmatter={})

        renderer = SlideRenderer()
        html = renderer.render_slide_deck(doc)

        # Should contain touch event handlers
        assert 'touchstart' in html
        assert 'touchend' in html
        assert 'touches[0].clientX' in html


class TestSlideBox:
    """Test SlideBox functionality"""

    def test_slide_box_creation(self):
        """Test creating slide box"""
        from compose.layout.tex_boxes import Box

        slide = SlideBox(
            slide_type="content",
            title="Test Slide"
        )

        # Manually set content_boxes for testing
        test_boxes = [Box(width=100, height=50, box_type="text")]
        slide.content_boxes = test_boxes

        assert slide.slide_type == "content"
        assert slide.title == "Test Slide"
        assert len(slide.content_boxes) == 1
        assert slide.box_type == "slide"

    def test_slide_box_with_animations(self):
        """Test slide box with animations"""
        slide = SlideBox(
            slide_type="content",
            title="Animated Slide",
            animations=[{"type": "fade_in", "element_id": "content", "delay": 0.5}]
        )

        assert len(slide.animations) == 1
        assert slide.animations[0]["type"] == "fade_in"
        assert slide.animations[0]["delay"] == 0.5
