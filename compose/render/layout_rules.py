"""
Layout constraint rules.

Rules check layout constraints and suggest fixes for violations.
"""

from abc import ABC, abstractmethod
from typing import List
from .constraint_primitives import LayoutState, Violation, Severity, Adjustment
from .layout_primitives import LayoutBox, BoxType


class LayoutRule(ABC):
    """
    Base class for layout constraint rules.
    
    A rule checks if a constraint is satisfied in the layout,
    and suggests adjustments if violations are found.
    """
    
    @abstractmethod
    def check(self, state: LayoutState) -> List[Violation]:
        """
        Check if rule is satisfied.
        
        Args:
            state: Current layout state
            
        Returns:
            List of violations (empty if rule satisfied)
        """
        pass
    
    @abstractmethod
    def suggest_fix(self, violation: Violation, 
                   state: LayoutState) -> List[Adjustment]:
        """
        Suggest adjustments to fix a violation.
        
        Args:
            violation: The violation to fix
            state: Current layout state
            
        Returns:
            List of suggested adjustments
        """
        pass


class NoOverflowRule(LayoutRule):
    """
    Prevent content from overflowing page boundaries.
    
    This is a critical rule - content must fit within page margins.
    """
    
    def check(self, state: LayoutState) -> List[Violation]:
        """Check for content overflow"""
        violations = []
        
        for page_idx, page in enumerate(state.pages):
            for box in page.boxes:
                # Check vertical overflow (bottom of page)
                if box.bottom < page.content_bottom:
                    overflow_amount = page.content_bottom - box.bottom
                    violations.append(Violation(
                        rule_name="no_overflow",
                        severity=Severity.ERROR,
                        element=box,
                        page=page_idx,
                        description=f"Element overflows page bottom by {overflow_amount:.1f}pt"
                    ))
                
                # Check horizontal overflow (right edge)
                if box.right > page.margin_left + page.content_width:
                    overflow_amount = box.right - (page.margin_left + page.content_width)
                    violations.append(Violation(
                        rule_name="no_overflow",
                        severity=Severity.ERROR,
                        element=box,
                        page=page_idx,
                        description=f"Element overflows page right by {overflow_amount:.1f}pt"
                    ))
        
        return violations
    
    def suggest_fix(self, violation: Violation, 
                   state: LayoutState) -> List[Adjustment]:
        """Suggest moving element to next page"""
        from .layout_adjustments import MoveToNextPageAdjustment
        return [MoveToNextPageAdjustment(violation.element)]


class MinimumSpacingRule(LayoutRule):
    """
    Ensure minimum spacing between elements.
    
    This improves visual appearance and readability.
    """
    
    def __init__(self, min_spacing: float = 6.0):
        """
        Initialize rule.
        
        Args:
            min_spacing: Minimum spacing in points
        """
        self.min_spacing = min_spacing
    
    def check(self, state: LayoutState) -> List[Violation]:
        """Check spacing between elements"""
        violations = []
        
        for page_idx, page in enumerate(state.pages):
            for i in range(len(page.boxes) - 1):
                box1 = page.boxes[i]
                box2 = page.boxes[i + 1]
                
                # Calculate spacing between boxes
                spacing = box1.bottom - box2.y
                
                if spacing < self.min_spacing:
                    violations.append(Violation(
                        rule_name="minimum_spacing",
                        severity=Severity.INFO,
                        element=box2,
                        page=page_idx,
                        description=f"Spacing {spacing:.1f}pt < minimum {self.min_spacing:.1f}pt"
                    ))
        
        return violations
    
    def suggest_fix(self, violation: Violation, 
                   state: LayoutState) -> List[Adjustment]:
        """Suggest increasing spacing"""
        from .layout_adjustments import IncreaseSpacingAdjustment
        return [IncreaseSpacingAdjustment(
            violation.element,
            self.min_spacing
        )]


