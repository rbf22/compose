# compose/layout/universal_box.py
"""
Universal box model for all content types in Compose.

This extends the mathematical box model to handle text, diagrams,
slides, media, and any other content requiring precise layout.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Union, Any, Dict


@dataclass
class Dimensions:
    """Box dimensions in TeX units (scaled points)."""
    width: float
    height: float  # Above baseline
    depth: float   # Below baseline
    right: float = 0  # For CSS-style margins/padding
    
    @property
    def total_height(self) -> float:
        """Total vertical extent."""
        return self.height + self.depth


@dataclass
class GlueSpace:
    """Variable-width spacing following TeX's glue model."""
    natural_width: float    # Preferred width
    stretch: float         # How much it can grow
    shrink: float          # How much it can contract
    stretch_order: int = 0 # Stretch priority (0=normal, 1=fil, 2=fill, 3=filll)
    shrink_order: int = 0  # Shrink priority
    
    def compute_width(self, adjustment_ratio: float) -> float:
        """Compute actual width given adjustment ratio."""
        if adjustment_ratio >= 0:
            # Stretching
            return self.natural_width + adjustment_ratio * self.stretch
        else:
            # Shrinking  
            return self.natural_width + adjustment_ratio * self.shrink


class ContentType(Enum):
    """Types of content that can be contained in boxes."""
    TEXT = "text"               # Plain text, formatted text
    MATH = "math"               # Mathematical expressions
    DIAGRAM = "diagram"         # Mermaid, flowcharts, etc.
    IMAGE = "image"             # Raster images, photos
    VECTOR = "vector"           # SVG, illustrations
    TABLE = "table"             # Structured tabular data
    CODE = "code"               # Source code blocks
    SLIDE = "slide"             # Presentation slides
    LAYOUT = "layout"           # Grid, column, container
    INTERACTIVE = "interactive" # Forms, buttons, links
    MEDIA = "media"             # Video, audio, animations


class BoxType(Enum):
    """Layout behavior types for boxes."""
    INLINE = "inline"           # Flows with text
    BLOCK = "block"             # Takes full width, stacks vertically
    FLOAT = "float"             # Floats left/right with text wrap
    ABSOLUTE = "absolute"       # Positioned absolutely
    FIXED = "fixed"             # Fixed position (slides, overlays)
    FLEX = "flex"               # Flexible layout container
    GRID = "grid"               # Grid layout container


class FloatPlacement(Enum):
    """Float placement options following LaTeX conventions."""
    HERE = "here"               # Place at current position
    TOP = "top"                 # Place at top of page/column
    BOTTOM = "bottom"           # Place at bottom of page/column
    PAGE = "page"               # Place on separate page


@dataclass
class RenderingStyle:
    """Styling information for content rendering."""
    # Typography
    font_family: str = "default"
    font_size: float = 10.0
    font_weight: str = "normal"  # normal, bold, etc.
    font_style: str = "normal"   # normal, italic, etc.
    line_height: float = 1.2
    
    # Colors
    color: str = "#000000"
    background_color: Optional[str] = None
    border_color: Optional[str] = None
    
    # Spacing
    margin: Dimensions = None
    padding: Dimensions = None
    border_width: float = 0.0
    
    # Layout
    text_align: str = "left"     # left, center, right, justify
    vertical_align: str = "baseline"  # top, middle, bottom, baseline
    
    # Effects
    opacity: float = 1.0
    shadow: Optional[str] = None
    
    def __post_init__(self):
        if self.margin is None:
            self.margin = Dimensions(0, 0, 0, 0)
        if self.padding is None:
            self.padding = Dimensions(0, 0, 0, 0)


@dataclass
class AnimationTiming:
    """Animation and transition timing for dynamic content."""
    delay: float = 0.0           # Seconds before animation starts
    duration: float = 0.5        # Animation duration in seconds
    easing: str = "ease"         # CSS easing function
    repeat: int = 1              # Number of repetitions
    direction: str = "normal"    # normal, reverse, alternate


@dataclass
class InteractionData:
    """Data for interactive elements."""
    clickable: bool = False
    hover_style: Optional[RenderingStyle] = None
    click_action: Optional[str] = None  # URL, JavaScript, etc.
    tooltip: Optional[str] = None


