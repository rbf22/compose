# compose/layout/knuth_plass.py
"""
Knuth-Plass line breaking algorithm implementation for Compose.

This implements the classic dynamic programming algorithm for optimal line breaking
in typography, adapted for both text and mathematical content.
"""

from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class BreakType(Enum):
    """Types of line breaks"""
    NORMAL = "normal"      # Regular line break
    FORCE = "force"        # Forced break (e.g., paragraph end)
    PREVENT = "prevent"    # Prevent break (e.g., don't break here)


@dataclass
class Breakpoint:
    """A potential line breaking point"""
    position: int          # Position in the text/items
    width: float          # Width from previous breakpoint to this one
    stretch: float        # Stretchability (glue)
    shrink: float         # Shrinkability (glue)
    penalty: float        # Break penalty
    break_type: BreakType
    is_hyphenated: bool   # Whether this break includes hyphenation


@dataclass
class LineBreak:
    """A computed line break"""
    start_position: int
    end_position: int
    width: float
    adjustment_ratio: float  # How much to stretch/shrink
    demerits: float         # Quality score


class KnuthPlassBreaker:
    """
    Implementation of the Knuth-Plass line breaking algorithm.

    This finds the optimal way to break paragraphs into lines by minimizing
    a demerits function that considers:
    - Badness of line spacing (stretch/shrink)
    - Penalties for breaking at certain points
    - Bonus for breaking at good points
    """

    def __init__(self, line_width: float, tolerance: float = 100.0):
        """
        Initialize the line breaker.

        Args:
            line_width: Target width for each line
            tolerance: Maximum allowed badness (higher = more tolerant)
        """
        self.line_width = line_width
        self.tolerance = tolerance

        # Algorithm parameters (from TeX)
        self.looseness = 0  # Allow stretching beyond tolerance
        self.paragraph_indent = 0.0
        self.emergency_stretch = 0.0  # Emergency stretchability

        # Fitness classes for different line types
        self.fitness_classes = {
            'tight': 0,     # Very tight line
            'decent': 1,    # Decent spacing
            'loose': 2,     # Loose spacing
            'very_loose': 3 # Very loose spacing
        }

    def find_optimal_breaks(self, breakpoints: List[Breakpoint]) -> List[LineBreak]:
        """
        Find optimal line breaks using dynamic programming.

        Args:
            breakpoints: List of potential breaking points

        Returns:
            List of optimal line breaks
        """
        if not breakpoints:
            return []

        n = len(breakpoints)

        # Dynamic programming tables
        active_lines = []  # Active (incomplete) lines
        best_breaks = {}   # Best predecessor for each breakpoint
        line_costs = {}    # Cost to reach each breakpoint

        # Initialize with starting point
        start_breakpoint = Breakpoint(0, 0, 0, 0, 0, BreakType.NORMAL, False)
        active_lines.append((0, 0, start_breakpoint))  # (position, fitness_class, breakpoint)
        line_costs[0] = 0

        for j in range(1, n):
            current_breakpoint = breakpoints[j]

            # Consider all possible predecessors
            best_predecessor = None
            best_cost = float('inf')
            best_fitness = None

            for position, fitness_class, prev_breakpoint in active_lines:
                # Calculate line width from position to j
                line_width = self._calculate_line_width(breakpoints, position, j)
                if line_width > self.line_width * 2:  # Skip impossibly long lines
                    continue

                # Calculate adjustment ratio and badness
                adjustment_ratio, badness = self._calculate_badness(line_width)

                if badness > self.tolerance:
                    continue

                # Calculate demerits for this break
                demerits = self._calculate_demerits(
                    badness, current_breakpoint.penalty,
                    fitness_class, self._get_fitness_class(adjustment_ratio)
                )

                total_cost = line_costs[position] + demerits

                if total_cost < best_cost:
                    best_cost = total_cost
                    best_predecessor = (position, fitness_class, prev_breakpoint)
                    best_fitness = self._get_fitness_class(adjustment_ratio)

            if best_predecessor is not None:
                best_breaks[j] = best_predecessor
                line_costs[j] = best_cost
                active_lines.append((j, best_fitness, current_breakpoint))

        # Find optimal path
        return self._reconstruct_breaks(best_breaks, n - 1, breakpoints)

    def _calculate_line_width(self, breakpoints: List[Breakpoint], start: int, end: int) -> float:
        """Calculate the width of a line from start to end breakpoint"""
        width = 0
        for i in range(start + 1, end + 1):
            width += breakpoints[i].width
        return width

    def _calculate_badness(self, line_width: float) -> Tuple[float, float]:
        """
        Calculate adjustment ratio and badness for a line.

        Returns:
            (adjustment_ratio, badness)
        """
        if line_width < self.line_width:
            # Line is too short, needs stretching
            adjustment_ratio = (self.line_width - line_width) / max(line_width * 0.5, 1)
        elif line_width > self.line_width:
            # Line is too long, needs shrinking
            adjustment_ratio = (line_width - self.line_width) / max(line_width * 0.5, 1)
        else:
            adjustment_ratio = 0

        # Badness is roughly proportional to adjustment ratio squared
        badness = 100 * abs(adjustment_ratio) ** 3
        return adjustment_ratio, badness

    def _calculate_demerits(self, badness: float, penalty: float,
                           prev_fitness: int, current_fitness: int) -> float:
        """Calculate demerits for a potential line break"""
        # Base demerits from badness and penalty
        demerits = (1 + badness + penalty) ** 2

        # Add penalty for consecutive fitness class changes
        if abs(prev_fitness - current_fitness) > 1:
            demerits *= 2

        return demerits

    def _get_fitness_class(self, adjustment_ratio: float) -> int:
        """Determine fitness class based on adjustment ratio"""
        ratio = abs(adjustment_ratio)
        if ratio < 0.5:
            return self.fitness_classes['decent']
        elif ratio < 1.0:
            return self.fitness_classes['tight'] if adjustment_ratio < 0 else self.fitness_classes['loose']
        else:
            return self.fitness_classes['very_loose']

    def _reconstruct_breaks(self, best_breaks: Dict[int, Tuple],
                           end_position: int, breakpoints: List[Breakpoint]) -> List[LineBreak]:
        """Reconstruct the optimal sequence of line breaks"""
        breaks = []
        current = end_position

        while current > 0:
            if current not in best_breaks:
                break

            prev_position, fitness_class, prev_breakpoint = best_breaks[current]
            current_breakpoint = breakpoints[current]

            # Calculate line properties
            line_width = self._calculate_line_width(breakpoints, prev_position, current)
            adjustment_ratio, badness = self._calculate_badness(line_width)

            line_break = LineBreak(
                start_position=prev_position,
                end_position=current,
                width=line_width,
                adjustment_ratio=adjustment_ratio,
                demerits=badness  # Simplified
            )

            breaks.insert(0, line_break)
            current = prev_position

        return breaks


