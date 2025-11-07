# compose/math/box_model.py
"""
TeX-inspired box and glue model for mathematical typesetting.

This implements the fundamental layout primitives used by TeX:
- Boxes: Fixed-size containers for characters, symbols, or subexpressions
- Glue: Variable-width spacing that can stretch or shrink
- Layout rules: Spacing and positioning algorithms
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Union
from .universal_box import Dimensions, GlueSpace


class BoxType(Enum):
    """Types of mathematical boxes following TeX conventions."""
    ATOM = "atom"           # Single character or symbol
    OPERATOR = "operator"   # Mathematical operators (+, -, etc.)
    RELATION = "relation"   # Relations (=, <, >, etc.)
    OPENING = "opening"     # Opening delimiters (, [, {
    CLOSING = "closing"     # Closing delimiters ), ], }
    PUNCTUATION = "punct"   # Punctuation (,, ;, etc.)
    FRACTION = "fraction"   # Fraction structure
    RADICAL = "radical"     # Square root, nth root
    SCRIPT = "script"       # Superscript or subscript
    ACCENT = "accent"       # Math accents
    LARGE_OP = "large_op"   # Large operators (∫, ∑, ∏)


@dataclass
class MathBox:
    """
    A mathematical box containing content with dimensions and type.
    
    This is the fundamental unit of TeX's mathematical layout system.
    Every mathematical element is represented as a box with specific
    dimensions and spacing rules.
    """
    content: Union[str, List['MathBox']]  # Character or nested boxes
    box_type: BoxType
    dimensions: Dimensions
    
    # Font and styling information
    font_size: float = 10.0  # Points
    font_style: str = "normal"  # normal, italic, bold, etc.
    
    # Positioning adjustments
    shift_up: float = 0.0    # Vertical adjustment (positive = up)
    shift_right: float = 0.0 # Horizontal adjustment (positive = right)
    
    # Spacing information
    left_glue: Optional[GlueSpace] = None
    right_glue: Optional[GlueSpace] = None
    
    def __post_init__(self):
        """Initialize default glue based on box type."""
        if self.left_glue is None or self.right_glue is None:
            self._set_default_spacing()
    
    def _set_default_spacing(self):
        """Set default spacing based on TeX rules."""
        # These are simplified TeX spacing rules
        # Full implementation would have a complex spacing table
        
        if self.box_type == BoxType.OPERATOR:
            # Binary operators get medium space on both sides
            space = GlueSpace(natural_width=4.0, stretch=2.0, shrink=1.0)
            self.left_glue = self.left_glue or space
            self.right_glue = self.right_glue or space
            
        elif self.box_type == BoxType.RELATION:
            # Relations get thick space on both sides
            space = GlueSpace(natural_width=5.0, stretch=2.5, shrink=1.5)
            self.left_glue = self.left_glue or space
            self.right_glue = self.right_glue or space
            
        elif self.box_type == BoxType.PUNCTUATION:
            # Punctuation gets thin space after
            self.left_glue = self.left_glue or GlueSpace(0, 0, 0)
            self.right_glue = self.right_glue or GlueSpace(2.0, 1.0, 0.5)
            
        elif self.box_type in (BoxType.OPENING, BoxType.CLOSING):
            # Delimiters get no space
            no_space = GlueSpace(0, 0, 0)
            self.left_glue = self.left_glue or no_space
            self.right_glue = self.right_glue or no_space
            
        else:
            # Default: no spacing
            no_space = GlueSpace(0, 0, 0)
            self.left_glue = self.left_glue or no_space
            self.right_glue = self.right_glue or no_space
    
    def total_width(self) -> float:
        """Calculate total width including glue at natural size."""
        left_width = self.left_glue.natural_width if self.left_glue else 0
        right_width = self.right_glue.natural_width if self.right_glue else 0
        return left_width + self.dimensions.width + right_width
    
    def is_atomic(self) -> bool:
        """Check if this is an atomic box (single character/symbol)."""
        return self.box_type == BoxType.ATOM and isinstance(self.content, str)
    
    def is_composite(self) -> bool:
        """Check if this box contains nested boxes."""
        return isinstance(self.content, list)


def create_atom_box(char: str, font_size: float = 10.0) -> MathBox:
    """Create a simple atomic box for a character."""
    # Simplified dimensions - real implementation would use font metrics
    width = font_size * 0.6  # Rough character width
    height = font_size * 0.7  # Rough ascent
    depth = font_size * 0.2   # Rough descent
    
    return MathBox(
        content=char,
        box_type=BoxType.ATOM,
        dimensions=Dimensions(width, height, depth),
        font_size=font_size
    )


def create_operator_box(op: str, font_size: float = 10.0) -> MathBox:
    """Create a box for a mathematical operator."""
    # Operators are typically wider and have specific spacing
    width = font_size * 0.8
    height = font_size * 0.5
    depth = font_size * 0.1
    
    return MathBox(
        content=op,
        box_type=BoxType.OPERATOR,
        dimensions=Dimensions(width, height, depth),
        font_size=font_size
    )


def create_fraction_box(numerator: MathBox, denominator: MathBox, 
                       rule_thickness: float = 0.4) -> MathBox:
    """Create a fraction box with proper layout."""
    # Calculate dimensions for the fraction
    num_width = numerator.total_width()
    den_width = denominator.total_width()
    
    # Fraction width is the maximum of numerator and denominator
    width = max(num_width, den_width)
    
    # Height includes numerator height plus spacing and rule
    height = numerator.dimensions.total_height + rule_thickness + 2.0
    
    # Depth includes denominator depth plus spacing and rule  
    depth = denominator.dimensions.total_height + rule_thickness + 2.0
    
    return MathBox(
        content=[numerator, denominator],
        box_type=BoxType.FRACTION,
        dimensions=Dimensions(width, height, depth),
        font_size=max(numerator.font_size, denominator.font_size)
    )


# Spacing constants following TeX conventions (in scaled points)
class MathSpacing:
    """Standard mathematical spacing amounts."""
    THIN_SPACE = 3.0      # \,
    MEDIUM_SPACE = 4.0    # \:  
    THICK_SPACE = 5.0     # \;
    NEGATIVE_THIN = -3.0  # \!
    QUAD_SPACE = 18.0     # \quad
    QQUAD_SPACE = 36.0    # \qquad
