# compose/microtypography.py
"""
Micro-typography system for Compose.

Implements character protrusion (hanging punctuation), font expansion,
and optical margin alignment for professional typography.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class CharacterMetrics:
    """Typography metrics for a character"""
    width: float          # Character width
    left_bearing: float   # Left side bearing
    right_bearing: float  # Right side bearing
    protrusion_left: float   # How much to protrude left of margin
    protrusion_right: float  # How much to protrude right of margin


@dataclass
class LineAdjustment:
    """Adjustments to apply to a line of text"""
    left_protrusion: float = 0.0  # Amount to extend left margin
    right_protrusion: float = 0.0 # Amount to extend right margin
    expansion_ratio: float = 1.0  # Font expansion factor
    letter_spacing: float = 0.0   # Additional letter spacing


class MicroTypographyEngine:
    """
    Engine for micro-typography adjustments.

    Provides character protrusion, font expansion, and optical margin alignment.
    """

    def __init__(self):
        # Character protrusion tables (in em units)
        self.protrusion_table = self._build_protrusion_table()

        # Expansion parameters
        self.min_expansion = 0.95   # Minimum font scaling
        self.max_expansion = 1.05   # Maximum font scaling
        self.target_expansion = 1.02 # Target expansion for loose lines

        # Protrusion limits (maximum protrusion in em units)
        self.max_protrusion = 0.1

    def _build_protrusion_table(self) -> Dict[str, Dict[str, float]]:
        """
        Build character protrusion table.

        Returns dictionary mapping characters to protrusion values
        for left/right margins.
        """
        return {
            # Punctuation that can hang left/right
            '"': {'left': 0.3, 'right': 0.05},
            "'": {'left': 0.2, 'right': 0.0},
            '(': {'left': 0.1, 'right': 0.0},
            '[': {'left': 0.1, 'right': 0.0},
            '{': {'left': 0.1, 'right': 0.0},

            # Punctuation that can hang right
            ')': {'left': 0.0, 'right': 0.1},
            ']': {'left': 0.0, 'right': 0.1},
            '}': {'left': 0.0, 'right': 0.1},
            ',': {'left': 0.0, 'right': 0.05},
            '.': {'left': 0.0, 'right': 0.05},
            ';': {'left': 0.0, 'right': 0.05},
            ':': {'left': 0.0, 'right': 0.05},
            '!': {'left': 0.0, 'right': 0.05},
            '?': {'left': 0.0, 'right': 0.05},
            '-': {'left': 0.0, 'right': 0.03},
            '–': {'left': 0.0, 'right': 0.03},  # en dash
            '—': {'left': 0.0, 'right': 0.03},  # em dash
        }

    def adjust_line(self, line_text: str, line_width: float,
                   target_width: float, font_size: float = 12.0) -> LineAdjustment:
        """
        Calculate micro-typography adjustments for a line.

        Args:
            line_text: The text of the line
            line_width: Current width of the line
            target_width: Target width (usually column width)
            font_size: Font size in points

        Returns:
            LineAdjustment with recommended changes
        """
        adjustment = LineAdjustment()

        # Calculate width difference
        width_diff = target_width - line_width

        # Apply character protrusion first
        left_protrusion, right_protrusion = self._calculate_protrusion(line_text, font_size)
        adjustment.left_protrusion = left_protrusion
        adjustment.right_protrusion = right_protrusion

        # Adjust for protrusion
        effective_width_diff = width_diff + left_protrusion + right_protrusion

        # Apply font expansion if still needed
        if abs(effective_width_diff) > 0.1:  # More than 0.1pt difference
            expansion = self._calculate_expansion(effective_width_diff, line_text, font_size)
            adjustment.expansion_ratio = expansion

        # Calculate letter spacing as fallback
        if abs(width_diff) > 0.5 and adjustment.expansion_ratio == 1.0:
            # Calculate additional letter spacing
            char_count = len(line_text.strip())
            if char_count > 1:
                spacing_per_char = width_diff / (char_count - 1)
                adjustment.letter_spacing = max(-0.5, min(0.5, spacing_per_char))  # Limit spacing

        return adjustment

    def _calculate_protrusion(self, line_text: str, font_size: float) -> Tuple[float, float]:
        """
        Calculate how much the line can protrude from margins.

        Returns:
            (left_protrusion, right_protrusion) in points
        """
        if not line_text.strip():
            return 0.0, 0.0

        # Convert em units to points (1 em = font_size)
        em_to_points = font_size

        # Check first character for left protrusion
        first_char = line_text.strip()[0] if line_text.strip() else ''
        left_protrusion = 0.0
        if first_char in self.protrusion_table:
            left_em = self.protrusion_table[first_char]['left']
            left_protrusion = min(left_em * em_to_points, self.max_protrusion * em_to_points)

        # Check last character for right protrusion
        last_char = line_text.strip()[-1] if line_text.strip() else ''
        right_protrusion = 0.0
        if last_char in self.protrusion_table:
            right_em = self.protrusion_table[last_char]['right']
            right_protrusion = min(right_em * em_to_points, self.max_protrusion * em_to_points)

        return left_protrusion, right_protrusion

    def _calculate_expansion(self, width_diff: float, line_text: str, font_size: float) -> float:
        """
        Calculate font expansion ratio to fit line to target width.

        Args:
            width_diff: How much to expand (positive) or compress (negative)
            line_text: The text being adjusted
            font_size: Current font size

        Returns:
            Expansion ratio (1.0 = no change)
        """
        if not line_text.strip():
            return 1.0

        # Estimate current width (simplified)
        current_width = len(line_text.strip()) * font_size * 0.5  # Rough estimate

        if current_width <= 0:
            return 1.0

        # Calculate target expansion ratio
        target_ratio = (current_width + width_diff) / current_width

        # Clamp to reasonable bounds
        expansion_ratio = max(self.min_expansion, min(self.max_expansion, target_ratio))

        return expansion_ratio

    def apply_optical_alignment(self, lines: List[str], alignment: str = "left") -> List[str]:
        """
        Apply optical margin alignment to a block of text.

        Args:
            lines: List of text lines
            alignment: "left", "right", or "justified"

        Returns:
            Lines with optical alignment applied
        """
        if alignment not in ["left", "right", "justified"]:
            return lines

        aligned_lines = []

        for line in lines:
            if alignment == "left":
                # Left alignment with optical margin
                aligned_lines.append(self._align_left_optical(line))
            elif alignment == "right":
                # Right alignment with optical margin
                aligned_lines.append(self._align_right_optical(line))
            elif alignment == "justified":
                # Justified with optical margins
                aligned_lines.append(self._justify_optical(line))

        return aligned_lines

    def _align_left_optical(self, line: str) -> str:
        """Apply optical alignment for left-aligned text"""
        # For left alignment, we mainly care about the first character
        # In a real implementation, this would adjust spacing
        return line  # Simplified for now

    def _align_right_optical(self, line: str) -> str:
        """Apply optical alignment for right-aligned text"""
        # For right alignment, we care about the last character
        # In a real implementation, this would adjust spacing
        return line  # Simplified for now

    def _justify_optical(self, line: str) -> str:
        """Apply optical alignment for justified text"""
        # For justified text, both ends matter
        # In a real implementation, this would adjust word spacing
        return line  # Simplified for now

    def enhance_paragraph(self, paragraph: str, line_width: float = 80) -> str:
        """
        Apply micro-typography enhancements to a paragraph.

        Args:
            paragraph: Text paragraph
            line_width: Target line width in characters

        Returns:
            Enhanced paragraph text
        """
        lines = paragraph.split('\n')
        enhanced_lines = []

        for line in lines:
            if not line.strip():
                enhanced_lines.append(line)
                continue

            # Calculate adjustments for this line
            current_width = len(line)
            adjustment = self.adjust_line(line, current_width, line_width)

            # Apply adjustments (simplified - in real implementation would modify rendering)
            enhanced_line = line

            # Add comments showing what adjustments would be made
            if adjustment.left_protrusion > 0 or adjustment.right_protrusion > 0:
                enhanced_line += f" % protrusion: L{adjustment.left_protrusion:.1f} R{adjustment.right_protrusion:.1f}"

            if adjustment.expansion_ratio != 1.0:
                enhanced_line += f" % expansion: {adjustment.expansion_ratio:.3f}"

            if adjustment.letter_spacing != 0.0:
                enhanced_line += f" % spacing: {adjustment.letter_spacing:.1f}pt"

            enhanced_lines.append(enhanced_line)

        return '\n'.join(enhanced_lines)


# Global micro-typography engine
microtypography_engine = MicroTypographyEngine()


# Convenience functions
def adjust_line(line_text: str, line_width: float, target_width: float,
               font_size: float = 12.0) -> LineAdjustment:
    """Calculate line adjustments"""
    return microtypography_engine.adjust_line(line_text, line_width, target_width, font_size)


def enhance_paragraph(paragraph: str, line_width: float = 80) -> str:
    """Apply micro-typography to a paragraph"""
    return microtypography_engine.enhance_paragraph(paragraph, line_width)


def apply_optical_alignment(lines: List[str], alignment: str = "left") -> List[str]:
    """Apply optical alignment to text lines"""
    return microtypography_engine.apply_optical_alignment(lines, alignment)


# Example usage:
# adjustment = microtypography_engine.adjust_line("Hello, world!", 13, 80)
# print(f"Protrusion: L{adjustment.left_protrusion:.1f} R{adjustment.right_protrusion:.1f}")
# print(f"Expansion: {adjustment.expansion_ratio:.3f}")
