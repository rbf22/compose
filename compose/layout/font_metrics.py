# compose/math/font_metrics.py
"""
Font metrics system for mathematical typesetting.

This module handles font measurements and positioning data
required for proper mathematical layout, following TeX's
approach to font metrics.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class FontStyle(Enum):
    """Mathematical font styles."""
    ROMAN = "roman"           # Regular text font
    ITALIC = "italic"         # Math italic (default for variables)
    BOLD = "bold"            # Bold font
    SCRIPT = "script"        # Script/calligraphic font
    FRAKTUR = "fraktur"      # Fraktur/blackletter font
    MONOSPACE = "monospace"  # Typewriter font
    SANS_SERIF = "sans"      # Sans serif font


@dataclass
class FontParameters:
    """
    Mathematical font parameters following TeX conventions.
    
    These parameters control the positioning and sizing of
    mathematical elements and are typically stored in the
    font's metric files (TFM or OpenType Math table).
    """
    # Basic measurements
    x_height: float          # Height of lowercase x
    quad_width: float        # Width of an em (M)
    
    # Superscript and subscript positioning
    sup_shift_up: float      # How high to raise superscripts
    sub_shift_down: float    # How low to lower subscripts
    sup_drop: float          # Superscript baseline drop
    sub_drop: float          # Subscript baseline drop
    
    # Fraction parameters
    num_shift_up: float      # Numerator shift in fractions
    denom_shift_down: float  # Denominator shift in fractions
    rule_thickness: float    # Thickness of fraction rule
    
    # Radical parameters
    radical_rule_thickness: float  # Thickness of radical vinculum
    radical_extra_ascender: float  # Extra height above radical
    
    # Operator spacing
    thin_mu_skip: float      # Thin space (3mu in TeX)
    med_mu_skip: float       # Medium space (4mu in TeX)
    thick_mu_skip: float     # Thick space (5mu in TeX)
    
    # Large operator parameters
    display_op_min_height: float  # Minimum height for display operators


@dataclass 
class CharacterMetrics:
    """Metrics for an individual character."""
    width: float
    height: float
    depth: float
    italic_correction: float = 0.0  # Adjustment for italic characters
    
    # Ligature and kerning information would go here in full implementation
    # ligatures: Dict[str, str] = None
    # kerning: Dict[str, float] = None


class MathFontMetrics:
    """
    Mathematical font metrics manager.
    
    This class provides access to font measurements and parameters
    needed for mathematical typesetting. In a full implementation,
    this would read from TFM files or OpenType Math tables.
    """
    
    def __init__(self, font_name: str = "Computer Modern"):
        self.font_name = font_name
        self._char_metrics: Dict[str, CharacterMetrics] = {}
        self._font_params = self._get_default_parameters()
        self._load_character_metrics()
    
    def _get_default_parameters(self) -> FontParameters:
        """Get default font parameters (simplified for prototype)."""
        return FontParameters(
            x_height=4.3,
            quad_width=10.0,
            sup_shift_up=4.2,
            sub_shift_down=1.5,
            sup_drop=3.8,
            sub_drop=0.5,
            num_shift_up=6.8,
            denom_shift_down=2.7,
            rule_thickness=0.4,
            radical_rule_thickness=0.4,
            radical_extra_ascender=1.0,
            thin_mu_skip=3.0,
            med_mu_skip=4.0,
            thick_mu_skip=5.0,
            display_op_min_height=8.5
        )
    
    def _load_character_metrics(self):
        """Load character metrics (simplified for prototype)."""
        # In a real implementation, this would read from font files
        
        # Basic Latin letters (rough approximations)
        for char in "abcdefghijklmnopqrstuvwxyz":
            self._char_metrics[char] = CharacterMetrics(
                width=5.5, height=4.3, depth=0.0, italic_correction=0.5
            )
        
        for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            self._char_metrics[char] = CharacterMetrics(
                width=7.0, height=6.8, depth=0.0, italic_correction=0.3
            )
        
        # Digits
        for char in "0123456789":
            self._char_metrics[char] = CharacterMetrics(
                width=5.0, height=6.2, depth=0.0
            )
        
        # Common operators
        operators = {
            '+': CharacterMetrics(7.8, 5.8, 0.8),
            '-': CharacterMetrics(7.8, 2.3, 0.0),
            '=': CharacterMetrics(7.8, 3.9, -1.1),
            '<': CharacterMetrics(7.8, 5.4, 0.4),
            '>': CharacterMetrics(7.8, 5.4, 0.4),
            '(': CharacterMetrics(3.9, 7.5, 2.5),
            ')': CharacterMetrics(3.9, 7.5, 2.5),
            '[': CharacterMetrics(2.8, 7.5, 2.5),
            ']': CharacterMetrics(2.8, 7.5, 2.5),
            '{': CharacterMetrics(3.9, 7.5, 2.5),
            '}': CharacterMetrics(3.9, 7.5, 2.5),
        }
        
        self._char_metrics.update(operators)
        
        # Greek letters (common ones)
        greek = {
            'α': CharacterMetrics(5.7, 4.3, 0.0, italic_correction=0.4),
            'β': CharacterMetrics(5.1, 6.9, 1.9, italic_correction=0.2),
            'γ': CharacterMetrics(5.1, 4.3, 1.9, italic_correction=0.4),
            'δ': CharacterMetrics(4.6, 6.9, 0.0, italic_correction=0.3),
            'π': CharacterMetrics(5.7, 4.3, 0.0, italic_correction=0.4),
            'θ': CharacterMetrics(5.1, 6.9, 0.0, italic_correction=0.3),
            'λ': CharacterMetrics(5.1, 6.9, 0.0, italic_correction=0.4),
            'μ': CharacterMetrics(5.7, 4.3, 1.9, italic_correction=0.4),
            'σ': CharacterMetrics(5.7, 4.3, 0.0, italic_correction=0.4),
            'φ': CharacterMetrics(6.1, 6.9, 1.9, italic_correction=0.3),
            'ω': CharacterMetrics(6.1, 4.3, 0.0, italic_correction=0.4),
        }
        
        self._char_metrics.update(greek)
    
    def get_char_metrics(self, char: str) -> Optional[CharacterMetrics]:
        """Get metrics for a specific character."""
        return self._char_metrics.get(char)
    
    def get_font_parameters(self) -> FontParameters:
        """Get font parameters for mathematical layout."""
        return self._font_params
    
    def get_operator_spacing(self, left_type: str, right_type: str) -> float:
        """
        Get spacing between two mathematical elements.
        
        This implements TeX's spacing table for mathematical operators.
        In the full implementation, this would be a comprehensive lookup table.
        """
        # Simplified spacing rules
        spacing_rules = {
            ('atom', 'operator'): self._font_params.med_mu_skip,
            ('operator', 'atom'): self._font_params.med_mu_skip,
            ('atom', 'relation'): self._font_params.thick_mu_skip,
            ('relation', 'atom'): self._font_params.thick_mu_skip,
            ('operator', 'relation'): self._font_params.thick_mu_skip,
            ('relation', 'operator'): self._font_params.thick_mu_skip,
            ('atom', 'punctuation'): 0.0,
            ('punctuation', 'atom'): self._font_params.thin_mu_skip,
            ('opening', 'atom'): 0.0,
            ('atom', 'closing'): 0.0,
        }
        
        return spacing_rules.get((left_type, right_type), 0.0)
    
    def scale_for_style(self, size: float, style: FontStyle) -> float:
        """Scale measurements for different math styles."""
        # TeX uses different scaling factors for different contexts
        style_scales = {
            FontStyle.ROMAN: 1.0,
            FontStyle.ITALIC: 1.0,
            FontStyle.SCRIPT: 0.7,      # Superscripts/subscripts
            FontStyle.BOLD: 1.0,
        }
        
        return size * style_scales.get(style, 1.0)
    
    def get_large_operator_metrics(self, operator: str, display_style: bool = False) -> CharacterMetrics:
        """
        Get metrics for large operators (∫, ∑, ∏, etc.).
        
        Large operators have different sizes in display vs inline math.
        """
        base_metrics = self.get_char_metrics(operator)
        if not base_metrics:
            # Default large operator metrics
            base_metrics = CharacterMetrics(8.0, 8.5, 2.0)
        
        if display_style:
            # Scale up for display math
            return CharacterMetrics(
                width=base_metrics.width * 1.4,
                height=base_metrics.height * 1.4,
                depth=base_metrics.depth * 1.4,
                italic_correction=base_metrics.italic_correction * 1.4
            )
        
        return base_metrics


# Global font metrics instance (simplified for prototype)
default_math_font = MathFontMetrics("Computer Modern Math")
