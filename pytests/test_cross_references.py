# tests/test_cross_references.py
"""Tests for cross-reference processing system"""

import pytest
from compose.render.cross_references import CrossReferenceProcessor, TableOfContentsGenerator
from compose.model.ast import Document, Paragraph, Text, Heading, MathBlock


class TestCrossReferenceProcessor:
    """Test cross-reference processing functionality"""

    def test_processor_initialization(self):
        """Test creating cross-reference processor"""
        processor = CrossReferenceProcessor()
        assert len(processor.labels) == 0
        assert len(processor.references) == 0
        assert len(processor.unresolved_refs) == 0

    def test_heading_label_extraction(self):
        """Test extracting labels from headings"""
        blocks = [
            Heading(level=1, content=[Text(content="Introduction")]),
            Heading(level=2, content=[Text(content="Background")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})

        processor = CrossReferenceProcessor()
        processor._extract_labels(doc)

        # Should have extracted heading labels
        assert len(processor.labels) >= 2

        # Check that introduction heading has a label
        intro_keys = [k for k in processor.labels.keys() if 'introduction' in k.lower()]
        assert len(intro_keys) > 0

    def test_math_label_extraction(self):
        """Test extracting labels from math blocks"""
        blocks = [
            MathBlock(content=r"\label{eq:pythagoras} a^2 + b^2 = c^2"),
            MathBlock(content=r"\label{eq:integral} \int f(x) dx"),
        ]
        doc = Document(blocks=blocks, frontmatter={})

        processor = CrossReferenceProcessor()
        processor._extract_labels(doc)

        assert 'eq:pythagoras' in processor.labels
        assert 'eq:integral' in processor.labels
        assert len(processor.labels) >= 2

    def test_manual_label_extraction(self):
        """Test extracting manual labels from paragraphs"""
        blocks = [
            Paragraph(content=[Text(content="See [the introduction]{#introduction} for details.")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})

        processor = CrossReferenceProcessor()
        processor._extract_labels(doc)

        assert 'introduction' in processor.labels

    def test_reference_resolution(self):
        """Test resolving cross-references"""
        blocks = [
            Heading(level=1, content=[Text(content="Introduction")]),
            Paragraph(content=[Text(content="See \\ref{introduction} for details.")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})

        processor = CrossReferenceProcessor()
        resolved_doc = processor.process_document(doc)

        # Document should be processed without errors
        assert resolved_doc is not None
        assert len(resolved_doc.blocks) == 2

    def test_unresolved_reference_handling(self):
        """Test handling of unresolved references"""
        blocks = [
            Paragraph(content=[Text(content="See \\ref{nonexistent} for details.")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})

        processor = CrossReferenceProcessor()
        resolved_doc = processor.process_document(doc)

        # Should track unresolved references
        assert 'nonexistent' in processor.unresolved_refs

    def test_cross_reference_validation(self):
        """Test reference validation functionality"""
        processor = CrossReferenceProcessor()
        processor.unresolved_refs.add('missing-ref')

        validation = processor.validate_references()

        assert validation['total_references'] == 0  # No resolved refs in this test
        assert validation['unresolved_references'] == ['missing-ref']
        assert validation['resolution_rate'] == 1.0  # No refs to resolve
        assert len(validation['issues']) == 1

    def test_multiple_reference_formats(self):
        """Test different reference formats"""
        blocks = [
            Heading(level=1, content=[Text(content="Introduction")]),
            Paragraph(content=[Text(content="See \\ref{introduction} and [the intro](#introduction).")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})

        processor = CrossReferenceProcessor()
        resolved_doc = processor.process_document(doc)

        # Should handle both \ref{} and []() formats
        assert len(processor.labels) > 0
        assert resolved_doc is not None

    def test_cross_reference_map(self):
        """Test getting cross-reference map"""
        blocks = [
            Heading(level=1, content=[Text(content="Test")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})

        processor = CrossReferenceProcessor()
        processor._extract_labels(doc)

        ref_map = processor.get_cross_reference_map()
        assert isinstance(ref_map, dict)
        assert len(ref_map) > 0


class TestTableOfContentsGenerator:
    """Test table of contents generation"""

    def test_toc_generator_initialization(self):
        """Test creating TOC generator"""
        generator = TableOfContentsGenerator()
        assert len(generator.toc_entries) == 0

    def test_toc_generation(self):
        """Test generating table of contents"""
        from compose.analysis.document_analyzer import DocumentAnalyzer

        blocks = [
            Heading(level=1, content=[Text(content="Introduction")]),
            Heading(level=2, content=[Text(content="Background")]),
            Heading(level=1, content=[Text(content="Methods")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})

        analyzer = DocumentAnalyzer(doc)
        toc = analyzer.structure.get_table_of_contents()

        assert len(toc) == 3

        # Check structure
        assert toc[0]['level'] == 1
        assert toc[0]['text'] == 'Introduction'
        assert 'id' in toc[0]

        assert toc[1]['level'] == 2
        assert toc[1]['text'] == 'Background'

        assert toc[2]['level'] == 1
        assert toc[2]['text'] == 'Methods'

    def test_toc_hierarchy_building(self):
        """Test building hierarchical TOC structure"""
        from compose.analysis.document_analyzer import DocumentAnalyzer

        blocks = [
            Heading(level=1, content=[Text(content="Chapter 1")]),
            Heading(level=2, content=[Text(content="Section 1.1")]),
            Heading(level=3, content=[Text(content="Subsection 1.1.1")]),
            Heading(level=2, content=[Text(content="Section 1.2")]),
            Heading(level=1, content=[Text(content="Chapter 2")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})

        analyzer = DocumentAnalyzer(doc)
        toc = analyzer.structure.get_table_of_contents()

        # Should maintain document order
        assert len(toc) == 5  # All headings

        assert toc[0]['level'] == 1
        assert toc[1]['level'] == 2
        assert toc[2]['level'] == 3
        assert toc[3]['level'] == 2
        assert toc[4]['level'] == 1

    def test_toc_html_rendering(self):
        """Test rendering TOC as HTML"""
        blocks = [
            Heading(level=1, content=[Text(content="Introduction")]),
            Heading(level=2, content=[Text(content="Background")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})

        generator = TableOfContentsGenerator()
        toc = generator.generate_toc(doc)
        html = generator.render_toc_html(toc)

        assert isinstance(html, str)
        assert '<nav class="table-of-contents">' in html
        assert '<h2>Table of Contents</h2>' in html
        assert '<ul>' in html
        assert 'Introduction' in html
        assert 'Background' in html
        # Note: hierarchical structure means Background is nested under Introduction

    def test_toc_depth_limiting(self):
        """Test limiting TOC depth in HTML rendering"""
        blocks = [
            Heading(level=1, content=[Text(content="Level 1")]),
            Heading(level=2, content=[Text(content="Level 2")]),
            Heading(level=3, content=[Text(content="Level 3")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})

        generator = TableOfContentsGenerator()
        toc = generator.generate_toc(doc)

        # Render with max depth 2
        html = generator.render_toc_html(toc, max_depth=2)

        assert 'Level 1' in html
        assert 'Level 2' in html
        # Level 3 should be excluded
        assert 'Level 3' not in html

    def test_empty_document_toc(self):
        """Test TOC generation for document with no headings"""
        blocks = [
            Paragraph(content=[Text(content="Just content, no headings.")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})

        generator = TableOfContentsGenerator()
        toc = generator.generate_toc(doc)

        assert len(toc) == 0

    def test_toc_id_generation(self):
        """Test heading ID generation for TOC"""
        blocks = [
            Heading(level=1, content=[Text(content="Special Characters: @#$%")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})

        generator = TableOfContentsGenerator()
        toc = generator.generate_toc(doc)

        assert len(toc) == 1
        toc_entry = toc[0]

        # ID should be URL-safe (no special chars)
        toc_id = toc_entry['id']
        assert 'special-characters' in toc_id or 'special_characters' in toc_id
        assert '@' not in toc_id
        assert '#' not in toc_id
        assert '$' not in toc_id
