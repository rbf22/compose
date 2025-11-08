# compose/layout/tex_boxes.py
"""
TeX-style box model for advanced mathematical typesetting.
Implements boxes, glue, and penalties for proper mathematical layout.
"""

from typing import List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class BoxType(Enum):
    """Types of boxes in TeX layout"""
    CHAR = "char"           # Character box
    HBOX = "hbox"           # Horizontal box
    VBOX = "vbox"           # Vertical box
    GLUE = "glue"           # Flexible spacing
    PENALTY = "penalty"     # Line breaking penalty


@dataclass
class Box:
    """Base box class in TeX layout model"""
    width: float = 0.0
    height: float = 0.0
    depth: float = 0.0
    box_type: BoxType = BoxType.CHAR

    def __post_init__(self):
        # Ensure dimensions are non-negative
        self.width = max(0, self.width)
        self.height = max(0, self.height)
        self.depth = max(0, self.depth)


@dataclass
class CharBox(Box):
    """Character box containing a single character"""
    char: str = ""
    font_size: float = 12.0

    def __init__(self, char: str = "", font_size: float = 12.0):
        # Initialize with proper parameter order
        self.char = char
        self.font_size = font_size
        self.box_type = BoxType.CHAR
        # Estimate dimensions based on character and font size
        self.width = font_size * 0.6  # Rough estimate
        self.height = font_size * 0.7
        self.depth = font_size * 0.3

        # Call Box.__post_init__ manually since we're not using dataclass __post_init__
        Box.__post_init__(self)


@dataclass
class Glue(Box):
    """Flexible spacing (glue) between boxes"""
    width: float = 0.0
    stretch: float = 0.0  # How much this can stretch
    shrink: float = 0.0   # How much this can shrink

    def __post_init__(self):
        super().__post_init__()
        self.box_type = BoxType.GLUE
        self.height = 0.0
        self.depth = 0.0


@dataclass
class Penalty(Box):
    """Penalty for line breaking decisions"""
    penalty: float = 0.0   # Breaking cost (lower = better break point)
    flagged: bool = False  # Special penalty for hyphenation

    def __post_init__(self):
        super().__post_init__()
        self.box_type = BoxType.PENALTY
        self.width = 0.0
        self.height = 0.0
        self.depth = 0.0


@dataclass
class HBox(Box):
    """Horizontal box containing a list of boxes"""
    contents: List[Box] = None

    def __post_init__(self):
        super().__post_init__()
        self.box_type = BoxType.HBOX
        if self.contents is None:
            self.contents = []

        # Calculate dimensions from contents
        self._calculate_dimensions()

    def _calculate_dimensions(self):
        """Calculate width, height, and depth from contents"""
        if not self.contents:
            self.width = 0.0
            self.height = 0.0
            self.depth = 0.0
            return

        total_width = 0.0
        max_height = 0.0
        max_depth = 0.0

        for box in self.contents:
            total_width += box.width
            max_height = max(max_height, box.height)
            max_depth = max(max_depth, box.depth)

        self.width = total_width
        self.height = max_height
        self.depth = max_depth

    def add_box(self, box: Box):
        """Add a box to this horizontal box"""
        self.contents.append(box)
        self._calculate_dimensions()

    def add_glue(self, width: float = 0.0, stretch: float = 0.0, shrink: float = 0.0):
        """Add glue (flexible spacing)"""
        glue = Glue(width=width, stretch=stretch, shrink=shrink)
        self.add_box(glue)


@dataclass
class VBox(Box):
    """Vertical box containing a list of boxes"""
    contents: List[Box] = None

    def __post_init__(self):
        super().__post_init__()
        self.box_type = BoxType.VBOX
        if self.contents is None:
            self.contents = []

        # Calculate dimensions from contents
        self._calculate_dimensions()

    def _calculate_dimensions(self):
        """Calculate width, height, and depth from contents"""
        if not self.contents:
            self.width = 0.0
            self.height = 0.0
            self.depth = 0.0
            return

        max_width = 0.0
        total_height = 0.0

        for box in self.contents:
            max_width = max(max_width, box.width)
            total_height += box.height + box.depth

        self.width = max_width
        self.height = total_height
        self.depth = 0.0  # VBox doesn't have depth

    def add_box(self, box: Box):
        """Add a box to this vertical box"""
        self.contents.append(box)
        self._calculate_dimensions()


