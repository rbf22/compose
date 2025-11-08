# compose/render/multi_page.py
"""
Multi-page document rendering and layout management.
Provides page break logic, page-based cross-references, and multi-page output.
"""

from typing import List, Dict, Any, Optional, Tuple
from ..model.ast import Document, BlockElement, Heading
from ..analysis.document_analyzer import DocumentAnalyzer, Page


class MultiPageRenderer:
    """
    Handles rendering documents across multiple pages.
    Manages page breaks, page-based layout, and cross-page references.
    """

    def __init__(self, page_width: int = 800, page_height: int = 600,
                 margins: Dict[str, int] = None):
        self.page_width = page_width
        self.page_height = page_height
        self.margins = margins or {
            'top': 50, 'bottom': 50, 'left': 40, 'right': 40
        }
        self.content_width = page_width - self.margins['left'] - self.margins['right']
        self.content_height = page_height - self.margins['top'] - self.margins['bottom']

    def render_multi_page(self, document: Document, output_format: str = 'html') -> List[Dict[str, Any]]:
        """
        Render document as multiple pages.

        Args:
            document: Document AST
            output_format: 'html', 'pdf', etc.

        Returns:
            List of page dictionaries with content and metadata
        """
        analyzer = DocumentAnalyzer(document)
        pages = self._calculate_page_layout(document, analyzer)

        rendered_pages = []
        for page in pages:
            if output_format == 'html':
                page_content = self._render_page_html(page, len(rendered_pages) + 1, len(pages))
            else:
                page_content = self._render_page_text(page, len(rendered_pages) + 1, len(pages))

            rendered_pages.append({
                'page_number': len(rendered_pages) + 1,
                'total_pages': len(pages),
                'content': page_content,
                'blocks': page.blocks,
                'word_count': self._count_words(page),
                'has_headings': any(isinstance(b, Heading) for b in page.blocks)
            })

        return rendered_pages

    def _calculate_page_layout(self, document: Document, analyzer: DocumentAnalyzer) -> List[Page]:
        """
        Calculate optimal page breaks based on content flow and semantic structure.
        """
        pages = []
        current_page = Page(page_number=1, blocks=[])
        current_height = 0

        for i, block in enumerate(document.blocks):
            block_height = analyzer._estimate_block_height(block, self.content_width)

            # Check for explicit page breaks
            if self._is_page_break(block):
                if current_page.blocks:
                    pages.append(current_page)
                current_page = Page(page_number=len(pages) + 1, blocks=[block])
                current_height = block_height
                continue

            # Check if block fits on current page
            if current_height + block_height > self.content_height and current_page.blocks:
                # Try to avoid breaking paragraphs mid-sentence
                if self._should_break_here(current_page.blocks, block):
                    pages.append(current_page)
                    current_page = Page(page_number=len(pages) + 1, blocks=[block])
                    current_height = block_height
                else:
                    # Keep paragraph together - start new page
                    pages.append(current_page)
                    current_page = Page(page_number=len(pages) + 1, blocks=[block])
                    current_height = block_height
            else:
                current_page.blocks.append(block)
                current_height += block_height

        if current_page.blocks:
            pages.append(current_page)

        return pages

    def _is_page_break(self, block: BlockElement) -> bool:
        """Check if block should force a page break."""
        # Could check for special page break markers or large headings
        if isinstance(block, Heading) and block.level == 1:
            return True  # Chapter headings start new pages
        return False

    def _should_break_here(self, current_blocks: List[BlockElement], next_block: BlockElement) -> bool:
        """Decide if it's okay to break the page at this point."""
        # Avoid breaking after headings
        if current_blocks and isinstance(current_blocks[-1], Heading):
            return False

        # Prefer breaking before new sections
        if isinstance(next_block, Heading):
            return True

        return True

    def _render_page_html(self, page: Page, page_num: int, total_pages: int) -> str:
        """Render a page as HTML."""
        from ..render.ast_renderer import HTMLRenderer

        # Create a temporary document with just this page's blocks
        from ..model.ast import Document
        temp_doc = Document(blocks=page.blocks, frontmatter={})

        renderer = HTMLRenderer()
        html_content = renderer.render(temp_doc, {'mode': 'document'})

        # Add page metadata and navigation
        page_html = f'''
        <div class="page" data-page="{page_num}" style="width: {self.page_width}px; height: {self.page_height}px; margin: 20px auto; border: 1px solid #ddd; padding: {self.margins['top']}px {self.margins['right']}px {self.margins['bottom']}px {self.margins['left']}px; background: white; position: relative;">
            <div class="page-header" style="position: absolute; top: 10px; left: 50%; transform: translateX(-50%); font-size: 10px; color: #666;">
                Page {page_num} of {total_pages}
            </div>
            <div class="page-content" style="margin-top: 30px;">
                {html_content}
            </div>
            <div class="page-footer" style="position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%); font-size: 10px; color: #666;">
                Page {page_num}
            </div>
        </div>
        '''

        return page_html

    def _render_page_text(self, page: Page, page_num: int, total_pages: int) -> str:
        """Render a page as plain text."""
        from ..render.ast_renderer import TextRenderer

        # Create a temporary document with just this page's blocks
        from ..model.ast import Document
        temp_doc = Document(blocks=page.blocks, frontmatter={})

        renderer = TextRenderer()
        text_content = renderer.render(temp_doc, {'mode': 'document'})

        # Add page separator
        page_text = f"\n{'='*50}\n"
        page_text += f"Page {page_num} of {total_pages}\n"
        page_text += f"{'='*50}\n\n"
        page_text += text_content
        page_text += f"\n\n--- End of Page {page_num} ---\n"

        return page_text

    def _count_words(self, page: Page) -> int:
        """Count words in a page."""
        word_count = 0
        for block in page.blocks:
            if hasattr(block, 'content'):
                if isinstance(block.content, str):
                    word_count += len(block.content.split())
                elif isinstance(block.content, list):
                    # Handle inline elements
                    for inline in block.content:
                        if hasattr(inline, 'content') and isinstance(inline.content, str):
                            word_count += len(inline.content.split())
                        elif hasattr(inline, 'children'):
                            # Recursively count in nested elements
                            word_count += self._count_inline_words(inline.children)
        return word_count

    def _count_inline_words(self, inlines: List) -> int:
        """Count words in inline elements."""
        count = 0
        for inline in inlines:
            if hasattr(inline, 'content') and isinstance(inline.content, str):
                count += len(inline.content.split())
            elif hasattr(inline, 'children'):
                count += self._count_inline_words(inline.children)
        return count


