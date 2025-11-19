"""Python port of KaTeX's buildCommon.js shared rendering helpers."""

from __future__ import annotations

import warnings
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
    Literal,
    TypedDict,
    cast,
)

from .dom_tree import (
    Anchor,
    DomNode,
    DomSpan,
    PathNode,
    Span,
    SvgNode,
    SvgSpan,
    SymbolNode,
    create_class,
)
from .font_metrics import get_character_metrics
from .options import Options
from .tree import DocumentFragment
from .types import Mode
from .units import Measurement, calculate_size, make_em

SymbolTable = Dict[Mode, Dict[str, Dict[str, str]]]
LigatureTable = Dict[str, bool]

try:
    from .symbols_data_generated import symbols as _SYMBOLS, ligatures as _LIGATURES
except ImportError:
    SYMBOLS: SymbolTable = {}
    LIGATURES: LigatureTable = {}
else:
    SYMBOLS = cast(SymbolTable, _SYMBOLS)
    LIGATURES = _LIGATURES

try:
    from .font_metrics_data import FONT_METRICS_DATA as _FONT_METRICS_DATA
except ImportError:
    FONT_METRICS_DATA: Dict[str, Any] = {}
else:
    FONT_METRICS_DATA = cast(Dict[str, Any], _FONT_METRICS_DATA)


class SymbolMetrics(TypedDict, total=False):
    height: float
    depth: float
    italic: float
    skew: float
    width: float


class LookupResult(TypedDict):
    value: str
    metrics: Optional[SymbolMetrics]


DomChild = Union[DomNode, DocumentFragment]


class VListChildElem(TypedDict, total=False):
    type: Literal["elem"]
    elem: DomNode
    shift: float
    marginLeft: str
    marginRight: str
    wrapperClasses: List[str]
    wrapperStyle: Dict[str, str]


class VListChildKern(TypedDict):
    type: Literal["kern"]
    size: float


VListChild = Union[VListChildElem, VListChildKern]


class VListParam(TypedDict, total=False):
    positionType: Literal["individualShift", "top", "bottom", "shift", "firstBaseline"]
    positionData: float
    children: List[VListChild]


def lookup_symbol(
    value: str, font_name: str, mode: Mode
) -> LookupResult:
    """Look up symbol with replacements."""
    replace = SYMBOLS.get(mode, {}).get(value, {}).get("replace")
    if replace:
        value = replace
    metrics = get_character_metrics(value, font_name, mode)
    return {
        "value": value,
        "metrics": cast(Optional[SymbolMetrics], metrics),
    }


def make_symbol(
    value: str,
    font_name: str,
    mode: Mode,
    options: Optional[Options] = None,
    classes: Optional[List[str]] = None,
) -> SymbolNode:
    """Create a SymbolNode with metrics."""
    lookup = lookup_symbol(value, font_name, mode)
    metrics = lookup["metrics"]
    value = lookup["value"]

    if metrics:
        italic = metrics.get("italic", 0)
        if mode == "text" or (options and options.font == "mathit"):
            italic = 0
        symbol_node = SymbolNode(
            text=value,
            height=metrics.get("height", 0),
            depth=metrics.get("depth", 0),
            italic=italic,
            skew=metrics.get("skew", 0),
            width=metrics.get("width", 0),
            classes=classes or [],
        )
    else:
        warnings.warn(f"No character metrics for '{value}' in style '{font_name}' and mode '{mode}'")
        symbol_node = SymbolNode(text=value, classes=classes or [])

    if options:
        symbol_node.max_font_size = options.size_multiplier
        if options.style.is_tight():
            symbol_node.classes.append("mtight")
        color = options.get_color()
        if color:
            symbol_node.style["color"] = color

    return symbol_node


def mathsym(
    value: str,
    mode: Mode,
    options: Options,
    classes: Optional[List[str]] = None,
) -> SymbolNode:
    """Create symbol for rel/bin/open/close/inner/punct."""
    if (
        options.font == "boldsymbol"
        and lookup_symbol(value, "Main-Bold", mode)["metrics"]
    ):
        return make_symbol(value, "Main-Bold", mode, options, (classes or []) + ["mathbf"])

    if value == "\\" or SYMBOLS.get(mode, {}).get(value, {}).get("font") == "main":
        return make_symbol(value, "Main-Regular", mode, options, classes)
    else:
        return make_symbol(value, "AMS-Regular", mode, options, (classes or []) + ["amsrm"])


def boldsymbol(
    value: str, mode: Mode, options: Options, classes: List[str], type_: str
) -> Dict[str, str]:
    """Determine bold font variant."""
    if type_ != "textord" and lookup_symbol(value, "Math-BoldItalic", mode)["metrics"]:
        return {"fontName": "Math-BoldItalic", "fontClass": "boldsymbol"}
    else:
        return {"fontName": "Main-Bold", "fontClass": "mathbf"}


