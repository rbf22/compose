# Constraint-Based Layout Architecture

## Overview

A constraint-based layout system that iteratively resolves rules until all constraints are satisfied. This enables sophisticated typesetting rules like widow/orphan prevention, balanced columns, optimal line breaking, etc.

## Core Concept

```
┌─────────────────────────────────────────────────────────────┐
│                    ITERATIVE LAYOUT LOOP                     │
└─────────────────────────────────────────────────────────────┘

1. Generate Initial Layout
   ↓
2. Test Constraints/Rules
   ↓
3. Violations Found? ──No──→ Layout Complete ✓
   ↓ Yes
4. Apply Adjustments
   ↓
5. Regenerate Layout
   ↓
   (Loop back to step 2)
```

## Architecture Layers

### Layer 1: Layout Generation (Stateless)

```python
@dataclass
class LayoutState:
    """Immutable snapshot of layout at a point in time"""
    pages: List[PageLayout]
    current_page: int
    current_y: float
    elements: List[LayoutBox]
    metadata: Dict[str, Any]
    
    def clone(self) -> 'LayoutState':
        """Create a copy for iteration"""
        return LayoutState(
            pages=list(self.pages),
            current_page=self.current_page,
            current_y=self.current_y,
            elements=list(self.elements),
            metadata=dict(self.metadata)
        )

class LayoutGenerator:
    """Generates layout from AST - pure, deterministic"""
    
    def generate_initial_layout(self, doc: Document, 
                                config: LayoutConfig) -> LayoutState:
        """
        Generate initial layout without constraint checking.
        
        This is the "naive" layout - just place elements sequentially
        without worrying about typographic rules.
        """
        state = LayoutState(pages=[], current_page=0, current_y=config.page_height)
        
        for block in doc.blocks:
            element_layout = self._layout_element(block, state, config)
            state = self._add_element(state, element_layout)
        
        return state
    
    def regenerate_with_adjustments(self, state: LayoutState, 
                                    adjustments: List[Adjustment]) -> LayoutState:
        """
        Regenerate layout applying adjustments.
        
        Adjustments might include:
        - Force page break before element X
        - Increase spacing between elements
        - Adjust line breaking parameters
        - Move element to next page
        """
        new_state = state.clone()
        
        for adjustment in adjustments:
            new_state = adjustment.apply(new_state)
        
        return new_state
```

### Layer 2: Constraint Rules

