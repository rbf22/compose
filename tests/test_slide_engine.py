# tests/test_slide_engine.py
"""Tests for the slide layout engine."""

from compose.layout.engines.slide_engine import (
    SlideLayoutEngine, SlideTemplate,
    create_simple_slide, create_math_slide, create_diagram_slide
)
from compose.layout import UniversalBox, ContentType, BoxType


def test_slide_template_creation():
    """Test creating slide templates."""
    template = SlideTemplate(
        name="test",
        width=800,
        height=600
    )
    
    assert template.name == "test"
    assert template.width == 800
    assert template.height == 600
    assert template.title_area is not None
    assert template.content_area is not None
    print("✅ test_slide_template_creation passed")


def test_slide_engine_creation():
    """Test creating a slide layout engine."""
    engine = SlideLayoutEngine()
    
    assert engine is not None
    assert len(engine.templates) > 0
    assert 'title' in engine.templates
    assert 'content' in engine.templates
    assert 'two_column' in engine.templates
    print("✅ test_slide_engine_creation passed")


def test_create_basic_slide():
    """Test creating a basic content slide."""
    engine = SlideLayoutEngine()
    
    content = [
        UniversalBox("First point", ContentType.TEXT, BoxType.BLOCK),
        UniversalBox("Second point", ContentType.TEXT, BoxType.BLOCK)
    ]
    
    slide = engine.create_slide('content', title="Test Slide", content=content)
    
    assert slide.content_type == ContentType.SLIDE
    assert slide.box_type == BoxType.FIXED
    assert slide.attributes['template'] == 'content'
    assert slide.attributes['slide_number'] == 1
    assert len(slide.content) >= 3  # title, content items, footer
    print("✅ test_create_basic_slide passed")


def test_create_title_slide():
    """Test creating a title slide."""
    engine = SlideLayoutEngine()
    
    slide = engine.create_title_slide(
        title="Presentation Title",
        subtitle="Subtitle Here",
        author="Author Name"
    )
    
    assert slide.content_type == ContentType.SLIDE
    assert slide.attributes['template'] == 'title'
    assert len(slide.content) >= 3  # title, subtitle, author, footer
    print("✅ test_create_title_slide passed")


def test_create_content_slide():
    """Test creating a content slide."""
    engine = SlideLayoutEngine()
    
    content = [
        UniversalBox("Bullet point 1", ContentType.TEXT, BoxType.BLOCK),
        UniversalBox("Bullet point 2", ContentType.TEXT, BoxType.BLOCK),
        UniversalBox("x^2 + y^2 = z^2", ContentType.MATH, BoxType.BLOCK)
    ]
    
    slide = engine.create_content_slide(
        title="Content Slide",
        content=content,
        speaker_notes="These are speaker notes"
    )
    
    assert slide.attributes['speaker_notes'] == "These are speaker notes"
    assert len(slide.content) >= 4  # title, 3 content items, footer
    print("✅ test_create_content_slide passed")


def test_create_two_column_slide():
    """Test creating a two-column slide."""
    engine = SlideLayoutEngine()
    
    left_content = [
        UniversalBox("Left point 1", ContentType.TEXT, BoxType.BLOCK),
        UniversalBox("Left point 2", ContentType.TEXT, BoxType.BLOCK)
    ]
    
    right_content = [
        UniversalBox("Right point 1", ContentType.TEXT, BoxType.BLOCK),
        UniversalBox("Right point 2", ContentType.TEXT, BoxType.BLOCK)
    ]
    
    slide = engine.create_two_column_slide(
        title="Two Column Slide",
        left_content=left_content,
        right_content=right_content
    )
    
    assert slide.attributes['template'] == 'two_column'
    assert len(slide.content) >= 5  # title, 4 content items, footer
    print("✅ test_create_two_column_slide passed")


def test_slide_numbering():
    """Test slide numbering system."""
    engine = SlideLayoutEngine()
    
    slide1 = engine.create_slide('content', title="Slide 1")
    slide2 = engine.create_slide('content', title="Slide 2")
    slide3 = engine.create_slide('content', title="Slide 3")
    
    assert slide1.attributes['slide_number'] == 1
    assert slide2.attributes['slide_number'] == 2
    assert slide3.attributes['slide_number'] == 3
    assert engine.get_slide_count() == 3
    print("✅ test_slide_numbering passed")


