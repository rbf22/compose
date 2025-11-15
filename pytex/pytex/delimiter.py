"""Python port of KaTeX's delimiter.js - delimiter sizing and rendering."""

from __future__ import annotations

from typing import Dict, List, Optional, Union

from .build_common import VListElem, make_span, make_svg_span, make_symbol, make_v_list
from .dom_tree import DomSpan, SvgSpan, SymbolNode
from .font_metrics import get_character_metrics
from .options import Options
from .parse_error import ParseError
from .style import Style
from .svg_geometry import make_square_root_path
from .types import Mode
from .units import make_em

# Placeholder - will be imported from generated data
try:
    from .symbols_data import symbols as SYMBOLS, ligatures as LIGATURES
except ImportError:
    SYMBOLS = {}
    LIGATURES = {}

try:
    from .font_metrics_data import FONT_METRICS_DATA
except ImportError:
    FONT_METRICS_DATA = {}


def get_metrics(symbol: str, font: str, mode: Mode) -> Optional[Dict[str, float]]:
    """Get metrics for symbol with replacements."""
    replace = SYMBOLS.get(mode, {}).get(symbol, {}).get("replace")
    return get_character_metrics(replace or symbol, font, mode)


def style_wrap(
    delim: Union[SymbolNode, DomSpan],
    to_style: Style,
    options: Options,
    classes: List[str],
) -> DomSpan:
    """Put delimiter in given style."""
    new_options = options.having_base_style(to_style)
    span = make_span(
        classes + new_options.sizing_classes(options),
        [delim],
        options
    )
    delim_size_multiplier = new_options.size_multiplier / options.size_multiplier
    span.height *= delim_size_multiplier
    span.depth *= delim_size_multiplier
    span.max_font_size = new_options.size_multiplier
    return span


def center_span(span: DomSpan, options: Options, style: Style) -> None:
    """Center delimiter around axis."""
    new_options = options.having_base_style(style)
    shift = (1 - options.size_multiplier / new_options.size_multiplier) * options.font_metrics()["axisHeight"]
    span.classes.append("delimcenter")
    span.style["top"] = make_em(shift)
    span.height -= shift
    span.depth += shift


def make_small_delim(
    delim: str,
    style: Style,
    center: bool,
    options: Options,
    mode: Mode,
    classes: List[str],
) -> DomSpan:
    """Make small delimiter in Main-Regular."""
    text = make_symbol(delim, "Main-Regular", mode, options)
    span = style_wrap(text, style, options, classes)
    if center:
        center_span(span, options, style)
    return span


def mathrm_size(value: str, size: int, mode: Mode, options: Options) -> SymbolNode:
    """Build symbol in SizeN-Regular."""
    return make_symbol(value, f"Size{size}-Regular", mode, options)


def make_large_delim(
    delim: str,
    size: int,
    center: bool,
    options: Options,
    mode: Mode,
    classes: List[str],
) -> DomSpan:
    """Make large delimiter in Size fonts."""
    inner = mathrm_size(delim, size, mode, options)
    span = style_wrap(
        make_span(["delimsizing", f"size{size}"], [inner], options),
        Style.TEXT,
        options,
        classes
    )
    if center:
        center_span(span, options, Style.TEXT)
    return span


def make_glyph_span(symbol: str, font: str, mode: Mode) -> VListElem:
    """Make glyph span for stacking."""
    size_class = "delim-size1" if font == "Size1-Regular" else "delim-size4"
    corner = make_span(
        ["delimsizinginner", size_class],
        [make_span([], [make_symbol(symbol, font, mode)])]
    )
    return {"type": "elem", "elem": corner}


