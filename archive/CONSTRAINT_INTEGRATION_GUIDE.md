# Integrating Constraint-Based Layout with Refactored Architecture

## Overview

This guide shows how to integrate the constraint-based layout system with the refactored layout/rendering architecture we just created.

## Architecture Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Document AST                          │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Layout Generator (Stateless)                │
│  - Uses TextLayoutEngine                                 │
│  - Produces LayoutState (immutable)                      │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Constraint Solver (Iterative)               │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Loop:                                           │   │
│  │    1. Check Rules → Violations                   │   │
│  │    2. Generate Adjustments                       │   │
│  │    3. Apply Adjustments → New LayoutState        │   │
│  │    4. Repeat until converged                     │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              PDF Renderer (Pure Conversion)              │
│  - Converts LayoutState to PDF commands                  │
│  - No calculation, just conversion                       │
└─────────────────────────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Extend Layout Primitives

Add constraint-aware metadata to existing structures:

```python
# In layout_primitives.py

@dataclass
class LayoutBox:
    """Generic layout box with constraint metadata"""
    box_type: BoxType
    x: float
    y: float
    width: float
    height: float
    content: Any = None
    children: List['LayoutBox'] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    # NEW: Constraint-related fields
    constraints: List[str] = field(default_factory=list)  # Applied constraints
    adjustments: List[str] = field(default_factory=list)  # Applied adjustments
    
    def add_constraint(self, constraint_name: str):
        """Mark that a constraint applies to this box"""
        if constraint_name not in self.constraints:
            self.constraints.append(constraint_name)
    
    def add_adjustment(self, adjustment_name: str):
        """Mark that an adjustment was applied"""
        if adjustment_name not in self.adjustments:
            self.adjustments.append(adjustment_name)

@dataclass
class LayoutState:
    """Complete layout state for constraint solving"""
    pages: List[PageLayout]
    current_page: int
    current_y: float
    elements: List[LayoutBox]
    metadata: Dict[str, Any] = field(default_factory=dict)
    iteration: int = 0  # Which iteration produced this state
    
    def clone(self) -> 'LayoutState':
        """Create deep copy for iteration"""
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
            content=box.content,  # Content is immutable
            children=[self._clone_box(c) for c in box.children],
            metadata=dict(box.metadata),
            constraints=list(box.constraints),
            adjustments=list(box.adjustments)
        )
```

### Step 2: Create Layout Generator

Wraps existing layout methods to produce LayoutState:

