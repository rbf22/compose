"""
Layout adjustments.

Adjustments modify layout state to fix constraint violations.
"""

from typing import TYPE_CHECKING
from .constraint_primitives import LayoutState, Adjustment
from .layout_primitives import LayoutBox, PageLayout

if TYPE_CHECKING:
    from .layout_generator import LayoutGenerator


class MoveToNextPageAdjustment(Adjustment):
    """
    Move an element to the next page.
    
    Used to fix overflow violations by moving content to next page.
    """
    
    def __init__(self, element: LayoutBox):
        """
        Initialize adjustment.
        
        Args:
            element: Element to move
        """
        self.element = element
    
    def apply(self, state: LayoutState, generator: 'LayoutGenerator') -> LayoutState:
        """
        Apply adjustment to state.
        
        Args:
            state: Current layout state
            generator: Layout generator (for creating new pages)
            
        Returns:
            New state with element moved to next page
        """
        new_state = state.clone()
        
        # Find element in current state
        page_idx, box_idx = new_state.find_element(self.element)
        
        if page_idx is None:
            # Element not found, return unchanged
            return new_state
        
        page = new_state.pages[page_idx]
        
        # Remove from current page
        page.boxes.pop(box_idx)
        
        # Ensure next page exists
        if page_idx + 1 >= len(new_state.pages):
            new_page = PageLayout(
                page_number=len(new_state.pages),
                width=page.width,
                height=page.height,
                margin_top=page.margin_top,
                margin_bottom=page.margin_bottom,
                margin_left=page.margin_left,
                margin_right=page.margin_right
            )
            new_state.pages.append(new_page)
        
        next_page = new_state.pages[page_idx + 1]
        
        # Create new box at top of next page
        moved_box = LayoutBox(
            box_type=self.element.box_type,
            x=self.element.x,
            y=next_page.content_top,
            width=self.element.width,
            height=self.element.height,
            content=self.element.content,
            children=self.element.children,
            metadata=dict(self.element.metadata)
        )
        moved_box.add_adjustment("moved_to_next_page")
        
        # Add to next page
        next_page.boxes.insert(0, moved_box)
        
        # Reflow subsequent elements on next page
        current_y = next_page.content_top - moved_box.height - 6
        for i, box in enumerate(next_page.boxes[1:], 1):
            box.y = current_y
            current_y -= box.height + 6
        
        return new_state


class IncreaseSpacingAdjustment(Adjustment):
    """
    Increase spacing after an element.
    
    Used to fix minimum spacing violations.
    """
    
    def __init__(self, element: LayoutBox, target_spacing: float):
        """
        Initialize adjustment.
        
        Args:
            element: Element after which to increase spacing
            target_spacing: Target spacing amount
        """
        self.element = element
        self.target_spacing = target_spacing
    
    def apply(self, state: LayoutState, generator: 'LayoutGenerator') -> LayoutState:
        """
        Apply adjustment to state.
        
        Args:
            state: Current layout state
            generator: Layout generator
            
        Returns:
            New state with increased spacing
        """
        new_state = state.clone()
        
        # Find element
        page_idx, box_idx = new_state.find_element(self.element)
        
        if page_idx is None or box_idx is None:
            return new_state
        
        page = new_state.pages[page_idx]
        
        # Calculate current spacing to previous element
        if box_idx > 0:
            prev_box = page.boxes[box_idx - 1]
            current_spacing = prev_box.bottom - self.element.y
            spacing_increase = self.target_spacing - current_spacing
            
            if spacing_increase > 0:
                # Move this element and all subsequent down
                for i in range(box_idx, len(page.boxes)):
                    page.boxes[i].y -= spacing_increase
                
                self.element.add_adjustment("spacing_increased")
        
        return new_state


class PullLineFromPreviousPageAdjustment(Adjustment):
    """
    Pull one more line from previous page to fix widow.
    
    This is complex - requires re-breaking the paragraph.
    For now, we'll implement a simple version that moves the element.
    """
    
    def __init__(self, element: LayoutBox):
        """
        Initialize adjustment.
        
        Args:
            element: Element to adjust
        """
        self.element = element
    
    def apply(self, state: LayoutState, generator: 'LayoutGenerator') -> LayoutState:
        """
        Apply adjustment to state.
        
        For now, this moves the element to previous page.
        A full implementation would re-break the paragraph.
        
        Args:
            state: Current layout state
            generator: Layout generator
            
        Returns:
            New state with adjustment applied
        """
        new_state = state.clone()
        
        # Find element
        page_idx, box_idx = new_state.find_element(self.element)
        
        if page_idx is None or page_idx == 0:
            return new_state
        
        # For now, just move to previous page
        # A full implementation would re-break the paragraph
        current_page = new_state.pages[page_idx]
        prev_page = new_state.pages[page_idx - 1]
        
        # Remove from current page
        current_page.boxes.pop(box_idx)
        
        # Add to previous page
        moved_box = LayoutBox(
            box_type=self.element.box_type,
            x=self.element.x,
            y=prev_page.content_bottom + self.element.height,
            width=self.element.width,
            height=self.element.height,
            content=self.element.content,
            children=self.element.children,
            metadata=dict(self.element.metadata)
        )
        moved_box.add_adjustment("pulled_from_next_page")
        
        prev_page.boxes.append(moved_box)
        
        return new_state
