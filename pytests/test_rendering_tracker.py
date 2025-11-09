"""
Tests for the RenderingTracker and overlap detection using strict AABB algorithm.
"""

import pytest
from compose.render.rendering_tracker import RenderingTracker, RenderedContent, ContentType


class TestStrictAABBOverlapDetection:
    """Test the strict AABB overlap detection algorithm"""
    
    def test_true_overlap(self):
        """Test case where boxes truly overlap"""
        # Box A: [0, 2] x [0, 2]
        box_a = RenderedContent(
            content_type=ContentType.TEXT,
            x=0, y=2, width=2, height=2,
            page=0
        )
        # Box B: [1, 3] x [1, 3]
        box_b = RenderedContent(
            content_type=ContentType.TEXT,
            x=1, y=3, width=2, height=2,
            page=0
        )
        
        # They overlap in the region [1, 2] x [1, 2]
        assert box_a.overlaps_with(box_b), "Boxes should overlap"
    
    def test_adjacent_shared_edge(self):
        """Test case where boxes share an edge but don't overlap"""
        # Box A: [0, 1] x [0, 1]
        box_a = RenderedContent(
            content_type=ContentType.TEXT,
            x=0, y=1, width=1, height=1,
            page=0
        )
        # Box B: [1, 2] x [0, 1] - shares right edge of A
        box_b = RenderedContent(
            content_type=ContentType.TEXT,
            x=1, y=1, width=1, height=1,
            page=0
        )
        
        # They should NOT overlap (shared edge doesn't count)
        assert not box_a.overlaps_with(box_b), "Adjacent boxes with shared edge should not overlap"
    
    def test_corner_share(self):
        """Test case where boxes share a corner but don't overlap"""
        # Box A: [0, 1] x [0, 1]
        box_a = RenderedContent(
            content_type=ContentType.TEXT,
            x=0, y=1, width=1, height=1,
            page=0
        )
        # Box B: [1, 2] x [1, 2] - shares corner with A
        box_b = RenderedContent(
            content_type=ContentType.TEXT,
            x=1, y=2, width=1, height=1,
            page=0
        )
        
        # They should NOT overlap (shared corner doesn't count)
        assert not box_a.overlaps_with(box_b), "Adjacent boxes with shared corner should not overlap"
    
    def test_no_overlap_separated(self):
        """Test case where boxes are completely separated"""
        # Box A: [0, 1] x [0, 1]
        box_a = RenderedContent(
            content_type=ContentType.TEXT,
            x=0, y=1, width=1, height=1,
            page=0
        )
        # Box B: [2, 3] x [2, 3] - completely separated
        box_b = RenderedContent(
            content_type=ContentType.TEXT,
            x=2, y=3, width=1, height=1,
            page=0
        )
        
        # They should NOT overlap
        assert not box_a.overlaps_with(box_b), "Separated boxes should not overlap"
    
    def test_different_pages_no_overlap(self):
        """Test that boxes on different pages don't overlap"""
        box_a = RenderedContent(
            content_type=ContentType.TEXT,
            x=0, y=1, width=1, height=1,
            page=0
        )
        box_b = RenderedContent(
            content_type=ContentType.TEXT,
            x=0, y=1, width=1, height=1,
            page=1
        )
        
        # Same coordinates but different pages - should NOT overlap
        assert not box_a.overlaps_with(box_b), "Boxes on different pages should not overlap"
    
    def test_one_box_inside_another(self):
        """Test case where one box is completely inside another"""
        # Box A: [0, 10] x [0, 10]
        box_a = RenderedContent(
            content_type=ContentType.TEXT,
            x=0, y=10, width=10, height=10,
            page=0
        )
        # Box B: [2, 5] x [2, 5] - completely inside A
        box_b = RenderedContent(
            content_type=ContentType.TEXT,
            x=2, y=5, width=3, height=3,
            page=0
        )
        
        # They should overlap
        assert box_a.overlaps_with(box_b), "Box inside another should overlap"
        assert box_b.overlaps_with(box_a), "Overlap should be symmetric"


class TestRenderingTrackerValidation:
    """Test the RenderingTracker validation system"""
    
    def test_content_within_margins(self):
        """Test that content within margins passes validation"""
        tracker = RenderingTracker()
        
        # Record content well within margins
        tracker.record_text(x=100, y=700, width=100, height=12, page=0)
        
        # Validate (page 792x612, margins 60 all around)
        errors = tracker.validate_all(
            page_height=792, page_width=612,
            margin_top=60, margin_bottom=60,
            margin_left=60, margin_right=60
        )
        
        # Should have no errors
        assert len(errors) == 0, f"Expected no errors, got: {errors}"
    
    def test_content_outside_left_margin(self):
        """Test detection of content outside left margin"""
        tracker = RenderingTracker()
        
        # Record content that extends past left margin (50 < 60)
        tracker.record_text(x=50, y=700, width=100, height=12, page=0)
        
        errors = tracker.validate_all(
            page_height=792, page_width=612,
            margin_top=60, margin_bottom=60,
            margin_left=60, margin_right=60
        )
        
        # Should have error about left margin
        assert any("left" in error.lower() for error in errors), f"Expected left margin error, got: {errors}"
    
    def test_adjacent_items_no_overlap(self):
        """Test that adjacent items with shared edge don't overlap (strict AABB)"""
        tracker = RenderingTracker()
        
        # Record two adjacent text items that share an edge
        # Item 1: x=100, width=50, so x2=150
        tracker.record_text(x=100, y=700, width=50, height=12, page=0, label="item1")
        
        # Item 2: x=150, width=50, so x2=200
        # They share an edge at x=150, but should NOT overlap (strict AABB)
        tracker.record_text(x=150, y=700, width=50, height=12, page=0, label="item2")
        
        errors = tracker.validate_all(
            page_height=792, page_width=612,
            margin_top=60, margin_bottom=60,
            margin_left=60, margin_right=60
        )
        
        # Should have no overlap errors (strict AABB allows shared edges)
        overlap_errors = [e for e in errors if "overlap" in e.lower()]
        assert len(overlap_errors) == 0, f"Expected no overlap errors, got: {overlap_errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