```python
from enum import Enum
from abc import ABC, abstractmethod

class Severity(Enum):
    """Severity of constraint violation"""
    ERROR = "error"      # Must fix (e.g., overflow)
    WARNING = "warning"  # Should fix (e.g., widow line)
    INFO = "info"        # Nice to fix (e.g., unbalanced columns)

@dataclass
class Violation:
    """A constraint violation found in layout"""
    rule_name: str
    severity: Severity
    element: LayoutBox
    page: int
    description: str
    suggested_fix: Optional['Adjustment'] = None

class LayoutRule(ABC):
    """Base class for layout constraint rules"""
    
    @abstractmethod
    def check(self, state: LayoutState) -> List[Violation]:
        """Check if rule is satisfied, return violations"""
        pass
    
    @abstractmethod
    def suggest_fix(self, violation: Violation, 
                    state: LayoutState) -> List['Adjustment']:
        """Suggest adjustments to fix violation"""
        pass

# Example Rules

class NoOrphanLinesRule(LayoutRule):
    """Prevent single line at bottom of page (orphan)"""
    
    def check(self, state: LayoutState) -> List[Violation]:
        violations = []
        
        for page_idx, page in enumerate(state.pages):
            # Check last element on page
            if not page.boxes:
                continue
            
            last_box = page.boxes[-1]
            
            # If it's a paragraph with only one line at bottom
            if (last_box.box_type == BoxType.PARAGRAPH and 
                isinstance(last_box.content, ParagraphLayout)):
                
                para = last_box.content
                
                # Check if only first line of multi-line paragraph
                if len(para.lines) > 1:
                    # Check if only one line fits on this page
                    lines_on_page = self._count_lines_on_page(para, page)
                    
                    if lines_on_page == 1:
                        violations.append(Violation(
                            rule_name="no_orphan_lines",
                            severity=Severity.WARNING,
                            element=last_box,
                            page=page_idx,
                            description=f"Orphan line: only 1 of {len(para.lines)} lines on page"
                        ))
        
        return violations
    
    def suggest_fix(self, violation: Violation, 
                    state: LayoutState) -> List['Adjustment']:
        """Move entire paragraph to next page"""
        return [MoveToNextPageAdjustment(violation.element)]

class NoWidowLinesRule(LayoutRule):
    """Prevent single line at top of page (widow)"""
    
    def check(self, state: LayoutState) -> List[Violation]:
        violations = []
        
        for page_idx, page in enumerate(state.pages):
            if not page.boxes:
                continue
            
            first_box = page.boxes[0]
            
            # If it's a paragraph starting on this page
            if (first_box.box_type == BoxType.PARAGRAPH and
                isinstance(first_box.content, ParagraphLayout)):
                
                para = first_box.content
                
                # Check if it's continuation from previous page
                if page_idx > 0:
                    prev_page = state.pages[page_idx - 1]
                    if prev_page.boxes and prev_page.boxes[-1] == first_box:
                        # This is a continuation
                        lines_on_page = self._count_lines_on_page(para, page)
                        
                        if lines_on_page == 1 and len(para.lines) > 1:
                            violations.append(Violation(
                                rule_name="no_widow_lines",
                                severity=Severity.WARNING,
                                element=first_box,
                                page=page_idx,
                                description=f"Widow line: only 1 of {len(para.lines)} lines on page"
                            ))
        
        return violations
    
    def suggest_fix(self, violation: Violation, 
                    state: LayoutState) -> List['Adjustment']:
        """Move one more line from previous page"""
        return [PullLineFromPreviousPageAdjustment(violation.element)]

class NoOverflowRule(LayoutRule):
    """Prevent content overflow beyond page boundaries"""
    
    def check(self, state: LayoutState) -> List[Violation]:
        violations = []
        
        for page_idx, page in enumerate(state.pages):
            for box in page.boxes:
                # Check if box extends beyond page bottom
                if box.bottom < page.content_bottom:
                    violations.append(Violation(
                        rule_name="no_overflow",
                        severity=Severity.ERROR,
                        element=box,
                        page=page_idx,
                        description=f"Element overflows page by {page.content_bottom - box.bottom}pt"
                    ))
                
                # Check if box extends beyond page right
                if box.right > page.content_width + page.margin_left:
                    violations.append(Violation(
                        rule_name="no_overflow",
                        severity=Severity.ERROR,
                        element=box,
                        page=page_idx,
                        description=f"Element overflows page width"
                    ))
        
        return violations
    
    def suggest_fix(self, violation: Violation, 
                    state: LayoutState) -> List['Adjustment']:
        """Force page break before element"""
        return [ForcePageBreakAdjustment(violation.element)]

class MinimumSpacingRule(LayoutRule):
    """Ensure minimum spacing between elements"""
    
    def __init__(self, min_spacing: float = 6.0):
        self.min_spacing = min_spacing
    
    def check(self, state: LayoutState) -> List[Violation]:
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
                        description=f"Spacing {spacing}pt < minimum {self.min_spacing}pt"
                    ))
        
        return violations
    
    def suggest_fix(self, violation: Violation, 
                    state: LayoutState) -> List['Adjustment']:
        """Increase spacing"""
        return [IncreaseSpacingAdjustment(
            violation.element, 
            self.min_spacing
        )]

class BalancedColumnsRule(LayoutRule):
    """Balance column heights in multi-column layout"""
    
    def check(self, state: LayoutState) -> List[Violation]:
        # Check if columns are balanced
        # Return violations if height difference > threshold
        pass
    
    def suggest_fix(self, violation: Violation, 
                    state: LayoutState) -> List['Adjustment']:
        """Redistribute content between columns"""
        pass
```

### Layer 3: Adjustments

```python
class Adjustment(ABC):
    """Base class for layout adjustments"""
    
    @abstractmethod
    def apply(self, state: LayoutState) -> LayoutState:
        """Apply adjustment to layout state"""
        pass

class ForcePageBreakAdjustment(Adjustment):
    """Force a page break before an element"""
    
    def __init__(self, element: LayoutBox):
        self.element = element
    
    def apply(self, state: LayoutState) -> LayoutState:
        new_state = state.clone()
        
        # Find element in state
        for page_idx, page in enumerate(new_state.pages):
            if self.element in page.boxes:
                # Remove from current page
                page.boxes.remove(self.element)
                
                # Add to next page (create if needed)
                if page_idx + 1 >= len(new_state.pages):
                    new_state.pages.append(PageLayout(
                        page_number=page_idx + 1,
                        width=page.width,
                        height=page.height
                    ))
                
                next_page = new_state.pages[page_idx + 1]
                
                # Recalculate element position for new page
                new_element = self._recalculate_position(
                    self.element, 
                    next_page
                )
                next_page.boxes.insert(0, new_element)
                break
        
        return new_state

class MoveToNextPageAdjustment(Adjustment):
    """Move element to next page"""
    
    def __init__(self, element: LayoutBox):
        self.element = element
    
    def apply(self, state: LayoutState) -> LayoutState:
        # Similar to ForcePageBreakAdjustment
        pass

class IncreaseSpacingAdjustment(Adjustment):
    """Increase spacing after an element"""
    
    def __init__(self, element: LayoutBox, target_spacing: float):
        self.element = element
        self.target_spacing = target_spacing
    
    def apply(self, state: LayoutState) -> LayoutState:
        new_state = state.clone()
        
        # Find element and adjust spacing
        for page in new_state.pages:
            for i, box in enumerate(page.boxes):
                if box == self.element:
                    # Adjust position of subsequent elements
                    spacing_increase = self.target_spacing - self._current_spacing(box, page)
                    
                    for j in range(i + 1, len(page.boxes)):
                        page.boxes[j].y -= spacing_increase
                    
                    break
        
        return new_state

class PullLineFromPreviousPageAdjustment(Adjustment):
    """Pull one more line from previous page to fix widow"""
    
    def __init__(self, element: LayoutBox):
        self.element = element
    
    def apply(self, state: LayoutState) -> LayoutState:
        # Complex: need to re-layout paragraph with different break point
        pass
```

