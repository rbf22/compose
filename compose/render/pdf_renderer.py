# compose/render/pdf_renderer.py
"""
PDF renderer for the Compose typesetting system.

This module implements PDF generation using only Python standard library.
Creates valid PDF files by generating the PDF file structure manually.

PDF format reference: https://www.adobe.com/content/dam/acom/en/devnet/pdf/pdf_reference_archive/pdf_reference_1-7.pdf
"""

import zlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from ..model.ast import Document, Heading, Paragraph, MathBlock, MathInline, CodeBlock, ListBlock, ListItem, Link, Image, Text, Bold, Italic, Strikethrough, CodeInline
from ..layout.box_model import MathBox, BoxType, Dimensions
from ..layout.engines.math_engine import MathLayoutEngine, ExpressionLayout
from ..layout.content.math_parser import MathExpressionParser


class PDFRenderer:
    """
    PDF renderer using only Python standard library.

    Generates valid PDF files by creating the PDF file structure,
    objects, and content streams manually.
    """

    def __init__(self):
        self.objects: List[str] = []
        self.object_offsets: List[int] = []
        self.current_y = 750  # Start near top of page
        self.page_height = 792  # Letter height in points
        self.page_width = 612   # Letter width in points
        self.margin = 72        # 1 inch margin
        self.line_height = 14
        self.font_size = 12

        # Layout engine for math processing
        self.math_engine = MathLayoutEngine()
        self.math_parser = MathExpressionParser()

    def render(self, doc: Document, config: Dict) -> bytes:
        """
        Render a document to PDF bytes using only standard library.

        Creates a complete PDF file structure with pages, fonts, and content.
        """
        # Reset state
        self.objects = []
        self.object_offsets = []
        self.current_y = 750

        # Create PDF structure
        self._create_pdf_structure(doc)

        # Generate the complete PDF
        return self._generate_pdf()

    def _create_pdf_structure(self, doc: Document):
        """Create the PDF file structure."""

        # 1. Catalog (root object)
        self._add_object("<<\n/Type /Catalog\n/Pages 2 0 R\n>>")

        # 2. Pages object
        self._add_object("<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>")

        # 3. Page object
        page_content = self._create_page_content(doc)
        content_stream = self._create_content_stream(page_content)

        page_object = f"""<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 {self.page_width} {self.page_height}]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
/F2 6 0 R
>>
>>
>>
"""
        self._add_object(page_object)

        # 4. Content stream
        self._add_object(content_stream)

        # 5. Font 1 (Times-Roman)
        self._add_object("""<<
/Type /Font
/Subtype /Type1
/BaseFont /Times-Roman
>>
""")

        # 6. Font 2 (Courier)
        self._add_object("""<<
/Type /Font
/Subtype /Type1
/BaseFont /Courier
>>
""")

    def _create_page_content(self, doc: Document) -> str:
        """Create the page content stream commands."""
        commands = []

        # Set initial position and font
        commands.append("BT")  # Begin text
        commands.append("/F1 12 Tf")  # Font 1, size 12
        commands.append("72 750 Td")  # Position at top-left margin

        # Reset Y position
        self.current_y = 750

        # Render document content
        for block in doc.blocks:
            block_commands = self._render_block_to_pdf(block)
            commands.extend(block_commands)

        commands.append("ET")  # End text

        return "\n".join(commands)

    def _render_block_to_pdf(self, block) -> List[str]:
        """Render a block to PDF content stream commands."""
        commands = []

        if isinstance(block, Heading):
            commands.extend(self._render_heading_to_pdf(block))
        elif isinstance(block, Paragraph):
            commands.extend(self._render_paragraph_to_pdf(block))
        elif isinstance(block, MathBlock):
            commands.extend(self._render_math_block_to_pdf(block))
        elif isinstance(block, CodeBlock):
            commands.extend(self._render_code_block_to_pdf(block))
        elif isinstance(block, ListBlock):
            commands.extend(self._render_list_block_to_pdf(block))

        return commands

    def _render_heading_to_pdf(self, heading: Heading) -> List[str]:
        """Render heading to PDF commands."""
        commands = []
        level = heading.level
        text = self._extract_text(heading.content)

        # Calculate font size based on level
        font_sizes = {1: 18, 2: 16, 3: 14, 4: 12, 5: 11, 6: 10}
        size = font_sizes.get(level, 12)

        commands.append(f"/F1 {size} Tf")
        commands.append(f"0 -{size + 5} Td")  # Move down
        commands.append(f"({text}) Tj")
        commands.append("0 -5 Td")  # Extra space after heading

        self.current_y -= (size + 10)

        return commands

    def _render_paragraph_to_pdf(self, paragraph: Paragraph) -> List[str]:
        """Render paragraph to PDF commands."""
        commands = []
        text = self._extract_text(paragraph.content)

        if text.strip():
            # Simple text rendering (no wrapping for now)
            commands.append("/F1 12 Tf")
            commands.append("0 -14 Td")  # Move down one line
            commands.append(f"({text}) Tj")

            self.current_y -= 14

        return commands

    def _render_math_block_to_pdf(self, math_block: MathBlock) -> List[str]:
        """Render math block to PDF commands."""
        commands = []
        content = math_block.content.strip()

        # Remove delimiters
        if content.startswith('$$') and content.endswith('$$'):
            content = content[2:-2].strip()
        elif content.startswith('$') and content.endswith('$'):
            content = content[1:-1].strip()

        # For now, render as simple text with brackets
        math_text = f"[MATH: {content}]"

        commands.append("/F1 12 Tf")
        commands.append("0 -18 Td")  # Extra space for math
        commands.append(f"({math_text}) Tj")
        commands.append("0 -4 Td")  # Extra spacing

        self.current_y -= 22

        return commands

    def _render_code_block_to_pdf(self, code_block: CodeBlock) -> List[str]:
        """Render code block to PDF commands."""
        commands = []
        lines = code_block.content.split('\n')

        commands.append("/F2 10 Tf")  # Courier font

        for line in lines:
            if line.strip():
                commands.append("0 -12 Td")
                commands.append(f"({line}) Tj")

        commands.append("/F1 12 Tf")  # Back to normal font
        commands.append("0 -6 Td")  # Extra space

        return commands

    def _render_list_block_to_pdf(self, list_block: ListBlock) -> List[str]:
        """Render list to PDF commands."""
        commands = []

        for i, item in enumerate(list_block.items):
            commands.extend(self._render_list_item_to_pdf(item, i + 1, list_block.ordered))

        return commands

    def _render_list_item_to_pdf(self, item: ListItem, index: int, ordered: bool) -> List[str]:
        """Render list item to PDF commands."""
        commands = []

        # Create bullet/number
        if ordered:
            prefix = f"{index}. "
        else:
            prefix = "• "

        text = self._extract_text(item.content)
        full_text = f"{prefix}{text}"

        commands.append("/F1 12 Tf")
        commands.append("0 -14 Td")
        commands.append(f"({full_text}) Tj")

        self.current_y -= 14

        return commands

    def _extract_text(self, elements) -> str:
        """Extract plain text from inline elements."""
        if not elements:
            return ""

        result = []
        for element in elements:
            if isinstance(element, Text):
                result.append(element.content)
            elif isinstance(element, Bold):
                inner = self._extract_text(element.children)
                result.append(inner)
            elif isinstance(element, Italic):
                inner = self._extract_text(element.children)
                result.append(inner)
            elif isinstance(element, CodeInline):
                result.append(f'`{element.content}`')
            elif isinstance(element, MathInline):
                result.append(f'[{element.content.strip("$")}]')
            elif isinstance(element, Link):
                result.append(element.text)
            else:
                result.append(str(element))

        return "".join(result)

    def _create_content_stream(self, content: str) -> bytes:
        """Create a PDF content stream object with compressed content."""
        # Convert to bytes using proper encoding, then compress
        content_bytes = content.encode('utf-8')
        compressed = zlib.compress(content_bytes)

        # Create the stream object as bytes
        stream_header = f"""<<
/Length {len(compressed)}
/Filter /FlateDecode
>>
stream
""".encode('ascii')

        stream_footer = b"\nendstream\n"

        return stream_header + compressed + stream_footer

    def _add_object(self, content):
        """Add an object to the PDF structure."""
        if isinstance(content, str):
            self.objects.append(content)
        elif isinstance(content, bytes):
            # For binary content streams, store as bytes
            self.objects.append(content)
        else:
            self.objects.append(str(content))

    def _generate_pdf(self) -> bytes:
        """Generate the complete PDF file."""
        pdf_parts = []

        # PDF header
        pdf_parts.append(b"%PDF-1.4")
        pdf_parts.append(b"%\xe2\xe3")  # Binary comment with high bytes

        # Objects
        for i, obj_content in enumerate(self.objects, 1):
            self.object_offsets.append(len(b''.join(pdf_parts)))
            pdf_parts.append(f"{i} 0 obj".encode('ascii'))
            pdf_parts.append(b'\n')
            if isinstance(obj_content, bytes):
                pdf_parts.append(obj_content)
            else:
                pdf_parts.append(obj_content.encode('ascii'))
            pdf_parts.append(b'\nendobj\n')

        # Cross-reference table
        xref_offset = len(b''.join(pdf_parts))
        xref_table = f"""xref
0 {len(self.objects) + 1}
0000000000 65535 f
"""

        for offset in self.object_offsets:
            xref_table += f"{offset:010d} 00000 n \n"

        pdf_parts.append(xref_table.encode('ascii'))

        # Trailer
        trailer = f"""trailer
<<
/Size {len(self.objects) + 1}
/Root 1 0 R
>>
startxref
{xref_offset}
%%EOF
"""

        pdf_parts.append(trailer.encode('ascii'))

        return b''.join(pdf_parts)

    def render_math_expression(self, math_content: str, display_style: bool = False) -> MathBox:
        """
        Render a mathematical expression using the layout engine.

        This method uses the MathLayoutEngine to properly lay out
        mathematical expressions for eventual rendering.

        Args:
            math_content: LaTeX math content (without delimiters)
            display_style: True for display math, False for inline

        Returns:
            MathBox with proper layout information
        """
        try:
            # Parse the expression
            parsed_box = self.math_parser.parse_expression(math_content)

            # Apply layout
            self.math_engine.display_style = display_style
            layout_box = self.math_engine.layout_expression([parsed_box])

            return layout_box

        except Exception as e:
            print(f"Math rendering failed for: {math_content}")
            print(f"Error: {e}")
            # Return a simple text box as fallback
            return MathBox(
                content=f"[Math Error: {math_content}]",
                box_type=BoxType.ATOM,
                dimensions=Dimensions(100, 12, 0)
            )
