"""
Advanced layout rules for professional typography.

These rules implement sophisticated typographic constraints:
- Balanced columns
- Optimal line breaking
- Heading orphan prevention
- Keep-together blocks
"""

from typing import List
from .constraint_primitives import LayoutState, Violation, Severity, Adjustment
from .layout_primitives import LayoutBox, BoxType


class HeadingOrphanRule:
    """
    Prevent headings from appearing alone at bottom of page.
    
    A heading orphan is when a heading appears at the bottom of a page
    with no content following it on the same page.
    """
    
    def check(self, state: LayoutState) -> List[Violation]:
        """Check for orphan headings"""
        violations = []
        
        for page_idx, page in enumerate(state.pages):
            if not page.boxes:
                continue
            
            # Check last element on page
            last_box = page.boxes[-1]
            
            # Only check headings
            if last_box.box_type != BoxType.HEADING:
                continue
            
            # Check if there's a next page with content
            if page_idx + 1 < len(state.pages):
                next_page = state.pages[page_idx + 1]
                
                # If heading is last on page and next page has content,
                # it's an orphan
                if next_page.boxes:
                    violations.append(Violation(
                        rule_name="no_heading_orphans",
                        severity=Severity.WARNING,
                        element=last_box,
                        page=page_idx,
                        description="Heading orphan: heading alone at bottom of page"
                    ))
        
        return violations
    
    def suggest_fix(self, violation: Violation, 
                   state: LayoutState) -> List[Adjustment]:
        """Suggest moving heading to next page"""
        from .layout_adjustments import MoveToNextPageAdjustment
        return [MoveToNextPageAdjustment(violation.element)]


class KeepTogetherRule:
    """
    Keep related elements together on same page.
    
    Prevents breaking between a heading and its first paragraph,
    or between list items that should stay together.
    """
    
    def check(self, state: LayoutState) -> List[Violation]:
        """Check for elements that should be kept together"""
        violations = []
        
        for page_idx, page in enumerate(state.pages):
            for i in range(len(page.boxes) - 1):
                box1 = page.boxes[i]
                box2 = page.boxes[i + 1]
                
                # Check if heading is followed by paragraph on different pages
                if (box1.box_type == BoxType.HEADING and 
                    box2.box_type == BoxType.PARAGRAPH):
                    
                    # If they're on different pages, they should be together
                    if box1.y > box2.y:  # box2 is on next page
                        violations.append(Violation(
                            rule_name="keep_together",
                            severity=Severity.INFO,
                            element=box1,
                            page=page_idx,
                            description="Heading and paragraph separated by page break"
                        ))
        
        return violations
    
    def suggest_fix(self, violation: Violation, 
                   state: LayoutState) -> List[Adjustment]:
        """Suggest moving heading to next page with its content"""
        from .layout_adjustments import MoveToNextPageAdjustment
        return [MoveToNextPageAdjustment(violation.element)]


class MaxLinesPerPageRule:
    """
    Ensure pages don't exceed maximum lines.
    
    Prevents pages from becoming too dense with content.
    """
    
    def __init__(self, max_lines: int = 50):
        """
        Initialize rule.
        
        Args:
            max_lines: Maximum lines per page
        """
        self.max_lines = max_lines
    
    def check(self, state: LayoutState) -> List[Violation]:
        """Check page line counts"""
        violations = []
        
        for page_idx, page in enumerate(state.pages):
            # Count lines on page
            line_count = 0
            
            for box in page.boxes:
                if box.box_type == BoxType.PARAGRAPH:
                    # Count lines in paragraph
                    if isinstance(box.content, list):
                        line_count += len(box.content)
            
            if line_count > self.max_lines:
                violations.append(Violation(
                    rule_name="max_lines_per_page",
                    severity=Severity.INFO,
                    element=page.boxes[-1] if page.boxes else None,
                    page=page_idx,
                    description=f"Page has {line_count} lines > maximum {self.max_lines}"
                ))
        
        return violations
    
    def suggest_fix(self, violation: Violation, 
                   state: LayoutState) -> List[Adjustment]:
        """Suggest moving content to next page"""
        from .layout_adjustments import MoveToNextPageAdjustment
        if violation.element:
            return [MoveToNextPageAdjustment(violation.element)]
        return []


