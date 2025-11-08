# compose/layout/style_system.py
"""
Centralized Style System for Compose.

Provides layered style management with cascading overrides:
defaults → mode → user config → inline styles
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
from .universal_box import RenderingStyle, Dimensions


class StyleLayer(Enum):
    """Style precedence layers in order of specificity."""
    DEFAULT = 0      # Built-in defaults
    MODE = 1         # Document mode (document, slides, poster)
    USER = 2         # User configuration
    INLINE = 3       # Element-specific overrides


class StyleScope(Enum):
    """Style application scopes."""
    GLOBAL = "global"       # Applies to entire document
    HEADING = "heading"     # Heading styles (h1, h2, etc.)
    BODY = "body"           # Body text
    MATH = "math"           # Mathematical expressions
    CODE = "code"           # Code blocks
    DIAGRAM = "diagram"     # Diagrams and visualizations
    TABLE = "table"         # Tables and figures
    SLIDE = "slide"         # Presentation slides


@dataclass
class StyleDefinition:
    """A complete style definition for a scope."""
    # Typography
    font_family: Optional[str] = None
    font_size: Optional[float] = None
    font_weight: Optional[str] = None
    font_style: Optional[str] = None
    line_height: Optional[float] = None

    # Colors
    color: Optional[str] = None
    background_color: Optional[str] = None
    border_color: Optional[str] = None

    # Spacing
    margin: Optional[Dimensions] = None
    padding: Optional[Dimensions] = None
    border_width: Optional[float] = None

    # Layout
    text_align: Optional[str] = None
    vertical_align: Optional[str] = None

    # Effects
    opacity: Optional[float] = None
    shadow: Optional[str] = None

    def merge(self, other: 'StyleDefinition') -> 'StyleDefinition':
        """Merge this style with another, preferring non-None values."""
        merged = StyleDefinition()

        # Merge all fields
        for field_name in self.__dataclass_fields__:
            self_value = getattr(self, field_name)
            other_value = getattr(other, field_name)

            # Use other value if it's not None, otherwise self value
            if other_value is not None:
                setattr(merged, field_name, other_value)
            else:
                setattr(merged, field_name, self_value)

        return merged

    def to_rendering_style(self) -> RenderingStyle:
        """Convert to RenderingStyle, filtering out None values."""
        style = RenderingStyle()

        # Only set non-None values
        if self.font_family is not None:
            style.font_family = self.font_family
        if self.font_size is not None:
            style.font_size = self.font_size
        if self.font_weight is not None:
            style.font_weight = self.font_weight
        if self.font_style is not None:
            style.font_style = self.font_style
        if self.line_height is not None:
            style.line_height = self.line_height
        if self.color is not None:
            style.color = self.color
        if self.background_color is not None:
            style.background_color = self.background_color
        if self.border_color is not None:
            style.border_color = self.border_color
        if self.margin is not None:
            style.margin = self.margin
        if self.padding is not None:
            style.padding = self.padding
        if self.border_width is not None:
            style.border_width = self.border_width
        if self.text_align is not None:
            style.text_align = self.text_align
        if self.vertical_align is not None:
            style.vertical_align = self.vertical_align
        if self.opacity is not None:
            style.opacity = self.opacity
        if self.shadow is not None:
            style.shadow = self.shadow

        return style


class StyleSystem:
    """
    Central style management system with layered overrides.

    Styles are resolved through a cascade:
    1. Default styles (built-in)
    2. Mode-specific styles (document, slides, etc.)
    3. User configuration styles
    4. Inline styles (highest precedence)
    """

    def __init__(self):
        self._styles: Dict[StyleLayer, Dict[StyleScope, StyleDefinition]] = {}
        self._current_mode: Optional[str] = None

        # Initialize style layers
        for layer in StyleLayer:
            self._styles[layer] = {}

        # Set up default styles
        self._initialize_defaults()

    def _initialize_defaults(self):
        """Initialize built-in default styles."""
        # Global defaults
        global_defaults = StyleDefinition(
            font_family="serif",
            font_size=12.0,
            font_weight="normal",
            font_style="normal",
            line_height=1.2,
            color="#000000",
            text_align="left",
            vertical_align="baseline",
            opacity=1.0
        )

        # Heading defaults
        heading_defaults = StyleDefinition(
            font_family="serif",
            font_weight="bold",
            font_style="normal",
            line_height=1.1,
            color="#000000",
            margin=Dimensions(0, 18.0, 9.0, 0),  # left, top, right, bottom
            text_align="left"
        )

        # Body text defaults
        body_defaults = StyleDefinition(
            font_family="serif",
            font_size=12.0,
            font_weight="normal",
            font_style="normal",
            line_height=1.4,
            color="#000000",
            margin=Dimensions(0, 12.0, 0, 12.0),  # left, top, right, bottom
            text_align="justify"
        )

        # Math defaults
        math_defaults = StyleDefinition(
            font_family="math",
            font_size=12.0,
            font_style="italic",
            color="#000000"
        )

        # Code defaults
        code_defaults = StyleDefinition(
            font_family="monospace",
            font_size=10.0,
            font_weight="normal",
            font_style="normal",
            background_color="#f5f5f5",
            padding=Dimensions(4.0, 4.0, 4.0, 4.0),
            border_width=1.0,
            border_color="#cccccc"
        )

        # Diagram defaults
        diagram_defaults = StyleDefinition(
            margin=Dimensions(18.0, 18.0, 18.0, 18.0),
            text_align="center"
        )

        # Table defaults
        table_defaults = StyleDefinition(
            font_family="serif",
            font_size=10.0,
            margin=Dimensions(12.0, 12.0, 12.0, 12.0),
            border_width=1.0,
            border_color="#cccccc"
        )

        # Slide defaults
        slide_defaults = StyleDefinition(
            font_family="sans-serif",
            font_size=14.0,
            background_color="#ffffff",
            padding=Dimensions(40.0, 40.0, 40.0, 40.0)
        )

        self._styles[StyleLayer.DEFAULT] = {
            StyleScope.GLOBAL: global_defaults,
            StyleScope.HEADING: heading_defaults,
            StyleScope.BODY: body_defaults,
            StyleScope.MATH: math_defaults,
            StyleScope.CODE: code_defaults,
            StyleScope.DIAGRAM: diagram_defaults,
            StyleScope.TABLE: table_defaults,
            StyleScope.SLIDE: slide_defaults
        }

    def set_mode(self, mode: str):
        """Set the current document mode (document, slides, poster)."""
        self._current_mode = mode
        self._initialize_mode_styles()

    def _initialize_mode_styles(self):
        """Initialize mode-specific style overrides."""
        if not self._current_mode:
            return

        mode_styles = {}

        if self._current_mode == "slides":
            # Slide mode overrides
            mode_styles[StyleScope.GLOBAL] = StyleDefinition(
                font_family="sans-serif",
                font_size=16.0,
                line_height=1.3
            )
            mode_styles[StyleScope.HEADING] = StyleDefinition(
                font_size=24.0,
                font_weight="bold",
                color="#2563eb"  # Blue headings for slides
            )
            mode_styles[StyleScope.BODY] = StyleDefinition(
                font_size=16.0,
                line_height=1.5,
                text_align="left"
            )
            mode_styles[StyleScope.SLIDE] = StyleDefinition(
                background_color="#ffffff",
                padding=Dimensions(60.0, 60.0, 60.0, 60.0)
            )

        elif self._current_mode == "poster":
            # Poster mode overrides
            mode_styles[StyleScope.GLOBAL] = StyleDefinition(
                font_size=18.0,
                line_height=1.2
            )
            mode_styles[StyleScope.HEADING] = StyleDefinition(
                font_size=36.0,
                font_weight="bold",
                color="#dc2626"  # Red headings for posters
            )
            mode_styles[StyleScope.BODY] = StyleDefinition(
                font_size=18.0,
                text_align="left"
            )

        elif self._current_mode == "academic":
            # Academic mode overrides
            mode_styles[StyleScope.GLOBAL] = StyleDefinition(
                font_family="serif",
                font_size=11.0
            )
            mode_styles[StyleScope.BODY] = StyleDefinition(
                font_size=11.0,
                line_height=1.4,
                text_align="justify"
            )

        self._styles[StyleLayer.MODE] = mode_styles

    def set_user_style(self, scope: StyleScope, style: StyleDefinition):
        """Set a user-defined style override."""
        self._styles[StyleLayer.USER][scope] = style

    def set_user_styles_from_config(self, config: Dict[str, Any]):
        """Load user styles from configuration dictionary."""
        # Parse configuration and create StyleDefinitions
        # This would handle TOML/YAML config parsing
        pass

    def get_style(self, scope: StyleScope, inline_style: Optional[StyleDefinition] = None) -> RenderingStyle:
        """
        Get the resolved style for a scope, including all layers and inline overrides.

        Returns a RenderingStyle ready to apply to boxes.
        """
        # Start with default
        resolved = self._styles[StyleLayer.DEFAULT].get(scope, StyleDefinition())

        # Apply mode overrides
        if scope in self._styles[StyleLayer.MODE]:
            resolved = resolved.merge(self._styles[StyleLayer.MODE][scope])

        # Apply user overrides
        if scope in self._styles[StyleLayer.USER]:
            resolved = resolved.merge(self._styles[StyleLayer.USER][scope])

        # Apply inline overrides
        if inline_style:
            resolved = resolved.merge(inline_style)

        return resolved.to_rendering_style()

    def get_heading_style(self, level: int, inline_style: Optional[StyleDefinition] = None) -> RenderingStyle:
        """Get style for a specific heading level."""
        base_style = self.get_style(StyleScope.HEADING, inline_style)

        # Adjust size based on heading level
        size_multipliers = {1: 2.0, 2: 1.5, 3: 1.2, 4: 1.1, 5: 1.0, 6: 1.0}
        multiplier = size_multipliers.get(level, 1.0)

        base_style.font_size *= multiplier
        base_style.font_weight = "bold"

        return base_style

    def apply_to_box(self, box: 'UniversalBox', scope: StyleScope, inline_style: Optional[StyleDefinition] = None):
        """Apply resolved styles to a UniversalBox."""
        resolved_style = self.get_style(scope, inline_style)
        box.style = resolved_style

    def reset(self):
        """Reset all styles to defaults."""
        self._styles = {}
        for layer in StyleLayer:
            self._styles[layer] = {}
        self._initialize_defaults()
        if self._current_mode:
            self._initialize_mode_styles()
