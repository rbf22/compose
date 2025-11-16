"""Rendering options container mirroring KaTeX's Options.js."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .font_metrics import get_global_metrics
from .style import Style, DEFAULT_STYLES


SIZE_STYLE_MAP: List[List[int]] = [
    [1, 1, 1],
    [2, 1, 1],
    [3, 1, 1],
    [4, 2, 1],
    [5, 2, 1],
    [6, 3, 1],
    [7, 4, 2],
    [8, 6, 3],
    [9, 7, 6],
    [10, 8, 7],
    [11, 10, 9],
]

SIZE_MULTIPLIERS: List[float] = [
    0.5,
    0.6,
    0.7,
    0.8,
    0.9,
    1.0,
    1.2,
    1.44,
    1.728,
    2.074,
    2.488,
]

FontWeight = str
FontShape = str


def size_at_style(size: int, style: Style) -> int:
    if style.size < 2:
        return size
    return SIZE_STYLE_MAP[size - 1][style.size - 1]


@dataclass
class Options:
    style: Style
    color: Optional[str]
    size: int
    text_size: int
    phantom: bool
    font: str
    font_family: str
    font_weight: FontWeight
    font_shape: FontShape
    size_multiplier: float
    max_size: float
    min_rule_thickness: float
    _font_metrics: Optional[Dict[str, float]] = None

    BASESIZE: int = 6

    def __init__(
        self,
        style: Style,
        color: Optional[str] = None,
        size: Optional[int] = None,
        text_size: Optional[int] = None,
        phantom: bool = False,
        font: str = "",
        font_family: str = "",
        font_weight: FontWeight = "",
        font_shape: FontShape = "",
        max_size: float = float("inf"),
        min_rule_thickness: float = 0.0,
    ) -> None:
        self.style = style
        self.color = color
        self.size = size or self.BASESIZE
        self.text_size = text_size or self.size
        self.phantom = phantom
        self.font = font
        self.font_family = font_family
        self.font_weight = font_weight
        self.font_shape = font_shape
        self.size_multiplier = SIZE_MULTIPLIERS[self.size - 1]
        self.max_size = max_size
        self.min_rule_thickness = min_rule_thickness
        self._font_metrics = None

    # ------------------------------------------------------------------
    # Factory helpers

    def _clone(self, **overrides: Any) -> "Options":
        params = {
            "style": overrides.get("style", self.style),
            "color": overrides.get("color", self.color),
            "size": overrides.get("size", self.size),
            "text_size": overrides.get("text_size", self.text_size),
            "phantom": overrides.get("phantom", self.phantom),
            "font": overrides.get("font", self.font),
            "font_family": overrides.get("font_family", self.font_family),
            "font_weight": overrides.get("font_weight", self.font_weight),
            "font_shape": overrides.get("font_shape", self.font_shape),
            "max_size": overrides.get("max_size", self.max_size),
            "min_rule_thickness": overrides.get("min_rule_thickness", self.min_rule_thickness),
        }
        clone = Options(**params)
        return clone

    def extend(self, **extension: Any) -> "Options":
        return self._clone(**extension)

    # ------------------------------------------------------------------
    # Style/size adjustments

    def having_style(self, style: Style) -> "Options":
        if self.style == style:
            return self
        return self.extend(style=style, size=size_at_style(self.text_size, style))

    def having_cramped_style(self) -> "Options":
        return self.having_style(self.style.cramp())

    def having_size(self, size: int) -> "Options":
        if self.size == size and self.text_size == size:
            return self
        return self.extend(
            style=self.style.text(),
            size=size,
            text_size=size,
            size_multiplier=SIZE_MULTIPLIERS[size - 1],
        )

    def having_base_style(self, style: Optional[Style] = None) -> "Options":
        target_style = style or self.style.text()
        want_size = size_at_style(self.BASESIZE, target_style)
        if (
            self.size == want_size
            and self.text_size == self.BASESIZE
            and self.style == target_style
        ):
            return self
        return self.extend(style=target_style, size=want_size, text_size=self.BASESIZE)

    def having_base_sizing(self) -> "Options":
        if self.style.id in (4, 5):
            size = 3
        elif self.style.id in (6, 7):
            size = 1
        else:
            size = 6
        return self.extend(style=self.style.text(), size=size)

    # ------------------------------------------------------------------
    # Font helpers

    def with_color(self, color: str) -> "Options":
        return self.extend(color=color)

    def with_phantom(self) -> "Options":
        return self.extend(phantom=True)

    def with_font(self, font: str) -> "Options":
        return self.extend(font=font)

    def with_text_font_family(self, font_family: str) -> "Options":
        return self.extend(font_family=font_family, font="")

    def with_text_font_weight(self, font_weight: FontWeight) -> "Options":
        return self.extend(font_weight=font_weight, font="")

    def with_text_font_shape(self, font_shape: FontShape) -> "Options":
        return self.extend(font_shape=font_shape, font="")

    # ------------------------------------------------------------------

    def sizing_classes(self, old: "Options") -> List[str]:
        if old.size != self.size:
            return ["sizing", f"reset-size{old.size}", f"size{self.size}"]
        return []

    def base_sizing_classes(self) -> List[str]:
        if self.size != self.BASESIZE:
            return ["sizing", f"reset-size{self.size}", f"size{self.BASESIZE}"]
        return []

    def font_metrics(self) -> Dict[str, float]:
        if self._font_metrics is None:
            self._font_metrics = get_global_metrics(self.size)
        return self._font_metrics

    def get_color(self) -> Optional[str]:
        if self.phantom:
            return "transparent"
        return self.color


def default_options() -> Options:
    return Options(
        style=DEFAULT_STYLES["text"],
        max_size=float("inf"),
        min_rule_thickness=0.0,
    )


__all__ = ["Options", "default_options", "size_at_style"]
