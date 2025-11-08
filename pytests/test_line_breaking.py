# tests/test_line_breaking.py
"""Tests for line breaking and typography layout engines"""

import pytest
from compose.render.line_breaking import (
    LineBreakingEngine, TypographyLayoutEngine, MicroTypographyEngine
)


class TestLineBreakingEngine:
    """Test line breaking engine functionality"""

    def test_line_breaking_initialization(self):
        """Test creating line breaking engine"""
        engine = LineBreakingEngine()
        assert engine.optimal_width == 60
        assert engine.demerit_penalty == 100

    def test_find_optimal_breaks_empty_input(self):
        """Test line breaking with empty input"""
        engine = LineBreakingEngine()
        breaks = engine.find_optimal_breaks([], 60)
        assert breaks == []

    def test_find_optimal_breaks_single_word(self):
        """Test line breaking with single word"""
        engine = LineBreakingEngine()
        breaks = engine.find_optimal_breaks(["hello"], 60)
        assert breaks == []

    def test_find_optimal_breaks_multiple_words(self):
        """Test line breaking with multiple words"""
        engine = LineBreakingEngine()
        words = ["This", "is", "a", "test", "sentence", "with", "many", "words"]
        breaks = engine.find_optimal_breaks(words, 20)  # Very narrow line

        # Should find some break points
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
        assert "Hello world this\nis a test" == result

    def test_break_paragraph(self):
        """Test breaking paragraph into lines"""
        engine = LineBreakingEngine()
        words = ["This", "is", "a", "long", "paragraph", "with", "many", "words", "that", "should", "be", "broken", "into", "multiple", "lines"]

        lines = engine.break_paragraph(words, 30)

        # Should create multiple lines
        assert len(lines) > 1
        assert isinstance(lines, list)
        assert all(isinstance(line, str) for line in lines)


class TestTypographyLayoutEngine:
    """Test typography layout engine"""

    def test_layout_engine_initialization(self):
        """Test creating typography layout engine"""
        engine = TypographyLayoutEngine()
        assert engine.min_widow_lines == 2
        assert engine.min_orphan_lines == 2

    def test_layout_paragraph_empty(self):
        """Test layout of empty paragraph"""
        engine = TypographyLayoutEngine()
        result = engine.layout_paragraph("")

        assert result['lines'] == []
        assert result['word_count'] == 0
        assert result['line_count'] == 0

    def test_layout_paragraph_simple(self):
        """Test layout of simple paragraph"""
        engine = TypographyLayoutEngine()
        text = "This is a simple test paragraph with some words."
        result = engine.layout_paragraph(text, 40)

        assert result['word_count'] > 0
        assert result['line_count'] > 0
        assert isinstance(result['lines'], list)
        assert all(isinstance(line, str) for line in result['lines'])
        assert 0 <= result['typography_score'] <= 100

    def test_layout_paragraph_long(self):
        """Test layout of longer paragraph"""
        engine = TypographyLayoutEngine()
        text = "This is a much longer paragraph that contains many more words and should definitely be broken into multiple lines when the width is constrained appropriately for testing purposes."

        result = engine.layout_paragraph(text, 50)

        assert result['word_count'] > 10
        assert result['line_count'] >= 2
        assert result['avg_line_length'] > 0

    def test_apply_typography_rules(self):
        """Test typography rules application"""
        engine = TypographyLayoutEngine()

        # Test with lines that might have widows/orphans
        lines = ["A", "This is a longer line with many words", "Short"]

        processed = engine._apply_typography_rules(lines)

        # Should handle the short lines appropriately
        assert isinstance(processed, list)
        assert all(isinstance(line, str) for line in processed)

    def test_tokenization(self):
        """Test text tokenization"""
        engine = TypographyLayoutEngine()

        text = "Hello, world! This is a test."
        words = engine._tokenize_text(text)

        assert "Hello," in words
        assert "world!" in words
        assert "This" in words
        assert "is" in words
        assert "a" in words
        assert "test." in words


class TestMicroTypographyEngine:
    """Test micro-typography features"""

    def test_micro_typography_initialization(self):
        """Test creating micro-typography engine"""
        engine = MicroTypographyEngine()
        assert isinstance(engine.protrusion_table, dict)
        assert ',' in engine.protrusion_table

    def test_apply_microtypography(self):
        """Test applying micro-typography"""
        engine = MicroTypographyEngine()
        text = "Hello, world! This is a test."

        result = engine.apply_microtypography(text)

        # For now, should return the same text (placeholder implementation)
        assert result == text

    def test_optimize_spacing(self):
        """Test spacing optimization"""
        engine = MicroTypographyEngine()

        # Test multiple spaces
        text = "Hello   world!   This   is   a   test."
        result = engine.optimize_spacing(text)

        # Should normalize spacing
        assert "   " not in result
        assert result.count(" ") == 5  # Should have single spaces between words

        # Test punctuation spacing
        assert " ," not in result  # Space before comma should be removed