class PageCrossReferenceManager:
    """
    Manages cross-references across multiple pages.
    Provides page-based linking and reference resolution.
    """

    def __init__(self, pages: List[Dict[str, Any]]):
        self.pages = pages
        self._build_reference_map()

    def _build_reference_map(self):
        """Build a map of references to their page locations."""
        self.reference_map = {}

        for page in self.pages:
            page_num = page['page_number']

            # Look for headings and labeled elements
            for block_idx, block in enumerate(page['blocks']):
                if isinstance(block, Heading):
                    # Generate heading ID consistently
                    heading_text = self._extract_text_from_inlines(block.content)
                    heading_id = f"heading-{block_idx}-{heading_text.lower().replace(' ', '-')}"
                    self.reference_map[heading_id] = {
                        'page': page_num,
                        'type': 'heading',
                        'block': block
                    }

                # Could extend for other referenceable elements
                # (math labels, figures, tables, etc.)

    def resolve_reference(self, reference_id: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a reference to its page location.

        Args:
            reference_id: The ID of the reference to resolve

        Returns:
            Dict with page number and reference info, or None if not found
        """
        return self.reference_map.get(reference_id)

    def get_page_references(self, page_num: int) -> List[Dict[str, Any]]:
        """
        Get all references that point TO a specific page.

        Args:
            page_num: Page number

        Returns:
            List of references pointing to this page
        """
        return [ref for ref in self.reference_map.values() if ref['page'] == page_num]

    def generate_page_navigation(self) -> Dict[int, Dict[str, Any]]:
        """
        Generate navigation information for each page.

        Returns:
            Dict mapping page numbers to navigation info
        """
        navigation = {}

        for i, page in enumerate(self.pages):
            page_num = page['page_number']
            navigation[page_num] = {
                'has_previous': page_num > 1,
                'has_next': page_num < len(self.pages),
                'previous_page': page_num - 1 if page_num > 1 else None,
                'next_page': page_num + 1 if page_num < len(self.pages) else None,
                'total_pages': len(self.pages),
                'references_on_page': self.get_page_references(page_num)
            }

        return navigation


    def _extract_text_from_inlines(self, inlines):
        """Extract text from inline elements."""
        result = []
        for inline in inlines:
            if hasattr(inline, 'content'):
                result.append(inline.content)
            elif hasattr(inline, 'children'):
                result.extend(self._extract_text_from_inlines(inline.children))
        return ''.join(result)
