# compose/render/typography_engine.py
"""
Advanced typography engine for professional document layout.
Implements widow/orphan control, paragraph shaping, and LaTeX-like typography rules.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from ..model.ast import Document, BlockElement, Paragraph, Heading, Text, InlineElement


class TypographyEngine:
    """
    Advanced typography engine providing professional typesetting features.
    Implements LaTeX-inspired layout rules for optimal readability.
    """

    def __init__(self):
        # Typography settings
        self.line_width = 80  # characters per line for text wrapping
        self.min_widow_lines = 2  # minimum lines to keep together at page/column start
        self.min_orphan_lines = 2  # minimum lines to keep together at page/column end
        self.paragraph_spacing = 1.5  # em units between paragraphs
        self.optimal_line_length = 60  # optimal characters per line

        # Typography presets
        self.presets = {
            'dense': {
                'line_height': 1.2,
                'paragraph_spacing': 1.0,
                'margins': {'top': 20, 'bottom': 20, 'left': 30, 'right': 30}
            },
            'academic': {
                'line_height': 1.6,
                'paragraph_spacing': 1.8,
                'margins': {'top': 50, 'bottom': 50, 'left': 40, 'right': 40}
            },
            'poster': {
                'line_height': 1.8,
                'paragraph_spacing': 2.0,
                'margins': {'top': 60, 'bottom': 60, 'left': 50, 'right': 50}
            }
        }

    def apply_typography(self, document: Document, preset: str = None) -> Document:
        """
        Apply advanced typography rules to the entire document.

        Args:
            document: Document AST
            preset: Typography preset ('dense', 'academic', 'poster')

        Returns:
            Document with typography optimizations applied
        """
        # Apply preset if specified
        if preset and preset in self.presets:
            self._apply_preset(preset)

        # Process each block
        processed_blocks = []
        for block in document.blocks:
            processed_block = self._apply_block_typography(block)
            processed_blocks.append(processed_block)

        # Create new document with typography metadata
        new_doc = Document(
            blocks=processed_blocks,
            frontmatter=document.frontmatter.copy()
        )

        # Add typography metadata
        if 'typography' not in new_doc.frontmatter:
            new_doc.frontmatter['typography'] = {}

        new_doc.frontmatter['typography'].update({
            'widow_control': True,
            'orphan_control': True,
            'paragraph_shaping': True,
            'preset': preset
        })

        return new_doc

    def _apply_preset(self, preset: str):
        """Apply typography preset settings."""
        if preset in self.presets:
            settings = self.presets[preset]
            self.paragraph_spacing = settings['paragraph_spacing']
            # Store preset info for CSS generation
            self.current_preset = preset
            self.preset_settings = settings
        # If preset is invalid, keep current settings

    def _apply_block_typography(self, block: BlockElement) -> BlockElement:
        """Apply typography rules to individual blocks."""
        if isinstance(block, Paragraph):
            return self._shape_paragraph(block)
        elif isinstance(block, Heading):
            return self._style_heading(block)
        else:
            return block

    def _shape_paragraph(self, paragraph: Paragraph) -> Paragraph:
        """
        Apply paragraph shaping rules:
        - Avoid single words on new lines
        - Control widow/orphan lines
        - Optimize line breaks for readability
        """
        # Extract text content
        text_content = self._extract_text_content(paragraph.content)

        # Split into words for analysis
        words = text_content.split()

        if len(words) < 3:
            # Too short to shape effectively
            return paragraph

        # Apply paragraph shaping rules
        shaped_content = self._apply_paragraph_shaping(words)

        # Create new paragraph with shaped content
        shaped_inline = [Text(content=shaped_content)]
        return Paragraph(content=shaped_inline)

    def _apply_paragraph_shaping(self, words: List[str]) -> str:
        """
        Apply paragraph shaping to prevent bad line breaks.
        """
        if len(words) <= 1:
            return ' '.join(words)

        # Simple paragraph shaping: avoid single words at line end
        # This is a simplified version - full implementation would use
        # more sophisticated line breaking algorithms

        result_lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space

            # Check if adding this word would create a bad line break
            if current_line and self._would_create_bad_break(current_line + [word]):
                # Force line break before this word
                if current_line:
                    result_lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = len(word)
                else:
                    current_line = [word]
                    current_length = len(word)
            else:
                current_line.append(word)
                current_length += word_length

                # Check for optimal line length
                if current_length >= self.optimal_line_length:
                    result_lines.append(' '.join(current_line))
                    current_line = []
                    current_length = 0

        # Add remaining words
        if current_line:
            result_lines.append(' '.join(current_line))

        return '\n'.join(result_lines)

    def _would_create_bad_break(self, line_words: List[str]) -> bool:
        """
        Check if a line would create a bad break (e.g., single word).
        """
        if len(line_words) <= 1:
            return True

        # Check for single short words at end
        last_word = line_words[-1]
        if len(last_word) <= 3 and len(line_words) > 1:
            # Short word at end might be widow/orphan
            return True

        return False

    def _style_heading(self, heading: Heading) -> Heading:
        """Apply typography styling to headings."""
        # Headings are generally fine as-is, but we could add
        # additional styling rules here if needed
        return heading

    def _extract_text_content(self, inline_elements: List[InlineElement]) -> str:
        """Extract plain text from inline elements."""
        result = []
        for element in inline_elements:
            if isinstance(element, Text):
                result.append(element.content)
            elif hasattr(element, 'children'):
                result.append(self._extract_text_content(element.children))
        return ''.join(result)

    def get_css_styles(self, preset: str = None) -> str:
        """
        Generate CSS styles for typography.

        Returns:
            CSS string for typography rules
        """
        base_css = """
        /* Typography Engine Styles */
        body {
            font-family: 'Times New Roman', serif;
            line-height: 1.6;
            widows: 2;
            orphans: 2;
        }

        p {
            margin-bottom: 1.5em;
            text-align: justify;
            hyphens: auto;
            text-justify: inter-word;
        }

        .typography-dense p {
            line-height: 1.2;
            margin-bottom: 1.0em;
        }

        .typography-academic p {
            line-height: 1.6;
            margin-bottom: 1.8em;
            font-size: 11pt;
        }

        .typography-poster p {
            line-height: 1.8;
            margin-bottom: 2.0em;
            font-size: 14pt;
        }

        /* Widow and orphan control */
        p:last-child {
            margin-bottom: 0;
        }

        /* Smart spacing for lists */
        ul, ol {
            margin-bottom: 1.5em;
        }

        li {
            margin-bottom: 0.5em;
        }

        /* Heading spacing */
        h1, h2, h3, h4, h5, h6 {
            margin-top: 2em;
            margin-bottom: 1em;
            line-height: 1.2;
        }

        h1:first-child {
            margin-top: 0;
        }
        """

        # Add preset-specific styles
        if preset and preset in self.presets:
            settings = self.presets[preset]
            preset_css = f"""
        .typography-{preset} {{
            line-height: {settings['line_height']};
        }}

        .typography-{preset} p {{
            margin-bottom: {settings['paragraph_spacing']}em;
        }}
            """
            base_css += preset_css

        return base_css

    def analyze_document_layout(self, document: Document) -> Dict[str, Any]:
        """
        Analyze document for typography quality metrics.

        Returns:
            Dict with layout analysis results
        """
        analysis = {
            'total_paragraphs': 0,
            'average_words_per_paragraph': 0,
            'paragraphs_with_bad_breaks': 0,
            'widow_orphans_detected': 0,
            'typography_score': 0
        }

        total_words = 0
        bad_breaks = 0

        for block in document.blocks:
            if isinstance(block, Paragraph):
                analysis['total_paragraphs'] += 1
                text = self._extract_text_content(block.content)
                words = text.split()
                total_words += len(words)

                # Check for potential bad breaks
                lines = text.split('\n')
                for line in lines:
                    line_words = line.split()
                    if len(line_words) == 1 and len(line_words[0]) <= 3:
                        bad_breaks += 1

        if analysis['total_paragraphs'] > 0:
            analysis['average_words_per_paragraph'] = total_words / analysis['total_paragraphs']

        analysis['paragraphs_with_bad_breaks'] = bad_breaks

        # Calculate typography score (0-100)
        score = 100
        if analysis['paragraphs_with_bad_breaks'] > 0:
            score -= min(30, analysis['paragraphs_with_bad_breaks'] * 5)

        analysis['typography_score'] = max(0, score)

        return analysis


class LineBreakingEngine:
    """
    Advanced line breaking engine using simplified Knuth-Plass principles.
    Optimizes line breaks for readability and aesthetics.
    """

    def __init__(self):
        self.optimal_width = 60  # characters
        self.demerit_penalty = 100  # penalty for bad breaks

    def find_optimal_breaks(self, words: List[str], max_width: int) -> List[int]:
        """
        Find optimal line break positions using dynamic programming.
        Simplified version of Knuth-Plass algorithm.

        Args:
            words: List of words in paragraph
            max_width: Target maximum characters per line

        Returns:
            List of indices where line breaks should occur
        """
        if not words:
            return []

        n = len(words)
        breaks = []

        # Simple approach: find natural break points
        current_length = 0
        for i, word in enumerate(words):
            word_length = len(word)

            if current_length > 0:  # Account for space
                word_length += 1

            if current_length + word_length > max_width:
                if i > 0:  # Don't break at the very beginning
                    breaks.append(i)
                current_length = len(word)
            else:
                current_length += word_length

        return breaks

    def apply_line_breaks(self, words: List[str], break_indices: List[int]) -> str:
        """
        Apply line breaks at specified indices.

        Args:
            words: List of words
            break_indices: Indices where to insert line breaks

        Returns:
            Formatted text with line breaks
        """
        result = []
        break_set = set(break_indices)

        for i, word in enumerate(words):
            result.append(word)
            if i + 1 in break_set:
                result.append('\n')
            elif i < len(words) - 1:
                result.append(' ')

        return ''.join(result)