@dataclass
class UniversalBox:
    """
    Universal box that can contain any type of content.
    
    This is the fundamental unit of Compose's layout system,
    extending TeX's box model to handle modern content types.
    """
    # Core content
    content: Union[str, List['UniversalBox'], Any]
    content_type: ContentType
    box_type: BoxType = BoxType.INLINE
    
    # Dimensions and positioning
    dimensions: Dimensions = None
    position: Dimensions = None  # x, y offset from container
    
    # Spacing (TeX-style glue)
    left_glue: Optional[GlueSpace] = None
    right_glue: Optional[GlueSpace] = None
    top_glue: Optional[GlueSpace] = None
    bottom_glue: Optional[GlueSpace] = None
    
    # Styling and appearance
    style: RenderingStyle = None
    
    # Dynamic behavior
    animation: Optional[AnimationTiming] = None
    interaction: Optional[InteractionData] = None
    
    # Float and caption support
    float_placement: Optional[FloatPlacement] = None
    caption: Optional[str] = None
    label: Optional[str] = None  # For cross-references
    
    # Metadata
    id: Optional[str] = None
    classes: List[str] = None
    attributes: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.dimensions is None:
            self.dimensions = Dimensions(0, 0, 0)
        if self.position is None:
            self.position = Dimensions(0, 0, 0)
        if self.style is None:
            self.style = RenderingStyle()
        if self.classes is None:
            self.classes = []
        if self.attributes is None:
            self.attributes = {}
        
        # Set default glue based on box type
        self._set_default_spacing()
    
    def _set_default_spacing(self):
        """Set default spacing based on content and box types."""
        no_space = GlueSpace(0, 0, 0)
        
        if self.box_type == BoxType.BLOCK:
            # Block elements get vertical spacing
            self.top_glue = self.top_glue or GlueSpace(12.0, 6.0, 3.0)
            self.bottom_glue = self.bottom_glue or GlueSpace(12.0, 6.0, 3.0)
            self.left_glue = self.left_glue or no_space
            self.right_glue = self.right_glue or no_space
            
        elif self.box_type == BoxType.INLINE:
            # Inline elements get minimal spacing
            self.left_glue = self.left_glue or no_space
            self.right_glue = self.right_glue or no_space
            self.top_glue = self.top_glue or no_space
            self.bottom_glue = self.bottom_glue or no_space
            
        elif self.content_type == ContentType.DIAGRAM:
            # Diagrams get generous spacing
            space = GlueSpace(18.0, 9.0, 6.0)
            self.top_glue = self.top_glue or space
            self.bottom_glue = self.bottom_glue or space
            self.left_glue = self.left_glue or no_space
            self.right_glue = self.right_glue or no_space
    
    def is_container(self) -> bool:
        """Check if this box contains other boxes."""
        return isinstance(self.content, list)
    
    def is_atomic(self) -> bool:
        """Check if this is an atomic content box."""
        return isinstance(self.content, str)
    
    def total_width(self) -> float:
        """Calculate total width including spacing."""
        left = self.left_glue.natural_width if self.left_glue else 0
        right = self.right_glue.natural_width if self.right_glue else 0
        return left + self.dimensions.width + right
    
    def total_height(self) -> float:
        """Calculate total height including spacing."""
        top = self.top_glue.natural_width if self.top_glue else 0
        bottom = self.bottom_glue.natural_width if self.bottom_glue else 0
        return top + self.dimensions.total_height + bottom
    
    def add_child(self, child: 'UniversalBox'):
        """Add a child box to this container."""
        if not self.is_container():
            self.content = []
        self.content.append(child)
    
    def get_children(self) -> List['UniversalBox']:
        """Get child boxes if this is a container."""
        if self.is_container():
            return self.content
        return []

    @property
    def children(self) -> List['UniversalBox']:
        """Get child boxes (alias for get_children for compatibility)."""
        return self.get_children()
    
    def apply_style(self, style: RenderingStyle):
        """Apply styling to this box."""
        # Merge styles (new style takes precedence)
        if style.font_family != "default":
            self.style.font_family = style.font_family
        if style.font_size != 10.0:
            self.style.font_size = style.font_size
        if style.color != "#000000":
            self.style.color = style.color
        # ... merge other style properties
    
    def set_animation(self, animation: AnimationTiming):
        """Set animation timing for this box."""
        self.animation = animation
    
    def make_interactive(self, interaction: InteractionData):
        """Make this box interactive."""
        self.interaction = interaction