def make_ord(
    group: Dict[str, Any], options: Options, type_: str
) -> Union[DocumentFragment, SymbolNode]:
    """Create mathord or textord symbol."""
    mode = group["mode"]
    text = group["text"]
    classes = ["mord"]

    # Math mode or Old font (i.e. \rm)
    is_font = mode == "math" or (mode == "text" and options.font)
    font_or_family = options.font if is_font else options.font_family
    wide_font_name = ""
    wide_font_class = ""
    if text and ord(text[0]) == 0xD835:  # surrogate pair
        from .wide_character import wide_character_font
        wide_font_name, wide_font_class = wide_character_font(text, mode)

    if wide_font_name:
        return make_symbol(text, wide_font_name, mode, options, classes + [wide_font_class])
    elif font_or_family:
        if font_or_family == "boldsymbol":
            font_data = boldsymbol(text, mode, options, classes, type_)
            font_name = font_data["fontName"]
            font_classes = [font_data["fontClass"]]
        elif is_font:
            font_name = FONT_MAP[font_or_family]["fontName"]
            font_classes = [font_or_family]
        else:
            font_name = retrieve_text_font_name(font_or_family, options.font_weight, options.font_shape)
            font_classes = [font_or_family, options.font_weight, options.font_shape]

        if lookup_symbol(text, font_name, mode)["metrics"]:
            return make_symbol(text, font_name, mode, options, classes + font_classes)
        elif LIGATURES.get(text, False) and font_name.startswith("Typewriter"):
            parts = [
                make_symbol(text[i], font_name, mode, options, classes + font_classes)
                for i in range(len(text))
            ]
            return make_fragment(parts)

    # Default fonts
    if type_ == "mathord":
        return make_symbol(text, "Math-Italic", mode, options, classes + ["mathnormal"])
    elif type_ == "textord":
        font = SYMBOLS.get(mode, {}).get(text, {}).get("font")
        if font == "ams":
            font_name = retrieve_text_font_name("amsrm", options.font_weight, options.font_shape)
            return make_symbol(
                text, font_name, mode, options,
                classes + ["amsrm", options.font_weight, options.font_shape]
            )
        elif font == "main" or not font:
            font_name = retrieve_text_font_name("textrm", options.font_weight, options.font_shape)
            return make_symbol(
                text, font_name, mode, options,
                classes + [options.font_weight, options.font_shape]
            )
        else:
            font_name = retrieve_text_font_name(font, options.font_weight, options.font_shape)
            return make_symbol(
                text, font_name, mode, options,
                classes + [font_name, options.font_weight, options.font_shape]
            )
    else:
        raise ValueError(f"Unexpected type: {type_} in make_ord")


def can_combine(prev: SymbolNode, next_: SymbolNode) -> bool:
    """Check if two SymbolNodes can be combined."""
    if (
        create_class(prev.classes) != create_class(next_.classes)
        or prev.skew != next_.skew
        or prev.max_font_size != next_.max_font_size
    ):
        return False

    if len(prev.classes) == 1 and prev.classes[0] in ("mbin", "mord"):
        return False

    for key in set(prev.style.keys()) | set(next_.style.keys()):
        if prev.style.get(key) != next_.style.get(key):
            return False

    return True


def try_combine_chars(chars: List[DomNode]) -> List[DomNode]:
    """Combine consecutive SymbolNodes."""
    i = 0
    while i < len(chars) - 1:
        prev = chars[i]
        next_ = chars[i + 1]
        if (
            isinstance(prev, SymbolNode)
            and isinstance(next_, SymbolNode)
            and can_combine(prev, next_)
        ):
            prev.text += next_.text
            prev.height = max(prev.height, next_.height)
            prev.depth = max(prev.depth, next_.depth)
            prev.italic = next_.italic
            chars.pop(i + 1)
        else:
            i += 1
    return chars


def size_element_from_children(elem: Union[DomNode, DocumentFragment]) -> None:
    """Calculate height/depth/maxFontSize from children."""
    height = 0.0
    depth = 0.0
    max_font_size = 0.0

    for child in getattr(elem, "children", []):
        height = max(height, getattr(child, "height", 0))
        depth = max(depth, getattr(child, "depth", 0))
        max_font_size = max(max_font_size, getattr(child, "max_font_size", 0))

    elem.height = height
    elem.depth = depth
    elem.max_font_size = max_font_size


def make_span(
    classes: Optional[List[str]] = None,
    children: Optional[Sequence[DomNode]] = None,
    options: Optional[Options] = None,
    style: Optional[Dict[str, str]] = None,
) -> DomSpan:
    """Create a Span with size calculation."""
    span = Span(
        classes=classes or [],
        children=list(children) if children is not None else [],
        style=style or {},
    )
    if options:
        # Mirror KaTeX's initNode behaviour: add mtight in tight styles and
        # propagate current color to the span.
        if options.style.is_tight():
            span.classes.append("mtight")
        color = options.get_color()
        if color:
            span.style["color"] = color
    size_element_from_children(span)
    return span


