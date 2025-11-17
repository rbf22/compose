from compose_app.math_pdf_layout import (
    SymbolBox,
    SuperBox,
    SubBox,
    SupSubBox,
    FractionBox,
    parse_latex_to_box,
)


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
