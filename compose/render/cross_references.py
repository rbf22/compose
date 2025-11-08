# compose/render/cross_references.py
"""
Cross-reference system for documents.
Provides linking between sections, figures, tables, and other referenceable elements.
"""

import re
from typing import List, Dict, Any, Optional, Set
from ..model.ast import Document, BlockElement, InlineElement, Heading, MathBlock, Paragraph, Text


class CrossReferenceProcessor:
    """
    Processes and resolves cross-references in documents.
    Handles labels, references, and linking between document elements.
    """

    def __init__(self):
        self.labels = {}  # label_id -> (element, location_info)
        self.references = []  # List of (reference_text, target_label, location)
        self.unresolved_refs = set()

    def process_document(self, document: Document) -> Document:
        """
        Process document for cross-references.
        Extracts labels and resolves references.

        Args:
            document: Document AST

        Returns:
            Document with resolved cross-references
        """
        # First pass: extract all labels
        self._extract_labels(document)

        # Second pass: find and resolve references
        resolved_doc = self._resolve_references(document)

        # Report unresolved references
        if self.unresolved_refs:
            print(f"Warning: Unresolved references: {', '.join(self.unresolved_refs)}")

        return resolved_doc

    def _extract_labels(self, document: Document):
        """Extract all labels from the document."""
        for block_idx, block in enumerate(document.blocks):
            self._extract_labels_from_block(block, block_idx)

    def _extract_labels_from_block(self, block: BlockElement, block_idx: int):
        """Extract labels from a block and its children."""
        if isinstance(block, MathBlock):
            # Check for \label{...} in math content
            labels = re.findall(r'\\label\{([^}]+)\}', block.content)
            for label in labels:
                self.labels[label] = {
                    'element': block,
                    'block_idx': block_idx,
                    'type': 'math',
                    'label': label
                }

        elif isinstance(block, Heading):
            # Generate implicit labels for headings
            heading_text = self._extract_text_from_inlines(block.content)
            # Create a URL-safe ID
            heading_id = self._generate_heading_id(heading_text, block_idx)
            self.labels[heading_id] = {
                'element': block,
                'block_idx': block_idx,
                'type': 'heading',
                'label': heading_id
            }

        elif isinstance(block, Paragraph):
            # Check for manual labels in paragraphs
            for inline in block.content:
                if isinstance(inline, Text):
                    # Look for [label]{#id} style labels
                    label_matches = re.findall(r'\[([^\]]+)\]\{#([^}]+)\}', inline.content)
                    for text, label_id in label_matches:
                        self.labels[label_id] = {
                            'element': block,
                            'block_idx': block_idx,
                            'type': 'manual',
                            'label': label_id,
                            'text': text
                        }

    def _resolve_references(self, document: Document) -> Document:
        """Resolve all references in the document."""
        resolved_blocks = []

        for block_idx, block in enumerate(document.blocks):
            resolved_block = self._resolve_references_in_block(block, block_idx)
            resolved_blocks.append(resolved_block)

        # Create new document with resolved blocks
        return Document(blocks=resolved_blocks, frontmatter=document.frontmatter)

    def _resolve_references_in_block(self, block: BlockElement, block_idx: int) -> BlockElement:
        """Resolve references within a block."""
        if isinstance(block, Paragraph):
            # Resolve references in paragraph text
            resolved_content = []
            for inline in block.content:
                if isinstance(inline, Text):
                    # Look for \ref{label} or [text](#label) patterns
                    resolved_text = self._resolve_text_references(inline.content, block_idx)
                    resolved_content.append(Text(content=resolved_text))
                else:
                    resolved_content.append(inline)

            # Create new paragraph with resolved content
            return Paragraph(content=resolved_content)

        elif isinstance(block, MathBlock):
            # Could resolve references in math content
            return block

        else:
            # Other block types remain unchanged
            return block

    def _resolve_text_references(self, text: str, block_idx: int) -> str:
        """Resolve cross-references in text content."""
        # Handle \ref{label} pattern
        def replace_ref(match):
            label = match.group(1)
            if label in self.labels:
                label_info = self.labels[label]
                # For HTML output, create a link
                return f'<a href="#{label}">§{label_info["block_idx"] + 1}</a>'
            else:
                self.unresolved_refs.add(label)
                return f'[ref:{label}]'

        text = re.sub(r'\\ref\{([^}]+)\}', replace_ref, text)

        # Handle [text](#label) pattern
        def replace_link_ref(match):
            link_text = match.group(1)
            label = match.group(2)
            if label in self.labels:
                return f'<a href="#{label}">{link_text}</a>'
            else:
                self.unresolved_refs.add(label)
                return f'{link_text}[broken link: {label}]'

        text = re.sub(r'\[([^\]]+)\]\(#([^)]+)\)', replace_link_ref, text)

        return text

    def _generate_heading_id(self, heading_text: str, block_idx: int) -> str:
        """Generate a URL-safe ID for a heading."""
        # Clean the text and create an ID
        clean_text = re.sub(r'[^\w\s-]', '', heading_text.lower())
        clean_text = re.sub(r'[\s_]+', '-', clean_text)
        return f"heading-{block_idx}-{clean_text}"

    def _extract_text_from_inlines(self, inlines: List[InlineElement]) -> str:
        """Extract plain text from inline elements."""
        result = []
        for inline in inlines:
            if isinstance(inline, Text):
                result.append(inline.content)
            elif hasattr(inline, 'children'):
                result.append(self._extract_text_from_inlines(inline.children))
            elif hasattr(inline, 'text'):
                result.append(inline.text)
        return ''.join(result)

    def get_cross_reference_map(self) -> Dict[str, Dict[str, Any]]:
        """
        Get a map of all cross-references in the document.

        Returns:
            Dict mapping reference IDs to their target information
        """
        return self.labels.copy()

    def validate_references(self) -> Dict[str, Any]:
        """
        Validate all references and return validation results.

        Returns:
            Dict with validation statistics and issues
        """
        total_refs = len(self.references)
        unresolved = len(self.unresolved_refs)
        resolved = total_refs - unresolved

        return {
            'total_references': total_refs,
            'resolved_references': resolved,
            'unresolved_references': list(self.unresolved_refs),
            'resolution_rate': resolved / total_refs if total_refs > 0 else 1.0,
            'issues': [
                {'type': 'unresolved_reference', 'reference': ref}
                for ref in self.unresolved_refs
            ]
        }


