"""Unit conversion utilities for the Python KaTeX renderer."""

from __future__ import annotations

from typing import TypedDict

from .options import Options
from .parse_error import ParseError

PT_PER_UNIT: dict[str, float] = {
    "pt": 1.0,
    "mm": 7227 / 2540,
    "cm": 7227 / 254,
    "in": 72.27,
    "bp": 803 / 800,
    "pc": 12.0,
    "dd": 1238 / 1157,
    "cc": 14856 / 1157,
    "nd": 685 / 642,
    "nc": 1370 / 107,
    "sp": 1 / 65536,
    "px": 803 / 800,
}

RELATIVE_UNITS = {"ex", "em", "mu"}


class Measurement(TypedDict):
    number: float
    unit: str


def valid_unit(unit: str) -> bool:
    return unit in PT_PER_UNIT or unit in RELATIVE_UNITS


def calculate_size(size_value: Measurement, options: Options) -> float:
    number = size_value["number"]
    unit = size_value["unit"]

    if unit in PT_PER_UNIT:
        scale = PT_PER_UNIT[unit] / options.font_metrics()["ptPerEm"] / options.size_multiplier
    elif unit == "mu":
        scale = options.font_metrics()["cssEmPerMu"]
    elif unit == "ex":
        unit_options = options.having_style(options.style.text()) if options.style.is_tight() else options
        scale = unit_options.font_metrics()["xHeight"]
        if unit_options is not options:
            scale *= unit_options.size_multiplier / options.size_multiplier
    elif unit == "em":
        unit_options = options.having_style(options.style.text()) if options.style.is_tight() else options
        scale = unit_options.font_metrics()["quad"]
        if unit_options is not options:
            scale *= unit_options.size_multiplier / options.size_multiplier
    else:
        raise ParseError(f"Invalid unit: '{unit}'")

    return min(number * scale, options.max_size)


def make_em(value: float) -> str:
    # Format with up to 4 decimal places, trimming trailing zeros and any
    # dangling decimal point so that e.g. 0.6250 -> 0.625 and 1.0000 -> 1.
    s = f"{value:.4f}"
    s = s.rstrip("0").rstrip(".") or "0"
    return f"{s}em"


__all__ = [
    "PT_PER_UNIT",
    "RELATIVE_UNITS",
    "Measurement",
    "valid_unit",
    "calculate_size",
    "make_em",
]
