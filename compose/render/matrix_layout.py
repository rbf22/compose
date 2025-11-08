# compose/render/matrix_layout.py
"""
Matrix layout engine for mathematical expressions.
Supports array and matrix environments like \begin{matrix}, \begin{pmatrix}, etc.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from ..layout.tex_boxes import HBox, VBox, CharBox, Glue, Box
from ..cache_system import math_cache, performance_monitor


class MatrixLayoutEngine:
    """
    Engine for laying out mathematical matrices and arrays.
    Handles various matrix environments and alignment options.
    """

    def __init__(self):
        self.default_matrix_spacing = 10  # pixels between elements
        self.matrix_vspace = 8  # pixels between rows

    @performance_monitor.time_operation("matrix_layout")
    def layout_matrix(self, content: str, environment: str = 'matrix') -> Box:
        """
        Layout a matrix from LaTeX matrix content with LaTeX-quality alignment.

        Args:
            content: Matrix content (e.g., "a & b \\ c & d")
            environment: Matrix environment type ('matrix', 'pmatrix', etc.)

        Returns:
            Box containing the laid out matrix
        """
        # Parse matrix content
        rows = self._parse_matrix_content(content)

        if not rows:
            return self._create_empty_matrix_box()

        # Create matrix layout with proper alignment
        matrix_box = self._create_matrix_layout_latex_quality(rows, environment)

        return matrix_box

    def _create_matrix_layout_latex_quality(self, rows: List[List[str]], environment: str) -> Box:
        """
        Create LaTeX-quality matrix layout with proper column alignment and spacing.

        Args:
            rows: Matrix rows and columns
            environment: Matrix environment type

        Returns:
            Box containing the aligned matrix
        """
        if not rows:
            return self._create_empty_matrix_box()

        num_rows = len(rows)
        num_cols = max(len(row) for row in rows) if rows else 0

        # Pre-layout all cells to determine column widths
        cell_layouts = self._layout_all_cells(rows)

        # Calculate column widths (maximum width per column)
        col_widths = [0] * num_cols
        for row_idx, row_layouts in enumerate(cell_layouts):
            for col_idx, cell_box in enumerate(row_layouts):
                if col_idx < num_cols:
                    col_widths[col_idx] = max(col_widths[col_idx], cell_box.width)

        # Calculate row heights
        row_heights = []
        for row_layouts in cell_layouts:
            if row_layouts:
                row_height = max(cell_box.height for cell_box in row_layouts)
                row_heights.append(row_height)
            else:
                row_heights.append(20)  # Default height

        # Create matrix content with proper spacing
        matrix_rows = []
        current_y = 0

        for row_idx, row_layouts in enumerate(cell_layouts):
            row_box = HBox()
            row_box.width = sum(col_widths) + (len(col_widths) - 1) * self.default_matrix_spacing
            row_box.height = row_heights[row_idx]

            # Position cells in row with proper column alignment
            current_x = 0
            for col_idx, cell_box in enumerate(row_layouts):
                if col_idx < len(col_widths):
                    # Center cell in its column
                    col_width = col_widths[col_idx]
                    cell_x = current_x + (col_width - cell_box.width) // 2

                    # Position cell vertically (baseline alignment)
                    cell_y = (row_heights[row_idx] - cell_box.height) // 2

                    cell_box._x_offset = cell_x
                    cell_box._y_offset = cell_y

                    row_box.add_box(cell_box)

                    current_x += col_width + self.default_matrix_spacing

            matrix_rows.append(row_box)

            # Add row spacing (except for last row)
            if row_idx < len(cell_layouts) - 1:
                spacing = Glue(height=self.matrix_vspace)
                matrix_rows.append(spacing)

        # Create vertical container for all rows
        matrix_vbox = VBox()
        total_height = sum(row_heights) + (len(row_heights) - 1) * self.matrix_vspace
        matrix_vbox.height = total_height
        matrix_vbox.width = sum(col_widths) + (len(col_widths) - 1) * self.default_matrix_spacing

        for row in matrix_rows:
            matrix_vbox.add_box(row)

        # Add matrix delimiters based on environment
        final_matrix = self._add_matrix_delimiters(matrix_vbox, environment)

        return final_matrix

    def _layout_all_cells(self, rows: List[List[str]]) -> List[List[Box]]:
        """
        Pre-layout all matrix cells to determine sizing requirements.

        Args:
            rows: Matrix content as strings

        Returns:
            List of rows, each containing laid-out cell boxes
        """
        cell_layouts = []

        for row in rows:
            row_layouts = []
            for cell_content in row:
                # Create cell with natural size first
                cell_box = self._create_matrix_cell(cell_content.strip(), 0, 0)
                row_layouts.append(cell_box)
            cell_layouts.append(row_layouts)

        return cell_layouts

    def _parse_matrix_content(self, content: str) -> List[List[str]]:
        """
        Parse matrix content into rows and columns.

        Args:
            content: Raw matrix content

        Returns:
            List of rows, each containing list of cell contents
        """
        if not content.strip():
            return []

        rows = []

        # Split by row separators (\\)
        row_strings = content.split('\\\\')
        row_strings = [row.strip() for row in row_strings if row.strip()]

        for row_str in row_strings:
            # Split by column separators (&)
            cells = [cell.strip() for cell in row_str.split('&')]
            if cells:
                rows.append(cells)

        return rows

    def _create_matrix_layout(self, rows: List[List[str]], environment: str) -> Box:
        """
        Create the actual matrix layout using boxes.

        Args:
            rows: Matrix rows and columns
            environment: Matrix environment type

        Returns:
            VBox containing the matrix
        """
        if not rows:
            return self._create_empty_matrix_box()

        # Determine matrix dimensions
        num_rows = len(rows)
        num_cols = max(len(row) for row in rows) if rows else 0

        # Create column widths (simplified - equal width for now)
        col_width = 40  # pixels per column
        row_height = 20  # pixels per row

        matrix_rows = []

        for row_idx, row in enumerate(rows):
            row_boxes = []

            for col_idx, cell_content in enumerate(row):
                # Create cell content (simplified - just text for now)
                cell_box = self._create_matrix_cell(cell_content, col_width, row_height)
                row_boxes.append(cell_box)

                # Add column spacing (except for last column)
                if col_idx < len(row) - 1:
                    row_boxes.append(Glue(width=self.default_matrix_spacing))

            # Create horizontal box for the row
            row_hbox = HBox()
            for box in row_boxes:
                row_hbox.add_box(box)

            matrix_rows.append(row_hbox)

            # Add row spacing (except for last row)
            if row_idx < len(rows) - 1:
                matrix_rows.append(Glue(height=self.matrix_vspace))

        # Create vertical box for the matrix
        matrix_vbox = VBox()
        for row in matrix_rows:
            matrix_vbox.add_box(row)

        # Add matrix delimiters based on environment
        final_matrix = self._add_matrix_delimiters(matrix_vbox, environment)

        return final_matrix

    def _create_matrix_cell(self, content: str, width: int = 0, height: int = 0) -> Box:
        """
        Create a matrix cell box with proper sizing.

        Args:
            content: Cell content
            width: Desired width (0 for auto)
            height: Desired height (0 for auto)

        Returns:
            Box representing the cell
        """
        if not content:
            content = ""  # Handle empty cells

        # Estimate dimensions based on content
        # This is a simplified approach - in a full implementation,
        # this would use proper font metrics
        content_width = max(20, len(content) * 10)  # Rough estimate
        content_height = 20  # Standard cell height

        if width > 0:
            content_width = width
        if height > 0:
            content_height = height

        # Create cell box
        cell_box = Box(width=content_width, height=content_height, box_type="matrix_cell")

        # Store content for rendering
        cell_box._content = content

        return cell_box

    def _add_matrix_delimiters(self, matrix_box: Box, environment: str) -> Box:
        """
        Add delimiters around the matrix based on environment type.

        Args:
            matrix_box: The matrix content box
            environment: Matrix environment type

        Returns:
            Box with delimiters
        """
        delimiter_map = {
            'pmatrix': ('(', ')'),
            'bmatrix': ('[', ']'),
            'Bmatrix': ('{', '}'),
            'vmatrix': ('|', '|'),
            'Vmatrix': ('‖', '‖'),
            'matrix': (None, None)  # No delimiters
        }

        left_delim, right_delim = delimiter_map.get(environment, (None, None))

        if left_delim and right_delim:
            # Create delimiter boxes
            delim_width = 8
            delim_height = matrix_box.height

            left_box = Box(width=delim_width, height=delim_height, box_type="delimiter")
            left_box._symbol = left_delim

            right_box = Box(width=delim_width, height=delim_height, box_type="delimiter")
            right_box._symbol = right_delim

            # Create horizontal box with delimiters
            hbox = HBox()
            hbox.add_box(left_box)
            hbox.add_box(Glue(width=4))  # Spacing
            hbox.add_box(matrix_box)
            hbox.add_box(Glue(width=4))  # Spacing
            hbox.add_box(right_box)

            return hbox

        return matrix_box

    def _create_empty_matrix_box(self) -> Box:
        """Create an empty matrix box for error cases."""
        box = Box(width=20, height=20, box_type="matrix")
        box._content = "∅"  # Empty set symbol
        return box

    def render_matrix_svg(self, matrix_box: Box) -> str:
        """
        Render matrix box to SVG.

        Args:
            matrix_box: Matrix box layout

        Returns:
            SVG string representation
        """
        # Calculate dimensions
        width = matrix_box.width + 40  # Add padding
        height = matrix_box.height + 40

        svg_parts = [f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">']

        # Add background
        svg_parts.append(f'<rect width="100%" height="100%" fill="#f8f9fa" stroke="#dee2e6" stroke-width="1" rx="4"/>')

        # Render the matrix content
        self._render_matrix_box_svg(matrix_box, svg_parts, 20, 20)

        svg_parts.append('</svg>')

        svg_content = '\n'.join(svg_parts)

        # Convert to data URL
        import base64
        svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{svg_base64}"

    def _render_matrix_box_svg(self, box: Box, svg_parts: List[str], x: int, y: int):
        """
        Recursively render box to SVG.

        Args:
            box: Box to render
            svg_parts: SVG parts list to append to
            x, y: Position to render at
        """
        if isinstance(box, HBox):
            current_x = x
            for child in box.contents:
                self._render_matrix_box_svg(child, svg_parts, current_x, y)
                current_x += child.width
        elif isinstance(box, VBox):
            current_y = y
            for child in box.contents:
                self._render_matrix_box_svg(child, svg_parts, x, current_y)
                current_y += child.height
        elif isinstance(box, Glue):
            # Glue doesn't render anything
            pass
        elif hasattr(box, '_content'):
            # Matrix cell with content
            svg_parts.append(f'<text x="{x + box.width//2}" y="{y + box.height//2}" '
                           f'text-anchor="middle" dominant-baseline="middle" '
                           f'font-family="Times New Roman, serif" font-size="14px">{box._content}</text>')
        elif hasattr(box, '_symbol'):
            # Delimiter
            svg_parts.append(f'<text x="{x + box.width//2}" y="{y + box.height//2}" '
                           f'text-anchor="middle" dominant-baseline="middle" '
                           f'font-family="Times New Roman, serif" font-size="18px">{box._symbol}</text>')
        else:
            # Generic box - draw outline
            svg_parts.append(f'<rect x="{x}" y="{y}" width="{box.width}" height="{box.height}" '
                           f'fill="none" stroke="#ccc" stroke-width="1"/>')


class MatrixParser:
    """
    Parser for matrix expressions in LaTeX.
        Handles \\begin{matrix}...\\end{matrix} and similar environments.
    """

    def __init__(self):
        self.matrix_layout_engine = MatrixLayoutEngine()

    def parse_matrix_expression(self, latex: str) -> Optional[Box]:
        """
        Parse a matrix expression from LaTeX.

        Args:
            latex: LaTeX matrix expression

        Returns:
            Matrix box if parsing succeeds, None otherwise
        """
        # Match \begin{environment}...\end{environment}
        matrix_pattern = r'\\begin\{(\w+)\}(.*?)\\end\{\1\}'
        match = re.search(matrix_pattern, latex, re.DOTALL)

        if match:
            environment = match.group(1)
            content = match.group(2).strip()

            # Create matrix layout
            matrix_box = self.matrix_layout_engine.layout_matrix(content, environment)

            return matrix_box

        return None

    def extract_matrix_from_latex(self, latex: str) -> List[str]:
        """
        Extract all matrix expressions from LaTeX text.

        Args:
            latex: LaTeX text containing matrices

        Returns:
            List of matrix expressions found
        """
        matrices = []

        # Find all matrix environments
        matrix_pattern = r'\\begin\{\w+\}.*?\\end\{\w+\}'
        matches = re.findall(matrix_pattern, latex, re.DOTALL)

        matrices.extend(matches)

        return matrices


# Global instance
matrix_engine = MatrixLayoutEngine()
matrix_parser = MatrixParser()


def render_matrix_to_svg(latex: str) -> Optional[str]:
    """
    Render a matrix expression to SVG.

    Args:
        latex: Matrix LaTeX expression

    Returns:
        SVG data URL if successful, None otherwise
    """
    # Check cache first
    cached_result = math_cache.get_rendered_math(latex, False)  # Use display=False for matrices
    if cached_result:
        return cached_result

    # Parse and render matrix
    matrix_box = matrix_parser.parse_matrix_expression(latex)

    if matrix_box:
        svg_data = matrix_engine.render_matrix_svg(matrix_box)

        # Cache the result
        math_cache.set_rendered_math(latex, False, svg_data)

        return svg_data

    return None


# Test functions
def test_matrix_parsing():
    """Test matrix parsing functionality"""
    parser = MatrixParser()

    # Test simple matrix
    latex = r'\begin{matrix} a & b \\ c & d \end{matrix}'
    matrix_box = parser.parse_matrix_expression(latex)

    if matrix_box:
        print("Matrix parsed successfully")
        print(f"Matrix dimensions: {matrix_box.width}x{matrix_box.height}")

        # Render to SVG
        svg = matrix_engine.render_matrix_svg(matrix_box)
        print("SVG rendered successfully")
    else:
        print("Matrix parsing failed")


if __name__ == "__main__":
    test_matrix_parsing()
