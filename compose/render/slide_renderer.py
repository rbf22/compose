# compose/render/slide_renderer.py
"""
Enhanced slide presentation system for Compose.
Provides professional slide layouts, animations, and interactive features.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from ..model.ast import Document, BlockElement, Heading, Paragraph, ListBlock, Text, MathBlock
from ..layout.universal_box import UniversalBox, ContentType, BoxType, create_text_box, RenderingStyle
from ..layout.style_system import StyleDefinition
from ..layout.style_system import StyleSystem, StyleScope


class SlideBox(UniversalBox):
    """Box representing a slide with layout and content"""
    slide_type: str = "content"  # title, content, comparison, etc.
    title: str = ""
    layout: Dict[str, Any] = None
    animations: List[Dict[str, Any]] = None

    def __init__(self, slide_type: str = "content", title: str = "",
                 layout: Dict[str, Any] = None,
                 animations: List[Dict[str, Any]] = None, **kwargs):
        # Extract our custom kwargs before passing to UniversalBox
        self.slide_type = slide_type
        self.title = title
        self.layout = layout or {}
        self.animations = animations or []

        # Initialize as a slide box
        super().__init__(
            content=[],  # Will be populated with child boxes
            content_type=ContentType.SLIDE,
            box_type=BoxType.FIXED,
            **kwargs
        )
    @property
    def content_boxes(self):
        """Backward compatibility: return content as list"""
        return self.content if isinstance(self.content, list) else []

    @content_boxes.setter
    def content_boxes(self, value):
        """Backward compatibility: set content from list"""
        self.content = value

    @property
    def width(self):
        """Backward compatibility: return width from dimensions"""
        return self.dimensions.width

    @width.setter
    def width(self, value):
        """Backward compatibility: set width in dimensions"""
        if self.dimensions is None:
            self.dimensions = self._create_dimensions(value, self.dimensions.height if self.dimensions else 0)
        else:
            self.dimensions.width = value

    @property
    def height(self):
        """Backward compatibility: return height from dimensions"""
        return self.dimensions.height

    @height.setter
    def height(self, value):
        """Backward compatibility: set height in dimensions"""
        if self.dimensions is None:
            self.dimensions = self._create_dimensions(self.dimensions.width if self.dimensions else 0, value)
        else:
            self.dimensions.height = value

    @property
    def box_type(self):
        """Backward compatibility: return box type as string"""
        return "slide"
    
    @box_type.setter
    def box_type(self, value):
        """Allow setting box_type from parent class"""
        # Store the actual box type but don't expose it
        pass


class SlideLayoutEngine:
    """
    Engine for creating professional slide layouts using UniversalBox.
    Handles different slide types with style system integration.
    """

    def __init__(self, style_system: Optional[StyleSystem] = None):
        self.slide_width = 1024
        self.slide_height = 768
        self.margin = 40
        # Backward compatibility attributes
        self.title_font_size = 48
        self.content_font_size = 24
        self.style_system = style_system or StyleSystem()
        # Set slides mode for appropriate styling
        self.style_system.set_mode("slides")

    def create_title_slide(self, title: str, subtitle: Optional[str] = None,
                          author: Optional[str] = None) -> SlideBox:
        """Create a professional title slide using UniversalBox"""
        slide_box = SlideBox(
            slide_type="title",
            title=title,
            dimensions=self._create_dimensions(self.slide_width, self.slide_height)
        )

        # Create a container for all title elements
        title_container = UniversalBox(
            content=[],
            content_type=ContentType.LAYOUT,
            box_type=BoxType.BLOCK
        )

        # Title box with slide heading style
        title_style = self.style_system.get_heading_style(1)
        title_box = create_text_box(title, title_style)
        title_container.add_child(title_box)

        if subtitle:
            subtitle_style = self.style_system.get_style(StyleScope.BODY)
            subtitle_style.font_size = 24.0  # Slightly smaller than title
            subtitle_box = create_text_box(subtitle, subtitle_style)
            title_container.add_child(subtitle_box)

        if author:
            author_style = self.style_system.get_style(StyleScope.BODY)
            author_style.font_size = 18.0
            author_box = create_text_box(f"by {author}", author_style)
            title_container.add_child(author_box)

        # Add the container to the slide
        slide_box.add_child(title_container)

        return slide_box

    def create_content_slide(self, title: str, content_blocks) -> SlideBox:
        """Create a content slide with title and bullet points"""
        slide_box = SlideBox(
            slide_type="content",
            title=title,
            dimensions=self._create_dimensions(self.slide_width, self.slide_height)
        )

        # Convert content blocks to UniversalBoxes and add them
        if hasattr(content_blocks, '__iter__'):  # Handle both lists and single objects
            for block in content_blocks:
                box = self._convert_block_to_box(block)
                slide_box.add_child(box)

        return slide_box

    def add_animation(self, slide: SlideBox, animation_type: str, 
                     element_selector: str = "*", delay: float = 0.0, 
                     duration: float = 0.5, easing: str = "ease") -> SlideBox:
        """Add animation to a slide element"""
        if not hasattr(slide, 'animations'):
            slide.animations = []
        
        animation = {
            'type': animation_type,
            'element': element_selector,
            'delay': delay,
            'duration': duration,
            'easing': easing,
            'played': False  # Track if animation has been triggered
        }
        
        slide.animations.append(animation)
        return slide

    def create_fade_in_animation(self, slide: SlideBox, element_selector: str = ".slide-content",
                                delay: float = 0.0, duration: float = 0.8) -> SlideBox:
        """Create a fade-in animation"""
        return self.add_animation(slide, 'fade-in', element_selector, delay, duration)

    def create_slide_up_animation(self, slide: SlideBox, element_selector: str = ".slide-content",
                                 delay: float = 0.2, duration: float = 0.6) -> SlideBox:
        """Create a slide-up animation"""
        return self.add_animation(slide, 'slide-up', element_selector, delay, duration)

    def create_typewriter_animation(self, slide: SlideBox, element_selector: str = ".slide-title",
                                   delay: float = 0.0, duration: float = 2.0) -> SlideBox:
        """Create a typewriter effect animation"""
        return self.add_animation(slide, 'typewriter', element_selector, delay, duration)

    def create_sequential_reveal(self, slide: SlideBox, elements: List[str], 
                                stagger_delay: float = 0.3) -> SlideBox:
        """Create sequential reveal animations for multiple elements"""
        for i, element in enumerate(elements):
            delay = i * stagger_delay
            self.add_animation(slide, 'fade-in', element, delay, 0.5)
        return slide

    def create_comparison_animation(self, slide: SlideBox, left_element: str = ".comparison-left",
                                   right_element: str = ".comparison-right", 
                                   delay: float = 0.5) -> SlideBox:
        """Create side-by-side comparison animation"""
        self.add_animation(slide, 'slide-left', left_element, 0.0, 0.8)
        self.add_animation(slide, 'slide-right', right_element, delay, 0.8)
        return slide

    def create_comparison_slide(self, left_title: str, left_content: List[UniversalBox],
                               right_title: str, right_content: List[UniversalBox]) -> SlideBox:
        """Create a side-by-side comparison slide"""
        slide_box = SlideBox(
            slide_type="comparison",
            title=f"{left_title} vs {right_title}",
            dimensions=self._create_dimensions(self.slide_width, self.slide_height)
        )

        # Left side container
        left_container = UniversalBox(
            content=[],
            content_type=ContentType.LAYOUT,
            box_type=BoxType.BLOCK,
            attributes={"class": "comparison-left"}
        )
        
        # Add left title and content
        left_title_style = self.style_system.get_heading_style(3)
        left_title_box = create_text_box(left_title, left_title_style)
        left_container.add_child(left_title_box)
        
        for content_box in left_content:
            left_container.add_child(content_box)

        # Right side container
        right_container = UniversalBox(
            content=[],
            content_type=ContentType.LAYOUT,
            box_type=BoxType.BLOCK,
            attributes={"class": "comparison-right"}
        )
        
        # Add right title and content
        right_title_style = self.style_system.get_heading_style(3)
        right_title_box = create_text_box(right_title, right_title_style)
        right_container.add_child(right_title_box)
        
        for content_box in right_content:
            right_container.add_child(content_box)
        
        slide_box.add_child(left_container)
        slide_box.add_child(right_container)
        
        # Add comparison animation
        self.create_comparison_animation(slide_box)
        
        return slide_box

    def _create_dimensions(self, width: float, height: float) -> 'Dimensions':
        """Create Dimensions object"""
        from ..layout.universal_box import Dimensions
        return Dimensions(width, height, 0)

    def _convert_block_to_box(self, block: BlockElement) -> UniversalBox:
        """Convert a block element to UniversalBox"""
        if isinstance(block, Paragraph):
            text = self._extract_text(block.content)
            style = self.style_system.get_style(StyleScope.BODY)
            return create_text_box(text, style)

        elif isinstance(block, ListBlock):
            # Convert to bullet points
            bullets = []
            for item in block.items:
                bullet_text = f"• {self._extract_text(item.content)}"
                style = self.style_system.get_style(StyleScope.BODY)
                bullet_box = create_text_box(bullet_text, style)
                bullets.append(bullet_box)

            # Container for bullet list
            list_container = UniversalBox(
                content=bullets,
                content_type=ContentType.LAYOUT,
                box_type=BoxType.BLOCK
            )
            return list_container

        elif isinstance(block, MathBlock):
            # Math content
            math_box = UniversalBox(
                content=block.content,
                content_type=ContentType.MATH,
                box_type=BoxType.INLINE
            )
            return math_box

        # Default fallback
        text = str(block)
        style = self.style_system.get_style(StyleScope.BODY)
        return create_text_box(text, style)

    def _extract_text(self, inline_elements) -> str:
        """Extract text from inline elements"""
        if isinstance(inline_elements, list):
            return ''.join(self._extract_text_from_element(elem) for elem in inline_elements)
        else:
            return self._extract_text_from_element(inline_elements)

    def _extract_text_from_element(self, element) -> str:
        """Extract text from a single inline element"""
        if hasattr(element, 'content'):
            return element.content
        elif hasattr(element, 'children'):
            return self._extract_text(element.children)
        elif hasattr(element, 'text'):
            return element.text
        return str(element)


class SlideAnimationSystem:
    """
    Handles slide animations and reveal sequences.
    """

    def __init__(self):
        self.animations = []

    def add_fade_in(self, element_id: str, delay: float = 0) -> Dict[str, Any]:
        """Add fade-in animation"""
        return {
            'type': 'fade_in',
            'element_id': element_id,
            'delay': delay,
            'duration': 0.5
        }

    def add_slide_up(self, element_id: str, delay: float = 0) -> Dict[str, Any]:
        """Add slide-up animation"""
        return {
            'type': 'slide_up',
            'element_id': element_id,
            'delay': delay,
            'duration': 0.7
        }

    def add_highlight(self, element_id: str, delay: float = 0) -> Dict[str, Any]:
        """Add highlight animation"""
        return {
            'type': 'highlight',
            'element_id': element_id,
            'delay': delay,
            'duration': 0.3
        }


class SlideRenderer:
    """
    Renders slides to HTML with animations and interactivity.
    """

    def __init__(self):
        self.layout_engine = SlideLayoutEngine()
        self.animation_system = SlideAnimationSystem()

    def render_slide_deck(self, document: Document) -> str:
        """
        Render entire document as slide deck.

        Args:
            document: Document AST

        Returns:
            HTML string for complete slide presentation
        """
        slides = self._extract_slides_from_document(document)

        # Generate HTML for each slide
        slide_htmls = []
        for i, slide in enumerate(slides):
            slide_htmls.append(self._render_slide_html(slide, i + 1, len(slides)))

        # Combine into full presentation
        slides_html = '\n'.join(slide_htmls)

        full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{document.frontmatter.get('title', 'Slides')}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: #000;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow: hidden;
        }}

        .slide {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: white;
            display: none;
            padding: 40px;
            box-sizing: border-box;
        }}

        .slide.active {{
            display: block;
        }}

        .slide-title {{
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 40px;
            color: #333;
        }}

        .slide-content {{
            font-size: 24px;
            line-height: 1.6;
            color: #555;
        }}

        .slide-content ul {{
            padding-left: 40px;
        }}

        .slide-content li {{
            margin: 20px 0;
        }}

        .slide-footer {{
            position: absolute;
            bottom: 20px;
            right: 40px;
            font-size: 14px;
            color: #999;
        }}

        .slide-number {{
            position: absolute;
            bottom: 20px;
            left: 40px;
            font-size: 14px;
            color: #999;
        }}

        /* Animation keyframes */
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        @keyframes slideUp {{
            from {{ transform: translateY(50px); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}

        @keyframes highlight {{
            0% {{ background-color: transparent; }}
            50% {{ background-color: #ffff00; }}
            100% {{ background-color: transparent; }}
        }}

        @keyframes slideLeft {{
            from {{ 
                opacity: 0; 
                transform: translateX(-100px); 
            }}
            to {{ 
                opacity: 1; 
                transform: translateX(0); 
            }}
        }}

        @keyframes slideRight {{
            from {{ 
                opacity: 0; 
                transform: translateX(100px); 
            }}
            to {{ 
                opacity: 1; 
                transform: translateX(0); 
            }}
        }}

        @keyframes typewriter {{
            from {{ width: 0; }}
            to {{ width: 100%; }}
        }}

        .animated {{
            animation-fill-mode: both;
        }}

        .fade-in {{
            animation-name: fadeIn;
        }}

        .slide-up {{
            animation-name: slideUp;
        }}

        .slide-left {{
            animation-name: slideLeft;
        }}

        .slide-right {{
            animation-name: slideRight;
        }}

        .typewriter {{
            animation-name: typewriter;
        }}

        .highlight {{
            animation-name: highlight;
        }}

        .comparison-layout {{
            display: flex;
            gap: 40px;
            justify-content: space-around;
            align-items: flex-start;
            margin-top: 40px;
        }}

        .comparison-left, .comparison-right {{
            flex: 1;
            padding: 20px;
            background: rgba(255,255,255,0.9);
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    {slides_html}

    <script>
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');

        function showSlide(index) {{
            slides.forEach((slide, i) => {{
                if (i === index) {{
                    slide.classList.add('active');
                }} else {{
                    slide.classList.remove('active');
                }}
            }});

            // Handle advanced animations from slide data
            const activeSlide = slides[index];
            const slideData = activeSlide.dataset;
            
            // Apply animations based on slide configuration
            setTimeout(() => {{
                applySlideAnimations(activeSlide);
            }}, 100);
        }}

        function applySlideAnimations(slideElement) {{
            // Find all elements with animation data
            const animatedElements = slideElement.querySelectorAll('[data-animation]');
            
            animatedElements.forEach(element => {{
                const animationType = element.dataset.animation;
                const delay = parseFloat(element.dataset.delay || 0);
                const duration = parseFloat(element.dataset.duration || 0.5);
                
                // Apply animation styles
                element.style.animationName = animationType;
                element.style.animationDuration = duration + 's';
                element.style.animationDelay = delay + 's';
                element.style.animationFillMode = 'both';
                element.style.animationTimingFunction = element.dataset.easing || 'ease';
                
                // Mark as played
                element.dataset.played = 'true';
            }});
        }}

        function resetSlideAnimations(slideElement) {{
            const animatedElements = slideElement.querySelectorAll('[data-animation]');
            animatedElements.forEach(element => {{
                element.style.animationName = '';
                element.style.animationDelay = '';
                element.dataset.played = 'false';
            }});
        }}

        function nextSlide() {{
            if (currentSlide < slides.length - 1) {{
                currentSlide++;
                showSlide(currentSlide);
            }}
        }}

        function prevSlide() {{
            if (currentSlide > 0) {{
                currentSlide--;
                showSlide(currentSlide);
            }}
        }}

        // Keyboard navigation
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'ArrowRight' || e.key === ' ') {{
                nextSlide();
            }} else if (e.key === 'ArrowLeft') {{
                prevSlide();
            }} else if (e.key === 'Home') {{
                currentSlide = 0;
                showSlide(currentSlide);
            }} else if (e.key === 'End') {{
                currentSlide = slides.length - 1;
                showSlide(currentSlide);
            }}
        }});

        // Touch navigation
        let touchStartX = 0;
        document.addEventListener('touchstart', function(e) {{
            touchStartX = e.touches[0].clientX;
        }});

        document.addEventListener('touchend', function(e) {{
            const touchEndX = e.changedTouches[0].clientX;
            const deltaX = touchEndX - touchStartX;

            if (Math.abs(deltaX) > 50) {{  // Minimum swipe distance
                if (deltaX > 0) {{
                    prevSlide();
                }} else {{
                    nextSlide();
                }}
            }}
        }});

        // Initialize first slide
        showSlide(0);
    </script>
</body>
</html>'''

        return full_html

    def _extract_slides_from_document(self, document: Document) -> List[SlideBox]:
        """Extract slides from document structure"""
        slides = []

        # Group content by level 1 headings as slide boundaries
        current_slide_blocks = []
        current_title = "Title Slide"

        for block in document.blocks:
            if isinstance(block, Heading) and block.level == 1:
                # Finish previous slide
                if current_slide_blocks:
                    # Convert blocks to boxes
                    content_boxes = [self.layout_engine._convert_block_to_box(b) for b in current_slide_blocks]
                    slides.append(self.layout_engine.create_content_slide(
                        current_title, content_boxes
                    ))

                # Start new slide
                current_title = self._extract_text(block.content)
                current_slide_blocks = []
            else:
                current_slide_blocks.append(block)

        # Add final slide
        if current_slide_blocks:
            content_boxes = [self.layout_engine._convert_block_to_box(b) for b in current_slide_blocks]
            slides.append(self.layout_engine.create_content_slide(
                current_title, content_boxes
            ))

        # If no level 1 headings, create single content slide
        if not slides and document.blocks:
            title = document.frontmatter.get('title', 'Presentation')
            content_boxes = [self.layout_engine._convert_block_to_box(b) for b in document.blocks]
            slides.append(self.layout_engine.create_content_slide(
                title, content_boxes
            ))
        elif not slides:
            # Create a default slide for empty documents
            slides.append(self.layout_engine.create_title_slide(
                document.frontmatter.get('title', 'Presentation')
            ))

        return slides

    def _render_slide_html(self, slide: SlideBox, slide_num: int, total_slides: int) -> str:
        """Render a single slide as HTML"""
        html = f'''
        <div class="slide" id="slide-{slide_num}">
            <div class="slide-number">{slide_num} / {total_slides}</div>
            <div class="slide-title">{slide.title}</div>
            <div class="slide-content">
        '''

        # Render content based on slide type and children
        if slide.slide_type == "title":
            html += '<div class="title-slide">'
            # Title slides show their children
            for child in slide.get_children():
                if child.content_type == ContentType.TEXT and isinstance(child.content, str):
                    # Apply title animation if configured
                    animation_attrs = self._get_animation_attrs(slide, 'title-element')
                    html += f'<div class="title-element"{animation_attrs}>{child.content}</div>'
        elif slide.slide_type == "content":
            html += '<ul>'
            # Content slides show bullet points from children
            for i, child in enumerate(slide.get_children()):
                if child.content_type == ContentType.TEXT and isinstance(child.content, str):
                    if child.content.startswith('•'):
                        # Apply sequential fade-in animation
                        animation_attrs = self._get_animation_attrs(slide, 'bullet', i * 0.2)
                        html += f'<li class="animated fade-in"{animation_attrs}>{child.content[1:].strip()}</li>'
                    else:
                        animation_attrs = self._get_animation_attrs(slide, 'paragraph', i * 0.1)
                        html += f'<p class="animated slide-up"{animation_attrs}>{child.content}</p>'
                elif child.is_container():
                    # Handle nested content like bullet lists
                    for j, nested_child in enumerate(child.get_children()):
                        if isinstance(nested_child.content, str) and nested_child.content.startswith('•'):
                            animation_attrs = self._get_animation_attrs(slide, 'nested-bullet', (i + j) * 0.15)
                            html += f'<li class="animated fade-in"{animation_attrs}>{nested_child.content[1:].strip()}</li>'
            html += '</ul>'
        elif slide.slide_type == "comparison":
            # Comparison slides have side-by-side layout
            html += '<div class="comparison-layout">'
            children = slide.get_children()
            if len(children) >= 2:
                left_container = children[0]
                right_container = children[1]
                left_attrs = self._get_animation_attrs(slide, 'comparison-left')
                right_attrs = self._get_animation_attrs(slide, 'comparison-right')
                html += f'<div class="comparison-left"{left_attrs}>'
                for child in left_container.get_children():
                    if isinstance(child.content, str):
                        html += f'<div>{child.content}</div>'
                html += '</div>'
                html += f'<div class="comparison-right"{right_attrs}>'
                for child in right_container.get_children():
                    if isinstance(child.content, str):
                        html += f'<div>{child.content}</div>'
                html += '</div>'
            html += '</div>'

        html += '''
            </div>
            <div class="slide-footer">Press arrow keys or space to navigate</div>
        </div>
        '''

        return html

    def _get_animation_attrs(self, slide: SlideBox, element_type: str, extra_delay: float = 0.0) -> str:
        """Generate animation data attributes for an element"""
        if not hasattr(slide, 'animations') or not slide.animations:
            return ""
        
        # Find animation for this element type
        for animation in slide.animations:
            if animation['element'] == element_type or animation['element'] == '*':
                # Calculate total delay
                total_delay = animation['delay'] + extra_delay
                
                attrs = f' data-animation="{animation["type"]}"'
                attrs += f' data-delay="{total_delay}"'
                attrs += f' data-duration="{animation["duration"]}"'
                attrs += f' data-easing="{animation["easing"]}"'
                return attrs
        
        return ""

    def _extract_text(self, inline_elements):
        """Extract text from inline elements."""
        if isinstance(inline_elements, list):
            return ''.join(self._extract_text_from_element(elem) for elem in inline_elements)
        else:
            return self._extract_text_from_element(inline_elements)

    def _extract_text_from_element(self, element):
        """Extract text from a single inline element."""
        if hasattr(element, 'content'):
            return element.content
        elif hasattr(element, 'children'):
            return self._extract_text(element.children)
        elif hasattr(element, 'text'):
            return element.text
        return str(element)