### Layer 4: Constraint Solver

```python
class ConstraintSolver:
    """Iteratively resolves layout constraints"""
    
    def __init__(self, rules: List[LayoutRule], max_iterations: int = 10):
        self.rules = rules
        self.max_iterations = max_iterations
    
    def solve(self, initial_state: LayoutState) -> LayoutState:
        """
        Iteratively apply rules until all constraints satisfied.
        
        Returns:
            Final layout state with all constraints satisfied
        """
        current_state = initial_state
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # Check all rules
            violations = self._check_all_rules(current_state)
            
            if not violations:
                # No violations - we're done!
                print(f"Layout converged in {iteration} iterations")
                return current_state
            
            # Sort violations by severity
            violations.sort(key=lambda v: (
                v.severity.value,  # ERROR > WARNING > INFO
                v.page              # Earlier pages first
            ))
            
            # Generate adjustments for violations
            adjustments = self._generate_adjustments(violations, current_state)
            
            if not adjustments:
                # No adjustments possible - accept current state
                print(f"No more adjustments possible, {len(violations)} violations remain")
                return current_state
            
            # Apply adjustments and regenerate layout
            generator = LayoutGenerator()
            current_state = generator.regenerate_with_adjustments(
                current_state, 
                adjustments
            )
        
        print(f"Max iterations ({self.max_iterations}) reached")
        return current_state
    
    def _check_all_rules(self, state: LayoutState) -> List[Violation]:
        """Check all rules and collect violations"""
        violations = []
        
        for rule in self.rules:
            rule_violations = rule.check(state)
            violations.extend(rule_violations)
        
        return violations
    
    def _generate_adjustments(self, violations: List[Violation], 
                             state: LayoutState) -> List[Adjustment]:
        """Generate adjustments to fix violations"""
        adjustments = []
        
        # Take top N violations (don't try to fix everything at once)
        for violation in violations[:5]:  # Fix top 5 per iteration
            # Ask rule for suggested fix
            for rule in self.rules:
                if rule.__class__.__name__.replace('Rule', '').lower() in violation.rule_name:
                    suggested = rule.suggest_fix(violation, state)
                    adjustments.extend(suggested)
                    break
        
        return adjustments
```

### Layer 5: Integration with Renderer

```python
class ProfessionalPDFRenderer:
    """PDF renderer with constraint-based layout"""
    
    def __init__(self):
        # ... existing initialization ...
        
        # Layout system
        self.layout_generator = LayoutGenerator()
        self.constraint_solver = ConstraintSolver(rules=[
            NoOverflowRule(),
            NoOrphanLinesRule(),
            NoWidowLinesRule(),
            MinimumSpacingRule(min_spacing=6.0)
        ])
    
    def render(self, doc: Document, config: dict = None) -> bytes:
        """Render document with constraint-based layout"""
        
        # 1. Generate initial layout
        print("Generating initial layout...")
        initial_state = self.layout_generator.generate_initial_layout(
            doc, 
            self._create_layout_config(config)
        )
        
        # 2. Solve constraints iteratively
        print("Resolving layout constraints...")
        final_state = self.constraint_solver.solve(initial_state)
        
        # 3. Render final layout to PDF
        print("Rendering to PDF...")
        pdf_bytes = self._render_layout_state_to_pdf(final_state)
        
        return pdf_bytes
    
    def _render_layout_state_to_pdf(self, state: LayoutState) -> bytes:
        """Convert final layout state to PDF commands"""
        # Reset PDF state
        self.objects = []
        self.pages = [[] for _ in state.pages]
        
        # Render each page
        for page_idx, page in enumerate(state.pages):
            self.current_page = page_idx
            
            for box in page.boxes:
                self._render_box_to_pdf(box)
        
        # Generate PDF file
        return self._generate_professional_pdf()
    
    def _render_box_to_pdf(self, box: LayoutBox):
        """Render a layout box to PDF commands"""
        if box.box_type == BoxType.PARAGRAPH:
            para_layout = box.content
            self._render_paragraph_layout_v2(para_layout)
        elif box.box_type == BoxType.HEADING:
            # Render heading
            pass
        # ... other box types ...
```