```python
# In compose/render/layout_generator.py

from typing import List
from ..model.ast import Document, Paragraph, Heading
from .layout_primitives import LayoutState, PageLayout, LayoutBox
from .text_layout_engine import TextLayoutEngine

class LayoutGenerator:
    """
    Generates layout state from document AST.
    
    Uses the refactored TextLayoutEngine and layout primitives.
    """
    
    def __init__(self, font_metrics: dict, page_config: dict):
        self.text_engine = TextLayoutEngine(font_metrics)
        self.page_config = page_config
        
        # Page dimensions
        self.page_width = page_config.get('width', 612)
        self.page_height = page_config.get('height', 792)
        self.margin_left = page_config.get('margin_left', 72)
        self.margin_right = page_config.get('margin_right', 72)
        self.margin_top = page_config.get('margin_top', 72)
        self.margin_bottom = page_config.get('margin_bottom', 72)
    
    def generate_initial_layout(self, doc: Document) -> LayoutState:
        """
        Generate initial layout without constraint checking.
        
        This uses the refactored layout methods to create a naive layout.
        """
        # Create initial state
        state = LayoutState(
            pages=[self._create_page(0)],
            current_page=0,
            current_y=self.page_height - self.margin_top,
            elements=[],
            metadata={'doc_title': getattr(doc, 'title', 'Untitled')}
        )
        
        # Layout each block
        for block in doc.blocks:
            state = self._layout_block(block, state)
        
        return state
    
    def _create_page(self, page_number: int) -> PageLayout:
        """Create a new page"""
        return PageLayout(
            page_number=page_number,
            width=self.page_width,
            height=self.page_height,
            margin_top=self.margin_top,
            margin_bottom=self.margin_bottom,
            margin_left=self.margin_left,
            margin_right=self.margin_right
        )
    
    def _layout_block(self, block, state: LayoutState) -> LayoutState:
        """Layout a single block element"""
        if isinstance(block, Paragraph):
            return self._layout_paragraph(block, state)
        elif isinstance(block, Heading):
            return self._layout_heading(block, state)
        # ... other block types ...
        
        return state
    
    def _layout_paragraph(self, paragraph: Paragraph, 
                         state: LayoutState) -> LayoutState:
        """
        Layout paragraph using refactored architecture.
        
        This uses the TextLayoutEngine we created earlier.
        """
        # Extract text
        text = self._extract_text_content(paragraph.content)
        
        if not text.strip():
            return state
        
        # Calculate layout using TextLayoutEngine
        max_width = self.page_width - self.margin_left - self.margin_right
        
        line_layouts = self.text_engine.layout_wrapped_text(
            text=text,
            x=self.margin_left,
            y=state.current_y,
            max_width=max_width,
            font="Helvetica",
            size=12,
            line_height_factor=1.2
        )
        
        # Calculate total height
        total_height = sum(line.height for line in line_layouts)
        
        # Create paragraph layout box
        para_box = LayoutBox(
            box_type=BoxType.PARAGRAPH,
            x=self.margin_left,
            y=state.current_y,
            width=max_width,
            height=total_height,
            content=line_layouts,
            metadata={'text': text}
        )
        
        # Check if fits on current page
        current_page = state.pages[state.current_page]
        
        if not current_page.has_space_for(total_height, state.current_y):
            # Need new page
            state = self._add_new_page(state)
            
            # Recalculate position for new page
            para_box.y = state.current_y
            line_layouts = self.text_engine.layout_wrapped_text(
                text=text,
                x=self.margin_left,
                y=state.current_y,
                max_width=max_width,
                font="Helvetica",
                size=12,
                line_height_factor=1.2
            )
            para_box.content = line_layouts
        
        # Add to current page
        state.pages[state.current_page].add_box(para_box)
        state.elements.append(para_box)
        
        # Update position
        state.current_y -= total_height + 6  # 6pt spacing
        
        return state
    
    def _add_new_page(self, state: LayoutState) -> LayoutState:
        """Add a new page to state"""
        new_page = self._create_page(len(state.pages))
        state.pages.append(new_page)
        state.current_page = len(state.pages) - 1
        state.current_y = self.page_height - self.margin_top
        return state
    
    def _extract_text_content(self, elements) -> str:
        """Extract plain text from inline elements"""
        # Simple implementation - would need to handle formatting
        text_parts = []
        for elem in elements:
            if hasattr(elem, 'content'):
                text_parts.append(str(elem.content))
            else:
                text_parts.append(str(elem))
        return ''.join(text_parts)
    
    def regenerate_with_adjustments(self, state: LayoutState,
                                   adjustments: List['Adjustment']) -> LayoutState:
        """
        Apply adjustments and regenerate layout.
        
        This is where the iterative refinement happens.
        """
        new_state = state.clone()
        
        # Apply each adjustment
        for adjustment in adjustments:
            new_state = adjustment.apply(new_state, self)
        
        return new_state
```

### Step 3: Implement Simple Rules

Start with basic rules:

```python
# In compose/render/layout_rules.py

from typing import List
from abc import ABC, abstractmethod
from .layout_primitives import LayoutState, LayoutBox, BoxType, Violation, Severity

class LayoutRule(ABC):
    """Base class for layout rules"""
    
    @abstractmethod
    def check(self, state: LayoutState) -> List[Violation]:
        """Check rule and return violations"""
        pass
    
    @abstractmethod
    def suggest_fix(self, violation: Violation, 
                    state: LayoutState) -> List['Adjustment']:
        """Suggest fixes for violation"""
        pass

class NoOverflowRule(LayoutRule):
    """Prevent content from overflowing page boundaries"""
    
    def check(self, state: LayoutState) -> List[Violation]:
        violations = []
        
        for page_idx, page in enumerate(state.pages):
            for box in page.boxes:
                # Check vertical overflow
                if box.bottom < page.content_bottom:
                    violations.append(Violation(
                        rule_name="no_overflow",
                        severity=Severity.ERROR,
                        element=box,
                        page=page_idx,
                        description=f"Element overflows page bottom by {page.content_bottom - box.bottom:.1f}pt"
                    ))
        
        return violations
    
    def suggest_fix(self, violation: Violation, 
                    state: LayoutState) -> List['Adjustment']:
        """Move element to next page"""
        from .layout_adjustments import MoveToNextPageAdjustment
        return [MoveToNextPageAdjustment(violation.element)]

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
                
                # Calculate spacing
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
                    state: LayoutState) -> List['Adjustment']:
        """Increase spacing"""
        from .layout_adjustments import IncreaseSpacingAdjustment
        return [IncreaseSpacingAdjustment(
            violation.element,
            self.min_spacing
        )]
```

### Step 4: Implement Adjustments