def make_inner(ch: str, height: float, options: Options) -> VListElem:
    """Create SVG inner part of tall delimiter."""
    width = (
        FONT_METRICS_DATA.get("Size4-Regular", {}).get(ord(ch), [0, 0, 0, 0, 0])[4]
        or FONT_METRICS_DATA.get("Size1-Regular", {}).get(ord(ch), [0, 0, 0, 0, 0])[4]
    )
    svg_node = make_svg_span([], [], options)
    svg_node.attributes.update({
        "width": make_em(width),
        "height": make_em(height),
        "viewBox": f"0 0 {1000 * width} {round(1000 * height)}",
        "preserveAspectRatio": "xMinYMin",
    })
    span = make_svg_span(["overlay"], [svg_node], options)
    span.height = height
    span.style["height"] = make_em(height)
    span.style["width"] = make_em(width)
    return {"type": "elem", "elem": span}


# Constants
LAP_IN_EMS = 0.008
LAP = {"type": "kern", "size": -LAP_IN_EMS}
VERTS = ["|", "\\lvert", "\\rvert", "\\vert"]
DOUBLE_VERTS = ["\\|", "\\lVert", "\\rVert", "\\Vert"]


def make_stacked_delim(
    delim: str,
    height_total: float,
    center: bool,
    options: Options,
    mode: Mode,
    classes: List[str],
) -> DomSpan:
    """Make stacked delimiter of given height."""
    top = repeat = bottom = delim
    middle = None
    font = "Size1-Regular"

    # Special handling for different delimiters
    if delim == "\\uparrow":
        repeat = bottom = "\u23d0"
    elif delim == "\\Uparrow":
        repeat = bottom = "\u2016"
    elif delim == "\\downarrow":
        top = repeat = "\u23d0"
    elif delim == "\\Downarrow":
        top = repeat = "\u2016"
    elif delim == "\\updownarrow":
        top = "\\uparrow"
        repeat = "\u23d0"
        bottom = "\\downarrow"
    elif delim == "\\Updownarrow":
        top = "\\Uparrow"
        repeat = "\u2016"
        bottom = "\\Downarrow"
    elif delim in VERTS:
        repeat = "\u2223"
        font = "Size4-Regular"
    elif delim in DOUBLE_VERTS:
        repeat = "\u2225"
        font = "Size4-Regular"
    elif delim in ("[", "\\lbrack"):
        top = "\u23a1"
        repeat = "\u23a2"
        bottom = "\u23a3"
        font = "Size4-Regular"
    elif delim in ("]", "\\rbrack"):
        top = "\u23a4"
        repeat = "\u23a5"
        bottom = "\u23a6"
        font = "Size4-Regular"
    elif delim in ("\\lfloor", "\u230a"):
        repeat = top = "\u23a2"
        bottom = "\u23a3"
        font = "Size4-Regular"
    elif delim in ("\\lceil", "\u2308"):
        top = "\u23a1"
        repeat = bottom = "\u23a2"
        font = "Size4-Regular"
    elif delim in ("\\rfloor", "\u230b"):
        repeat = top = "\u23a5"
        bottom = "\u23a6"
        font = "Size4-Regular"
    elif delim in ("\\rceil", "\u2309"):
        top = "\u23a4"
        repeat = bottom = "\u23a5"
        font = "Size4-Regular"
    elif delim in ("(", "\\lparen"):
        top = "\u239b"
        repeat = "\u239c"
        bottom = "\u239d"
        font = "Size4-Regular"
    elif delim in (")", "\\rparen"):
        top = "\u239e"
        repeat = "\u239f"
        bottom = "\u23a0"
        font = "Size4-Regular"
    elif delim in ("\\{", "\\lbrace"):
        top = "\u23a7"
        middle = "\u23a8"
        bottom = "\u23a9"
        repeat = "\u23aa"
        font = "Size4-Regular"
    elif delim in ("\\}", "\\rbrace"):
        top = "\u23ab"
        middle = "\u23ac"
        bottom = "\u23ad"
        repeat = "\u23aa"
        font = "Size4-Regular"

    # Get metrics
    top_metrics = get_metrics(top, font, mode)
    top_height_total = top_metrics["height"] + top_metrics["depth"] if top_metrics else 0
    repeat_metrics = get_metrics(repeat, font, mode)
    repeat_height_total = repeat_metrics["height"] + repeat_metrics["depth"] if repeat_metrics else 0
    bottom_metrics = get_metrics(bottom, font, mode)
    bottom_height_total = bottom_metrics["height"] + bottom_metrics["depth"] if bottom_metrics else 0

    middle_height_total = 0
    middle_factor = 1
    if middle:
        middle_metrics = get_metrics(middle, font, mode)
        middle_height_total = middle_metrics["height"] + middle_metrics["depth"] if middle_metrics else 0
        middle_factor = 2

    min_height = top_height_total + bottom_height_total + middle_height_total
    repeat_count = max(0, round((height_total - min_height) / (middle_factor * repeat_height_total)))
    real_height_total = min_height + repeat_count * middle_factor * repeat_height_total

    axis_height = options.font_metrics()["axisHeight"]
    if center:
        axis_height *= options.size_multiplier
    depth = real_height_total / 2 - axis_height

    stack = []

    if font == "Size4-Regular":
        # SVG-based stacking
        mid_height = real_height_total - top_height_total - bottom_height_total
        make_square_root_path("sqrtTall", 0, mid_height * 1000)  # Generate path (not used)
        # Placeholder for SVG path creation
        wrapper = make_span([], [], options)
        wrapper.height = real_height_total / 1000
        stack.append({"type": "elem", "elem": wrapper})
    else:
        stack.append(make_glyph_span(bottom, font, mode))
        stack.append(LAP)

        if middle is None:
            inner_height = real_height_total - top_height_total - bottom_height_total + 2 * LAP_IN_EMS
            stack.append(make_inner(repeat, inner_height, options))
        else:
            inner_height = (real_height_total - top_height_total - bottom_height_total - middle_height_total) / 2 + 2 * LAP_IN_EMS
            stack.append(make_inner(repeat, inner_height, options))
            stack.append(LAP)
            stack.append(make_glyph_span(middle, font, mode))
            stack.append(LAP)
            stack.append(make_inner(repeat, inner_height, options))

        stack.append(LAP)
        stack.append(make_glyph_span(top, font, mode))

    new_options = options.having_base_style(Style.TEXT)
    inner = make_v_list({
        "positionType": "bottom",
        "positionData": depth,
        "children": stack,
    }, new_options)

    return style_wrap(
        make_span(["delimsizing", "mult"], [inner], new_options),
        Style.TEXT,
        options,
        classes
    )


