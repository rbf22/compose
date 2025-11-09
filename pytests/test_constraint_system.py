"""
Tests for the constraint-based layout system.

Tests the iterative constraint solving pipeline.
"""

import pytest
from compose.render.constraint_primitives import (
    LayoutState, Violation, Severity, Adjustment
)
from compose.render.layout_primitives import (
    LayoutBox, PageLayout, BoxType, LineLayout, TextRun
)
from compose.render.layout_rules import (
    NoOverflowRule, MinimumSpacingRule, NoOrphanLinesRule, NoWidowLinesRule
)
from compose.render.layout_adjustments import (
    MoveToNextPageAdjustment, IncreaseSpacingAdjustment
)
from compose.render.constraint_solver import ConstraintSolver
from compose.render.layout_generator import LayoutGenerator


class TestLayoutState:
    """Test LayoutState immutability and cloning"""
    
    def test_layout_state_creation(self):
        """Test creating a layout state"""
        page = PageLayout(page_number=0, width=612, height=792)
        state = LayoutState(
            pages=[page],
            current_page=0,
            current_y=720,
            elements=[]
        )
        
        assert state.current_page == 0
        assert state.current_y == 720
        assert len(state.pages) == 1
        assert state.iteration == 0
    
    def test_layout_state_clone(self):
        """Test cloning a layout state"""
        page = PageLayout(page_number=0, width=612, height=792)
        box = LayoutBox(BoxType.PARAGRAPH, 72, 720, 468, 100)
        page.add_box(box)
        
        state = LayoutState(
            pages=[page],
            current_page=0,
            current_y=620,
            elements=[box]
        )
        
        # Clone state
        cloned = state.clone()
        
        # Should be different objects
        assert cloned is not state
        assert cloned.pages is not state.pages
        assert cloned.iteration == 1
        
        # But same values
        assert cloned.current_page == state.current_page
        assert cloned.current_y == state.current_y
        assert len(cloned.pages) == len(state.pages)
    
    def test_find_element(self):
        """Test finding element in state"""
        page = PageLayout(page_number=0, width=612, height=792)
        box1 = LayoutBox(BoxType.PARAGRAPH, 72, 720, 468, 100)
        box2 = LayoutBox(BoxType.HEADING, 72, 600, 468, 50)
        page.add_box(box1)
        page.add_box(box2)
        
        state = LayoutState(pages=[page], current_page=0, current_y=550, elements=[])
        
        # Find boxes
        page_idx, box_idx = state.find_element(box1)
        assert page_idx == 0
        assert box_idx == 0
        
        page_idx, box_idx = state.find_element(box2)
        assert page_idx == 0
        assert box_idx == 1
        
        # Find non-existent box
        box3 = LayoutBox(BoxType.PARAGRAPH, 0, 0, 0, 0)
        page_idx, box_idx = state.find_element(box3)
        assert page_idx is None
        assert box_idx is None


class TestNoOverflowRule:
    """Test the no overflow rule"""
    
    def test_no_overflow_rule_passes(self):
        """Test rule passes when no overflow"""
        page = PageLayout(page_number=0, width=612, height=792)
        box = LayoutBox(BoxType.PARAGRAPH, 72, 720, 468, 100)
        page.add_box(box)
        
        state = LayoutState(pages=[page], current_page=0, current_y=620, elements=[])
        
        rule = NoOverflowRule()
        violations = rule.check(state)
        
        assert len(violations) == 0
    
    def test_no_overflow_rule_detects_overflow(self):
        """Test rule detects overflow"""
        page = PageLayout(page_number=0, width=612, height=792)
        # Box extends below page bottom (72)
        box = LayoutBox(BoxType.PARAGRAPH, 72, 720, 468, 700)
        page.add_box(box)
        
        state = LayoutState(pages=[page], current_page=0, current_y=20, elements=[])
        
        rule = NoOverflowRule()
        violations = rule.check(state)
        
        assert len(violations) == 1
        assert violations[0].severity == Severity.ERROR
        assert violations[0].rule_name == "no_overflow"
    
    def test_overflow_rule_suggests_fix(self):
        """Test rule suggests moving to next page"""
        page = PageLayout(page_number=0, width=612, height=792)
        box = LayoutBox(BoxType.PARAGRAPH, 72, 720, 468, 700)
        page.add_box(box)
        
        state = LayoutState(pages=[page], current_page=0, current_y=20, elements=[])
        
        rule = NoOverflowRule()
        violations = rule.check(state)
        
        adjustments = rule.suggest_fix(violations[0], state)
        
        assert len(adjustments) == 1
        assert isinstance(adjustments[0], MoveToNextPageAdjustment)