def test_slide_sequence_creation():
    """Test creating a sequence of slides."""
    engine = SlideLayoutEngine()
    
    slides_data = [
        {
            'type': 'title',
            'title': 'My Presentation',
            'subtitle': 'A Great Topic',
            'author': 'John Doe'
        },
        {
            'type': 'content',
            'title': 'Introduction',
            'content': ['Point 1', 'Point 2', 'Point 3'],
            'speaker_notes': 'Introduce the topic'
        },
        {
            'type': 'two_column',
            'title': 'Comparison',
            'left_content': ['Left A', 'Left B'],
            'right_content': ['Right A', 'Right B']
        }
    ]
    
    slides = engine.create_slide_sequence(slides_data)
    
    assert len(slides) == 3
    assert slides[0].attributes['template'] == 'title'
    assert slides[1].attributes['template'] == 'content'
    assert slides[2].attributes['template'] == 'two_column'
    assert engine.total_slides == 3
    print("✅ test_slide_sequence_creation passed")


def test_slide_animation():
    """Test adding animations to slides."""
    from compose.layout.universal_box import AnimationTiming
    
    engine = SlideLayoutEngine()
    
    content = [
        UniversalBox("Animated text", ContentType.TEXT, BoxType.BLOCK)
    ]
    
    slide = engine.create_content_slide("Animated Slide", content)
    
    # Add animation to first content element (index 1, after title)
    animation = AnimationTiming(delay=0.5, duration=1.0, easing="ease-in")
    animated_slide = engine.add_animation(slide, 1, animation)
    
    # Check that animation was added
    animated_element = animated_slide.content[1]
    assert animated_element.animation is not None
    assert animated_element.animation.delay == 0.5
    assert animated_element.animation.duration == 1.0
    print("✅ test_slide_animation passed")


def test_slide_dimensions():
    """Test slide dimensions and positioning."""
    engine = SlideLayoutEngine()
    
    slide = engine.create_slide('content', title="Test Dimensions")
    
    # Check slide dimensions
    assert slide.dimensions.width == 1024.0  # Standard slide width
    assert slide.dimensions.height == 768.0  # Standard slide height
    
    # Check that child elements have positions
    for child in slide.content:
        if child.content_type != ContentType.SLIDE:  # Skip nested slides
            assert child.position is not None
            assert child.position.width >= 0  # x position
            assert child.position.height >= 0  # y position
    
    print("✅ test_slide_dimensions passed")


def test_create_simple_slide_factory():
    """Test simple slide factory function."""
    slide = create_simple_slide(
        title="Simple Slide",
        content=["Point 1", "Point 2", "Point 3"]
    )
    
    assert slide.content_type == ContentType.SLIDE
    assert slide.attributes['template'] == 'content'
    print("✅ test_create_simple_slide_factory passed")


def test_create_math_slide_factory():
    """Test math slide factory function."""
    slide = create_math_slide(
        title="Mathematical Slide",
        equations=["E = mc^2", "F = ma", "\\int x dx = \\frac{x^2}{2}"]
    )
    
    assert slide.content_type == ContentType.SLIDE
    
    # Check that content contains math boxes
    math_content = [box for box in slide.content 
                   if box.content_type == ContentType.MATH]
    assert len(math_content) == 3
    print("✅ test_create_math_slide_factory passed")


def test_create_diagram_slide_factory():
    """Test diagram slide factory function."""
    diagram_code = """
graph TD
    A[Start] --> B[Process] --> C[End]
"""
    
    slide = create_diagram_slide("Process Flow", diagram_code.strip())
    
    assert slide.content_type == ContentType.SLIDE
    
    # Check that content contains diagram box
    diagram_content = [box for box in slide.content 
                      if box.content_type == ContentType.DIAGRAM]
    assert len(diagram_content) == 1
    assert diagram_content[0].attributes['diagram_type'] == 'mermaid'
    print("✅ test_create_diagram_slide_factory passed")


def test_slide_counter_reset():
    """Test resetting the slide counter."""
    engine = SlideLayoutEngine()
    
    # Create some slides
    engine.create_slide('content', title="Slide 1")
    engine.create_slide('content', title="Slide 2")
    assert engine.get_slide_count() == 2
    
    # Reset counter
    engine.reset_slide_counter()
    assert engine.current_slide_number == 1
    assert engine.total_slides == 0
    
    # Create new slide
    slide = engine.create_slide('content', title="New Slide 1")
    assert slide.attributes['slide_number'] == 1
    print("✅ test_slide_counter_reset passed")


def test_invalid_template():
    """Test handling of invalid template names."""
    engine = SlideLayoutEngine()
    
    try:
        engine.create_slide('nonexistent_template', title="Test")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown template" in str(e)
    
    print("✅ test_invalid_template passed")