def make_svg_span(
    classes: Optional[List[str]] = None,
    children: Optional[Sequence[DomNode]] = None,
    options: Optional[Options] = None,
    style: Optional[Dict[str, str]] = None,
) -> SvgSpan:
    """Create SVG Span."""
    span = SvgSpan(
        classes=classes or [],
        children=list(children) if children is not None else [],
        style=style or {},
    )
    if options:
        if options.style.is_tight():
            span.classes.append("mtight")
        color = options.get_color()
        if color:
            span.style["color"] = color
    size_element_from_children(span)
    return span


def make_line_span(class_name: str, options: Options, thickness: Optional[float] = None) -> DomSpan:
    """Create line span."""
    line = make_span([class_name], [], options)
    line.height = max(thickness or options.font_metrics()["defaultRuleThickness"], options.min_rule_thickness)
    line.style["borderBottomWidth"] = make_em(line.height)
    line.max_font_size = 1.0
    return line


def make_anchor(
    href: str, classes: List[str], children: List[DomNode], options: Options
) -> Anchor:
    """Create Anchor with size calculation."""
    anchor = Anchor(classes=classes, children=children)
    anchor.attributes["href"] = href
    size_element_from_children(anchor)
    return anchor


def make_fragment(children: Sequence[DomNode]) -> DocumentFragment:
    """Create DocumentFragment with size calculation."""
    fragment = DocumentFragment(children=children)
    size_element_from_children(fragment)
    return fragment


def wrap_fragment(group: DomNode, options: Options) -> DomNode:
    """Wrap DocumentFragment in span."""
    if isinstance(group, DocumentFragment):
        return make_span([], [group], options)
    return group


# VList types
VListElem = Dict[str, Any]

def get_v_list_children_and_depth(params: Dict[str, Any]) -> Tuple[List[VListChild], float]:
    """Calculate VList children and depth."""
    if params["positionType"] == "individualShift":
        old_children = params["children"]
        children: List[VListChild] = [old_children[0]]
        depth = -old_children[0]["shift"] - old_children[0]["elem"].depth
        curr_pos = depth
        for i in range(1, len(old_children)):
            diff = -old_children[i]["shift"] - curr_pos - old_children[i]["elem"].depth
            size = diff - (old_children[i - 1]["elem"].height + old_children[i - 1]["elem"].depth)
            curr_pos += diff
            children.append({"type": "kern", "size": size})
            children.append(old_children[i])
        return children, depth

    if params["positionType"] == "top":
        bottom = params["positionData"]
        for child in params["children"]:
            if child["type"] == "kern":
                bottom -= child["size"]
            else:
                bottom -= child["elem"].height + child["elem"].depth
        depth = bottom
    elif params["positionType"] == "bottom":
        depth = -params["positionData"]
    else:
        first_child = params["children"][0]
        if first_child["type"] != "elem":
            raise ValueError('First child must have type "elem".')
        if params["positionType"] == "shift":
            depth = -first_child["elem"].depth - params["positionData"]
        elif params["positionType"] == "firstBaseline":
            depth = -first_child["elem"].depth
        else:
            raise ValueError(f"Invalid positionType {params['positionType']}.")
    return params["children"], depth


def make_v_list(params: Dict[str, Any], options: Options) -> DomSpan:
    """Create vertical list."""
    children, depth = get_v_list_children_and_depth(params)

    # Match KaTeX's pstrut sizing: start at 0, take the maximum of the
    # children's maxFontSize/height, then add 2em of padding so the strut
    # is taller than any child.  This ensures correct baseline alignment
    # and overall vlist height.
    pstrut_size = 0.0
    for child in children:
        if child["type"] == "elem":
            elem = child["elem"]
            pstrut_size = max(pstrut_size, elem.max_font_size, elem.height)
    pstrut_size += 2.0
    pstrut = make_span(["pstrut"], [])
    pstrut.style["height"] = make_em(pstrut_size)

    real_children = []
    min_pos = depth
    max_pos = depth
    curr_pos = depth
    for child in children:
        if child["type"] == "kern":
            curr_pos += child["size"]
        else:
            elem = child["elem"]
            classes = child.get("wrapperClasses", [])
            style = child.get("wrapperStyle", {})

            child_wrap = make_span(classes, [pstrut, elem], None, style)
            child_wrap.style["top"] = make_em(-pstrut_size - curr_pos - elem.depth)
            if "marginLeft" in child:
                child_wrap.style["marginLeft"] = child["marginLeft"]
            if "marginRight" in child:
                child_wrap.style["marginRight"] = child["marginRight"]

            real_children.append(child_wrap)
            curr_pos += elem.height + elem.depth
        min_pos = min(min_pos, curr_pos)
        max_pos = max(max_pos, curr_pos)

    vlist = make_span(["vlist"], real_children)
    vlist.style["height"] = make_em(max_pos)

    if min_pos < 0:
        empty_span = make_span([], [])
        depth_strut = make_span(["vlist"], [empty_span])
        depth_strut.style["height"] = make_em(-min_pos)
        top_strut = make_span(["vlist-s"], [SymbolNode(text="\u200b")])
        rows = [
            make_span(["vlist-r"], [vlist, top_strut]),
            make_span(["vlist-r"], [depth_strut])
        ]
    else:
        rows = [make_span(["vlist-r"], [vlist])]

    vtable = make_span(["vlist-t"], rows)
    if len(rows) == 2:
        vtable.classes.append("vlist-t2")
    vtable.height = max_pos
    vtable.depth = -min_pos
    return vtable