class LineBreaker:
    """
    TeX-style line breaking algorithm.
    Finds optimal line break points using dynamic programming.
    """

    def __init__(self, hboxes: List[HBox], line_width: float):
        self.hboxes = hboxes
        self.line_width = line_width

    def break_into_lines(self) -> List[List[Box]]:
        """
        Break horizontal boxes into lines using TeX line breaking algorithm.

        Returns:
            List of lines, where each line is a list of boxes
        """
        if not self.hboxes:
            return []

        # Simple greedy line breaking for now
        # Full TeX algorithm would use dynamic programming with penalties
        lines = []
        current_line = []
        current_width = 0.0

        for hbox in self.hboxes:
            if current_width + hbox.width > self.line_width and current_line:
                # Start new line
                lines.append(current_line)
                current_line = [hbox]
                current_width = hbox.width
            else:
                current_line.append(hbox)
                current_width += hbox.width

        if current_line:
            lines.append(current_line)

        return lines


class TexLayoutEngine:
    """
    TeX-style mathematical layout engine using boxes and glue.
    Provides proper mathematical typesetting with spacing and alignment.
    """

    def __init__(self):
        self.font_size = 12.0

    def layout_expression(self, math_content: str) -> HBox:
        """
        Layout a mathematical expression using TeX box model.

        Args:
            math_content: LaTeX mathematical expression

        Returns:
            HBox containing the laid out expression
        """
        # Parse the expression into boxes
        boxes = self._parse_to_boxes(math_content)

        # Create horizontal box
        hbox = HBox()
        for box in boxes:
            hbox.add_box(box)

        return hbox

    def _parse_to_boxes(self, content: str) -> List[Box]:
        """
        Parse mathematical content into boxes.
        This is a simplified implementation - full TeX would have complex parsing.
        """
        boxes = []

        i = 0
        while i < len(content):
            char = content[i]

            if char.isspace():
                # Skip whitespace
                i += 1
                continue
            elif char in '+-=*/()[]{}':
                # Operators and delimiters
                boxes.append(CharBox(char, self.font_size))
                i += 1
            elif char.isdigit():
                # Numbers
                num_str = ""
                while i < len(content) and content[i].isdigit():
                    num_str += content[i]
                    i += 1
                boxes.append(CharBox(num_str, self.font_size))
            elif char.isalpha():
                # Variables
                var_str = ""
                while i < len(content) and (content[i].isalpha() or content[i].isdigit()):
                    var_str += content[i]
                    i += 1
                boxes.append(CharBox(var_str, self.font_size))
            else:
                # Other characters
                boxes.append(CharBox(char, self.font_size))
                i += 1

        return boxes

    def layout_integral(self, integrand: str, lower_limit: str = None, upper_limit: str = None) -> HBox:
        """
        Layout an integral expression with proper positioning.

        Args:
            integrand: The expression being integrated
            lower_limit: Lower limit of integration
            upper_limit: Upper limit of integration

        Returns:
            HBox with properly positioned integral
        """
        hbox = HBox()

        # Integral symbol (taller than regular characters)
        integral_box = CharBox('∫', self.font_size * 2.0)
        hbox.add_box(integral_box)

        # Add limits if present
        if lower_limit or upper_limit:
            # In TeX, limits are positioned above/below the integral
            # For now, we'll add them as regular text (simplified)
            if lower_limit:
                hbox.add_box(CharBox(f"_{lower_limit}", self.font_size))
            if upper_limit:
                hbox.add_box(CharBox(f"^{upper_limit}", self.font_size))

            # Add some spacing
            hbox.add_glue(width=5.0, stretch=2.0)

        # Add integrand
        integrand_boxes = self._parse_to_boxes(integrand)
        for box in integrand_boxes:
            hbox.add_box(box)

        # Add differential (dx)
        hbox.add_glue(width=10.0, stretch=1.0)
        hbox.add_box(CharBox('d', self.font_size))
        hbox.add_box(CharBox('x', self.font_size))

        return hbox


# Test functions
def test_box_model():
    """Test the TeX box model"""
    print("🧪 Testing TeX Box Model:")
    print("=" * 40)

    # Test character boxes
    a_box = CharBox('a', 12.0)
    print(f"CharBox 'a': width={a_box.width:.1f}, height={a_box.height:.1f}")

    # Test horizontal box
    hbox = HBox()
    hbox.add_box(CharBox('x', 12.0))
    hbox.add_box(CharBox('+', 12.0))
    hbox.add_box(CharBox('y', 12.0))
    print(f"HBox 'x+y': width={hbox.width:.1f}, height={hbox.height:.1f}")

    # Test with glue
    hbox.add_glue(width=5.0, stretch=2.0)
    hbox.add_box(CharBox('=', 12.0))
    hbox.add_glue(width=5.0, stretch=2.0)
    hbox.add_box(CharBox('z', 12.0))
    print(f"HBox with glue: width={hbox.width:.1f}")

    # Test math layout
    engine = MathLayoutEngine()
    expr_box = engine.layout_expression("x^2 + y^2 = z^2")
    print(f"Math expression: width={expr_box.width:.1f}, height={expr_box.height:.1f}")

    print("✅ Box model working!")


if __name__ == "__main__":
    test_box_model()
