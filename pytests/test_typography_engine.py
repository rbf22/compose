# tests/test_typography_engine.py
"""Tests for advanced typography engine"""

import pytest
from compose.render.typography_engine import TypographyEngine, LineBreakingEngine
from compose.model.ast import Document, Paragraph, Heading, Text


class TestTypographyEngine:
    """Test typography engine functionality"""

    def test_engine_initialization(self):
        """Test creating typography engine"""
        engine = TypographyEngine()
        assert engine.line_width == 80
        assert engine.min_widow_lines == 2
        assert engine.min_orphan_lines == 2
        assert engine.paragraph_spacing == 1.5

    def test_apply_preset(self):
        """Test applying typography presets"""
        engine = TypographyEngine()

        # Test dense preset
        engine._apply_preset('dense')
        assert engine.paragraph_spacing == 1.0
        assert engine.current_preset == 'dense'

        # Test academic preset
        engine._apply_preset('academic')
        assert engine.paragraph_spacing == 1.8

        # Test poster preset
        engine._apply_preset('poster')
        assert engine.paragraph_spacing == 2.0

    def test_invalid_preset(self):
        """Test handling of invalid presets"""
        engine = TypographyEngine()

        # Should not crash with invalid preset
        engine._apply_preset('invalid')
        assert engine.paragraph_spacing == 1.5  # Should remain default

    def test_apply_typography_to_document(self):
        """Test applying typography to entire document"""
        # Create test document
        blocks = [
            Paragraph(content=[Text(content="This is a short paragraph.")]),
            Heading(level=1, content=[Text(content="Heading")]),
            Paragraph(content=[Text(content="This is a longer paragraph with more words that might need typography adjustments for better readability and flow.")])
        ]
        doc = Document(blocks=blocks, frontmatter={})

        engine = TypographyEngine()
        processed_doc = engine.apply_typography(doc, 'academic')

        # Should return a document
        assert isinstance(processed_doc, Document)
        assert len(processed_doc.blocks) == 3

        # Should add typography metadata to frontmatter
        assert 'typography' in processed_doc.frontmatter
        assert processed_doc.frontmatter['typography']['preset'] == 'academic'
        assert processed_doc.frontmatter['typography']['widow_control'] == True

    def test_paragraph_shaping(self):
        """Test paragraph shaping functionality"""
        engine = TypographyEngine()

        # Create paragraph with text that might have bad breaks
        paragraph = Paragraph(content=[Text(content="This is a very short word that might cause issues with line breaking in typography.")])

        shaped = engine._shape_paragraph(paragraph)

        # Should return a paragraph (may be modified or unchanged)
        assert isinstance(shaped, Paragraph)

    def test_css_generation(self):
        """Test CSS generation for typography"""
        engine = TypographyEngine()
        css = engine.get_css_styles()

        # Should contain basic typography CSS
        assert 'body {' in css
        assert 'widows: 2' in css
        assert 'orphans: 2' in css
        assert 'text-justify: inter-word' in css

    def test_css_with_preset(self):
        """Test CSS generation with typography preset"""
        engine = TypographyEngine()
        css = engine.get_css_styles('dense')

        # Should contain preset-specific styles
        assert '.typography-dense' in css
        assert 'line-height: 1.2' in css

    def test_document_analysis(self):
        """Test document layout analysis"""
        # Create test document
        blocks = [
            Paragraph(content=[Text(content="Short paragraph.")]),
            Paragraph(content=[Text(content="This is a much longer paragraph with many words that should provide good analysis data for the typography engine.")])
        ]
        doc = Document(blocks=blocks, frontmatter={})

        engine = TypographyEngine()
        analysis = engine.analyze_document_layout(doc)

        # Should return analysis dictionary
        assert isinstance(analysis, dict)
        assert 'total_paragraphs' in analysis
        assert 'average_words_per_paragraph' in analysis
        assert 'typography_score' in analysis

        # Should have correct counts
        assert analysis['total_paragraphs'] == 2
        assert analysis['typography_score'] >= 0
        assert analysis['typography_score'] <= 100

    def test_empty_document_analysis(self):
        """Test analysis of empty document"""
        doc = Document(blocks=[], frontmatter={})

        engine = TypographyEngine()
        analysis = engine.analyze_document_layout(doc)

        assert analysis['total_paragraphs'] == 0
        assert analysis['typography_score'] == 100  # Perfect score for no issues


class TestLineBreakingEngine:
    """Test line breaking engine functionality"""

    def test_line_breaking_initialization(self):
        """Test creating line breaking engine"""
        engine = LineBreakingEngine()
        assert engine.optimal_width == 60
        assert engine.demerit_penalty == 100

    def test_find_optimal_breaks(self):
        """Test finding optimal line break positions"""
        engine = LineBreakingEngine()

        words = ["This", "is", "a", "test", "sentence", "with", "several", "words", "that", "might", "need", "breaking"]
        breaks = engine.find_optimal_breaks(words, 40)

        # Should return list of indices
        assert isinstance(breaks, list)
        for break_idx in breaks:
            assert isinstance(break_idx, int)
            assert 0 < break_idx < len(words)

    def test_apply_line_breaks(self):
        """Test applying line breaks to text"""
        engine = LineBreakingEngine()

        words = ["Hello", "world", "this", "is", "a", "test"]
        breaks = [3]  # Break after "is"

        result = engine.apply_line_breaks(words, breaks)

        # Should contain line break
        assert '\n' in result
        assert 'Hello world this\nis a test' == result

    def test_line_breaks_empty_input(self):
        """Test line breaking with empty input"""
        engine = LineBreakingEngine()

        breaks = engine.find_optimal_breaks([], 60)
        assert breaks == []

        result = engine.apply_line_breaks([], [])
        assert result == ""

    def test_single_word_breaking(self):
        """Test line breaking with single word"""
        engine = LineBreakingEngine()

        words = ["word"]
        breaks = engine.find_optimal_breaks(words, 60)
        assert breaks == []  # No breaks needed

        result = engine.apply_line_breaks(words, breaks)
        assert result == "word"