class TestMinimumSpacingRule:
    """Test the minimum spacing rule"""
    
    def test_spacing_rule_passes(self):
        """Test rule passes when spacing adequate"""
        page = PageLayout(page_number=0, width=612, height=792)
        box1 = LayoutBox(BoxType.PARAGRAPH, 72, 720, 468, 100)
        box2 = LayoutBox(BoxType.PARAGRAPH, 72, 600, 468, 100)
        page.add_box(box1)
        page.add_box(box2)
        
        state = LayoutState(pages=[page], current_page=0, current_y=500, elements=[])
        
        rule = MinimumSpacingRule(min_spacing=6.0)
        violations = rule.check(state)
        
        assert len(violations) == 0
    
    def test_spacing_rule_detects_violation(self):
        """Test rule detects insufficient spacing"""
        page = PageLayout(page_number=0, width=612, height=792)
        box1 = LayoutBox(BoxType.PARAGRAPH, 72, 720, 468, 100)
        box2 = LayoutBox(BoxType.PARAGRAPH, 72, 615, 468, 100)  # Only 5pt spacing
        page.add_box(box1)
        page.add_box(box2)
        
        state = LayoutState(pages=[page], current_page=0, current_y=515, elements=[])
        
        rule = MinimumSpacingRule(min_spacing=6.0)
        violations = rule.check(state)
        
        assert len(violations) == 1
        assert violations[0].severity == Severity.INFO
        assert violations[0].rule_name == "minimum_spacing"


class TestMoveToNextPageAdjustment:
    """Test moving elements to next page"""
    
    def test_move_to_next_page(self):
        """Test moving element to next page"""
        page1 = PageLayout(page_number=0, width=612, height=792)
        box = LayoutBox(BoxType.PARAGRAPH, 72, 720, 468, 100)
        page1.add_box(box)
        
        state = LayoutState(pages=[page1], current_page=0, current_y=620, elements=[])
        
        # Apply adjustment
        adjustment = MoveToNextPageAdjustment(box)
        new_state = adjustment.apply(state, None)
        
        # Box should be removed from page 1
        assert len(new_state.pages[0].boxes) == 0
        
        # Box should be on page 2
        assert len(new_state.pages) == 2
        assert len(new_state.pages[1].boxes) == 1
        assert new_state.pages[1].boxes[0].y == new_state.pages[1].content_top
    
    def test_move_creates_new_page_if_needed(self):
        """Test that adjustment creates new page if needed"""
        page = PageLayout(page_number=0, width=612, height=792)
        box = LayoutBox(BoxType.PARAGRAPH, 72, 720, 468, 100)
        page.add_box(box)
        
        state = LayoutState(pages=[page], current_page=0, current_y=620, elements=[])
        
        assert len(state.pages) == 1
        
        adjustment = MoveToNextPageAdjustment(box)
        new_state = adjustment.apply(state, None)
        
        assert len(new_state.pages) == 2


class TestConstraintSolver:
    """Test the constraint solver"""
    
    def test_solver_with_no_violations(self):
        """Test solver when no violations"""
        page = PageLayout(page_number=0, width=612, height=792)
        box = LayoutBox(BoxType.PARAGRAPH, 72, 720, 468, 100)
        page.add_box(box)
        
        state = LayoutState(pages=[page], current_page=0, current_y=620, elements=[])
        
        solver = ConstraintSolver(rules=[NoOverflowRule()], verbose=False)
        final_state = solver.solve(state, None)
        
        assert final_state == state
        assert len(solver.iteration_history) == 1
        assert solver.iteration_history[0]['violations'] == 0
    
    def test_solver_detects_and_suggests_fixes(self):
        """Test solver detects violations and suggests fixes"""
        page = PageLayout(page_number=0, width=612, height=792)
        # Box overflows
        box = LayoutBox(BoxType.PARAGRAPH, 72, 720, 468, 700)
        page.add_box(box)
        
        state = LayoutState(pages=[page], current_page=0, current_y=20, elements=[])
        
        # Create mock generator that just clones
        class MockGenerator:
            def regenerate_with_adjustments(self, state, adjustments):
                return state.clone()
        
        solver = ConstraintSolver(rules=[NoOverflowRule()], verbose=False)
        final_state = solver.solve(state, MockGenerator())
        
        # Should have detected violations
        assert len(solver.iteration_history) >= 1
        assert solver.iteration_history[0]['violations'] > 0
    
    def test_solver_respects_max_iterations(self):
        """Test solver respects max iterations"""
        page = PageLayout(page_number=0, width=612, height=792)
        box = LayoutBox(BoxType.PARAGRAPH, 72, 720, 468, 700)
        page.add_box(box)
        
        state = LayoutState(pages=[page], current_page=0, current_y=20, elements=[])
        
        # Create generator that doesn't fix violations
        class BadGenerator:
            def regenerate_with_adjustments(self, state, adjustments):
                return state.clone()  # No actual changes
        
        solver = ConstraintSolver(
            rules=[NoOverflowRule()],
            max_iterations=3,
            verbose=False
        )
        final_state = solver.solve(state, BadGenerator())
        
        # Should have tried max iterations (or stopped early if no adjustments)
        assert len(solver.iteration_history) <= 3
        # Should still have violations since generator didn't fix them
        final_violations = solver._check_all_rules(final_state)
        assert len(final_violations) > 0


