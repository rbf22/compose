# tests/test_document_analyzer.py
"""Tests for document analysis and relationship tracking"""

import pytest
from compose.model.ast import Document, Heading, Paragraph, Text, MathBlock
from compose.analysis.document_analyzer import DocumentAnalyzer


class TestDocumentAnalyzer:
    """Test document analysis functionality"""

    def test_analyzer_creation(self):
        """Test creating document analyzer"""
        doc = Document(blocks=[], frontmatter={})
        analyzer = DocumentAnalyzer(doc)

        assert analyzer.document == doc
        assert analyzer.structure is not None

    def test_heading_analysis(self):
        """Test analyzing document with headings"""
        blocks = [
            Heading(level=1, content=[Text(content="Chapter 1")]),
            Heading(level=2, content=[Text(content="Section 1.1")]),
            Heading(level=1, content=[Text(content="Chapter 2")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})
        analyzer = DocumentAnalyzer(doc)

        # Should have analyzed headings
        assert 1 in analyzer.structure.headings_by_level
        assert 2 in analyzer.structure.headings_by_level
        assert len(analyzer.structure.headings_by_level[1]) == 2
        assert len(analyzer.structure.headings_by_level[2]) == 1

    def test_table_of_contents(self):
        """Test generating table of contents"""
        blocks = [
            Heading(level=1, content=[Text(content="Introduction")]),
            Heading(level=2, content=[Text(content="Background")]),
            Heading(level=1, content=[Text(content="Methods")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})
        analyzer = DocumentAnalyzer(doc)

        toc = analyzer.structure.get_table_of_contents()

        assert len(toc) == 3
        assert toc[0]['level'] == 1
        assert toc[0]['text'] == 'Introduction'
        assert toc[1]['level'] == 2
        assert toc[1]['text'] == 'Background'
        assert toc[2]['level'] == 1
        assert toc[2]['text'] == 'Methods'

    def test_math_label_analysis(self):
        """Test analyzing math expressions with labels"""
        blocks = [
            MathBlock(content=r"\label{eq:pythagoras} a^2 + b^2 = c^2"),
            Paragraph(content=[Text(content="See equation \\ref{eq:pythagoras}")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})
        analyzer = DocumentAnalyzer(doc)

        # Should have found the label
        assert "eq:pythagoras" in analyzer.structure.references

    def test_cross_reference_resolution(self):
        """Test cross-reference resolution"""
        blocks = [
            Heading(level=1, content=[Text(content="Introduction")]),
            MathBlock(content=r"\label{eq:main} x^2 + y^2 = z^2"),
        ]
        doc = Document(blocks=blocks, frontmatter={})
        analyzer = DocumentAnalyzer(doc)

        # Should be able to resolve references
        ref = analyzer.structure.resolve_reference("eq:main")
        assert ref is not None
        assert isinstance(ref, MathBlock)

    def test_document_validation(self):
        """Test document structure validation"""
        blocks = [
            Heading(level=1, content=[Text(content="Chapter 1")]),
            Heading(level=3, content=[Text(content="Subsection 1.1.1")]),  # Skips level 2
        ]
        doc = Document(blocks=blocks, frontmatter={})
        analyzer = DocumentAnalyzer(doc)

        warnings = analyzer.validate_document_structure()

        # Should warn about skipped heading level
        assert len(warnings) > 0
        assert "heading level jumps" in warnings[0].lower()

    def test_page_layout_calculation(self):
        """Test page layout calculation"""
        blocks = [
            Paragraph(content=[Text(content="Short paragraph.")]),
            Paragraph(content=[Text(content="This is a much longer paragraph with more content that should potentially wrap to multiple lines when rendered.")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})
        analyzer = DocumentAnalyzer(doc)

        pages = analyzer.get_page_layout(400, 300)  # Narrow page

        assert len(pages) >= 1
        assert len(pages[0].blocks) > 0

    def test_generate_cross_references(self):
        """Test generating cross-reference data"""
        blocks = [
            Heading(level=1, content=[Text(content="Introduction")]),
            MathBlock(content=r"\label{eq:integral} \int f(x) dx"),
        ]
        doc = Document(blocks=blocks, frontmatter={})
        analyzer = DocumentAnalyzer(doc)

        xrefs = analyzer.generate_cross_references()

        # Should have heading and math references
        assert len(xrefs) > 0

        # Should have heading reference
        heading_keys = [k for k in xrefs.keys() if 'heading' in k]
        assert len(heading_keys) > 0

        # Should have math reference
        assert 'eq:integral' in xrefs
        assert xrefs['eq:integral']['type'] == 'math_label'
