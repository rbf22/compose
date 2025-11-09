"""
FPDF2-based renderer for Compose

Replaces fragile manual PDF command generation with robust fpdf2 high-level API.
Provides automatic layout management, proper math rendering, and eliminates positioning errors.
"""

import io
from typing import Dict, List, Optional, Tuple, Any
from fpdf import FPDF
from ..model.ast import Document, Heading, Paragraph, MathBlock, MathInline, CodeBlock, ListBlock, ListItem, Link, Image, Text, Bold, Italic, Strikethrough, CodeInline, Table
from .rendering_tracker import RenderingTracker


class FPDF2Renderer:
    """
    Robust PDF renderer using fpdf2 high-level API.

    Features:
    - Automatic page breaks and margin handling
    - Proper math rendering via matplotlib
    - Robust text positioning and layout
    - Integration with RenderingTracker for validation
    """

    def __init__(self, page_width: float = 612, page_height: float = 792,
                 margin_left: float = 50, margin_right: float = 50,
                 margin_top: float = 60, margin_bottom: float = 60):
        """
        Initialize fpdf2 renderer with page dimensions and margins.
        """
        # Create fpdf2 instance
        self.pdf = FPDF(unit='pt', format=(page_width, page_height))
        self.pdf.add_page()
        self.pdf.set_margins(left=margin_left, top=margin_top, right=margin_right)

        # Page and margin settings
        self.page_width = page_width
        self.page_height = page_height
        self.margin_left = margin_left
        self.margin_right = margin_right
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom

        # RenderingTracker for validation
        self.tracker = RenderingTracker()
        self.current_page = 0

        # Font setup - use built-in fonts initially
        self.setup_fonts()

        # Typography settings
        self.current_font_size = 12
        self.line_height_factor = 1.2

    def setup_fonts(self):
        """Setup fonts for rendering using only built-in fpdf2 fonts."""
        # Use only built-in fonts that come with fpdf2
        # Available built-in fonts: 'helvetica', 'times', 'courier' (case-insensitive)
        self.font_family = 'helvetica'  # Default to helvetica (Arial-like)
        self.bold_font_family = 'helvetica'  # Bold variant
        self.mono_font_family = 'courier'  # Monospace

        self.pdf.set_font(self.font_family, '', 12)

    def render(self, doc: Document, config: Dict = None) -> bytes:
        """
        Render document using fpdf2 with automatic layout management.

        Args:
            doc: Document AST to render
            config: Configuration options

        Returns:
            Complete PDF file as bytes
        """
        config = config or {}

        # Apply configuration
        self._apply_config(config)

        # Reset state
        self._reset_render_state()

        # Layout document using Measure → Update → Render → Check pipeline
        self._layout_document_clean(doc)

        # Validate final layout
        errors = self.tracker.validate_all(
            page_height=self.page_height,
            page_width=self.page_width,
            margin_top=self.margin_top,
            margin_bottom=self.margin_bottom,
            margin_left=self.margin_left,
            margin_right=self.margin_right
        )

        if errors:
            print(f"Rendering validation errors: {len(errors)}")
            for error in errors[:10]:
                print(f"  {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more errors")

        # Return final PDF bytes
        return self.pdf.output()

    def _apply_config(self, config: Dict):
        """Apply configuration settings."""
        if 'dpi' in config:
            # fpdf2 handles DPI differently, but we can store for math rendering
            self.dpi = config.get('dpi', 300)
        if 'margins' in config:
            margins = config['margins']
            self.margin_left = margins.get('left', 50)
            self.margin_right = margins.get('right', 50)
            self.margin_top = margins.get('top', 60)
            self.margin_bottom = margins.get('bottom', 60)
            # Update fpdf2 margins
            self.pdf.set_margins(left=self.margin_left, top=self.margin_top, right=self.margin_right)
        if 'typography' in config:
            typo = config['typography']
            self.line_height_factor = typo.get('line_height', 1.2)

    def _reset_render_state(self):
        """Reset rendering state for new document."""
        # Reset fpdf2
        self.pdf = FPDF(unit='pt', format=(self.page_width, self.page_height))
        self.pdf.add_page()
        self.pdf.set_margins(left=self.margin_left, top=self.margin_top, right=self.margin_right)

        # Reset fonts
        self.setup_fonts()

        # Reset tracker and page counter
        self.tracker.clear()
        self.current_page = 0

    def _layout_document_clean(self, doc: Document):
        """
        Clean implementation using Measure → Update → Render → Check pipeline with fpdf2.

        fpdf2 handles most layout automatically, but we still use the pipeline for:
        - Measurement-based decisions
        - Tracker validation
        - Complex layout logic
        """
        # Title page if specified
        if doc.frontmatter.get('title'):
            self._render_title_page(doc)

        # Process each block using the pipeline
        for block in doc.blocks:
            # MEASURE phase - still useful for complex layout decisions
            # Note: fpdf2 handles most positioning automatically

            # UPDATE phase - minimal since fpdf2 handles layout
            # We mainly need to handle page breaks for complex elements

            # RENDER phase - use fpdf2 methods
            self._render_block_fpdf2(block)

        # CHECK phase - validate final layout
        # Already done in render() method

    def _render_title_page(self, doc: Document):
        """Render title page using fpdf2."""
        title = doc.frontmatter.get('title', 'Document')
        author = doc.frontmatter.get('author', '')
        date = doc.frontmatter.get('date', '')

        # Position title page content
        title_y = self.page_height - 150
        author_y = self.page_height - 250
        date_y = self.page_height - 320

        # Title
        self.pdf.set_font(self.font_family, 'B', 36)
        self.pdf.set_xy(self.margin_left, title_y)
        self.pdf.cell(0, 40, title)

        # Author
        if author:
            self.pdf.set_font(self.font_family, '', 18)
            self.pdf.set_xy(self.margin_left, author_y)
            self.pdf.cell(0, 20, f"Author: {author}")

        # Date
        if date:
            self.pdf.set_font(self.font_family, '', 12)
            self.pdf.set_xy(self.margin_left, date_y)
            self.pdf.cell(0, 15, f"Date: {date}")

        # New page for content
        self.pdf.add_page()
        self.current_page += 1
        self.tracker.current_page = self.current_page

    def _render_block_fpdf2(self, block):
        """Render a block using fpdf2 methods."""
        if isinstance(block, Heading):
            self._render_heading_fpdf2(block)
        elif isinstance(block, Paragraph):
            self._render_paragraph_fpdf2(block)
        elif isinstance(block, MathBlock):
            self._render_math_block_fpdf2(block)
        elif isinstance(block, CodeBlock):
            self._render_code_block_fpdf2(block)
        elif isinstance(block, ListBlock):
            self._render_list_block_fpdf2(block)
        elif isinstance(block, Image):
            self._render_image_fpdf2(block)
        elif isinstance(block, Table):
            self._render_table_fpdf2(block)
        elif hasattr(block, '__class__') and block.__class__.__name__ == 'HorizontalRule':
            self._render_horizontal_rule_fpdf2(block)
        # Skip unknown blocks silently

    def _convert_fpdf2_to_pdf_coords(self, fpdf2_y: float, height: float = 0) -> Tuple[float, float]:
        """
        Convert fpdf2 coordinates (Y from top) to PDF coordinates (Y from bottom).
        
        Args:
            fpdf2_y: Y coordinate in fpdf2 (distance from top)
            height: Height of the element
            
        Returns:
            Tuple of (pdf_y_top, pdf_y_bottom)
        """
        page_height = self.pdf.h
        pdf_y_top = page_height - fpdf2_y  # Convert to distance from bottom
        pdf_y_bottom = pdf_y_top - height
        return pdf_y_top, pdf_y_bottom

    def _render_heading_fpdf2(self, heading: Heading):
        """Render heading using fpdf2 multi_cell for proper text wrapping."""
        level = heading.level
        text = self._extract_text_content(heading.content)

        # Heading sizes
        font_sizes = {1: 24, 2: 20, 3: 16, 4: 14, 5: 12, 6: 12}
        font_size = font_sizes.get(level, 12)

        # Set font with bold style
        self.pdf.set_font(self.font_family, 'B', font_size)

        # Add spacing before (fpdf2 handles this automatically)
        spacing_before = {1: 36, 2: 24, 3: 18, 4: 12, 5: 12, 6: 12}.get(level, 12)
        if spacing_before > 0:
            self.pdf.ln(spacing_before)

        # Get position before rendering
        start_y = self.pdf.get_y()

        # Calculate available width for wrapping
        available_width = self.pdf.w - self.pdf.l_margin - self.pdf.r_margin

        # Use multi_cell for proper text wrapping
        line_height = font_size * 1.2
        self.pdf.multi_cell(available_width, line_height, text)

        # Calculate the height of the heading (may span multiple lines)
        end_y = self.pdf.get_y()
        heading_height = end_y - start_y

        # Convert coordinates for tracker
        pdf_y_top, pdf_y_bottom = self._convert_fpdf2_to_pdf_coords(start_y, heading_height)
        # Move to next line after paragraph
        self.pdf.ln(line_height)

        # Record paragraph in tracker
        pdf_y_top, pdf_y_bottom = self._convert_fpdf2_to_pdf_coords(start_y, line_height)
        self.tracker.record_text(
            x=self.pdf.l_margin,
            y=pdf_y_top,
            width=available_width,
            height=line_height,
            page=self.current_page,
            label=f"h{level}_{text[:20]}"
        )

        # Add paragraph spacing
        if self.pdf.get_y() + 6 > self.pdf.h - self.pdf.b_margin:
            self.pdf.add_page()
            self.current_page += 1
            self.tracker.current_page = self.current_page
        else:
            self.pdf.ln(6)

        # Add spacing after
        spacing_after = {1: 18, 2: 12, 3: 9, 4: 6, 5: 6, 6: 6}.get(level, 6)
        if spacing_after > 0:
            self.pdf.ln(spacing_after)

    def _render_paragraph_fpdf2(self, paragraph: Paragraph):
        """Render paragraph with proper inline formatting support."""
        if not paragraph.content:
            return

        # Set base font
        self.pdf.set_font(self.font_family, '', self.current_font_size)
        available_width = self.pdf.w - self.pdf.l_margin - self.pdf.r_margin
        line_height = self.current_font_size * self.line_height_factor

        # Start position
        start_y = self.pdf.get_y()
        current_x = self.pdf.l_margin

        # Process inline elements recursively
        self._render_inline_elements(paragraph.content, current_x, start_y, available_width, line_height)

        # Move to next line after paragraph
        self.pdf.ln(line_height)

        # Record paragraph in tracker
        pdf_y_top, pdf_y_bottom = self._convert_fpdf2_to_pdf_coords(start_y, line_height)
        self.tracker.record_text(
            x=self.pdf.l_margin,
            y=pdf_y_top,
            width=available_width,
            height=line_height,
            page=self.current_page,
            label=f"paragraph_para"
        )

        # Add paragraph spacing
        if self.pdf.get_y() + 6 > self.pdf.h - self.pdf.b_margin:
            self.pdf.add_page()
            self.current_page += 1
            self.tracker.current_page = self.current_page
        else:
            self.pdf.ln(6)

    def _render_inline_elements(self, elements, start_x, start_y, max_width, line_height):
        """Recursively render inline elements with proper font handling."""
        current_x = start_x
        
        for element in elements:
            if isinstance(element, Text):
                # Plain text - render with current font
                text = self._sanitize_text(element.content)
                text = self._filter_html_comments(text)
                if text.strip():
                    self._render_text_with_wrapping(text, current_x, start_y, max_width, line_height)
            elif isinstance(element, Bold):
                # Bold text - switch to bold font
                original_font = self.pdf.font_family
                original_style = self.pdf.font_style
                self.pdf.set_font(self.font_family, 'B', self.current_font_size)
                self._render_inline_elements(element.children, current_x, start_y, max_width, line_height)
                self.pdf.set_font(original_font, original_style, self.current_font_size)  # Restore
            elif isinstance(element, Italic):
                # Italic text - switch to italic font
                original_font = self.pdf.font_family
                original_style = self.pdf.font_style
                self.pdf.set_font(self.font_family, 'I', self.current_font_size)
                self._render_inline_elements(element.children, current_x, start_y, max_width, line_height)
                self.pdf.set_font(original_font, original_style, self.current_font_size)  # Restore
            elif isinstance(element, CodeInline):
                # Inline code - switch to monospace font
                original_font = self.pdf.font_family
                original_style = self.pdf.font_style
                self.pdf.set_font(self.mono_font_family, '', self.current_font_size)
                code_text = self._sanitize_text(element.content)
                self._render_text_with_wrapping(code_text, current_x, start_y, max_width, line_height)
                self.pdf.set_font(original_font, original_style, self.current_font_size)  # Restore
            elif isinstance(element, MathInline):
                # Inline math - placeholder
                math_text = f'[{element.content.strip("$")}]'
                math_text = self._sanitize_text(math_text)
                self._render_text_with_wrapping(math_text, current_x, start_y, max_width, line_height)
            elif isinstance(element, Link):
                # Link - just render text for now
                link_text = self._sanitize_text(element.text)
                self._render_text_with_wrapping(link_text, current_x, start_y, max_width, line_height)
            
            # Update current position after each element
            current_x = self.pdf.get_x()

    def _render_text_with_wrapping(self, text: str, start_x: float, start_y: float, max_width: float, line_height: float):
        """Render text with automatic wrapping, updating current position."""
        words = text.split()
        current_line = []
        current_width = 0
        
        for word in words:
            word_width = self.pdf.get_string_width(word + ' ')
            if current_line and current_width + word_width > max_width:
                # Render current line
                line_text = ' '.join(current_line)
                self.pdf.text(start_x, self.pdf.get_y() + line_height * 0.8, line_text)
                self.pdf.set_xy(start_x, self.pdf.get_y() + line_height)
                current_line = [word]
                current_width = word_width
            else:
                current_line.append(word)
                current_width += word_width
        
        # Render remaining line
        if current_line:
            line_text = ' '.join(current_line)
            self.pdf.text(start_x, self.pdf.get_y() + line_height * 0.8, line_text)
            self.pdf.set_xy(start_x + self.pdf.get_string_width(line_text), self.pdf.get_y())

    def _render_math_block_fpdf2(self, math_block: MathBlock):
        """Render math block with matplotlib integration."""
        content = math_block.content.strip()
        if content.startswith('$$') and content.endswith('$$'):
            content = content[2:-2].strip()
        elif content.startswith('$') and content.endswith('$'):
            content = content[1:-1].strip()

        # Try matplotlib rendering first
        if self._render_math_with_matplotlib(content):
            return

        # Fallback to text rendering
        self.pdf.set_font(self.font_family, '', 12)
        math_text = f"[MATH: {content}]"

        # Center the math text
        text_width = self.pdf.get_string_width(math_text)
        x_pos = (self.pdf.w - text_width) / 2

        start_y = self.pdf.get_y()
        self.pdf.set_xy(x_pos, start_y)
        self.pdf.cell(text_width, 14, math_text, ln=True)

        # Record in tracker
        self.tracker.record_text(
            x=x_pos,
            y=start_y,
            width=text_width,
            height=14,
            page=self.current_page,
            label=f"math_fallback_{content[:20]}"
        )

        # Add spacing
        self.pdf.ln(12)

    def _render_math_with_matplotlib(self, latex: str) -> bool:
        """Render math expression using matplotlib."""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')

            # Create math rendering
            fig, ax = plt.subplots(figsize=(6, 1))
            ax.text(0.5, 0.5, f'${latex}$',
                   fontsize=16, ha='center', va='center',
                   transform=ax.transAxes)

            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')

            # Convert to PNG
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=300,
                       bbox_inches='tight', transparent=True)
            plt.close(fig)
            buf.seek(0)

            # Center on page
            img_width = 120  # pts
            x_pos = (self.pdf.w - img_width) / 2
            start_y = self.pdf.get_y()

            self.pdf.image(buf, x=x_pos, y=start_y, w=img_width)

            # Record in tracker
            self.tracker.record_text(
                x=x_pos,
                y=start_y,
                width=img_width,
                height=30,  # Approximate height
                page=self.current_page,
                label=f"math_{latex[:20]}"
            )

            # Move past the math
            self.pdf.set_y(start_y + 35)
            self.pdf.ln(12)

            return True

        except Exception as e:
            print(f"Math rendering failed: {e}")
            return False

    def _render_code_block_fpdf2(self, code_block: CodeBlock):
        """Render code block using fpdf2."""
        lines = code_block.content.split('\n')

        # Set monospace font
        self.pdf.set_font(self.mono_font_family, '', 10)

        start_y = self.pdf.get_y()

        for line in lines:
            if line.strip():
                # Sanitize the line for fpdf2 compatibility
                sanitized_line = self._sanitize_text(line)
                self.pdf.cell(0, 12, sanitized_line, ln=True)

                # Record in tracker
                line_width = self.pdf.get_string_width(sanitized_line)
                self.tracker.record_text(
                    x=self.pdf.l_margin,
                    y=self.pdf.get_y() - 12,
                    width=line_width,
                    height=12,
                    page=self.current_page,
                    label="code_line"
                )

        # Reset font
        self.pdf.set_font(self.font_family, '', self.current_font_size)
        self.pdf.ln(6)

    def _render_list_block_fpdf2(self, list_block: ListBlock):
        """Render list block with manual page break handling."""
        for i, item in enumerate(list_block.items):
            if isinstance(item, ListItem):
                # Create bullet/number
                if list_block.ordered:
                    prefix = f"{i+1}. "
                else:
                    prefix = "* "

                text = prefix + self._extract_text_content(item.content)

                # Set font
                self.pdf.set_font(self.font_family, '', self.current_font_size)

                # Manual text wrapping for list items
                indent = 20
                available_width = self.pdf.w - self.pdf.l_margin - self.pdf.r_margin - indent
                line_height = self.current_font_size * self.line_height_factor

                # Split text into lines
                words = text.split()
                lines = []
                current_line = []
                current_width = 0

                for word in words:
                    word_width = self.pdf.get_string_width(word + ' ')
                    if current_line and current_width + word_width > available_width:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                        current_width = word_width
                    else:
                        current_line.append(word)
                        current_width += word_width

                if current_line:
                    lines.append(' '.join(current_line))

                # Render lines with proper indentation and page breaks
                for j, line in enumerate(lines):
                    # Check page break
                    if self.pdf.get_y() + line_height > self.pdf.h - self.pdf.b_margin:
                        self.pdf.add_page()
                        self.current_page += 1
                        self.tracker.current_page = self.current_page
                        self.pdf.set_y(self.pdf.t_margin)

                    # Set X position with indentation
                    x_pos = self.pdf.l_margin + (indent if j > 0 else 0)
                    self.pdf.set_x(x_pos)

                    # Render line
                    self.pdf.cell(available_width, line_height, line, ln=True)

                    # Record in tracker
                    line_width = self.pdf.get_string_width(line)
                    current_y = self.pdf.get_y() - line_height
                    pdf_y_top, pdf_y_bottom = self._convert_fpdf2_to_pdf_coords(current_y, line_height)

                    self.tracker.record_text(
                        x=x_pos,
                        y=pdf_y_top,
                        width=available_width,  # Use constrained width
                        height=line_height,
                        page=self.current_page,
                        label="list_item"
                    )

    def _render_table_fpdf2(self, table: Table):
        """Render professional table with styling, colors, and proper borders."""
        if not table.headers and not table.rows:
            return

        # Table styling constants
        HEADER_BG_COLOR = (0.9, 0.9, 0.9)  # Light gray background for headers
        BORDER_COLOR = (0.3, 0.3, 0.3)     # Dark gray borders
        CELL_PADDING = 4
        LINE_WIDTH = 0.5

        # Calculate dimensions
        available_width = self.pdf.w - self.pdf.l_margin - self.pdf.r_margin
        num_cols = len(table.headers) if table.headers else len(table.rows[0]) if table.rows else 0
        
        if num_cols == 0:
            return
            
        col_width = available_width / num_cols
        start_y = self.pdf.get_y()

        # Save current drawing state
        prev_line_width = self.pdf.line_width
        self.pdf.set_line_width(LINE_WIDTH)

        # Render headers with background
        if table.headers:
            header_height = 14
            
            # Draw header background
            self.pdf.set_fill_color(*[int(c * 255) for c in HEADER_BG_COLOR])
            self.pdf.rect(self.pdf.l_margin, start_y, available_width, header_height, style='F')
            
            # Draw header borders
            self.pdf.set_draw_color(*[int(c * 255) for c in BORDER_COLOR])
            self.pdf.rect(self.pdf.l_margin, start_y, available_width, header_height, style='D')
            
            # Draw vertical lines
            for i in range(1, num_cols):
                x = self.pdf.l_margin + (i * col_width)
                self.pdf.line(x, start_y, x, start_y + header_height)
            
            # Render header text
            self.pdf.set_font(self.font_family, 'B', 10)
            self.pdf.set_text_color(0, 0, 0)  # Black text
            
            for i, cell in enumerate(table.headers):
                cell_text = self._extract_text_content(cell)
                x_pos = self.pdf.l_margin + (i * col_width) + CELL_PADDING
                y_pos = start_y + CELL_PADDING + 8  # 8 is approx text height offset
                
                # Handle text that might be too wide
                if self.pdf.get_string_width(cell_text) > col_width - (2 * CELL_PADDING):
                    # Truncate with ellipsis
                    while cell_text and self.pdf.get_string_width(cell_text + '...') > col_width - (2 * CELL_PADDING):
                        cell_text = cell_text[:-1]
                    cell_text += '...'
                
                self.pdf.text(x_pos, y_pos, cell_text)
                
                # Record header cell
                pdf_y_top, pdf_y_bottom = self._convert_fpdf2_to_pdf_coords(start_y, header_height)
                self.tracker.record_text(
                    x=self.pdf.l_margin + (i * col_width),
                    y=pdf_y_top,
                    width=col_width,
                    height=header_height,
                    page=self.current_page,
                    label=f"table_header_{i}"
                )

            start_y += header_height

        # Render data rows
        self.pdf.set_font(self.font_family, '', 10)
        self.pdf.set_text_color(0, 0, 0)
        
        row_height = 12
        
        for row_idx, row in enumerate(table.rows):
            # Draw row borders
            self.pdf.set_draw_color(*[int(c * 255) for c in BORDER_COLOR])
            self.pdf.rect(self.pdf.l_margin, start_y, available_width, row_height, style='D')
            
            # Draw vertical lines
            for i in range(1, num_cols):
                x = self.pdf.l_margin + (i * col_width)
                self.pdf.line(x, start_y, x, start_y + row_height)
            
            # Render cell text
            for col_idx, cell in enumerate(row):
                cell_text = self._extract_text_content(cell)
                x_pos = self.pdf.l_margin + (col_idx * col_width) + CELL_PADDING
                y_pos = start_y + CELL_PADDING + 8
                
                # Handle text that might be too wide
                if self.pdf.get_string_width(cell_text) > col_width - (2 * CELL_PADDING):
                    # Truncate with ellipsis
                    while cell_text and self.pdf.get_string_width(cell_text + '...') > col_width - (2 * CELL_PADDING):
                        cell_text = cell_text[:-1]
                    cell_text += '...'
                
                self.pdf.text(x_pos, y_pos, cell_text)
                
                # Record data cell
                pdf_y_top, pdf_y_bottom = self._convert_fpdf2_to_pdf_coords(start_y, row_height)
                self.tracker.record_text(
                    x=self.pdf.l_margin + (col_idx * col_width),
                    y=pdf_y_top,
                    width=col_width,
                    height=row_height,
                    page=self.current_page,
                    label=f"table_cell_{row_idx}_{col_idx}"
                )
            
            start_y += row_height

        # Restore drawing state
        self.pdf.set_line_width(prev_line_width)
        self.pdf.set_fill_color(255, 255, 255)  # Reset to white
        self.pdf.set_draw_color(0, 0, 0)        # Reset to black

        # Add spacing after table
        self.pdf.ln(12)

    def _render_image_fpdf2(self, image: Image):
        """Render image using fpdf2 (placeholder)."""
        # For now, just add some space
        self.pdf.ln(50)

    def _render_horizontal_rule_fpdf2(self, block):
        """Render horizontal rule (page break)."""
        self.pdf.add_page()
        self.current_page += 1
        self.tracker.current_page = self.current_page

    def _extract_text_content(self, elements) -> str:
        """Extract plain text from inline elements, sanitizing for fpdf2 compatibility."""
        # Handle case where elements is a single InlineElement instead of a list
        if not isinstance(elements, list):
            elements = [elements]
        
        if not elements:
            return ""

        result = []
        for element in elements:
            if isinstance(element, Text):
                # Sanitize text for fpdf2 compatibility
                text = self._sanitize_text(element.content)
                # Filter out HTML comments
                text = self._filter_html_comments(text)
                if text.strip():  # Only add non-empty text
                    result.append(text)
            elif isinstance(element, (Bold, Italic)):
                inner = self._extract_text_content(element.children)
                if inner.strip():
                    result.append(inner)
            elif isinstance(element, CodeInline):
                text = self._sanitize_text(f'`{element.content}`')
                result.append(text)
            elif isinstance(element, MathInline):
                text = self._sanitize_text(f'[{element.content.strip("$")}]')
                result.append(text)
            elif isinstance(element, Link):
                text = self._sanitize_text(element.text)
                result.append(text)
            else:
                text = self._sanitize_text(str(element))
                if text.strip():
                    result.append(text)

        return "".join(result)

    def _filter_html_comments(self, text: str) -> str:
        """Remove HTML comments from text content."""
        import re
        # Remove HTML comments: <!-- comment -->
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        return text.strip()

    def _sanitize_text(self, text: str) -> str:
        """Sanitize text for fpdf2 compatibility by removing unsupported Unicode characters."""
        # First, replace common Unicode characters with ASCII equivalents
        replacements = {
            '→': '->',
            '←': '<-',
            '•': '*',
            '✓': '[x]',
            '❌': '[x]',
            '✅': '[v]',
            '🚀': '[rocket]',
            '🎯': '[target]',
            '🏗️': '[construction]',
            '📊': '[chart]',
            '📏': '[ruler]',
            '📄': '[page]',
            '🎉': '[party]',
            '🏗': '[construction]',  # Without variation selector
            # Mathematical symbols
            '∑': 'SUM',
            '∫': 'INT',
            '√': 'SQRT',
            'π': 'PI',
            '∞': 'INF',
            '≤': '<=',
            '≥': '>=',
            '≠': '!=',
            '≈': '~=',
            # Quotes and dashes
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
            '–': '-',
            '—': '--',
            '…': '...',
        }

        result = text
        for unicode_char, replacement in replacements.items():
            result = result.replace(unicode_char, replacement)

        # Remove emojis and other problematic Unicode characters
        import re
        # Remove emoji characters (basic emoji range)
        result = re.sub(r'[\U0001F600-\U0001F64F]', '', result)  # Emoticons
        result = re.sub(r'[\U0001F300-\U0001F5FF]', '', result)  # Symbols & Pictographs
        result = re.sub(r'[\U0001F680-\U0001F6FF]', '', result)  # Transport & Map
        result = re.sub(r'[\U0001F1E0-\U0001F1FF]', '', result)  # Flags
        result = re.sub(r'[\U00002700-\U000027BF]', '', result)  # Dingbats
        result = re.sub(r'[\U0001f926-\U0001f937]', '', result)  # Gestures
        result = re.sub(r'[\U00010000-\U0010ffff]', '', result)  # Other Unicode planes
        result = re.sub(r'\u200d', '', result)  # Zero width joiner
        result = re.sub(r'\ufe0f', '', result)  # Variation selector

        # Remove any remaining non-ASCII characters that can't be handled
        # Keep only characters that can be encoded in latin-1
        result = result.encode('latin-1', errors='ignore').decode('latin-1')

        return result.strip()
