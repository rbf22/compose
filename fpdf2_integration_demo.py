"""
Proof of concept: How fpdf2 could improve Compose's rendering

This shows how fpdf2's high-level API could replace manual PDF command generation
and provide better math rendering capabilities.
"""

from fpdf import FPDF
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import io

class FPDF2MathRenderer:
    """Demonstrates how fpdf2 + matplotlib could render math"""

    def __init__(self):
        self.pdf = FPDF()
        self.pdf.add_page()
        self.pdf.set_margins(50, 60, 50)

    def render_math_expression(self, latex_code):
        """Render a LaTeX math expression using matplotlib"""
        try:
            # Create matplotlib figure with math text
            fig, ax = plt.subplots(figsize=(6, 1))
            ax.text(0.5, 0.5, f'${latex_code}$',
                   fontsize=16, ha='center', va='center',
                   transform=ax.transAxes)

            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')

            # Convert to PNG bytes
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=300,
                       bbox_inches='tight', transparent=True)
            plt.close(fig)

            # Embed in PDF
            buf.seek(0)
            self.pdf.image(buf, w=120)  # Auto-size width

            return True
        except Exception as e:
            print(f"Math rendering failed: {e}")
            # Fallback to text
            self.pdf.set_font('Arial', '', 12)
            self.pdf.cell(0, 10, f'[MATH: {latex_code}]', ln=True)
            return False

    def render_heading(self, text, level=1):
        """Clean heading rendering with automatic sizing"""
        sizes = {1: 24, 2: 20, 3: 16, 4: 14, 5: 12}
        self.pdf.set_font('Arial', 'B', sizes.get(level, 12))
        self.pdf.cell(0, 12, text, ln=True)

    def render_paragraph(self, text):
        """Automatic text wrapping and positioning"""
        self.pdf.set_font('Arial', '', 12)
        self.pdf.multi_cell(0, 6, text)
        self.pdf.ln(3)  # Add some spacing

    def get_pdf_bytes(self):
        """Get final PDF as bytes"""
        return self.pdf.output(dest='S').encode('latin1')

# Demonstration
if __name__ == "__main__":
    renderer = FPDF2MathRenderer()

    renderer.render_heading("Compose + fpdf2 Integration", 1)
    renderer.render_paragraph("This demonstrates how fpdf2 could provide robust rendering with automatic layout management.")

    renderer.render_heading("Math Rendering", 2)
    renderer.render_math_expression("E = mc^2")
    renderer.render_math_expression("\\frac{a}{b} + \\sqrt{x^2 + y^2}")

    pdf_bytes = renderer.get_pdf_bytes()
    print(f"Generated PDF with {len(pdf_bytes)} bytes using fpdf2")
    print("Benefits: Automatic margins, page breaks, text positioning")
    print("Math rendering via matplotlib integration")