## Usage Example

```python
# Create document
doc = parser.parse(markdown_text)

# Create renderer with rules
renderer = ProfessionalPDFRenderer()

# Add custom rules
renderer.constraint_solver.rules.append(
    CustomSpacingRule(min_spacing=12.0)
)

# Render with constraint solving
pdf_bytes = renderer.render(doc)

# Output will show:
# Generating initial layout...
# Resolving layout constraints...
#   Iteration 1: Found 5 violations (3 orphans, 2 spacing)
#   Iteration 2: Found 2 violations (1 widow, 1 spacing)
#   Iteration 3: Found 0 violations
# Layout converged in 3 iterations
# Rendering to PDF...
```

## Benefits

### 1. Separation of Concerns

- **Layout Generation**: Pure calculation
- **Constraint Checking**: Independent rules
- **Adjustment Application**: Modular fixes
- **Rendering**: Final conversion

### 2. Extensibility

Add new rules easily:

```python
class NoShortLastLineRule(LayoutRule):
    """Prevent very short last line in paragraph"""
    
    def check(self, state: LayoutState) -> List[Violation]:
        # Check if last line < 30% of line width
        pass
    
    def suggest_fix(self, violation: Violation, 
                    state: LayoutState) -> List[Adjustment]:
        # Adjust line breaking to pull more text to last line
        return [AdjustLineBreakingAdjustment(violation.element)]
```

### 3. Testability

Test rules independently:

```python
def test_orphan_rule():
    rule = NoOrphanLinesRule()
    
    # Create state with orphan
    state = create_test_state_with_orphan()
    
    # Check rule
    violations = rule.check(state)
    assert len(violations) == 1
    assert violations[0].rule_name == "no_orphan_lines"
    
    # Test fix
    adjustments = rule.suggest_fix(violations[0], state)
    new_state = adjustments[0].apply(state)
    
    # Verify fix
    violations_after = rule.check(new_state)
    assert len(violations_after) == 0
```

### 4. Debuggability

Track iterations:

```python
class ConstraintSolver:
    def solve(self, initial_state: LayoutState) -> LayoutState:
        history = []
        
        for iteration in range(self.max_iterations):
            violations = self._check_all_rules(current_state)
            
            history.append({
                'iteration': iteration,
                'violations': len(violations),
                'details': violations
            })
            
            if not violations:
                self._print_history(history)
                return current_state
            
            # ... continue solving ...
```

## Advanced Features

### 1. Constraint Priorities

```python
class LayoutRule(ABC):
    priority: int = 0  # Higher = more important
    
class NoOverflowRule(LayoutRule):
    priority = 100  # Must fix
    
class NoOrphanLinesRule(LayoutRule):
    priority = 50  # Should fix
    
class MinimumSpacingRule(LayoutRule):
    priority = 10  # Nice to fix
```

### 2. Conflict Resolution

```python
class ConstraintSolver:
    def _resolve_conflicts(self, adjustments: List[Adjustment]) -> List[Adjustment]:
        """Remove conflicting adjustments"""
        # If two adjustments affect same element, keep higher priority
        pass
```

### 3. Optimization

```python
class ConstraintSolver:
    def _optimize_layout(self, state: LayoutState) -> LayoutState:
        """
        After constraints satisfied, optimize for aesthetics:
        - Balance page fullness
        - Minimize hyphenation
        - Optimize spacing
        """
        pass
```

### 4. Caching

```python
class LayoutGenerator:
    @lru_cache(maxsize=1000)
    def _layout_element_cached(self, element_hash: str, 
                               constraints: tuple) -> LayoutBox:
        """Cache element layouts for repeated content"""
        pass
```

## Summary

The constraint-based architecture provides:

✅ **Iterative refinement** - Layout improves each iteration
✅ **Modular rules** - Easy to add/remove/test rules
✅ **Separation of concerns** - Layout, rules, adjustments separate
✅ **Professional typography** - Widow/orphan prevention, spacing, etc.
✅ **Debuggable** - Track iterations and violations
✅ **Testable** - Test rules independently
✅ **Extensible** - Add custom rules easily

This is the foundation for professional-quality typesetting with sophisticated layout rules.