class TableOfContentsGenerator:
    """
    Generates hierarchical table of contents from document structure.
    """

    def __init__(self):
        self.toc_entries = []

    def generate_toc(self, document: Document) -> List[Dict[str, Any]]:
        """
        Generate table of contents from document headings.

        Args:
            document: Document AST

        Returns:
            List of TOC entries with hierarchy information
        """
        self.toc_entries = []

        for block_idx, block in enumerate(document.blocks):
            if isinstance(block, Heading):
                toc_entry = {
                    'level': block.level,
                    'text': self._extract_text_from_inlines(block.content),
                    'id': self._generate_heading_id(block_idx, block),
                    'block_idx': block_idx,
                    'children': []
                }
                self.toc_entries.append(toc_entry)

        # Build hierarchy
        return self._build_hierarchy()

    def _build_hierarchy(self) -> List[Dict[str, Any]]:
        """Build hierarchical structure from flat TOC entries."""
        if not self.toc_entries:
            return []

        # Sort by block index to maintain document order
        sorted_entries = sorted(self.toc_entries, key=lambda x: x['block_idx'])

        # Build tree structure
        root = {'children': []}
        stack = [root]

        for entry in sorted_entries:
            level = entry['level']

            # Find the appropriate parent level
            while len(stack) > level:
                stack.pop()

            # Ensure we have enough levels in the stack
            while len(stack) < level:
                # Add intermediate levels if missing
                new_level = {'level': len(stack), 'children': []}
                stack[-1]['children'].append(new_level)
                stack.append(new_level)

            # Add this entry to the current parent
            parent = stack[-1]
            parent['children'].append(entry)

        return root['children']

    def _generate_heading_id(self, block_idx: int, heading: Heading) -> str:
        """Generate heading ID."""
        text = self._extract_text_from_inlines(heading.content)
        clean_text = re.sub(r'[^\w\s-]', '', text.lower())
        clean_text = re.sub(r'[\s_]+', '-', clean_text)
        return f"heading-{block_idx}-{clean_text}"

    def _extract_text_from_inlines(self, inlines: List[InlineElement]) -> str:
        """Extract text from inline elements."""
        result = []
        for inline in inlines:
            if isinstance(inline, Text):
                result.append(inline.content)
            elif hasattr(inline, 'children'):
                result.append(self._extract_text_from_inlines(inline.children))
            elif hasattr(inline, 'text'):
                result.append(inline.text)
        return ''.join(result)

    def render_toc_html(self, toc_entries: List[Dict[str, Any]], max_depth: int = 3) -> str:
        """
        Render table of contents as HTML.

        Args:
            toc_entries: Hierarchical TOC entries
            max_depth: Maximum heading level to include

        Returns:
            HTML string for the table of contents
        """
        def render_entries(entries, current_depth=1):
            if current_depth > max_depth:
                return ""

            html = ""
            for entry in entries:
                # Skip entries that don't have required fields (container entries)
                if 'id' not in entry or 'text' not in entry:
                    # This is a container entry, process its children
                    if entry.get('children'):
                        html += render_entries(entry['children'], current_depth)
                    continue

                if entry['level'] <= max_depth:
                    indent = "  " * (entry['level'] - 1)
                    html += f'{indent}<li><a href="#{entry["id"]}">{entry["text"]}</a>'

                    if entry.get('children'):
                        html += '\n<ul>\n'
                        html += render_entries(entry['children'], current_depth + 1)
                        html += '</ul>\n'

                    html += '</li>\n'

            return html

        html = '<nav class="table-of-contents">\n<h2>Table of Contents</h2>\n<ul>\n'
        html += render_entries(toc_entries)
        html += '</ul>\n</nav>\n'

        return html
