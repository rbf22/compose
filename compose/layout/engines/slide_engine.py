# compose/layout/engines/slide_engine.py
"""
Slide layout engine for presentations.

This module handles the specific layout requirements for presentation
slides, including templates, animations, and speaker notes.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from ..universal_box import UniversalBox, ContentType, BoxType, RenderingStyle, AnimationTiming
from ..box_model import Dimensions


@dataclass
class SlideTemplate:
    """Template definition for slide layouts."""
    name: str
    width: float = 1024.0  # Standard slide width
    height: float = 768.0  # Standard slide height
    title_area: Dict[str, float] = None  # x, y, width, height
    content_area: Dict[str, float] = None
    footer_area: Dict[str, float] = None
    
    def __post_init__(self):
        if self.title_area is None:
            self.title_area = {'x': 50, 'y': 50, 'width': 924, 'height': 100}
        if self.content_area is None:
            self.content_area = {'x': 50, 'y': 180, 'width': 924, 'height': 500}
        if self.footer_area is None:
            self.footer_area = {'x': 50, 'y': 720, 'width': 924, 'height': 40}


class SlideLayoutEngine:
    """
    Layout engine for presentation slides.
    
    Handles slide templates, content positioning, animations,
    and speaker notes for presentation creation.
    """
    
    def __init__(self):
        self.templates = self._create_default_templates()
        self.current_slide_number = 1
        self.total_slides = 0
    
    def _create_default_templates(self) -> Dict[str, SlideTemplate]:
        """Create default slide templates."""
        templates = {}
        
        # Title slide template
        templates['title'] = SlideTemplate(
            name='title',
            title_area={'x': 100, 'y': 250, 'width': 824, 'height': 150},
            content_area={'x': 100, 'y': 450, 'width': 824, 'height': 100},
            footer_area={'x': 50, 'y': 720, 'width': 924, 'height': 40}
        )
        
        # Content slide template
        templates['content'] = SlideTemplate(
            name='content',
            title_area={'x': 50, 'y': 50, 'width': 924, 'height': 80},
            content_area={'x': 50, 'y': 150, 'width': 924, 'height': 550},
            footer_area={'x': 50, 'y': 720, 'width': 924, 'height': 40}
        )
        
        # Two-column template
        templates['two_column'] = SlideTemplate(
            name='two_column',
            title_area={'x': 50, 'y': 50, 'width': 924, 'height': 80},
            content_area={'x': 50, 'y': 150, 'width': 450, 'height': 550},  # Left column
            footer_area={'x': 50, 'y': 720, 'width': 924, 'height': 40}
        )
        
        # Full content (no title)
        templates['full'] = SlideTemplate(
            name='full',
            title_area={'x': 0, 'y': 0, 'width': 0, 'height': 0},  # No title area
            content_area={'x': 50, 'y': 50, 'width': 924, 'height': 650},
            footer_area={'x': 50, 'y': 720, 'width': 924, 'height': 40}
        )
        
        return templates
    
    def create_slide(self, template_name: str = 'content', 
                    title: Optional[str] = None,
                    content: List[UniversalBox] = None,
                    speaker_notes: Optional[str] = None) -> UniversalBox:
        """Create a slide with the specified template and content."""
        
        if template_name not in self.templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = self.templates[template_name]
        content = content or []
        
        # Create slide container
        slide = UniversalBox(
            content=[],
            content_type=ContentType.SLIDE,
            box_type=BoxType.FIXED,
            dimensions=Dimensions(template.width, template.height, 0),
            attributes={
                'template': template_name,
                'slide_number': self.current_slide_number,
                'speaker_notes': speaker_notes
            }
        )
        
        # Add title if provided and template supports it
        if title and template.title_area['height'] > 0:
            title_box = self._create_title_box(title, template.title_area)
            slide.add_child(title_box)
        
        # Position content in content area
        positioned_content = self._position_content(content, template.content_area)
        for box in positioned_content:
            slide.add_child(box)
        
        # Add slide number footer
        footer_box = self._create_footer_box(template.footer_area)
        slide.add_child(footer_box)
        
        self.current_slide_number += 1
        return slide
    
    def _create_title_box(self, title: str, area: Dict[str, float]) -> UniversalBox:
        """Create a title box for the slide."""
        title_style = RenderingStyle(
            font_family="Arial",
            font_size=36.0,
            font_weight="bold",
            text_align="center",
            color="#333333"
        )
        
        title_box = UniversalBox(
            content=title,
            content_type=ContentType.TEXT,
            box_type=BoxType.BLOCK,
            dimensions=Dimensions(area['width'], area['height'], 0),
            position=Dimensions(area['x'], area['y'], 0),
            style=title_style
        )
        
        return title_box
    
    def _create_footer_box(self, area: Dict[str, float]) -> UniversalBox:
        """Create a footer box with slide number."""
        footer_style = RenderingStyle(
            font_family="Arial",
            font_size=12.0,
            text_align="right",
            color="#666666"
        )
        
        footer_text = f"Slide {self.current_slide_number}"
        
        footer_box = UniversalBox(
            content=footer_text,
            content_type=ContentType.TEXT,
            box_type=BoxType.BLOCK,
            dimensions=Dimensions(area['width'], area['height'], 0),
            position=Dimensions(area['x'], area['y'], 0),
            style=footer_style
        )
        
        return footer_box
    
    def _position_content(self, content: List[UniversalBox], 
                         area: Dict[str, float]) -> List[UniversalBox]:
        """Position content boxes within the content area."""
        if not content:
            return []
        
        positioned = []
        y_offset = area['y']
        available_width = area['width']
        
        for box in content:
            # Set horizontal position
            box.position = Dimensions(area['x'], y_offset, 0)
            
            # Adjust box width to fit content area
            if box.box_type == BoxType.BLOCK:
                box.dimensions.width = min(box.dimensions.width, available_width)
            
            # Update vertical position for next box
            y_offset += box.total_height() + 20  # 20pt spacing between elements
            
            positioned.append(box)
        
        return positioned
    
    def create_title_slide(self, title: str, subtitle: str = "", 
                          author: str = "") -> UniversalBox:
        """Create a title slide."""
        content = []
        
        if subtitle:
            subtitle_box = UniversalBox(
                content=subtitle,
                content_type=ContentType.TEXT,
                style=RenderingStyle(font_size=24.0, text_align="center")
            )
            content.append(subtitle_box)
        
        if author:
            author_box = UniversalBox(
                content=f"by {author}",
                content_type=ContentType.TEXT,
                style=RenderingStyle(font_size=18.0, text_align="center", color="#666666")
            )
            content.append(author_box)
        
        return self.create_slide('title', title=title, content=content)
    
    def create_content_slide(self, title: str, content: List[UniversalBox],
                           speaker_notes: Optional[str] = None) -> UniversalBox:
        """Create a standard content slide."""
        return self.create_slide('content', title=title, content=content, 
                                speaker_notes=speaker_notes)
    
    def create_two_column_slide(self, title: str, left_content: List[UniversalBox],
                               right_content: List[UniversalBox]) -> UniversalBox:
        """Create a two-column slide."""
        # Position left content
        left_positioned = self._position_content(
            left_content, 
            {'x': 50, 'y': 150, 'width': 450, 'height': 550}
        )
        
        # Position right content
        right_positioned = self._position_content(
            right_content,
            {'x': 520, 'y': 150, 'width': 450, 'height': 550}
        )
        
        all_content = left_positioned + right_positioned
        return self.create_slide('two_column', title=title, content=all_content)
    
    def add_animation(self, slide: UniversalBox, element_index: int,
                     animation: AnimationTiming) -> UniversalBox:
        """Add animation to a slide element."""
        if not slide.is_container() or element_index >= len(slide.content):
            return slide
        
        element = slide.content[element_index]
        element.set_animation(animation)
        
        return slide
    
    def create_slide_sequence(self, slides_data: List[Dict[str, Any]]) -> List[UniversalBox]:
        """Create a sequence of slides from data."""
        slides = []
        
        for slide_data in slides_data:
            slide_type = slide_data.get('type', 'content')
            title = slide_data.get('title', '')
            content = slide_data.get('content', [])
            speaker_notes = slide_data.get('speaker_notes')
            
            # Convert content strings to boxes if needed
            content_boxes = []
            for item in content:
                if isinstance(item, str):
                    content_boxes.append(UniversalBox(
                        content=item,
                        content_type=ContentType.TEXT,
                        box_type=BoxType.BLOCK
                    ))
                else:
                    content_boxes.append(item)
            
            if slide_type == 'title':
                subtitle = slide_data.get('subtitle', '')
                author = slide_data.get('author', '')
                slide = self.create_title_slide(title, subtitle, author)
            elif slide_type == 'two_column':
                left = slide_data.get('left_content', [])
                right = slide_data.get('right_content', [])
                
                # Convert left and right content to boxes
                left_boxes = []
                for item in left:
                    if isinstance(item, str):
                        left_boxes.append(UniversalBox(
                            content=item,
                            content_type=ContentType.TEXT,
                            box_type=BoxType.BLOCK
                        ))
                    else:
                        left_boxes.append(item)
                
                right_boxes = []
                for item in right:
                    if isinstance(item, str):
                        right_boxes.append(UniversalBox(
                            content=item,
                            content_type=ContentType.TEXT,
                            box_type=BoxType.BLOCK
                        ))
                    else:
                        right_boxes.append(item)
                
                slide = self.create_two_column_slide(title, left_boxes, right_boxes)
            else:
                slide = self.create_content_slide(title, content_boxes, speaker_notes)
            
            slides.append(slide)
        
        self.total_slides = len(slides)
        return slides
    
    def get_slide_count(self) -> int:
        """Get the total number of slides created."""
        return self.current_slide_number - 1
    
    def reset_slide_counter(self):
        """Reset the slide counter."""
        self.current_slide_number = 1
        self.total_slides = 0


# Factory functions for common slide types

def create_simple_slide(title: str, content: List[str]) -> UniversalBox:
    """Create a simple slide with text content."""
    engine = SlideLayoutEngine()
    
    content_boxes = [
        UniversalBox(text, ContentType.TEXT, BoxType.BLOCK)
        for text in content
    ]
    
    return engine.create_content_slide(title, content_boxes)


def create_math_slide(title: str, equations: List[str]) -> UniversalBox:
    """Create a slide with mathematical content."""
    engine = SlideLayoutEngine()
    
    content_boxes = [
        UniversalBox(eq, ContentType.MATH, BoxType.BLOCK)
        for eq in equations
    ]
    
    return engine.create_content_slide(title, content_boxes)


def create_diagram_slide(title: str, diagram_code: str) -> UniversalBox:
    """Create a slide with a diagram."""
    engine = SlideLayoutEngine()
    
    diagram_box = UniversalBox(
        content=diagram_code,
        content_type=ContentType.DIAGRAM,
        box_type=BoxType.BLOCK,
        attributes={'diagram_type': 'mermaid'}
    )
    
    return engine.create_content_slide(title, [diagram_box])
