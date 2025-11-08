# compose/layout/math_layout.py
"""
Advanced mathematical layout system for Compose.

Implements professional math typesetting including:
- Matrix layout with alignment
- Large operators (integrals, sums) with limits
- Radical layout (square roots, nth roots)
- Automatic delimiter sizing
- Math style contexts (display, inline, script)
"""

from typing import List, Dict, Any, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass
from .universal_box import UniversalBox, ContentType, BoxType, Dimensions


class MathStyle(Enum):
    """Mathematical style contexts"""
    DISPLAY = "display"           # Display math ($$...$$)
    INLINE = "inline"            # Inline math ($...$)
    SCRIPT = "script"            # Superscript/subscript
    SCRIPT_SCRIPT = "scriptscript"  # Nested scripts


class MathAtomType(Enum):
    """Types of mathematical atoms"""
    ORDINARY = "ordinary"        # Regular symbols
    OPERATOR = "operator"        # Binary operators
    RELATION = "relation"        # Relations (=, <, >, etc.)
    OPENING = "opening"          # Opening delimiters
    CLOSING = "closing"         # Closing delimiters
    PUNCTUATION = "punctuation"  # Punctuation
    VARIABLE = "variable"        # Variables
    NUMBER = "number"           # Numbers
    LARGE_OP = "large_op"       # Large operators (sum, integral)


@dataclass
class MathAtom:
    """A mathematical atom with type and content"""
    content: str
    atom_type: MathAtomType
    style: MathStyle = MathStyle.INLINE
    nucleus: Optional['UniversalBox'] = None
    superscript: Optional['UniversalBox'] = None
    subscript: Optional['UniversalBox'] = None