def make_glue(measurement: Measurement, options: Options) -> DomSpan:
    """Create glue span."""
    rule = make_span(["mspace"], [], options)
    size = calculate_size(measurement, options)
    rule.style["marginRight"] = make_em(size)
    return rule


def retrieve_text_font_name(font_family: str, font_weight: str, font_shape: str) -> str:
    """Get font name from family/weight/shape."""
    base_font_name = {
        "amsrm": "AMS",
        "textrm": "Main",
        "textsf": "SansSerif",
        "texttt": "Typewriter",
    }.get(font_family, font_family)

    font_styles_name = {
        ("textbf", "textit"): "BoldItalic",
        "textbf": "Bold",
        "textit": "Italic",
    }.get((font_weight, font_shape) if font_shape == "textit" and font_weight == "textbf"
          else font_weight or font_shape, "Regular")

    return f"{base_font_name}-{font_styles_name}"


# Font map
FONT_MAP: Dict[str, Dict[str, str]] = {
    "mathbf": {"variant": "bold", "fontName": "Main-Bold"},
    "mathrm": {"variant": "normal", "fontName": "Main-Regular"},
    "textit": {"variant": "italic", "fontName": "Main-Italic"},
    "mathit": {"variant": "italic", "fontName": "Main-Italic"},
    "mathnormal": {"variant": "italic", "fontName": "Math-Italic"},
    "mathsfit": {"variant": "sans-serif-italic", "fontName": "SansSerif-Italic"},
    "mathbb": {"variant": "double-struck", "fontName": "AMS-Regular"},
    "mathcal": {"variant": "script", "fontName": "Caligraphic-Regular"},
    "mathfrak": {"variant": "fraktur", "fontName": "Fraktur-Regular"},
    "mathscr": {"variant": "script", "fontName": "Script-Regular"},
    "mathsf": {"variant": "sans-serif", "fontName": "SansSerif-Regular"},
    "mathtt": {"variant": "monospace", "fontName": "Typewriter-Regular"},
}

SVG_DATA: Dict[str, Tuple[str, float, float]] = {
    "vec": ("vec", 0.471, 0.714),
    "oiintSize1": ("oiintSize1", 0.957, 0.499),
    "oiintSize2": ("oiintSize2", 1.472, 0.659),
    "oiiintSize1": ("oiiintSize1", 1.304, 0.499),
    "oiiintSize2": ("oiiintSize2", 1.98, 0.659),
}


def static_svg(value: str, options: Options) -> SvgSpan:
    """Render a predefined inline SVG (e.g., vector arrows) as a span."""
    try:
        path_name, width, height = SVG_DATA[value]
    except KeyError as exc:  # pragma: no cover - developer error
        raise ValueError(f"Unknown static SVG '{value}'") from exc

    path = PathNode(path_data=path_name)
    svg_node = SvgNode(children=[path])
    svg_node.set_attribute("width", make_em(width))
    svg_node.set_attribute("height", make_em(height))
    svg_node.set_attribute("style", f"width:{make_em(width)}")
    svg_node.set_attribute("viewBox", f"0 0 {int(1000 * width)} {int(1000 * height)}")
    svg_node.set_attribute("preserveAspectRatio", "xMinYMin")

    span = make_svg_span(["overlay"], [svg_node], options)
    span.height = height
    span.style["height"] = make_em(height)
    span.style["width"] = make_em(width)
    return span


__all__ = [
    "FONT_MAP",
    "make_symbol",
    "mathsym",
    "make_span",
    "make_svg_span",
    "make_line_span",
    "make_anchor",
    "make_fragment",
    "wrap_fragment",
    "make_v_list",
    "make_ord",
    "make_glue",
    "static_svg",
    "SVG_DATA",
    "try_combine_chars",
]