```python
# In compose/render/layout_adjustments.py

from abc import ABC, abstractmethod
from .layout_primitives import LayoutState, LayoutBox

class Adjustment(ABC):
    """Base class for layout adjustments"""
    
    @abstractmethod
    def apply(self, state: LayoutState, generator: 'LayoutGenerator') -> LayoutState:
        """Apply adjustment to state"""
        pass

class MoveToNextPageAdjustment(Adjustment):
    """Move an element to the next page"""
    
    def __init__(self, element: LayoutBox):
        self.element = element
    
    def apply(self, state: LayoutState, generator: 'LayoutGenerator') -> LayoutState:
        """Move element to next page"""
        # Find element
        for page_idx, page in enumerate(state.pages):
            try:
                box_idx = page.boxes.index(self.element)
                
                # Remove from current page
                page.boxes.pop(box_idx)
                
                # Ensure next page exists
                if page_idx + 1 >= len(state.pages):
                    new_page = generator._create_page(len(state.pages))
                    state.pages.append(new_page)
                
                # Add to next page
                next_page = state.pages[page_idx + 1]
                
                # Recalculate position
                new_y = next_page.content_top
                moved_box = LayoutBox(
                    box_type=self.element.box_type,
                    x=self.element.x,
                    y=new_y,
                    width=self.element.width,
                    height=self.element.height,
                    content=self.element.content,
                    children=self.element.children,
                    metadata=self.element.metadata
                )
                moved_box.add_adjustment("moved_to_next_page")
                
                next_page.boxes.insert(0, moved_box)
                
                # Reflow subsequent elements on next page
                current_y = new_y - moved_box.height - 6
                for i, box in enumerate(next_page.boxes[1:], 1):
                    box.y = current_y
                    current_y -= box.height + 6
                
                break
                
            except ValueError:
                continue
        
        return state

class IncreaseSpacingAdjustment(Adjustment):
    """Increase spacing after an element"""
    
    def __init__(self, element: LayoutBox, target_spacing: float):
        self.element = element
        self.target_spacing = target_spacing
    
    def apply(self, state: LayoutState, generator: 'LayoutGenerator') -> LayoutState:
        """Increase spacing by moving subsequent elements down"""
        for page in state.pages:
            try:
                box_idx = page.boxes.index(self.element)
                
                # Calculate spacing increase needed
                if box_idx > 0:
                    prev_box = page.boxes[box_idx - 1]
                    current_spacing = prev_box.bottom - self.element.y
                    spacing_increase = self.target_spacing - current_spacing
                    
                    if spacing_increase > 0:
                        # Move this element and all subsequent down
                        for i in range(box_idx, len(page.boxes)):
                            page.boxes[i].y -= spacing_increase
                        
                        self.element.add_adjustment("spacing_increased")
                
                break
                
            except ValueError:
                continue
        
        return state
```

### Step 5: Create Constraint Solver

```python
# In compose/render/constraint_solver.py

from typing import List
from .layout_primitives import LayoutState, Violation
from .layout_rules import LayoutRule

class ConstraintSolver:
    """Iteratively resolves layout constraints"""
    
    def __init__(self, rules: List[LayoutRule], max_iterations: int = 10):
        self.rules = rules
        self.max_iterations = max_iterations
        self.verbose = True
    
    def solve(self, initial_state: LayoutState, 
             generator: 'LayoutGenerator') -> LayoutState:
        """
        Iteratively apply rules until constraints satisfied.
        
        Returns:
            Final layout state with constraints satisfied
        """
        current_state = initial_state
        
        for iteration in range(self.max_iterations):
            if self.verbose:
                print(f"\nIteration {iteration + 1}:")
            
            # Check all rules
            violations = self._check_all_rules(current_state)
            
            if not violations:
                if self.verbose:
                    print(f"✓ Layout converged - no violations")
                return current_state
            
            if self.verbose:
                self._print_violations(violations)
            
            # Generate adjustments
            adjustments = self._generate_adjustments(violations, current_state)
            
            if not adjustments:
                if self.verbose:
                    print(f"⚠ No adjustments possible, accepting current state")
                return current_state
            
            # Apply adjustments
            current_state = generator.regenerate_with_adjustments(
                current_state,
                adjustments
            )
        
        if self.verbose:
            print(f"\n⚠ Max iterations ({self.max_iterations}) reached")
        
        return current_state
    
    def _check_all_rules(self, state: LayoutState) -> List[Violation]:
        """Check all rules"""
        violations = []
        for rule in self.rules:
            violations.extend(rule.check(state))
        return violations
    
    def _generate_adjustments(self, violations: List[Violation],
                             state: LayoutState) -> List['Adjustment']:
        """Generate adjustments for violations"""
        # Sort by severity
        violations.sort(key=lambda v: (
            0 if v.severity == Severity.ERROR else
            1 if v.severity == Severity.WARNING else 2,
            v.page
        ))
        
        adjustments = []
        
        # Fix top violations
        for violation in violations[:3]:  # Top 3 per iteration
            for rule in self.rules:
                if rule.__class__.__name__.replace('Rule', '').lower() in violation.rule_name:
                    suggested = rule.suggest_fix(violation, state)
                    adjustments.extend(suggested)
                    break
        
        return adjustments
    
    def _print_violations(self, violations: List[Violation]):
        """Print violations summary"""
        by_severity = {}
        for v in violations:
            by_severity.setdefault(v.severity, []).append(v)
        
        for severity in [Severity.ERROR, Severity.WARNING, Severity.INFO]:
            if severity in by_severity:
                count = len(by_severity[severity])
                print(f"  {severity.value.upper()}: {count} violations")
```