class MathLayoutEngine:
    """
    Advanced mathematical layout engine.

    Handles complex mathematical expressions with proper spacing,
    alignment, and professional typesetting.
    """

    def __init__(self):
        # Math spacing rules (in em units, TeX style)
        self.spacing_rules = {
            (MathAtomType.ORDINARY, MathAtomType.OPERATOR): 0.25,
            (MathAtomType.OPERATOR, MathAtomType.ORDINARY): 0.25,
            (MathAtomType.ORDINARY, MathAtomType.RELATION): 0.5,
            (MathAtomType.RELATION, MathAtomType.ORDINARY): 0.5,
            (MathAtomType.OPERATOR, MathAtomType.RELATION): 0.25,
            (MathAtomType.RELATION, MathAtomType.OPERATOR): 0.25,
        }

        # Delimiter sizing rules
        self.delimiter_sizes = {
            '(': ['(', '\\left(', '\\big(', '\\Big(', '\\bigg(', '\\Bigg('],
            ')': [')', '\\right)', '\\big)', '\\Big)', '\\bigg)', '\\Bigg)'],
            '[': ['[', '\\left[', '\\big[', '\\Big[', '\\bigg[', '\\Bigg['],
            ']': [']', '\\right]', '\\big]', '\\Big]', '\\bigg]', '\\Bigg]'],
            '{': ['\\{', '\\left\\{', '\\big\\{', '\\Big\\{', '\\bigg\\{', '\\Bigg\\{'],
            '}': ['\\}', '\\right\\}', '\\big\\}', '\\Big\\}', '\\bigg\\}', '\\Bigg\\}'],
        }

        # Large operator limits positioning
        self.large_ops = {
            '\\sum': {'height': 2.0, 'depth': 0.5},
            '\\prod': {'height': 2.0, 'depth': 0.5},
            '\\int': {'height': 2.5, 'depth': 1.0},
            '\\oint': {'height': 2.5, 'depth': 1.0},
            '\\bigcup': {'height': 1.8, 'depth': 0.3},
            '\\bigcap': {'height': 1.8, 'depth': 0.3},
        }

    def layout_matrix(self, rows: List[List[str]], style: MathStyle = MathStyle.DISPLAY) -> UniversalBox:
        """
        Layout a matrix with proper alignment.

        Args:
            rows: List of rows, each containing column elements
            style: Math style context

        Returns:
            UniversalBox containing the laid out matrix
        """
        if not rows:
            return UniversalBox(content="", content_type=ContentType.MATH)

        matrix_box = UniversalBox(
            content=[],
            content_type=ContentType.MATH,
            box_type=BoxType.BLOCK,
            attributes={"math_type": "matrix"}
        )

        # Calculate column widths
        num_cols = max(len(row) for row in rows) if rows else 0
        col_widths = [0] * num_cols

        # First pass: determine column widths
        for row in rows:
            for col_idx, cell_content in enumerate(row):
                if col_idx < num_cols:
                    # Estimate cell width (simplified)
                    cell_width = len(cell_content) * 0.6
                    col_widths[col_idx] = max(col_widths[col_idx], cell_width)

        # Second pass: create cell boxes with consistent widths
        row_boxes = []
        for row in rows:
            row_box = UniversalBox(
                content=[],
                content_type=ContentType.MATH,
                box_type=BoxType.BLOCK,
                attributes={"math_type": "matrix_row"}
            )

            for col_idx, cell_content in enumerate(row):
                cell_box = UniversalBox(
                    content=cell_content,
                    content_type=ContentType.MATH,
                    box_type=BoxType.INLINE,
                    dimensions=Dimensions(width=col_widths[col_idx], height=1.0, depth=0.0),
                    attributes={"math_type": "matrix_cell"}
                )
                row_box.add_child(cell_box)

            # Add padding cells for missing columns
            while len(row_box.children) < num_cols:
                padding_box = UniversalBox(
                    content="",
                    content_type=ContentType.MATH,
                    box_type=BoxType.INLINE,
                    dimensions=Dimensions(width=col_widths[len(row_box.children)], height=1.0, depth=0.0),
                    attributes={"math_type": "matrix_cell"}
                )
                row_box.add_child(padding_box)

            row_boxes.append(row_box)

        # Combine rows
        total_height = 0
        for row_box in row_boxes:
            matrix_box.add_child(row_box)
            total_height += 1.2  # Row spacing

        # Set matrix dimensions
        matrix_box.dimensions.width = sum(col_widths) + (num_cols - 1) * 0.5  # Column spacing
        matrix_box.dimensions.height = total_height

        return matrix_box

    def layout_large_operator(self, operator: str, lower_limit: Optional[str] = None,
                            upper_limit: Optional[str] = None, style: MathStyle = MathStyle.DISPLAY) -> UniversalBox:
        """
        Layout a large operator with limits.

        Args:
            operator: The operator symbol (e.g., '\\sum', '\\int')
            lower_limit: Lower limit expression
            upper_limit: Upper limit expression
            style: Math style context

        Returns:
            UniversalBox containing the operator with limits
        """
        if operator not in self.large_ops:
            # Fallback for unknown operators
            return UniversalBox(content=operator, content_type=ContentType.MATH)

        op_metrics = self.large_ops[operator]

        # Create operator box
        op_box = UniversalBox(
            content=operator,
            content_type=ContentType.MATH,
            box_type=BoxType.INLINE,
            dimensions=Dimensions(width=1.5, height=op_metrics['height'], depth=op_metrics['depth']),
            attributes={"math_type": "large_operator"}
        )

        # Create limit boxes if provided
        limit_boxes = []

        if lower_limit:
            lower_box = UniversalBox(
                content=lower_limit,
                content_type=ContentType.MATH,
                box_type=BoxType.INLINE,
                attributes={"math_type": "operator_limit", "position": "lower"}
            )
            limit_boxes.append(("lower", lower_box))

        if upper_limit:
            upper_box = UniversalBox(
                content=upper_limit,
                content_type=ContentType.MATH,
                box_type=BoxType.INLINE,
                attributes={"math_type": "operator_limit", "position": "upper"}
            )
            limit_boxes.append(("upper", upper_box))

        # Position limits based on style
        if style == MathStyle.DISPLAY and limit_boxes:
            # Display style: limits above/below
            total_width = op_box.dimensions.width
            total_height = op_box.dimensions.height + op_box.dimensions.depth

            for position, limit_box in limit_boxes:
                if position == "upper":
                    # Upper limit goes above
                    limit_box.dimensions.y_offset = -op_box.dimensions.height - 0.3
                elif position == "lower":
                    # Lower limit goes below
                    limit_box.dimensions.y_offset = op_box.dimensions.depth + 0.3

                total_width = max(total_width, limit_box.dimensions.width)
                op_box.add_child(limit_box)

            op_box.dimensions.width = total_width
            op_box.dimensions.height = total_height + 0.6  # Extra space for limits

        elif limit_boxes:
            # Inline style: limits as sub/super scripts
            for position, limit_box in limit_boxes:
                if position == "upper":
                    op_box.superscript = limit_box
                elif position == "lower":
                    op_box.subscript = limit_box

        return op_box

    def layout_radical(self, radicand: str, index: Optional[str] = None,
                      style: MathStyle = MathStyle.INLINE) -> UniversalBox:
        """
        Layout a radical (square root, nth root).

        Args:
            radicand: Expression under the radical
            index: Root index (for nth roots)
            style: Math style context

        Returns:
            UniversalBox containing the radical expression
        """
        # Create radicand box
        radicand_box = UniversalBox(
            content=radicand,
            content_type=ContentType.MATH,
            box_type=BoxType.INLINE,
            attributes={"math_type": "radicand"}
        )

        # Create index box if provided
        index_box = None
        if index:
            index_box = UniversalBox(
                content=index,
                content_type=ContentType.MATH,
                box_type=BoxType.INLINE,
                attributes={"math_type": "radical_index"}
            )

        # Create radical symbol box
        radical_symbol = "√"
        radical_width = 0.8
        radical_height = radicand_box.dimensions.height + 0.3

        radical_box = UniversalBox(
            content=radical_symbol,
            content_type=ContentType.MATH,
            box_type=BoxType.INLINE,
            dimensions=Dimensions(width=radical_width, height=radical_height, depth=0.0),
            attributes={"math_type": "radical_symbol"}
        )

        # Position radicand next to radical symbol
        radicand_box.dimensions.x_offset = radical_width + 0.1

        # If there is an index, return a container that includes all three parts
        if index_box:
            # Position elements relative to container
            radical_symbol_box = radical_box
            radicand_box.dimensions.x_offset = radical_width + 0.1
            index_box.dimensions.x_offset = 0.1
            index_box.dimensions.y_offset = -radical_height + 0.2

            container = UniversalBox(
                content=[],
                content_type=ContentType.MATH,
                box_type=BoxType.INLINE,
                dimensions=Dimensions(width=radical_width + radicand_box.dimensions.width + 0.2,
                                      height=radical_height, depth=0.0),
                attributes={"math_type": "radical"}
            )
            container.add_child(radical_symbol_box)
            container.add_child(radicand_box)
            container.add_child(index_box)
            return container

        # No index: combine radical symbol and radicand within the symbol box
        radical_box.add_child(radicand_box)
        total_width = radical_width + radicand_box.dimensions.width + 0.2
        radical_box.dimensions.width = total_width
        return radical_box

    def layout_fraction(self, numerator: str, denominator: str,
                       style: MathStyle = MathStyle.INLINE) -> UniversalBox:
        """
        Layout a fraction with proper alignment.

        Args:
            numerator: Numerator expression
            denominator: Denominator expression
            style: Math style context

        Returns:
            UniversalBox containing the fraction
        """
        # Create numerator and denominator boxes
        num_box = UniversalBox(
            content=numerator,
            content_type=ContentType.MATH,
            box_type=BoxType.INLINE,
            attributes={"math_type": "numerator"}
        )

        den_box = UniversalBox(
            content=denominator,
            content_type=ContentType.MATH,
            box_type=BoxType.INLINE,
            attributes={"math_type": "denominator"}
        )

        # Determine fraction rule thickness and positioning
        if style == MathStyle.DISPLAY:
            rule_thickness = 0.05
            num_offset = -0.8
            den_offset = 0.8
        else:
            rule_thickness = 0.03
            num_offset = -0.5
            den_offset = 0.5

        # Create fraction rule
        fraction_width = max(num_box.dimensions.width, den_box.dimensions.width) + 0.4
        rule_box = UniversalBox(
            content="",  # Rule is visual, no content
            content_type=ContentType.MATH,
            box_type=BoxType.INLINE,
            dimensions=Dimensions(width=fraction_width, height=rule_thickness, depth=0.0),
            attributes={"math_type": "fraction_rule"}
        )

        # Position numerator above rule
        num_box.dimensions.y_offset = num_offset

        # Position denominator below rule
        den_box.dimensions.y_offset = den_offset

        # Combine elements
        fraction_box = UniversalBox(
            content=[],
            content_type=ContentType.MATH,
            box_type=BoxType.INLINE,
            dimensions=Dimensions(width=fraction_width, height=2.0, depth=0.0),
            attributes={"math_type": "fraction", "style": ("display" if style == MathStyle.DISPLAY else "inline")}
        )

        fraction_box.add_child(num_box)
        fraction_box.add_child(rule_box)
        fraction_box.add_child(den_box)

        return fraction_box

    def auto_size_delimiters(self, left_delim: str, right_delim: str,
                           content: UniversalBox, style: MathStyle = MathStyle.INLINE) -> Tuple[UniversalBox, UniversalBox]:
        """
        Auto-size delimiters based on content height.

        Args:
            left_delim: Left delimiter character
            right_delim: Right delimiter character
            content: Content box between delimiters
            style: Math style context

        Returns:
            Tuple of (left_delimiter_box, right_delimiter_box)
        """
        content_height = content.dimensions.height + content.dimensions.depth

        # Determine delimiter size based on content height
        if content_height < 1.2:
            size_index = 0  # Normal size
        elif content_height < 2.0:
            size_index = 1  # Big size
        elif content_height < 3.0:
            size_index = 2  # Bigg size
        else:
            size_index = 3  # Biggg size

        # Get sized delimiters
        left_sized = self.delimiter_sizes.get(left_delim, [left_delim] * 4)[size_index]
        right_sized = self.delimiter_sizes.get(right_delim, [right_delim] * 4)[size_index]

        # Create delimiter boxes
        left_box = UniversalBox(
            content=left_sized,
            content_type=ContentType.MATH,
            box_type=BoxType.INLINE,
            dimensions=Dimensions(width=0.5, height=content_height, depth=0.0),
            attributes={"math_type": "delimiter", "position": "left"}
        )

        right_box = UniversalBox(
            content=right_sized,
            content_type=ContentType.MATH,
            box_type=BoxType.INLINE,
            dimensions=Dimensions(width=0.5, height=content_height, depth=0.0),
            attributes={"math_type": "delimiter", "position": "right"}
        )

        return left_box, right_box

    def apply_math_spacing(self, atoms: List[MathAtom]) -> List[MathAtom]:
        """
        Apply proper mathematical spacing between atoms.

        Args:
            atoms: List of math atoms

        Returns:
            Atoms with spacing applied
        """
        if len(atoms) < 2:
            return atoms

        spaced_atoms = [atoms[0]]  # First atom unchanged

        for i in range(1, len(atoms)):
            prev_atom = atoms[i-1]
            current_atom = atoms[i]

            # Determine spacing
            spacing_key = (prev_atom.atom_type, current_atom.atom_type)
            spacing = self.spacing_rules.get(spacing_key, 0.1)  # Default spacing

            # Create spacing atom if needed
            if spacing > 0:
                spacing_atom = MathAtom(
                    content="",  # Invisible spacing
                    atom_type=MathAtomType.ORDINARY,
                    style=current_atom.style
                )
                spacing_atom.nucleus = UniversalBox(
                    content="",
                    content_type=ContentType.MATH,
                    box_type=BoxType.INLINE,
                    dimensions=Dimensions(width=spacing, height=0.1, depth=0.0),
                    attributes={"math_type": "spacing"}
                )
                spaced_atoms.append(spacing_atom)

            spaced_atoms.append(current_atom)

        return spaced_atoms


# Global math layout engine instance
math_layout_engine = MathLayoutEngine()


# Convenience functions
def layout_matrix(rows: List[List[str]], style: MathStyle = MathStyle.DISPLAY) -> UniversalBox:
    """Convenience function for matrix layout"""
    return math_layout_engine.layout_matrix(rows, style)


def layout_fraction(numerator: str, denominator: str, style: MathStyle = MathStyle.INLINE) -> UniversalBox:
    """Convenience function for fraction layout"""
    return math_layout_engine.layout_fraction(numerator, denominator, style)


def layout_large_operator(operator: str, lower_limit: Optional[str] = None,
                         upper_limit: Optional[str] = None, style: MathStyle = MathStyle.DISPLAY) -> UniversalBox:
    """Convenience function for large operator layout"""
    return math_layout_engine.layout_large_operator(operator, lower_limit, upper_limit, style)


def layout_radical(radicand: str, index: Optional[str] = None, style: MathStyle = MathStyle.INLINE) -> UniversalBox:
    """Convenience function for radical layout"""
    return math_layout_engine.layout_radical(radicand, index, style)