class NoOrphanLinesRule(LayoutRule):
    """
    Prevent orphan lines (single line at bottom of page).
    
    An orphan is when the first line of a paragraph appears alone
    at the bottom of a page.
    """
    
    def check(self, state: LayoutState) -> List[Violation]:
        """Check for orphan lines"""
        violations = []
        
        for page_idx, page in enumerate(state.pages):
            if not page.boxes:
                continue
            
            # Check last element on page
            last_box = page.boxes[-1]
            
            # Only check paragraphs
            if last_box.box_type != BoxType.PARAGRAPH:
                continue
            
            # Check if it's a multi-line paragraph
            if not hasattr(last_box.content, '__len__'):
                continue
            
            lines = last_box.content
            if not isinstance(lines, list) or len(lines) <= 1:
                continue
            
            # Count how many lines fit on this page
            lines_on_page = self._count_lines_on_page(last_box, page)
            
            # If only 1 line of multi-line paragraph on page, it's an orphan
            if lines_on_page == 1 and len(lines) > 1:
                violations.append(Violation(
                    rule_name="no_orphan_lines",
                    severity=Severity.WARNING,
                    element=last_box,
                    page=page_idx,
                    description=f"Orphan line: only 1 of {len(lines)} lines on page"
                ))
        
        return violations
    
    def suggest_fix(self, violation: Violation, 
                   state: LayoutState) -> List[Adjustment]:
        """Suggest moving entire paragraph to next page"""
        from .layout_adjustments import MoveToNextPageAdjustment
        return [MoveToNextPageAdjustment(violation.element)]
    
    def _count_lines_on_page(self, box: LayoutBox, page) -> int:
        """Count how many lines of a paragraph fit on page"""
        if not hasattr(box.content, '__len__'):
            return 0
        
        lines = box.content
        count = 0
        
        for line in lines:
            # Check if line is within page bounds
            if hasattr(line, 'y') and hasattr(line, 'height'):
                if line.y >= page.content_bottom and line.y - line.height <= page.content_top:
                    count += 1
        
        return count


class NoWidowLinesRule(LayoutRule):
    """
    Prevent widow lines (single line at top of page).
    
    A widow is when the last line of a paragraph appears alone
    at the top of a page.
    """
    
    def check(self, state: LayoutState) -> List[Violation]:
        """Check for widow lines"""
        violations = []
        
        for page_idx in range(1, len(state.pages)):  # Start from page 2
            page = state.pages[page_idx]
            
            if not page.boxes:
                continue
            
            # Check first element on page
            first_box = page.boxes[0]
            
            # Only check paragraphs
            if first_box.box_type != BoxType.PARAGRAPH:
                continue
            
            # Check if it's a continuation from previous page
            prev_page = state.pages[page_idx - 1]
            if not prev_page.boxes or prev_page.boxes[-1] != first_box:
                continue
            
            # Check if it's multi-line
            if not hasattr(first_box.content, '__len__'):
                continue
            
            lines = first_box.content
            if not isinstance(lines, list) or len(lines) <= 1:
                continue
            
            # Count lines on this page
            lines_on_page = self._count_lines_on_page(first_box, page)
            
            # If only 1 line on page and it's multi-line, it's a widow
            if lines_on_page == 1 and len(lines) > 1:
                violations.append(Violation(
                    rule_name="no_widow_lines",
                    severity=Severity.WARNING,
                    element=first_box,
                    page=page_idx,
                    description=f"Widow line: only 1 of {len(lines)} lines on page"
                ))
        
        return violations
    
    def suggest_fix(self, violation: Violation, 
                   state: LayoutState) -> List[Adjustment]:
        """Suggest pulling line from previous page"""
        from .layout_adjustments import PullLineFromPreviousPageAdjustment
        return [PullLineFromPreviousPageAdjustment(violation.element)]
    
    def _count_lines_on_page(self, box: LayoutBox, page) -> int:
        """Count how many lines of a paragraph fit on page"""
        if not hasattr(box.content, '__len__'):
            return 0
        
        lines = box.content
        count = 0
        
        for line in lines:
            if hasattr(line, 'y') and hasattr(line, 'height'):
                if line.y >= page.content_bottom and line.y - line.height <= page.content_top:
                    count += 1
        
        return count