class TestLayoutGenerator:
    """Test the layout generator"""
    
    @pytest.fixture
    def font_metrics(self):
        """Sample font metrics"""
        return {
            "Helvetica": {
                "ascent": 770,
                "descent": -230,
                "line_gap": 20,
                "units_per_em": 1000,
                "glyph_widths": {chr(i): 4.4 for i in range(32, 127)}
            }
        }
    
    @pytest.fixture
    def page_config(self):
        """Sample page config"""
        return {
            'width': 612,
            'height': 792,
            'margin_left': 72,
            'margin_right': 72,
            'margin_top': 72,
            'margin_bottom': 72,
            'font': 'Helvetica',
            'font_size': 12,
            'line_height_factor': 1.2
        }
    
    def test_generator_creates_initial_layout(self, font_metrics, page_config):
        """Test generator creates initial layout"""
        from compose.model.ast import Document, Paragraph, Text
        
        doc = Document(
            frontmatter={},
            blocks=[
                Paragraph(content=[Text(content="Hello World")])
            ]
        )
        
        generator = LayoutGenerator(font_metrics, page_config)
        state = generator.generate_initial_layout(doc)
        
        assert len(state.pages) >= 1
        assert len(state.elements) >= 1
        assert state.elements[0].box_type == BoxType.PARAGRAPH
    
    def test_generator_handles_multiple_paragraphs(self, font_metrics, page_config):
        """Test generator handles multiple paragraphs"""
        from compose.model.ast import Document, Paragraph, Text
        
        doc = Document(
            frontmatter={},
            blocks=[
                Paragraph(content=[Text(content="Paragraph 1")]),
                Paragraph(content=[Text(content="Paragraph 2")]),
                Paragraph(content=[Text(content="Paragraph 3")])
            ]
        )
        
        generator = LayoutGenerator(font_metrics, page_config)
        state = generator.generate_initial_layout(doc)
        
        assert len(state.elements) == 3
        for elem in state.elements:
            assert elem.box_type == BoxType.PARAGRAPH


class TestIntegration:
    """Integration tests for the full constraint system"""
    
    def test_full_pipeline(self):
        """Test full constraint solving pipeline"""
        from compose.model.ast import Document, Paragraph, Text
        
        # Create document
        doc = Document(
            frontmatter={},
            blocks=[
                Paragraph(content=[Text(content="Test paragraph")])
            ]
        )
        
        # Setup
        font_metrics = {
            "Helvetica": {
                "ascent": 770,
                "descent": -230,
                "line_gap": 20,
                "units_per_em": 1000,
                "glyph_widths": {chr(i): 4.4 for i in range(32, 127)}
            }
        }
        
        page_config = {
            'width': 612,
            'height': 792,
            'margin_left': 72,
            'margin_right': 72,
            'margin_top': 72,
            'margin_bottom': 72
        }
        
        # Generate layout
        generator = LayoutGenerator(font_metrics, page_config)
        initial_state = generator.generate_initial_layout(doc)
        
        # Solve constraints
        solver = ConstraintSolver(
            rules=[NoOverflowRule(), MinimumSpacingRule()],
            verbose=False
        )
        final_state = solver.solve(initial_state, generator)
        
        # Verify result
        assert final_state is not None
        assert len(final_state.pages) >= 1
        
        # Check no violations
        violations = solver._check_all_rules(final_state)
        assert len(violations) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