### Step 6: Integrate with PDF Renderer

```python
# In pdf_renderer.py - add constraint-based rendering

class ProfessionalPDFRenderer:
    def __init__(self):
        # ... existing initialization ...
        
        # NEW: Constraint-based layout system
        self.use_constraint_layout = True  # Feature flag
        self.layout_generator = None  # Created when needed
        self.constraint_solver = None  # Created when needed
    
    def render(self, doc: Document, config: dict = None) -> bytes:
        """Render with optional constraint-based layout"""
        
        if self.use_constraint_layout:
            return self._render_with_constraints(doc, config)
        else:
            return self._render_legacy(doc, config)
    
    def _render_with_constraints(self, doc: Document, config: dict) -> bytes:
        """Render using constraint-based layout"""
        
        # Create layout system
        page_config = self._extract_page_config(config)
        self.layout_generator = LayoutGenerator(self.font_metrics, page_config)
        self.constraint_solver = ConstraintSolver(rules=[
            NoOverflowRule(),
            MinimumSpacingRule(min_spacing=6.0)
        ])
        
        # 1. Generate initial layout
        print("Generating initial layout...")
        initial_state = self.layout_generator.generate_initial_layout(doc)
        
        # 2. Solve constraints
        print("Resolving constraints...")
        final_state = self.constraint_solver.solve(initial_state, self.layout_generator)
        
        # 3. Render to PDF
        print("Rendering to PDF...")
        return self._render_layout_state(final_state)
    
    def _render_layout_state(self, state: LayoutState) -> bytes:
        """Convert layout state to PDF"""
        # Reset PDF state
        self.objects = []
        self.pages = [[] for _ in state.pages]
        
        # Render each page
        for page_idx, page in enumerate(state.pages):
            self.current_page = page_idx
            
            for box in page.boxes:
                self._render_box(box)
        
        # Generate PDF
        return self._generate_professional_pdf()
    
    def _render_box(self, box: LayoutBox):
        """Render a layout box using refactored methods"""
        if box.box_type == BoxType.PARAGRAPH:
            # Use refactored paragraph rendering
            para_layout = ParagraphLayout(
                lines=box.content,
                x=box.x,
                y=box.y,
                width=box.width,
                height=box.height
            )
            self._render_paragraph_layout_v2(para_layout)
            
            # Draw bounding box if debug enabled
            if self.debug_bounding_boxes:
                self._draw_bounding_box_from_layout(box, self.debug_colors['paragraph'])
```

## Testing Strategy

```python
# test_constraint_layout.py

def test_overflow_rule():
    """Test that overflow rule detects and fixes overflows"""
    # Create state with overflow
    state = create_test_state_with_overflow()
    
    # Check rule
    rule = NoOverflowRule()
    violations = rule.check(state)
    
    assert len(violations) == 1
    assert violations[0].severity == Severity.ERROR
    
    # Apply fix
    adjustments = rule.suggest_fix(violations[0], state)
    generator = LayoutGenerator(test_font_metrics, test_config)
    new_state = generator.regenerate_with_adjustments(state, adjustments)
    
    # Verify fix
    violations_after = rule.check(new_state)
    assert len(violations_after) == 0

def test_constraint_solver_convergence():
    """Test that solver converges"""
    doc = create_test_document()
    generator = LayoutGenerator(test_font_metrics, test_config)
    solver = ConstraintSolver(rules=[NoOverflowRule()])
    
    initial_state = generator.generate_initial_layout(doc)
    final_state = solver.solve(initial_state, generator)
    
    # Should have no violations
    violations = solver._check_all_rules(final_state)
    assert len(violations) == 0
```

## Summary

This integration provides:

✅ **Backward compatible** - Feature flag for gradual adoption
✅ **Uses refactored architecture** - Builds on TextLayoutEngine and layout primitives
✅ **Iterative refinement** - Solves constraints progressively
✅ **Testable** - Each component testable independently
✅ **Extensible** - Easy to add new rules
✅ **Professional typography** - Sophisticated layout rules

The constraint-based system sits on top of the refactored layout/rendering separation, providing iterative refinement while maintaining clean architecture.
