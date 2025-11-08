# compose/analysis/document_analyzer.py
"""
Document analyzer for understanding relationships and structure.
Provides the relationship intelligence needed for complex formatting features.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from ..model.ast import Document, BlockElement, InlineElement, Heading, Paragraph, MathBlock
from ..model.enhanced_ast import DocumentStructure, EnhancedDocument


class DocumentAnalyzer:
    """
    Analyzes document structure and relationships.
    Provides intelligence for complex formatting features like:
    - Table of contents generation
    - Cross-references
    - Footnotes and citations
    - Multi-page layout
    """

    def __init__(self, document: Document):
        self.document = document
        self.structure = DocumentStructure(document)

    def analyze(self) -> EnhancedDocument:
        """Perform complete document analysis"""
        # The DocumentStructure already does the analysis in __post_init__
        return EnhancedDocument(
            blocks=self.document.blocks,
            frontmatter=self.document.frontmatter,
            structure=self.structure
        )

    def find_references_to(self, target) -> List[Any]:
        """Find all elements that reference a target"""
        references = []

        def scan_blocks(blocks: List[BlockElement]):
            for block in blocks:
                if isinstance(block, Paragraph):
                    for inline in block.content:
                        if self._references_target(inline, target):
                            references.append(block)
                elif isinstance(block, Heading):
                    if self._references_target_in_inline(block.content, target):
                        references.append(block)
                # Add other block types as needed

        scan_blocks(self.document.blocks)
        return references

    def _references_target(self, inline: InlineElement, target) -> bool:
        """Check if an inline element references a target"""
        # This would need to be implemented based on specific reference syntax
        # For now, return False
        return False

    def _references_target_in_inline(self, inlines: List[InlineElement], target) -> bool:
        """Check if any inline element in a list references target"""
        return any(self._references_target(inline, target) for inline in inlines)

    def get_page_layout(self, page_width: int, page_height: int) -> List['Page']:
        """
        Calculate page layout for multi-page documents.
        This would need integration with the layout engine.
        """
        # Placeholder for page layout analysis
        pages = []

        current_page = Page(page_number=1, blocks=[])
        current_height = 0

        for block in self.document.blocks:
            block_height = self._estimate_block_height(block, page_width)

            if current_height + block_height > page_height and current_page.blocks:
                pages.append(current_page)
                current_page = Page(page_number=len(pages) + 1, blocks=[])
                current_height = 0

            current_page.blocks.append(block)
            current_height += block_height

        if current_page.blocks:
            pages.append(current_page)

        return pages

    def _estimate_block_height(self, block: BlockElement, page_width: int) -> float:
        """Estimate the height of a block in the layout"""
        # This would use the layout engine to estimate block dimensions
        # For now, return a rough estimate
        if isinstance(block, Heading):
            return 30 + (7 - block.level) * 10  # Headings get taller as level decreases
        elif isinstance(block, Paragraph):
            # Rough estimate: 20px per line, assume 60 chars per line
            char_count = sum(len(getattr(inline, 'content', '')) for inline in block.content
                           if hasattr(inline, 'content'))
            return max(20, (char_count / 60) * 20)
        else:
            return 20  # Default block height

    def validate_document_structure(self) -> List[str]:
        """Validate document structure and return warnings/errors"""
        warnings = []

        # Check for orphaned references
        for label, target in self.structure.references.items():
            references = self.find_references_to(target)
            if not references:
                warnings.append(f"Label '{label}' is defined but never referenced")

        # Check heading hierarchy
        prev_level = 0
        for heading in self._get_all_headings():
            if heading.level > prev_level + 1:
                warnings.append(f"Heading level jumps from {prev_level} to {heading.level}")
            prev_level = heading.level

        return warnings

    def _get_all_headings(self) -> List[Heading]:
        """Get all headings in order"""
        headings = []
        for block in self.document.blocks:
            if isinstance(block, Heading):
                headings.append(block)
        return headings

    def generate_cross_references(self) -> Dict[str, Any]:
        """Generate cross-reference data for the document"""
        xrefs = {}

        # Build heading references
        for heading in self._get_all_headings():
            heading_text = self._extract_text_from_inline(heading.content)
            heading_id = self.structure._generate_heading_id(heading, self.document.blocks.index(heading))

            xrefs[heading_id] = {
                'type': 'heading',
                'text': heading_text,
                'level': heading.level,
                'block_index': self.document.blocks.index(heading)
            }

        # Add other reference types (math labels, etc.)
        for label, target in self.structure.references.items():
            xrefs[label] = {
                'type': 'math_label' if isinstance(target, MathBlock) else 'unknown',
                'target': target,
                'block_index': self.document.blocks.index(target) if hasattr(target, '__class__') and target in self.document.blocks else None
            }

        return xrefs

    def _extract_text_from_inline(self, inlines: List[InlineElement]) -> str:
        """Extract plain text from inline elements"""
        result = []
        for inline in inlines:
            if hasattr(inline, 'content') and isinstance(inline.content, str):
                result.append(inline.content)
            elif hasattr(inline, 'children'):
                result.append(self._extract_text_from_inline(inline.children))
            elif hasattr(inline, 'text'):
                result.append(inline.text)
        return ''.join(result)


@dataclass
class Page:
    """Represents a page in a multi-page document"""
    page_number: int
    blocks: List[BlockElement]

    def get_page_content(self) -> str:
        """Get the text content of this page"""
        content = []
        for block in self.blocks:
            if isinstance(block, Heading):
                content.append(f"{'#' * block.level} {DocumentAnalyzer._extract_text_from_inline_static(block.content)}")
            elif isinstance(block, Paragraph):
                content.append(DocumentAnalyzer._extract_text_from_inline_static(block.content))
            # Add other block types
        return '\n\n'.join(content)

    @staticmethod
    def _extract_text_from_inline_static(inlines: List[InlineElement]) -> str:
        """Static version of text extraction"""
        result = []
        for inline in inlines:
            if hasattr(inline, 'content') and isinstance(inline.content, str):
                result.append(inline.content)
            elif hasattr(inline, 'children'):
                result.append(Page._extract_text_from_inline_static(inline.children))
            elif hasattr(inline, 'text'):
                result.append(inline.text)
        return ''.join(result)
