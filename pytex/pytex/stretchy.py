"""Python port of KaTeX's stretchy.js - stretchy wide element rendering."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence, TypedDict, Union, cast

from .build_common import make_span, make_svg_span
from .dom_tree import DomSpan, HtmlDomNode, LineNode, PathNode, SvgNode, SvgSpan
from .mathml_tree import MathNode, TextNode
from .options import Options
from .units import make_em


STRETCHY_CODE_POINT: Dict[str, str] = {
    "widehat": "^",
    "widecheck": "ˇ",
    "widetilde": "~",
    "utilde": "~",
    "overleftarrow": "\u2190",
    "underleftarrow": "\u2190",
    "xleftarrow": "\u2190",
    "overrightarrow": "\u2192",
    "underrightarrow": "\u2192",
    "xrightarrow": "\u2192",
    "underbrace": "\u23df",
    "overbrace": "\u23de",
    "overgroup": "\u23e0",
    "undergroup": "\u23e1",
    "overleftrightarrow": "\u2194",
    "underleftrightarrow": "\u2194",
    "xleftrightarrow": "\u2194",
    "Overrightarrow": "\u21d2",
    "xRightarrow": "\u21d2",
    "overleftharpoon": "\u21bc",
    "xleftharpoonup": "\u21bc",
    "overrightharpoon": "\u21c0",
    "xrightharpoonup": "\u21c0",
    "xLeftarrow": "\u21d0",
    "xLeftrightarrow": "\u21d4",
    "xhookleftarrow": "\u21a9",
    "xhookrightarrow": "\u21aa",
    "xmapsto": "\u21a6",
    "xrightharpoondown": "\u21c1",
    "xleftharpoondown": "\u21bd",
    "xrightleftharpoons": "\u21cc",
    "xleftrightharpoons": "\u21cb",
    "xtwoheadleftarrow": "\u219e",
    "xtwoheadrightarrow": "\u21a0",
    "xlongequal": "=",
    "xtofrom": "\u21c4",
    "xrightleftarrows": "\u21c4",
    "xrightequilibrium": "\u21cc",  # Not a perfect match.
    "xleftequilibrium": "\u21cb",   # None better available.
    "\\cdrightarrow": "\u2192",
    "\\cdleftarrow": "\u2190",
    "\\cdlongequal": "=",
}


def math_ml_node(label: str) -> MathNode:
    """Create MathML node for stretchy element."""
    code_point = STRETCHY_CODE_POINT.get(label.lstrip("\\"), "")
    node = MathNode("mo", [TextNode(code_point)])
    node.set_attribute("stretchy", "true")
    return node


# KaTeX SVG images data
# Stored as heterogeneous sequences; concrete access is type-safe via casts below.
KATEX_IMAGES_DATA: Dict[str, Sequence[object]] = {
    # path(s), minWidth, height, align
    "overrightarrow": [["rightarrow"], 0.888, 522, "xMaxYMin"],
    "overleftarrow": [["leftarrow"], 0.888, 522, "xMinYMin"],
    "underrightarrow": [["rightarrow"], 0.888, 522, "xMaxYMin"],
    "underleftarrow": [["leftarrow"], 0.888, 522, "xMinYMin"],
    "xrightarrow": [["rightarrow"], 1.469, 522, "xMaxYMin"],
    "\\cdrightarrow": [["rightarrow"], 3.0, 522, "xMaxYMin"],  # CD minwidth2.5pc
    "xleftarrow": [["leftarrow"], 1.469, 522, "xMinYMin"],
    "\\cdleftarrow": [["leftarrow"], 3.0, 522, "xMinYMin"],
    "Overrightarrow": [["doublerightarrow"], 0.888, 560, "xMaxYMin"],
    "xRightarrow": [["doublerightarrow"], 1.526, 560, "xMaxYMin"],
    "xLeftarrow": [["doubleleftarrow"], 1.526, 560, "xMinYMin"],
    "overleftharpoon": [["leftharpoon"], 0.888, 522, "xMinYMin"],
    "xleftharpoonup": [["leftharpoon"], 0.888, 522, "xMinYMin"],
    "xleftharpoondown": [["leftharpoondown"], 0.888, 522, "xMinYMin"],
    "overrightharpoon": [["rightharpoon"], 0.888, 522, "xMaxYMin"],
    "xrightharpoonup": [["rightharpoon"], 0.888, 522, "xMaxYMin"],
    "xrightharpoondown": [["rightharpoondown"], 0.888, 522, "xMaxYMin"],
    "xlongequal": [["longequal"], 0.888, 334, "xMinYMin"],
    "\\cdlongequal": [["longequal"], 3.0, 334, "xMinYMin"],
    "xtwoheadleftarrow": [["twoheadleftarrow"], 0.888, 334, "xMinYMin"],
    "xtwoheadrightarrow": [["twoheadrightarrow"], 0.888, 334, "xMaxYMin"],

    # Multi-path elements
    "overleftrightarrow": [["leftarrow", "rightarrow"], 0.888, 522],
    "overbrace": [["leftbrace", "midbrace", "rightbrace"], 1.6, 548],
    "underbrace": [["leftbraceunder", "midbraceunder", "rightbraceunder"], 1.6, 548],
    "underleftrightarrow": [["leftarrow", "rightarrow"], 0.888, 522],
    "xleftrightarrow": [["leftarrow", "rightarrow"], 1.75, 522],
    "xLeftrightarrow": [["doubleleftarrow", "doublerightarrow"], 1.75, 560],
    "xrightleftharpoons": [["leftharpoondownplus", "rightharpoonplus"], 1.75, 716],
    "xleftrightharpoons": [["leftharpoonplus", "rightharpoonplus"], 1.75, 716],
    "xhookleftarrow": [["leftarrow", "righthook"], 1.08, 522],
    "xhookrightarrow": [["lefthook", "rightarrow"], 1.08, 522],
    "overlinesegment": [["leftlinesegment", "rightlinesegment"], 0.888, 522],
    "underlinesegment": [["leftlinesegment", "rightlinesegment"], 0.888, 522],
    "overgroup": [["leftgroup", "rightgroup"], 0.888, 342],
    "undergroup": [["leftgroupunder", "rightgroupunder"], 0.888, 342],
    "xmapsto": [["leftmapsto", "rightarrow"], 1.5, 522],
    "xtofrom": [["leftToFrom", "rightToFrom"], 1.75, 528],

    # mhchem package arrows
    "xrightleftarrows": [["baraboveleftarrow", "rightarrowabovebar"], 1.75, 901],
    "xrightequilibrium": [["baraboveshortleftharpoon", "rightharpoonaboveshortbar"], 1.75, 716],
    "xleftequilibrium": [["shortbaraboveleftharpoon", "shortrightharpoonabovebar"], 1.75, 716],
}


def group_length(arg: Mapping[str, Any]) -> int:
    """Get the length of a parse node group."""
    if arg.get("type") == "ordgroup":
        return len(arg.get("body", []))
    else:
        return 1


class _StretchySvgResult(TypedDict):
    span: Union[DomSpan, SvgSpan]
    minWidth: float
    height: float


def svg_span(group: Mapping[str, Any], options: Options) -> Union[DomSpan, SvgSpan]:
    """Create SVG span for stretchy element."""

    def build_svg_span() -> _StretchySvgResult:
        view_box_width = 400000  # default
        raw_label = group.get("label", "")
        label = raw_label[1:] if isinstance(raw_label, str) and raw_label.startswith("\\") else cast(str, raw_label)

        if label in ["widehat", "widecheck", "widetilde", "utilde"]:
            # Accent-type stretchy elements
            base_node = group.get("base")
            if isinstance(base_node, Mapping):
                num_chars = group_length(base_node)
            else:
                num_chars = 1
            view_box_height: float
            path_name: str
            height: float

            if num_chars > 5:
                if label in ["widehat", "widecheck"]:
                    view_box_height = 420
                    view_box_width = 2364
                    height = 0.42
                    path_name = label + "4"
                else:
                    view_box_height = 312
                    view_box_width = 2340
                    height = 0.34
                    path_name = "tilde4"
            else:
                img_index = [1, 1, 2, 2, 3, 3][num_chars] if num_chars < 6 else 3
                if label in ["widehat", "widecheck"]:
                    widths = [0, 1062, 2364, 2364, 2364]
                    heights = [0, 239, 300, 360, 420]
                    height_vals = [0, 0.24, 0.3, 0.3, 0.36, 0.42]
                    view_box_width = widths[img_index]
                    view_box_height = heights[img_index]
                    height = height_vals[img_index]
                    path_name = label + str(img_index)
                else:
                    widths = [0, 600, 1033, 2339, 2340]
                    heights = [0, 260, 286, 306, 312]
                    height_vals = [0, 0.26, 0.286, 0.3, 0.306, 0.34]
                    view_box_width = widths[img_index]
                    view_box_height = heights[img_index]
                    height = height_vals[img_index]
                    path_name = "tilde" + str(img_index)

            path = PathNode(path_data=path_name)
            svg_node = SvgNode(children=[path])
            svg_node.set_attribute("width", "100%")
            svg_node.set_attribute("height", make_em(height))
            svg_node.set_attribute("viewBox", f"0 0 {view_box_width} {view_box_height}")
            svg_node.set_attribute("preserveAspectRatio", "none")
            return {
                "span": make_svg_span([], [svg_node], options),
                "minWidth": 0,
                "height": height,
            }
        else:
            # Regular stretchy elements
            spans: List[SvgSpan] = []
            data = KATEX_IMAGES_DATA[label]
            paths = cast(List[str], data[0])
            min_width = float(cast(float, data[1]))
            view_box_height = float(cast(float, data[2]))

            height = view_box_height / 1000
            num_svg_children = len(paths)

            if num_svg_children == 1:
                # Single path with alignment
                align = cast(str, data[3]) if len(data) > 3 else "xMinYMin"
                width_classes = ["hide-tail"]
                aligns = [align]
            elif num_svg_children == 2:
                width_classes = ["halfarrow-left", "halfarrow-right"]
                aligns = ["xMinYMin", "xMaxYMin"]
            elif num_svg_children == 3:
                width_classes = ["brace-left", "brace-center", "brace-right"]
                aligns = ["xMinYMin", "xMidYMin", "xMaxYMin"]
            else:
                raise ValueError(
                    f"Correct katexImagesData or update code here to support "
                    f"{num_svg_children} children."
                )

            for i in range(num_svg_children):
                path = PathNode(path_data=paths[i])
                svg_node = SvgNode(children=[path])
                svg_node.set_attribute("width", "400em")
                svg_node.set_attribute("height", make_em(height))
                svg_node.set_attribute("viewBox", f"0 0 {view_box_width} {view_box_height}")
                svg_node.set_attribute("preserveAspectRatio", f"{aligns[i]} slice")

                span = make_svg_span([width_classes[i]], [svg_node], options)
                if num_svg_children == 1:
                    return {"span": span, "minWidth": min_width, "height": height}
                else:
                    span.style["height"] = make_em(height)
                    spans.append(span)

            return {
                "span": make_span(["stretchy"], spans, options),
                "minWidth": min_width,
                "height": height,
            }

    result = build_svg_span()
    span = result["span"]
    min_width = result["minWidth"]
    height = result["height"]

    # Note that we are returning span.depth = 0.
    # Any adjustments relative to the baseline must be done in buildHTML.
    span.height = height
    span.style["height"] = make_em(height)
    if min_width > 0:
        span.style["minWidth"] = make_em(min_width)

    return span


def enclose_span(
    inner: HtmlDomNode,
    label: str,
    top_pad: float,
    bottom_pad: float,
    options: Options,
) -> Union[DomSpan, SvgSpan]:
    r"""Create enclosed span for elements like \cancel, \fbox, etc."""
    total_height = inner.height + inner.depth + top_pad + bottom_pad

    if "fbox" in label or "color" in label or "angl" in label:
        img = make_span(["stretchy", label], [], options)

        if label == "fbox":
            color = options.get_color() if hasattr(options, 'color') and options.color else None
            if color:
                img.style["borderColor"] = color
    else:
        # \cancel, \bcancel, or \xcancel
        lines: List[HtmlDomNode] = []

        if "bcancel" in label or "xcancel" in label:
            line = LineNode()
            line.attributes.update({
                "x1": "0",
                "y1": "0",
                "x2": "100%",
                "y2": "100%",
                "stroke-width": "0.046em",
            })
            lines.append(line)

        if "xcancel" in label:
            line = LineNode()
            line.attributes.update({
                "x1": "0",
                "y1": "100%",
                "x2": "100%",
                "y2": "0",
                "stroke-width": "0.046em",
            })
            lines.append(line)

        svg_node = SvgNode(children=lines)
        svg_node.set_attribute("width", "100%")
        svg_node.set_attribute("height", make_em(total_height))

        img = make_svg_span([], [svg_node], options)

    img.height = total_height
    img.style["height"] = make_em(total_height)

    return img


__all__ = ["enclose_span", "math_ml_node", "svg_span", "STRETCHY_CODE_POINT", "KATEX_IMAGES_DATA"]
