"""
Layout primitives for separating layout calculation from rendering.

This module provides data structures that represent the result of layout
calculations without any rendering-specific code. This enables:
- Testing layout logic independently
- Caching layout results
- Supporting multiple output formats from same layout
- Parallelizing rendering
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Tuple
from enum import Enum


class BoxType(Enum):
    """Type of layout box"""
    TEXT = "text"
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    CODE_BLOCK = "code_block"
    LIST = "list"
    LIST_ITEM = "list_item"
    TABLE = "table"
    TABLE_ROW = "table_row"
    TABLE_CELL = "table_cell"
    MATH = "math"
    IMAGE = "image"
    HORIZONTAL_RULE = "horizontal_rule"
    PAGE = "page"


@dataclass
class TextRun:
    """
    A single run of text with consistent formatting.
    
    This is the atomic unit of text layout - represents text that can be
    rendered in one PDF text operation.
    """
    text: str
    font: str
    size: float
    x: float
    y: float
    width: float
    color: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    underline: bool = False
    strikethrough: bool = False
    
    def __post_init__(self):
        """Validate text run parameters"""
        if self.size <= 0:
            raise ValueError(f"Font size must be positive, got {self.size}")
        if self.width < 0:
            raise ValueError(f"Width cannot be negative, got {self.width}")


@dataclass
class LineLayout:
    """
    Layout information for a single line of text.
    
    Contains multiple TextRuns if the line has mixed formatting.
    """
    runs: List[TextRun]
    x: float
    y: float  # Baseline position
    width: float
    height: float
    baseline_offset: float = 0.0  # Distance from top to baseline
    
    @property
    def text(self) -> str:
        """Get the complete text of this line"""
        return ''.join(run.text for run in self.runs)
    
    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box as (x, y, width, height)"""
        return (self.x, self.y - self.height, self.width, self.height)


@dataclass
class LayoutBox:
    """
    Generic layout box representing any positioned element.
    
    This is the core abstraction - all layout elements are represented as
    boxes with positions, dimensions, and optional children.
    """
    box_type: BoxType
    x: float
    y: float  # Top-left corner
    width: float
    height: float
    content: Any = None  # Type-specific content
    children: List['LayoutBox'] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    adjustments: List[str] = field(default_factory=list)
    
    @property
    def bottom(self) -> float:
        """Bottom edge of the box"""
        return self.y - self.height
    
    @property
    def right(self) -> float:
        """Right edge of the box"""
        return self.x + self.width
    
    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box as (x, y, width, height)"""
        return (self.x, self.y, self.width, self.height)
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside this box"""
        return (self.x <= x <= self.right and 
                self.bottom <= y <= self.y)
    
    def intersects(self, other: 'LayoutBox') -> bool:
        """Check if this box intersects with another"""
        return not (self.right < other.x or 
                   self.x > other.right or
                   self.y < other.bottom or
                   self.bottom > other.y)
    
    def add_constraint(self, constraint_name: str):
        """Mark that a constraint applies to this box"""
        if constraint_name not in self.constraints:
            self.constraints.append(constraint_name)
    
    def add_adjustment(self, adjustment_name: str):
        """Mark that an adjustment was applied"""
        if adjustment_name not in self.adjustments:
            self.adjustments.append(adjustment_name)


@dataclass
class ParagraphLayout:
    """
    Layout information for a paragraph.
    
    Contains multiple lines, each potentially with multiple text runs.
    """
    lines: List[LineLayout]
    x: float
    y: float  # Top of paragraph
    width: float
    height: float
    spacing_after: float = 0.0
    alignment: str = "left"  # left, center, right, justify
    
    @property
    def text(self) -> str:
        """Get the complete text of this paragraph"""
        return '\n'.join(line.text for line in self.lines)
    
    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box as (x, y, width, height)"""
        return (self.x, self.y, self.width, self.height)
    
    def to_layout_box(self) -> LayoutBox:
        """Convert to generic LayoutBox"""
        return LayoutBox(
            box_type=BoxType.PARAGRAPH,
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
            content=self,
            metadata={'alignment': self.alignment}
        )


@dataclass
class PageLayout:
    """
    Layout information for a complete page.
    
    Contains all boxes that appear on this page.
    """
    page_number: int
    width: float
    height: float
    boxes: List[LayoutBox] = field(default_factory=list)
    margin_top: float = 72.0
    margin_bottom: float = 72.0
    margin_left: float = 72.0
    margin_right: float = 72.0
    
    @property
    def content_width(self) -> float:
        """Width of content area (excluding margins)"""
        return self.width - self.margin_left - self.margin_right
    
    @property
    def content_height(self) -> float:
        """Height of content area (excluding margins)"""
        return self.height - self.margin_top - self.margin_bottom
    
    @property
    def content_top(self) -> float:
        """Y coordinate of top of content area"""
        return self.height - self.margin_top
    
    @property
    def content_bottom(self) -> float:
        """Y coordinate of bottom of content area"""
        return self.margin_bottom
    
    def add_box(self, box: LayoutBox):
        """Add a box to this page"""
        self.boxes.append(box)
    
    def has_space_for(self, height: float, current_y: float) -> bool:
        """Check if there's space for an element of given height"""
        return current_y - height >= self.content_bottom


@dataclass
class DocumentLayout:
    """
    Complete layout information for a document.
    
    Contains all pages and document-level metadata.
    """
    pages: List[PageLayout]
    title: str = "Untitled Document"
    metadata: dict = field(default_factory=dict)
    
    @property
    def page_count(self) -> int:
        """Number of pages in the document"""
        return len(self.pages)
    
    def add_page(self, page: PageLayout):
        """Add a page to the document"""
        self.pages.append(page)


@dataclass
class TextMeasurement:
    """
    Result of measuring text dimensions.
    
    Used for caching text measurement results.
    """
    text: str
    font: str
    size: float
    width: float
    height: float
    ascent: float
    descent: float
    
    def __hash__(self):
        """Make hashable for caching"""
        return hash((self.text, self.font, self.size))
