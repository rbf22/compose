"""
Layout generator.

Generates layout state from document AST.
Uses the refactored TextLayoutEngine and layout primitives.
"""

from typing import List, Dict, Any, TYPE_CHECKING
from ..model.ast import Document, Paragraph, Heading, Text
from .constraint_primitives import LayoutState
from .layout_primitives import LayoutBox, PageLayout, BoxType, ParagraphLayout
from .text_layout_engine import TextLayoutEngine

if TYPE_CHECKING:
    from .layout_adjustments import Adjustment


class LayoutGenerator:
    """
    Generates layout state from document AST.
    
    Uses TextLayoutEngine for text measurement and wrapping.
    Produces immutable LayoutState objects.
    """
    
    def __init__(self, font_metrics: Dict[str, Dict], page_config: Dict[str, Any]):
        """
        Initialize generator.
        
        Args:
            font_metrics: Font metrics dictionary
            page_config: Page configuration (width, height, margins)
        """
        self.text_engine = TextLayoutEngine(font_metrics)
        self.page_config = page_config
        
        # Page dimensions
        self.page_width = page_config.get('width', 612)
        self.page_height = page_config.get('height', 792)
        self.margin_left = page_config.get('margin_left', 72)
        self.margin_right = page_config.get('margin_right', 72)
        self.margin_top = page_config.get('margin_top', 72)
        self.margin_bottom = page_config.get('margin_bottom', 72)
        
        # Typography
        self.default_font = page_config.get('font', 'Helvetica')
        self.default_size = page_config.get('font_size', 12)
        self.line_height_factor = page_config.get('line_height_factor', 1.2)
    
    def generate_initial_layout(self, doc: Document) -> LayoutState:
        """
        Generate initial layout without constraint checking.
        
        This is the "naive" layout - just place elements sequentially.
        
        Args:
            doc: Document to layout
            
        Returns:
            Initial layout state
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
    
    def regenerate_with_adjustments(self, state: LayoutState,
                                   adjustments: List['Adjustment']) -> LayoutState:
        """
        Apply adjustments and regenerate layout.
        
        Args:
            state: Current layout state
            adjustments: Adjustments to apply
            
        Returns:
            New layout state with adjustments applied
        """
        new_state = state.clone()
        
        # Apply each adjustment
        for adjustment in adjustments:
            new_state = adjustment.apply(new_state, self)
        
        return new_state
    
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
        
        return state
    
    def _layout_paragraph(self, paragraph: Paragraph, 
                         state: LayoutState) -> LayoutState:
        """
        Layout paragraph using TextLayoutEngine.
        
        Args:
            paragraph: Paragraph to layout
            state: Current layout state
            
        Returns:
            Updated layout state
        """
        # Extract text
        text = self._extract_text_content(paragraph.content)
        
        if not text.strip():
            return state
        
        # Calculate available width
        max_width = self.page_width - self.margin_left - self.margin_right
        
        # Use text layout engine
        line_layouts = self.text_engine.layout_wrapped_text(
            text=text,
            x=self.margin_left,
            y=state.current_y,
            max_width=max_width,
            font=self.default_font,
            size=self.default_size,
            line_height_factor=self.line_height_factor
        )
        
        if not line_layouts:
            return state
        
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
                font=self.default_font,
                size=self.default_size,
                line_height_factor=self.line_height_factor
            )
            para_box.content = line_layouts
        
        # Add to current page
        state.pages[state.current_page].add_box(para_box)
        state.elements.append(para_box)
        
        # Update position (with spacing)
        paragraph_spacing = 6.0
        state.current_y -= total_height + paragraph_spacing
        
        return state
    
    def _layout_heading(self, heading: Heading, 
                       state: LayoutState) -> LayoutState:
        """
        Layout heading.
        
        Args:
            heading: Heading to layout
            state: Current layout state
            
        Returns:
            Updated layout state
        """
        # Extract text
        text = self._extract_text_content(heading.content)
        
        if not text.strip():
            return state
        
        # Calculate font size based on level
        font_sizes = {1: 24, 2: 20, 3: 16, 4: 14, 5: 12, 6: 12}
        font_size = font_sizes.get(heading.level, 12)
        
        # Calculate available width
        max_width = self.page_width - self.margin_left - self.margin_right
        
        # Layout heading text
        line_layouts = self.text_engine.layout_wrapped_text(
            text=text,
            x=self.margin_left,
            y=state.current_y,
            max_width=max_width,
            font="Helvetica-Bold",
            size=font_size,
            line_height_factor=1.2
        )
        
        if not line_layouts:
            return state
        
        # Calculate total height
        total_height = sum(line.height for line in line_layouts)
        
        # Create heading box
        heading_box = LayoutBox(
            box_type=BoxType.HEADING,
            x=self.margin_left,
            y=state.current_y,
            width=max_width,
            height=total_height,
            content=line_layouts,
            metadata={'level': heading.level, 'text': text}
        )
        
        # Check if fits on current page
        current_page = state.pages[state.current_page]
        
        if not current_page.has_space_for(total_height, state.current_y):
            state = self._add_new_page(state)
            heading_box.y = state.current_y
        
        # Add to current page
        state.pages[state.current_page].add_box(heading_box)
        state.elements.append(heading_box)
        
        # Update position (with spacing)
        heading_spacing = 12.0
        state.current_y -= total_height + heading_spacing
        
        return state
    
    def _add_new_page(self, state: LayoutState) -> LayoutState:
        """Add a new page to state"""
        new_page = self._create_page(len(state.pages))
        state.pages.append(new_page)
        state.current_page = len(state.pages) - 1
        state.current_y = self.page_height - self.margin_top
        return state
    
    def _extract_text_content(self, elements) -> str:
        """
        Extract plain text from inline elements.
        
        Args:
            elements: List of inline elements
            
        Returns:
            Plain text string
        """
        text_parts = []
        
        for elem in elements:
            if isinstance(elem, Text):
                text_parts.append(elem.content)
            elif hasattr(elem, 'content'):
                text_parts.append(str(elem.content))
            else:
                text_parts.append(str(elem))
        
        return ''.join(text_parts)
