"""
Concrete fpdf2 Integration for Compose

Since fpdf2 and matplotlib are already in pyproject.toml,
we can immediately start using them to fix the current rendering issues.
"""

import io
from typing import Optional
from fpdf import FPDF
from compose.render.rendering_tracker import RenderingTracker


class FPDF2ComposeRenderer:
    """
    fpdf2-based renderer that fixes current issues:

    - Automatic page breaks (no bottom margin violations)
    - Robust text positioning (no negative coordinates)
    - Better math rendering via matplotlib
    - Automatic layout management
    """

    def __init__(self, page_width=612, page_height=792, margins=(50, 60, 50)):
        self.pdf = FPDF(unit='pt', format=(page_width, page_height))
        self.pdf.add_page()
        self.pdf.set_margins(*margins)

        # Keep our validation system
        self.tracker = RenderingTracker()
        self.current_page = 0

        # Font setup
        self.pdf.add_font('DejaVu', '', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf', uni=True)
        self.pdf.set_font('DejaVu', '', 12)

    def render_heading(self, text: str, level: int = 1):
        """Robust heading rendering with automatic positioning"""
        font_sizes = {1: 24, 2: 20, 3: 16, 4: 14, 5: 12, 6: 12}

        # Set font and size
        self.pdf.set_font('DejaVu', 'B', font_sizes.get(level, 12))

        # Calculate spacing
        spacing_before = {1: 36, 2: 24, 3: 18, 4: 12, 5: 12, 6: 12}.get(level, 12)
        if spacing_before > 0:
            self.pdf.ln(spacing_before)

        # Render text (fpdf2 handles page breaks automatically)
        self.pdf.cell(0, font_sizes.get(level, 12) * 1.2, text, ln=True)

        # Record for validation
        y_pos = self.pdf.get_y()
        self.tracker.record_text(
            x=self.pdf.l_margin,
            y=y_pos,
            width=self.pdf.get_string_width(text),
            height=font_sizes.get(level, 12),
            page=self.current_page,
            label=f'h{level}_{text[:20]}'
        )

    def render_paragraph(self, text: str):
        """Automatic text wrapping and positioning"""
        self.pdf.set_font('DejaVu', '', 12)

        # Get current position before rendering
        start_y = self.pdf.get_y()

        # Render with automatic wrapping
        self.pdf.multi_cell(0, 14, text)  # 12pt font * 1.2 line height

        # Record paragraph bounds for validation
        end_y = self.pdf.get_y()
        self.tracker.record_text(
            x=self.pdf.l_margin,
            y=start_y,
            width=self.pdf.w - self.pdf.l_margin - self.pdf.r_margin,
            height=end_y - start_y,
            page=self.current_page,
            label=f'paragraph_{text[:20]}'
        )

        # Add paragraph spacing
        self.pdf.ln(6)

    def render_math(self, latex: str):
        """Real math rendering using matplotlib"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')

            # Create math rendering
            fig, ax = plt.subplots(figsize=(6, 1))
            ax.text(0.5, 0.5, f'${latex}$',
                   fontsize=16, ha='center', va='center',
                   transform=ax.transAxes, usetex=False)  # Use mathtext
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')

            # Convert to image
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=300,
                       bbox_inches='tight', transparent=True)
            plt.close(fig)
            buf.seek(0)

            # Center the math on page
            img_width = 120  # pts
            x_pos = (self.pdf.w - img_width) / 2
            self.pdf.image(buf, x=x_pos, w=img_width)

            # Record for validation
            self.tracker.record_text(
                x=x_pos,
                y=self.pdf.get_y(),
                width=img_width,
                height=30,  # Approximate height
                page=self.current_page,
                label=f'math_{latex[:20]}'
            )

        except ImportError:
            # Fallback if matplotlib not available
            self.pdf.set_font('DejaVu', '', 12)
            self.pdf.cell(0, 14, f'[MATH: {latex}]', ln=True)

    def validate_layout(self) -> list[str]:
        """Use existing tracker validation"""
        return self.tracker.validate_all(
            page_height=self.pdf.h,
            page_width=self.pdf.w,
            margin_top=self.pdf.t_margin,
            margin_bottom=60,  # Default bottom margin
            margin_left=self.pdf.l_margin,
            margin_right=self.pdf.r_margin
        )

    def get_pdf_bytes(self) -> bytes:
        """Get final PDF"""
        return self.pdf.output(dest='S').encode('latin1')


# Example usage
if __name__ == "__main__":
    renderer = FPDF2ComposeRenderer()

    renderer.render_heading("Compose with fpdf2", 1)
    renderer.render_paragraph("This demonstrates robust rendering with automatic layout management.")

    renderer.render_heading("Math Support", 2)
    renderer.render_math("E = mc^2")
    renderer.render_math("\\frac{a}{b} + \\sqrt{x^2 + y^2}")

    # Validate layout
    errors = renderer.validate_layout()
    if errors:
        print(f"Layout errors: {len(errors)}")
        for error in errors[:5]:
            print(f"  {error}")
    else:
        print("✅ Layout validation passed")

    pdf_bytes = renderer.get_pdf_bytes()
    print(f"Generated {len(pdf_bytes)} bytes of robust PDF")
