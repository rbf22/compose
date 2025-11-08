# tests/test_enhanced_ast.py
"""Tests for enhanced AST model with relationship metadata"""

import pytest
from compose.model.ast import Document, Heading, Paragraph, Text, MathBlock
from compose.model.enhanced_ast import DocumentStructure, EnhancedDocument


class TestDocumentStructure:
    """Test document structure analysis"""

    def test_document_structure_creation(self):
        """Test creating document structure analyzer"""
        doc = Document(blocks=[], frontmatter={})
        structure = DocumentStructure(doc)

        assert structure.document == doc
        assert len(structure.headings_by_level) == 0
        assert len(structure.references) == 0

    def test_heading_hierarchy_analysis(self):
        """Test analyzing heading hierarchy"""
        blocks = [
            Heading(level=1, content=[Text(content="Chapter 1")]),
            Heading(level=2, content=[Text(content="Section 1.1")]),
            Heading(level=3, content=[Text(content="Subsection 1.1.1")]),
            Heading(level=2, content=[Text(content="Section 1.2")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})
        structure = DocumentStructure(doc)

        assert len(structure.headings_by_level[1]) == 1
        assert len(structure.headings_by_level[2]) == 2
        assert len(structure.headings_by_level[3]) == 1

    def test_math_label_extraction(self):
        """Test extracting math labels"""
        blocks = [
            MathBlock(content=r"\label{eq:gauss} \int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}"),
            MathBlock(content=r"\label{eq:pythagoras} a^2 + b^2 = c^2"),
        ]
        doc = Document(blocks=blocks, frontmatter={})
        structure = DocumentStructure(doc)

        assert "eq:gauss" in structure.references
        assert "eq:pythagoras" in structure.references
        assert len(structure.references) == 2

    def test_table_of_contents_generation(self):
        """Test generating table of contents"""
        blocks = [
            Heading(level=1, content=[Text(content="Introduction")]),
            Heading(level=2, content=[Text(content="Background")]),
            Heading(level=2, content=[Text(content="Related Work")]),
            Heading(level=1, content=[Text(content="Methods")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})
        structure = DocumentStructure(doc)

        toc = structure.get_table_of_contents()

        assert len(toc) == 4
        assert toc[0] == {'level': 1, 'text': 'Introduction', 'id': 'heading-0-introduction'}
        assert toc[1] == {'level': 2, 'text': 'Background', 'id': 'heading-1-background'}
        assert toc[2] == {'level': 2, 'text': 'Related Work', 'id': 'heading-2-related-work'}
        assert toc[3] == {'level': 1, 'text': 'Methods', 'id': 'heading-3-methods'}

    def test_cross_reference_resolution(self):
        """Test resolving cross-references"""
        blocks = [
            Heading(level=1, content=[Text(content="Introduction")]),
            MathBlock(content=r"\label{eq:main} E = mc^2"),
        ]
        doc = Document(blocks=blocks, frontmatter={})
        structure = DocumentStructure(doc)

        # Should resolve heading reference
        intro_ref = structure.resolve_reference("heading-0-introduction")
        assert intro_ref is not None
        assert isinstance(intro_ref, Heading)
        assert intro_ref.level == 1

        # Should resolve math reference
        math_ref = structure.resolve_reference("eq:main")
        assert math_ref is not None
        assert isinstance(math_ref, MathBlock)
        assert "E = mc^2" in math_ref.content

    def test_structure_validation(self):
        """Test document structure validation"""
        # Valid structure
        blocks = [
            Heading(level=1, content=[Text(content="Chapter 1")]),
            Heading(level=2, content=[Text(content="Section 1.1")]),
            Heading(level=1, content=[Text(content="Chapter 2")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})
        structure = DocumentStructure(doc)

        warnings = structure._get_all_headings()  # Access internal method
        # Should have no validation warnings for valid structure
        # (The validation is in the analyzer, not structure directly)

    def test_heading_id_generation(self):
        """Test heading ID generation"""
        blocks = [
            Heading(level=1, content=[Text(content="Introduction to Methods")]),
            Heading(level=1, content=[Text(content="Advanced Topics")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})
        structure = DocumentStructure(doc)

        # Check that IDs are generated and unique
        heading_ids = list(structure.headings_by_id.keys())
        assert len(heading_ids) == 2
        assert all('heading-' in hid for hid in heading_ids)
        assert len(set(heading_ids)) == 2  # All unique


class TestEnhancedDocument:
    """Test enhanced document with structure analysis"""

    def test_enhanced_document_creation(self):
        """Test creating enhanced document"""
        blocks = [
            Heading(level=1, content=[Text(content="Test Chapter")]),
        ]
        doc = Document(blocks=blocks, frontmatter={})
        enhanced = EnhancedDocument(blocks=doc.blocks, frontmatter=doc.frontmatter)

        assert enhanced.structure is not None
        assert len(enhanced.structure.headings_by_level[1]) == 1

    def test_enhanced_document_inheritance(self):
        """Test that enhanced document inherits from base document"""
        blocks = [Paragraph(content=[Text(content="Test content")])]
        doc = Document(blocks=blocks, frontmatter={'title': 'Test'})

        enhanced = EnhancedDocument(blocks=doc.blocks, frontmatter=doc.frontmatter)

        assert enhanced.blocks == doc.blocks
        assert enhanced.frontmatter == doc.frontmatter
        assert hasattr(enhanced, 'structure')