VB_PAD = 80
EM_PAD = 0.08


def sqrt_svg(
    sqrt_name: str,
    height: float,
    view_box_height: int,
    extra_vinculum: float,
    options: Options,
) -> SvgSpan:
    """Create SVG for sqrt."""
    make_square_root_path(sqrt_name, extra_vinculum, view_box_height)  # Generate path
    svg_node = make_svg_span([], [], options)
    svg_node.attributes.update({
        "width": "400em",
        "height": make_em(height),
        "viewBox": f"0 0 400000 {view_box_height}",
        "preserveAspectRatio": "xMinYMin slice",
    })
    return make_svg_span(["hide-tail"], [svg_node], options)


def make_sqrt_image(height: float, options: Options) -> Dict[str, Union[SvgSpan, float]]:
    """Make sqrt image of given height."""
    new_options = options.having_base_sizing()
    delim = traverse_sequence("\\surd", height * new_options.size_multiplier,
                             STACK_LARGE_DELIMITER_SEQUENCE, new_options)

    extra_vinculum = max(0, options.min_rule_thickness - options.font_metrics()["sqrtRuleThickness"])

    span: Optional[SvgSpan] = None
    span_height = 0.0
    tex_height = 0.0
    view_box_height = 0
    advance_width = 0.0

    if delim["type"] == "small":
        view_box_height = 1000 + round(1000 * extra_vinculum) + VB_PAD
        size_multiplier = 1.0 if height < 1.0 else (0.7 if height < 1.4 else new_options.size_multiplier)
        span_height = (1.0 + extra_vinculum + EM_PAD) / size_multiplier
        tex_height = (1.0 + extra_vinculum) / size_multiplier
        span = sqrt_svg("sqrtMain", span_height, view_box_height, extra_vinculum, options)
        span.style["minWidth"] = "0.853em"
        advance_width = 0.833 / size_multiplier

    elif delim["type"] == "large":
        view_box_height = (1000 + VB_PAD) * SIZE_TO_MAX_HEIGHT[delim["size"]]
        tex_height = (SIZE_TO_MAX_HEIGHT[delim["size"]] + extra_vinculum) / new_options.size_multiplier
        span_height = (SIZE_TO_MAX_HEIGHT[delim["size"]] + extra_vinculum + EM_PAD) / new_options.size_multiplier
        span = sqrt_svg(f"sqrtSize{delim['size']}", span_height, view_box_height, extra_vinculum, options)
        span.style["minWidth"] = "1.02em"
        advance_width = 1.0 / new_options.size_multiplier

    else:  # tall
        span_height = height + extra_vinculum + EM_PAD
        tex_height = height + extra_vinculum
        view_box_height = round(1000 * height + extra_vinculum) + VB_PAD
        span = sqrt_svg("sqrtTall", span_height, view_box_height, extra_vinculum, options)
        span.style["minWidth"] = "0.742em"
        advance_width = 1.056

    span.height = tex_height
    span.style["height"] = make_em(span_height)

    return {
        "span": span,
        "advanceWidth": advance_width,
        "ruleWidth": (options.font_metrics()["sqrtRuleThickness"] + extra_vinculum) * new_options.size_multiplier,
    }