# Factory functions for common box types

def create_text_box(text: str, style: Optional[RenderingStyle] = None) -> UniversalBox:
    """Create a text box."""
    return UniversalBox(
        content=text,
        content_type=ContentType.TEXT,
        box_type=BoxType.INLINE,
        style=style or RenderingStyle()
    )

def create_paragraph_box(content: List[UniversalBox]) -> UniversalBox:
    """Create a paragraph container."""
    return UniversalBox(
        content=content,
        content_type=ContentType.TEXT,
        box_type=BoxType.BLOCK
    )

def create_diagram_box(diagram_code: str, diagram_type: str = "mermaid") -> UniversalBox:
    """Create a diagram box."""
    return UniversalBox(
        content=diagram_code,
        content_type=ContentType.DIAGRAM,
        box_type=BoxType.BLOCK,
        attributes={"diagram_type": diagram_type}
    )

def create_slide_box(title: str, content: List[UniversalBox]) -> UniversalBox:
    """Create a slide container."""
    return UniversalBox(
        content=content,
        content_type=ContentType.SLIDE,
        box_type=BoxType.FIXED,
        attributes={"title": title}
    )

def create_image_box(src: str, alt: str = "", caption: str = "") -> UniversalBox:
    """Create an image box."""
    return UniversalBox(
        content=src,
        content_type=ContentType.IMAGE,
        box_type=BoxType.BLOCK,
        attributes={"alt": alt, "caption": caption}
    )

def create_code_box(code: str, language: str = "") -> UniversalBox:
    """Create a code block box."""
    return UniversalBox(
        content=code,
        content_type=ContentType.CODE,
        box_type=BoxType.BLOCK,
        attributes={"language": language},
        style=RenderingStyle(font_family="monospace")
    )


def create_figure_box(content: Union[str, UniversalBox], caption: str = "", 
                      label: str = "", float_placement: FloatPlacement = FloatPlacement.HERE) -> UniversalBox:
    """Create a figure box with caption and float placement."""
    # If content is a string, wrap it in an appropriate box
    if isinstance(content, str):
        # Assume it's an image path
        content_box = UniversalBox(
            content=content,
            content_type=ContentType.IMAGE,
            box_type=BoxType.BLOCK
        )
    else:
        content_box = content
    
    # Create figure container
    figure_box = UniversalBox(
        content=[content_box],
        content_type=ContentType.IMAGE,  # Could be ContentType.FIGURE if we add it
        box_type=BoxType.FLOAT,
        float_placement=float_placement,
        caption=caption,
        label=label
    )
    
    # Add caption if provided
    if caption:
        caption_box = create_text_box(f"Figure: {caption}", 
                                    RenderingStyle(font_size=10.0, font_style="italic"))
        figure_box.add_child(caption_box)
    
    return figure_box


def create_table_box(table_data: List[List[str]], headers: Optional[List[str]] = None,
                    caption: str = "", label: str = "", 
                    float_placement: FloatPlacement = FloatPlacement.HERE) -> UniversalBox:
    """Create a table box with caption and float placement."""
    # Create table content structure
    table_content = {
        'headers': headers or [],
        'rows': table_data
    }
    
    table_box = UniversalBox(
        content=table_content,
        content_type=ContentType.TABLE,
        box_type=BoxType.FLOAT,
        float_placement=float_placement,
        caption=caption,
        label=label
    )
    
    # Add caption if provided
    if caption:
        caption_box = create_text_box(f"Table: {caption}", 
                                    RenderingStyle(font_size=10.0, font_style="italic"))
        table_box.add_child(caption_box)
    
    return table_box


def create_float_box(content: Union[str, UniversalBox], float_placement: FloatPlacement,
                    caption: Optional[str] = None, label: Optional[str] = None) -> UniversalBox:
    """Create a floating box with specified placement."""
    if isinstance(content, str):
        content_box = create_text_box(content)
    else:
        content_box = content
    
    float_box = UniversalBox(
        content=[content_box],
        content_type=content_box.content_type,
        box_type=BoxType.FLOAT,
        float_placement=float_placement,
        caption=caption,
        label=label
    )
    
    return float_box
