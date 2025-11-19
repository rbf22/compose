"""Font metric helpers ported from KaTeX."""

from __future__ import annotations

from typing import cast

from .unicode_scripts import supported_codepoint

SIGMAS_AND_XIS: dict[str, tuple[float, float, float]] = {
    "slant": (0.250, 0.250, 0.250),
    "space": (0.000, 0.000, 0.000),
    "stretch": (0.000, 0.000, 0.000),
    "shrink": (0.000, 0.000, 0.000),
    "xHeight": (0.431, 0.431, 0.431),
    "quad": (1.000, 1.171, 1.472),
    "extraSpace": (0.000, 0.000, 0.000),
    "num1": (0.677, 0.732, 0.925),
    "num2": (0.394, 0.384, 0.387),
    "num3": (0.444, 0.471, 0.504),
    "denom1": (0.686, 0.752, 1.025),
    "denom2": (0.345, 0.344, 0.532),
    "sup1": (0.413, 0.503, 0.504),
    "sup2": (0.363, 0.431, 0.404),
    "sup3": (0.289, 0.286, 0.294),
    "sub1": (0.150, 0.143, 0.200),
    "sub2": (0.247, 0.286, 0.400),
    "supDrop": (0.386, 0.353, 0.494),
    "subDrop": (0.050, 0.071, 0.100),
    "delim1": (2.390, 1.700, 1.980),
    "delim2": (1.010, 1.157, 1.420),
    "axisHeight": (0.250, 0.250, 0.250),
    "defaultRuleThickness": (0.040, 0.049, 0.049),
    "bigOpSpacing1": (0.111, 0.111, 0.111),
    "bigOpSpacing2": (0.166, 0.166, 0.166),
    "bigOpSpacing3": (0.200, 0.200, 0.200),
    "bigOpSpacing4": (0.600, 0.611, 0.611),
    "bigOpSpacing5": (0.100, 0.143, 0.143),
    "sqrtRuleThickness": (0.040, 0.040, 0.040),
    "ptPerEm": (10.0, 10.0, 10.0),
    "doubleRuleSep": (0.200, 0.200, 0.200),
    "arrayRuleWidth": (0.040, 0.040, 0.040),
    "fboxsep": (0.300, 0.300, 0.300),
    "fboxrule": (0.040, 0.040, 0.040),
}

EXTRA_CHARACTER_MAP = {
    "Å": "A",
    "Ð": "D",
    "Þ": "o",
    "å": "a",
    "ð": "d",
    "þ": "o",
    "А": "A",
    "Б": "B",
    "В": "B",
    "Г": "F",
    "Д": "A",
    "Е": "E",
    "Ж": "K",
    "З": "3",
    "И": "N",
    "Й": "N",
    "К": "K",
    "Л": "N",
    "М": "M",
    "Н": "H",
    "О": "O",
    "П": "N",
    "Р": "P",
    "С": "C",
    "Т": "T",
    "У": "y",
    "Ф": "O",
    "Х": "X",
    "Ц": "U",
    "Ч": "h",
    "Ш": "W",
    "Щ": "W",
    "Ъ": "B",
    "Ы": "X",
    "Ь": "B",
    "Э": "3",
    "Ю": "X",
    "Я": "R",
    "а": "a",
    "б": "b",
    "в": "a",
    "г": "r",
    "д": "y",
    "е": "e",
    "ж": "m",
    "з": "e",
    "и": "n",
    "й": "n",
    "к": "n",
    "л": "n",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "n",
    "р": "p",
    "с": "c",
    "т": "o",
    "у": "y",
    "ф": "b",
    "х": "x",
    "ц": "n",
    "ч": "n",
    "ш": "w",
    "щ": "w",
    "ъ": "a",
    "ы": "m",
    "ь": "a",
    "э": "e",
    "ю": "m",
    "я": "r",
}

MetricMap = dict[str, dict[int, tuple[float, float, float, float, float]]]
_metric_map: MetricMap = {}
_font_metrics_by_size_index: dict[int, dict[str, float]] = {}


def set_font_metrics(font_name: str, metrics: dict[int, tuple[float, float, float, float, float]]) -> None:
    _metric_map[font_name] = metrics


def load_metrics(metric_map: dict[str, dict[str, list[float]]]) -> None:
    for font, data in metric_map.items():
        parsed = {int(code): tuple(values) for code, values in data.items()}
        set_font_metrics(
            font,
            cast(dict[int, tuple[float, float, float, float, float]], parsed),
        )


def get_character_metrics(character: str, font: str, mode: str) -> dict[str, float] | None:
    if font not in _metric_map:
        raise KeyError(f"Font metrics not found for font: {font}.")

    ch = ord(character[0])
    metrics = _metric_map[font].get(ch)

    if metrics is None and character[0] in EXTRA_CHARACTER_MAP:
        ch = ord(EXTRA_CHARACTER_MAP[character[0]])
        metrics = _metric_map[font].get(ch)

    if metrics is None and mode == "text" and supported_codepoint(ch):
        metrics = _metric_map[font].get(77)  # 'M'

    if metrics is None:
        return None

    depth, height, italic, skew, width = metrics
    return {
        "depth": depth,
        "height": height,
        "italic": italic,
        "skew": skew,
        "width": width,
    }


def get_global_metrics(size: int) -> dict[str, float]:
    if size >= 5:
        size_index = 0
    elif size >= 3:
        size_index = 1
    else:
        size_index = 2

    if size_index not in _font_metrics_by_size_index:
        metrics = {"cssEmPerMu": SIGMAS_AND_XIS["quad"][size_index] / 18}
        for key, value in SIGMAS_AND_XIS.items():
            metrics[key] = value[size_index]
        _font_metrics_by_size_index[size_index] = metrics
    return _font_metrics_by_size_index[size_index]


__all__ = [
    "set_font_metrics",
    "load_metrics",
    "get_character_metrics",
    "get_global_metrics",
    "SIGMAS_AND_XIS",
]