class MinimumPageFullnessRule:
    """
    Ensure pages are adequately filled.
    
    Prevents pages from being too sparse with lots of whitespace.
    """
    
    def __init__(self, min_fullness: float = 0.7):
        """
        Initialize rule.
        
        Args:
            min_fullness: Minimum page fullness (0-1)
        """
        self.min_fullness = min_fullness
    
    def check(self, state: LayoutState) -> List[Violation]:
        """Check page fullness"""
        violations = []
        
        for page_idx, page in enumerate(state.pages):
            # Calculate page fullness
            total_content_height = sum(box.height for box in page.boxes)
            available_height = page.height - page.margin_top - page.margin_bottom
            
            if available_height > 0:
                fullness = total_content_height / available_height
                
                # Check all pages except last
                if page_idx < len(state.pages) - 1:
                    if fullness < self.min_fullness:
                        violations.append(Violation(
                            rule_name="minimum_page_fullness",
                            severity=Severity.INFO,
                            element=page.boxes[-1] if page.boxes else None,
                            page=page_idx,
                            description=f"Page fullness {fullness:.1%} < minimum {self.min_fullness:.1%}"
                        ))
        
        return violations
    
    def suggest_fix(self, violation: Violation, 
                   state: LayoutState) -> List[Adjustment]:
        """Suggest pulling content from next page"""
        # This would require complex re-layout, so we skip for now
        return []


class BalancedSpacingRule:
    """
    Ensure consistent spacing between elements.
    
    Prevents some elements from having too much space while others have too little.
    """
    
    def __init__(self, tolerance: float = 0.2):
        """
        Initialize rule.
        
        Args:
            tolerance: Tolerance for spacing variation (0-1)
        """
        self.tolerance = tolerance
    
    def check(self, state: LayoutState) -> List[Violation]:
        """Check spacing consistency"""
        violations = []
        
        for page_idx, page in enumerate(state.pages):
            spacings = []
            
            # Calculate spacings between elements
            for i in range(len(page.boxes) - 1):
                box1 = page.boxes[i]
                box2 = page.boxes[i + 1]
                spacing = box1.bottom - box2.y
                spacings.append(spacing)
            
            if not spacings:
                continue
            
            # Calculate average and variance
            avg_spacing = sum(spacings) / len(spacings)
            
            # Check for outliers
            for i, spacing in enumerate(spacings):
                deviation = abs(spacing - avg_spacing) / avg_spacing if avg_spacing > 0 else 0
                
                if deviation > self.tolerance:
                    violations.append(Violation(
                        rule_name="balanced_spacing",
                        severity=Severity.INFO,
                        element=page.boxes[i + 1],
                        page=page_idx,
                        description=f"Spacing {spacing:.1f}pt deviates {deviation:.1%} from average {avg_spacing:.1f}pt"
                    ))
        
        return violations
    
    def suggest_fix(self, violation: Violation, 
                   state: LayoutState) -> List[Adjustment]:
        """Suggest adjusting spacing"""
        from .layout_adjustments import IncreaseSpacingAdjustment
        # Increase spacing to average
        return [IncreaseSpacingAdjustment(violation.element, 12.0)]


class NoBlankPagesRule:
    """
    Prevent completely blank pages.
    
    Ensures every page has at least some content.
    """
    
    def check(self, state: LayoutState) -> List[Violation]:
        """Check for blank pages"""
        violations = []
        
        for page_idx, page in enumerate(state.pages):
            # Check if page is empty
            if not page.boxes:
                violations.append(Violation(
                    rule_name="no_blank_pages",
                    severity=Severity.WARNING,
                    element=None,
                    page=page_idx,
                    description="Page is completely blank"
                ))
        
        return violations
    
    def suggest_fix(self, violation: Violation, 
                   state: LayoutState) -> List[Adjustment]:
        """Suggest removing blank page"""
        # This would require page removal logic
        return []
