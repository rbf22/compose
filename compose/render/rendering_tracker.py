"""
Rendering tracker to record actual rendered content extents.

This tracks what was actually rendered so we can draw accurate bounding boxes
based on reality, not predictions.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum


class ContentType(Enum):
    """Type of rendered content"""
    TEXT = "text"
    OBJECT = "object"
    SPACER = "spacer"


@dataclass
class RenderedContent:
    """Record of a rendered item"""
    content_type: ContentType
    x: float
    y: float
    width: float
    height: float
    page: int
    label: str = ""  # For debugging
    
    @property
    def x2(self) -> float:
        """Right edge"""
        return self.x + self.width
    
    @property
    def y_bottom(self) -> float:
        """Bottom edge (in PDF coords, lower Y value)"""
        return self.y - self.height
    
    def overlaps_with(self, other: 'RenderedContent') -> bool:
        """
        Check if this content has interior overlap with another using strict AABB test.
        
        Uses strict inequalities so that shared edges/corners do NOT count as overlap.
        This is the standard algorithm for detecting true spatial overlap.
        """
        if self.page != other.page:
            return False
        
        # Strict AABB Intersection Test
        # Two boxes have overlapping interiors if they overlap on both axes using strict inequalities
        x_overlap = (self.x < other.x2) and (self.x2 > other.x)
        y_overlap = (self.y > other.y_bottom) and (self.y_bottom < other.y)
        
        return x_overlap and y_overlap


class RenderingTracker:
    """Tracks actual rendered content to generate accurate bounding boxes"""
    
    def __init__(self):
        self.content: List[RenderedContent] = []
        self.current_page = 0
    
    def record_text(self, x: float, y: float, width: float, height: float, 
                   page: int, label: str = ""):
        """Record rendered text"""
        item = RenderedContent(
            content_type=ContentType.TEXT,
            x=x,
            y=y,
            width=width,
            height=height,
            page=page,
            label=label
        )
        self.content.append(item)
        return item
    
    def record_object(self, x: float, y: float, width: float, height: float,
                     page: int, label: str = ""):
        """Record rendered object"""
        self.content.append(RenderedContent(
            content_type=ContentType.OBJECT,
            x=x,
            y=y,
            width=width,
            height=height,
            page=page,
            label=label
        ))
    
    def record_spacer(self, x: float, y: float, width: float, height: float,
                     page: int, label: str = ""):
        """Record spacing area"""
        item = RenderedContent(
            content_type=ContentType.SPACER,
            x=x,
            y=y,
            width=width,
            height=height,
            page=page,
            label=label
        )
        self.content.append(item)
        return item
    
    def get_last_content_bottom(self, page: int) -> Optional[float]:
        """Get the bottom Y coordinate of the last rendered content (non-spacer) on a page"""
        # Find the last non-spacer item on this page
        for item in reversed(self.content):
            if item.page == page and item.content_type != ContentType.SPACER:
                return item.y_bottom
        return None
    
    def get_bounding_box_for_group(self, indices: List[int]) -> Optional[Tuple[float, float, float, float]]:
        """Get bounding box that encompasses a group of content items"""
        if not indices:
            return None
        
        items = [self.content[i] for i in indices]
        
        x_min = min(item.x for item in items)
        x_max = max(item.x2 for item in items)
        y_max = max(item.y for item in items)
        y_min = min(item.y_bottom for item in items)
        
        return (x_min, y_max, x_max, y_min)
    
    def validate_all(self, page_height: float, page_width: float, 
                    margin_top: float, margin_bottom: float,
                    margin_left: float, margin_right: float) -> List[str]:
        """Validate all rendered content and return list of errors"""
        errors = []
        
        content_top = page_height - margin_top
        content_bottom = margin_bottom
        content_left = margin_left
        content_right = page_width - margin_right
        page_top = page_height  # Actual top of page
        
        # Check each item
        for i, item in enumerate(self.content):
            # Check if outside margins
            if item.x < content_left:
                errors.append(f"ERROR: Item {i} ({item.label}) left {item.x:.1f} < margin_left {content_left:.1f}")
            if item.x2 > content_right:
                errors.append(f"ERROR: Item {i} ({item.label}) right {item.x2:.1f} > margin_right {content_right:.1f}")
            # Check if top of content is above the actual page top (should never happen)
            if item.y > page_top:
                errors.append(f"ERROR: Item {i} ({item.label}) top {item.y:.1f} > page_top {page_top:.1f}")
            # Check if bottom of content is above the content area baseline (extends into margin)
            if item.y_bottom > content_top:
                errors.append(f"ERROR: Item {i} ({item.label}) extends into top margin: bottom {item.y_bottom:.1f} > margin_baseline {content_top:.1f}")
            if item.y_bottom < content_bottom:
                errors.append(f"ERROR: Item {i} ({item.label}) bottom {item.y_bottom:.1f} < margin_bottom {content_bottom:.1f}")
            
            # Check overlaps with other content
            for j in range(i + 1, len(self.content)):
                other = self.content[j]
                
                # Skip overlaps between spacing and content (spacing provides intentional gaps)
                if (item.content_type == ContentType.SPACER and other.content_type != ContentType.SPACER) or \
                   (other.content_type == ContentType.SPACER and item.content_type != ContentType.SPACER):
                    continue
                
                # AABB algorithm for actual content overlaps
                if item.overlaps_with(other):
                    errors.append(f"ERROR: Item {i} ({item.label}) overlaps with item {j} ({other.label})")
        
        return errors
    
    def clear(self):
        """Clear all tracked content"""
        self.content = []
