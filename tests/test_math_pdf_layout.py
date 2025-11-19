import pytest

from compose.math_pdf_layout import (
    FractionBox,
    SqrtBox,
    SubBox,
    SuperBox,
    SupSubBox,
    SymbolBox,
    measure_math_box,
    parse_latex_to_box,
)
from pytex.font_metrics import get_global_metrics, load_metrics
from pytex.font_metrics_data import FONT_METRICS_DATA


def test_parse_superscript_simple() -> None:
    box = parse_latex_to_box("x^2")
    assert isinstance(box, SuperBox)
    assert isinstance(box.base, SymbolBox)
    assert isinstance(box.superscript, SymbolBox)
    assert box.base.text == "x"
    assert box.superscript.text == "2"


def test_parse_superscript_braced() -> None:
    box = parse_latex_to_box("x^{2}")
    assert isinstance(box, SuperBox)
    assert isinstance(box.base, SymbolBox)
    assert isinstance(box.superscript, SymbolBox)
    assert box.base.text == "x"
    assert box.superscript.text == "2"


def test_parse_fraction_simple() -> None:
    box = parse_latex_to_box(r"\frac{a}{b}")
    assert isinstance(box, FractionBox)
    assert isinstance(box.numerator, SymbolBox)
    assert isinstance(box.denominator, SymbolBox)
    assert box.numerator.text == "a"
    assert box.denominator.text == "b"


def test_parse_unsupported_returns_none() -> None:
    assert parse_latex_to_box("") is None
    assert parse_latex_to_box(r"\frac{a}{b}{extra}") is None


def test_parse_subscript_simple() -> None:
    box = parse_latex_to_box("x_1")
    assert isinstance(box, SubBox)
    assert isinstance(box.base, SymbolBox)
    assert isinstance(box.subscript, SymbolBox)
    assert box.base.text == "x"
    assert box.subscript.text == "1"


def test_parse_supsub_simple() -> None:
    box = parse_latex_to_box("x_1^2")
    assert isinstance(box, SupSubBox)
    assert isinstance(box.base, SymbolBox)
    assert isinstance(box.subscript, SymbolBox)
    assert isinstance(box.superscript, SymbolBox)
    assert box.base.text == "x"
    assert box.subscript.text == "1"
    assert box.superscript.text == "2"


def test_parse_nested_fraction_with_sup() -> None:
    box = parse_latex_to_box(r"\frac{x^2}{y_1}")
    assert isinstance(box, FractionBox)
    assert isinstance(box.numerator, SuperBox)
    assert isinstance(box.denominator, SubBox)


class _DummyPdf:
    def __init__(self) -> None:
        self.font_family = ""
        self.font_size = 0

    def set_font(self, family: str, size: int) -> None:  # type: ignore[override]
        self.font_family = family
        self.font_size = size

    def get_string_width(self, text: str) -> float:  # type: ignore[override]
        return len(text) * (self.font_size * 0.5)


def test_metrics_superscript_increases_height() -> None:
    box_base = parse_latex_to_box("x")
    box_sup = parse_latex_to_box("x^2")
    assert isinstance(box_base, SymbolBox)
    assert isinstance(box_sup, SuperBox)

    pdf = _DummyPdf()
    font_family = "Helvetica"
    font_size = 10

    base_metrics = measure_math_box(pdf, box_base, font_family, font_size)
    sup_metrics = measure_math_box(pdf, box_sup, font_family, font_size)

    assert sup_metrics.height > base_metrics.height
    assert sup_metrics.depth >= base_metrics.depth


def test_metrics_fraction_increases_height_and_depth() -> None:
    box_base = parse_latex_to_box("x")
    box_frac = parse_latex_to_box(r"\frac{x}{y}")
    assert isinstance(box_base, SymbolBox)
    assert isinstance(box_frac, FractionBox)

    pdf = _DummyPdf()
    font_family = "Helvetica"
    font_size = 10

    base_metrics = measure_math_box(pdf, box_base, font_family, font_size)
    frac_metrics = measure_math_box(pdf, box_frac, font_family, font_size)

    assert frac_metrics.height > base_metrics.height
    assert frac_metrics.depth > base_metrics.depth


def test_metrics_sqrt_adds_axis_height_padding() -> None:
    load_metrics(FONT_METRICS_DATA)
    global_metrics = get_global_metrics(5)
    axis_height = float(global_metrics["axisHeight"])
    sqrt_rule = float(global_metrics["sqrtRuleThickness"])

    box_base = parse_latex_to_box("x")
    box_sqrt = parse_latex_to_box(r"\sqrt{x}")
    assert isinstance(box_base, SymbolBox)
    assert isinstance(box_sqrt, SqrtBox)

    pdf = _DummyPdf()
    font_family = "Helvetica"
    font_size = 10

    base_metrics = measure_math_box(pdf, box_base, font_family, font_size)
    sqrt_metrics = measure_math_box(pdf, box_sqrt, font_family, font_size)

    extra_height = sqrt_metrics.height - base_metrics.height
    expected_extra = (axis_height + sqrt_rule) * font_size
    assert extra_height == pytest.approx(expected_extra, rel=1e-3)