# Delimiter categories
STACK_LARGE_DELIMITERS = [
    "(", "\\lparen", ")", "\\rparen",
    "[", "\\lbrack", "]", "\\rbrack",
    "\\{", "\\lbrace", "\\}", "\\rbrace",
    "\\lfloor", "\\rfloor", "\u230a", "\u230b",
    "\\lceil", "\\rceil", "\u2308", "\u2309",
    "\\surd",
]

STACK_ALWAYS_DELIMITERS = [
    "\\uparrow", "\\downarrow", "\\updownarrow",
    "\\Uparrow", "\\Downarrow", "\\Updownarrow",
    "|", "\\|", "\\vert", "\\Vert",
    "\\lvert", "\\rvert", "\\lVert", "\\rVert",
    "\\lgroup", "\\rgroup", "\u27ee", "\u27ef",
    "\\lmoustache", "\\rmoustache", "\u23b0", "\u23b1",
]

STACK_NEVER_DELIMITERS = [
    "<", ">", "\\langle", "\\rangle", "/", "\\backslash", "\\lt", "\\gt",
]

SIZE_TO_MAX_HEIGHT = [0, 1.2, 1.8, 2.4, 3.0]


def make_sized_delim(
    delim: str,
    size: int,
    options: Options,
    mode: Mode,
    classes: List[str],
) -> DomSpan:
    """Make delimiter of specific size."""
    if delim in ("<", "\\lt", "\u27e8"):
        delim = "\\langle"
    elif delim in (">", "\\gt", "\u27e9"):
        delim = "\\rangle"

    if delim in STACK_LARGE_DELIMITERS + STACK_NEVER_DELIMITERS:
        return make_large_delim(delim, size, False, options, mode, classes)
    elif delim in STACK_ALWAYS_DELIMITERS:
        return make_stacked_delim(delim, SIZE_TO_MAX_HEIGHT[size], False, options, mode, classes)
    else:
        raise ParseError(f"Illegal delimiter: '{delim}'")


# Delimiter sequences
STACK_NEVER_DELIMITER_SEQUENCE = [
    {"type": "small", "style": Style.SCRIPTSCRIPT},
    {"type": "small", "style": Style.SCRIPT},
    {"type": "small", "style": Style.TEXT},
    {"type": "large", "size": 1},
    {"type": "large", "size": 2},
    {"type": "large", "size": 3},
    {"type": "large", "size": 4},
]