class MathKnuthPlassBreaker(KnuthPlassBreaker):
    """
    Specialized Knuth-Plass breaker for mathematical expressions.

    Handles math-specific breaking rules and penalties.
    """

    def __init__(self, line_width: float, tolerance: float = 200.0):
        super().__init__(line_width, tolerance)
        # Math expressions can tolerate more stretching/shrinking
        self.emergency_stretch = 2.0

    def _calculate_badness(self, line_width: float) -> Tuple[float, float]:
        """
        Math-specific badness calculation.

        Math expressions can tolerate more variation than regular text.
        """
        adjustment_ratio, badness = super()._calculate_badness(line_width)

        # Math can stretch/shrink more before becoming "bad"
        if abs(adjustment_ratio) > 2.0:
            badness *= 2  # Penalize extreme stretching more

        return adjustment_ratio, badness

    def _calculate_demerits(self, badness: float, penalty: float,
                           prev_fitness: int, current_fitness: int) -> float:
        """Math-specific demerits calculation"""
        # Math has higher penalties for breaking within expressions
        if penalty > 0:  # Breaking penalty
            penalty *= 2  # Math breaking is more costly

        return super()._calculate_demerits(badness, penalty, prev_fitness, current_fitness)


def create_breakpoints_from_text(text: str, font_metrics: Dict[str, Any]) -> List[Breakpoint]:
    """
    Create breakpoints from plain text.

    Args:
        text: Input text
        font_metrics: Font metrics for width calculation

    Returns:
        List of breakpoints
    """
    breakpoints = [Breakpoint(0, 0, 0, 0, 0, BreakType.NORMAL, False)]

    words = text.split()
    current_position = 0

    for word in words:
        word_width = len(word) * 0.6  # Simplified width calculation

        # Space between words (glue)
        space_width = 0.25
        space_stretch = 0.15
        space_shrink = 0.05

        # Add breakpoint after word
        breakpoint = Breakpoint(
            position=current_position + len(word),
            width=word_width + space_width,
            stretch=space_stretch,
            shrink=space_shrink,
            penalty=0,  # Normal break
            break_type=BreakType.NORMAL,
            is_hyphenated=False
        )

        breakpoints.append(breakpoint)
        current_position += len(word) + 1

    return breakpoints


# Example usage:
# breaker = KnuthPlassBreaker(line_width=80)
# breakpoints = create_breakpoints_from_text("Your text here", font_metrics)
# breaks = breaker.find_optimal_breaks(breakpoints)
