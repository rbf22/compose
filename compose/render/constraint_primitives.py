"""
Constraint-based layout primitives.

Core data structures for the iterative constraint-solving layout system.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from .layout_primitives import LayoutBox, PageLayout


class Severity(Enum):
    """Severity level of a constraint violation"""
    ERROR = "error"      # Must fix (e.g., overflow)
    WARNING = "warning"  # Should fix (e.g., orphan line)
    INFO = "info"        # Nice to fix (e.g., spacing)


@dataclass
class Violation:
    """
    A constraint violation found during layout checking.
    
    Represents a single rule violation that needs to be fixed.
    """
    rule_name: str
    severity: Severity
    element: LayoutBox
    page: int
    description: str
    suggested_fix: Optional['Adjustment'] = None
    
    def __repr__(self) -> str:
        return f"Violation({self.rule_name}, {self.severity.value}, page {self.page}: {self.description})"


@dataclass
class LayoutState:
    """
    Immutable snapshot of layout at a point in time.
    
    Each iteration of constraint solving produces a new LayoutState.
    """
    pages: List[PageLayout]
    current_page: int
    current_y: float
    elements: List[LayoutBox]
    metadata: Dict[str, Any] = field(default_factory=dict)
    iteration: int = 0
    
    def clone(self) -> 'LayoutState':
        """
        Create a deep copy for the next iteration.
        
        Returns:
            New LayoutState with cloned pages and elements
        """
        return LayoutState(
            pages=[self._clone_page(p) for p in self.pages],
            current_page=self.current_page,
            current_y=self.current_y,
            elements=list(self.elements),
            metadata=dict(self.metadata),
            iteration=self.iteration + 1
        )
    
    def _clone_page(self, page: PageLayout) -> PageLayout:
        """Deep clone a page"""
        return PageLayout(
            page_number=page.page_number,
            width=page.width,
            height=page.height,
            boxes=[self._clone_box(b) for b in page.boxes],
            margin_top=page.margin_top,
            margin_bottom=page.margin_bottom,
            margin_left=page.margin_left,
            margin_right=page.margin_right
        )
    
    def _clone_box(self, box: LayoutBox) -> LayoutBox:
        """Deep clone a box"""
        return LayoutBox(
            box_type=box.box_type,
            x=box.x,
            y=box.y,
            width=box.width,
            height=box.height,
            content=box.content,
            children=[self._clone_box(c) for c in box.children],
            metadata=dict(box.metadata),
            constraints=list(box.constraints),
            adjustments=list(box.adjustments)
        )
    
    def get_page(self, page_num: int) -> Optional[PageLayout]:
        """Get a page by number"""
        if 0 <= page_num < len(self.pages):
            return self.pages[page_num]
        return None
    
    def find_element(self, element: LayoutBox) -> tuple[Optional[int], Optional[int]]:
        """
        Find element in state.
        
        Returns:
            (page_index, box_index) or (None, None) if not found
        """
        for page_idx, page in enumerate(self.pages):
            try:
                box_idx = page.boxes.index(element)
                return (page_idx, box_idx)
            except ValueError:
                continue
        return (None, None)


class Adjustment:
    """
    Base class for layout adjustments.
    
    An adjustment modifies the layout state to fix violations.
    """
    
    def apply(self, state: LayoutState, generator: 'LayoutGenerator') -> LayoutState:
        """
        Apply this adjustment to the layout state.
        
        Args:
            state: Current layout state
            generator: Layout generator (for recalculation if needed)
            
        Returns:
            New layout state with adjustment applied
        """
        raise NotImplementedError


@dataclass
class AdjustmentResult:
    """Result of applying an adjustment"""
    success: bool
    new_state: Optional[LayoutState] = None
    error_message: Optional[str] = None
