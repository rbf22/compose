# tests/test_multi_page.py
"""Tests for multi-page document rendering"""

import pytest
from compose.render.multi_page import MultiPageRenderer, PageCrossReferenceManager
from compose.model.ast import Document, Paragraph, Text, Heading


class TestMultiPageRenderer:
    """Test multi-page rendering functionality"""

    def test_renderer_initialization(self):
        """Test creating a multi-page renderer"""
        renderer = MultiPageRenderer()
        assert renderer.page_width == 800
        assert renderer.page_height == 600
        assert renderer.margins == {'top': 50, 'bottom': 50, 'left': 40, 'right': 40}

    def test_custom_page_dimensions(self):
        """Test renderer with custom page dimensions"""
        renderer = MultiPageRenderer(
            page_width=1000,
            page_height=800,
            margins={'top': 30, 'bottom': 30, 'left': 25, 'right': 25}
        )
        assert renderer.page_width == 1000
        assert renderer.page_height == 800
        assert renderer.margins['top'] == 30

    def test_single_page_rendering(self):
        """Test rendering a simple document as single page"""
        # Create a simple document with only paragraphs (no headings that force page breaks)
        blocks = [
            Paragraph(content=[Text(content="This is a simple paragraph.")]),
            Paragraph(content=[Text(content="This is another paragraph.")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})

        renderer = MultiPageRenderer(page_height=800)
        pages = renderer.render_multi_page(doc, 'html')

        assert len(pages) == 1
        assert pages[0]['page_number'] == 1
        assert pages[0]['total_pages'] == 1
        assert 'page' in pages[0]['content'].lower()
        assert 'simple paragraph' in pages[0]['content']

    def test_multi_page_rendering(self):
        """Test rendering document across multiple pages"""
        # Create content that should span multiple pages
        blocks = []
        for i in range(50):  # Create many paragraphs
            blocks.append(Paragraph(content=[Text(content=f"Paragraph {i} with some content that takes up space.")]))

        doc = Document(blocks=blocks, frontmatter={})

        renderer = MultiPageRenderer(page_height=200)  # Small page height to force breaks
        pages = renderer.render_multi_page(doc, 'html')

        assert len(pages) > 1  # Should create multiple pages
        assert all(page['page_number'] > 0 for page in pages)
        assert all(page['total_pages'] == len(pages) for page in pages)

    def test_page_break_detection(self):
        """Test that page breaks are inserted at appropriate places"""
        blocks = [
            Paragraph(content=[Text(content="Before break")]),
            Heading(level=1, content=[Text(content="Chapter Break")]),  # Should force page break
            Paragraph(content=[Text(content="After break")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})

        renderer = MultiPageRenderer()
        pages = renderer.render_multi_page(doc, 'html')

        # Should create at least 2 pages due to heading
        assert len(pages) >= 2

    def test_page_navigation(self):
        """Test page navigation information"""
        blocks = [Paragraph(content=[Text(content=f"Page {i}")]) for i in range(10)]
        doc = Document(blocks=blocks, frontmatter={})

        renderer = MultiPageRenderer(page_height=100)  # Force multiple pages
        pages = renderer.render_multi_page(doc, 'html')

        assert len(pages) > 1

        # Check navigation info
        first_page = pages[0]
        last_page = pages[-1]

        assert 'has_next' in first_page or first_page['page_number'] < len(pages)
        assert 'has_previous' not in last_page or last_page['page_number'] == len(pages)

    def test_html_page_structure(self):
        """Test that HTML pages have correct structure"""
        blocks = [Paragraph(content=[Text(content="Test content")])]
        doc = Document(blocks=blocks, frontmatter={})

        renderer = MultiPageRenderer()
        pages = renderer.render_multi_page(doc, 'html')

        content = pages[0]['content']
        assert '<div class="page"' in content
        assert 'data-page="1"' in content
        assert 'Test content' in content  # Should contain the rendered paragraph

    def test_text_page_rendering(self):
        """Test rendering pages as plain text"""
        blocks = [Paragraph(content=[Text(content="Test content")])]
        doc = Document(blocks=blocks, frontmatter={})

        renderer = MultiPageRenderer()
        pages = renderer.render_multi_page(doc, 'text')

        content = pages[0]['content']
        assert 'Page 1 of 1' in content
        assert 'Test content' in content
        assert '--- End of Page 1 ---' in content


class TestPageCrossReferenceManager:
    """Test cross-reference management across pages"""

    def test_cross_reference_initialization(self):
        """Test creating cross-reference manager"""
        pages = [{'page_number': 1, 'blocks': []}]
        manager = PageCrossReferenceManager(pages)
        assert manager.pages == pages

    def test_reference_resolution(self):
        """Test resolving references to page locations"""
        # Create pages with some referenceable content
        blocks1 = [Heading(level=1, content=[Text(content="Introduction")])]
        blocks2 = [Paragraph(content=[Text(content="More content")])]

        pages = [
            {'page_number': 1, 'blocks': blocks1},
            {'page_number': 2, 'blocks': blocks2}
        ]

        manager = PageCrossReferenceManager(pages)

        # Should be able to resolve heading reference
        ref = manager.resolve_reference('heading-0-introduction')
        assert ref is not None
        assert ref['page'] == 1
        assert ref['type'] == 'heading'

    def test_unresolved_reference(self):
        """Test handling of unresolved references"""
        pages = [{'page_number': 1, 'blocks': []}]
        manager = PageCrossReferenceManager(pages)

        ref = manager.resolve_reference('nonexistent-ref')
        assert ref is None

    def test_page_references(self):
        """Test getting references for a specific page"""
        # Create mock pages with references
        pages = [
            {'page_number': 1, 'blocks': []},
            {'page_number': 2, 'blocks': []}
        ]

        manager = PageCrossReferenceManager(pages)
        # Manually add a reference for testing
        manager.reference_map['test-ref'] = {'page': 1, 'type': 'test'}

        refs = manager.get_page_references(1)
        assert len(refs) == 1
        assert refs[0]['type'] == 'test'

    def test_navigation_generation(self):
        """Test generating navigation information"""
        pages = [
            {'page_number': 1, 'blocks': []},
            {'page_number': 2, 'blocks': []},
            {'page_number': 3, 'blocks': []}
        ]

        manager = PageCrossReferenceManager(pages)
        navigation = manager.generate_page_navigation()

        assert len(navigation) == 3

        # Check first page navigation
        nav1 = navigation[1]
        assert nav1['has_previous'] == False
        assert nav1['has_next'] == True
        assert nav1['next_page'] == 2

        # Check middle page navigation
        nav2 = navigation[2]
        assert nav2['has_previous'] == True
        assert nav2['has_next'] == True
        assert nav2['previous_page'] == 1
        assert nav2['next_page'] == 3

        # Check last page navigation
        nav3 = navigation[3]
        assert nav3['has_previous'] == True
        assert nav3['has_next'] == False
        assert nav3['previous_page'] == 2