STACK_ALWAYS_DELIMITER_SEQUENCE = [
    {"type": "small", "style": Style.SCRIPTSCRIPT},
    {"type": "small", "style": Style.SCRIPT},
    {"type": "small", "style": Style.TEXT},
    {"type": "stack"},
]

STACK_LARGE_DELIMITER_SEQUENCE = [
    {"type": "small", "style": Style.SCRIPTSCRIPT},
    {"type": "small", "style": Style.SCRIPT},
    {"type": "small", "style": Style.TEXT},
    {"type": "large", "size": 1},
    {"type": "large", "size": 2},
    {"type": "large", "size": 3},
    {"type": "large", "size": 4},
    {"type": "stack"},
]


def delim_type_to_font(type_: Dict[str, Union[str, int]]) -> str:
    """Get font for delimiter type."""
    if type_["type"] == "small":
        return "Main-Regular"
    elif type_["type"] == "large":
        return f"Size{type_['size']}-Regular"
    elif type_["type"] == "stack":
        return "Size4-Regular"
    else:
        raise ValueError(f"Unknown delim type: {type_['type']}")


def traverse_sequence(
    delim: str,
    height: float,
    sequence: List[Dict[str, Union[str, int]]],
    options: Options,
) -> Dict[str, Union[str, int]]:
    """Find appropriate delimiter in sequence."""
    start = min(2, 3 - options.style.size)
    for i in range(start, len(sequence)):
        if sequence[i]["type"] == "stack":
            break
        metrics = get_metrics(delim, delim_type_to_font(sequence[i]), "math")
        if not metrics:
            continue
        height_depth = metrics["height"] + metrics["depth"]
        if sequence[i]["type"] == "small":
            new_options = options.having_base_style(sequence[i]["style"])
            height_depth *= new_options.size_multiplier
        if height_depth > height:
            return sequence[i]
    return sequence[-1]


def make_custom_sized_delim(
    delim: str,
    height: float,
    center: bool,
    options: Options,
    mode: Mode,
    classes: List[str],
) -> DomSpan:
    """Make delimiter of custom height."""
    if delim in ("<", "\\lt", "\u27e8"):
        delim = "\\langle"
    elif delim in (">", "\\gt", "\u27e9"):
        delim = "\\rangle"

    if delim in STACK_NEVER_DELIMITERS:
        sequence = STACK_NEVER_DELIMITER_SEQUENCE
    elif delim in STACK_LARGE_DELIMITERS:
        sequence = STACK_LARGE_DELIMITER_SEQUENCE
    else:
        sequence = STACK_ALWAYS_DELIMITER_SEQUENCE

    delim_type = traverse_sequence(delim, height, sequence, options)

    if delim_type["type"] == "small":
        return make_small_delim(delim, delim_type["style"], center, options, mode, classes)
    elif delim_type["type"] == "large":
        return make_large_delim(delim, delim_type["size"], center, options, mode, classes)
    else:  # stack
        return make_stacked_delim(delim, height, center, options, mode, classes)


def make_left_right_delim(
    delim: str,
    height: float,
    depth: float,
    options: Options,
    mode: Mode,
    classes: List[str],
) -> DomSpan:
    """Make left/right delimiter."""
    axis_height = options.font_metrics()["axisHeight"] * options.size_multiplier
    delimiter_factor = 901
    delimiter_extend = 5.0 / options.font_metrics()["ptPerEm"]

    max_dist_from_axis = max(height - axis_height, depth + axis_height)
    total_height = max(
        max_dist_from_axis / 500 * delimiter_factor,
        2 * max_dist_from_axis - delimiter_extend
    )

    return make_custom_sized_delim(delim, total_height, True, options, mode, classes)


__all__ = [
    "make_sized_delim",
    "make_custom_sized_delim",
    "make_left_right_delim",
]
