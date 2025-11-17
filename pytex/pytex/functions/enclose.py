"""Python port of KaTeX's functions/enclose.js - enclosure commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, cast

from ..build_common import make_span, make_v_list, wrap_fragment
from ..define_function import define_function
from ..mathml_tree import MathNode
from ..parse_node import assert_node_type
from ..stretchy import enclose_span
from ..units import Measurement, calculate_size, make_em
from ..utils import is_character_box

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import (
        AnyParseNode,
        ColorTokenParseNode,
        EncloseParseNode,
        ParseNode,
    )


def _measurement(number: float, unit: str) -> Measurement:
    """Convenience helper to construct Measurement literals."""
    return Measurement(number=number, unit=unit)


def html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for enclosure commands."""
    from .. import build_html as html

    enclose_group = cast("EncloseParseNode", group)
    # Build the inner content
    inner = wrap_fragment(html.build_group(enclose_group["body"], options), options)

    label = enclose_group["label"][1:]  # Remove backslash
    scale = options.size_multiplier
    img = None
    img_shift: float = 0.0

    # Check if single character (affects geometry)
    is_single_char = is_character_box(cast(Dict[str, Any], enclose_group["body"]))

    if label == "sout":
        # Strikethrough
        img = make_span(["stretchy", "sout"])
        img.height = options.font_metrics().get("defaultRuleThickness", 0.04) / scale
        img_shift = -0.5 * options.font_metrics().get("xHeight", 0.4)

    elif label == "phase":
        # Phase angle (phasor)
        line_weight = calculate_size(_measurement(0.6, "pt"), options)
        clearance = calculate_size(_measurement(0.35, "ex"), options)

        # Prevent size changes from affecting line thickness
        new_options = options.having_base_sizing()
        scale = scale / new_options.size_multiplier

        angle_height = inner.height + inner.depth + line_weight + clearance
        # Reserve left pad for angle
        inner.style["paddingLeft"] = make_em(angle_height / 2 + line_weight)

        # Create SVG for phase angle
        from ..svg_geometry import phase_path
        view_box_height = int(1000 * angle_height * scale)
        path = phase_path(view_box_height)

        from ..dom_tree import PathNode, SvgNode
        svg_node = SvgNode(children=[PathNode(path_data=path)], attributes={
            "width": "400em",
            "height": make_em(view_box_height / 1000),
            "viewBox": f"0 0 400000 {view_box_height}",
            "preserveAspectRatio": "xMinYMin slice",
        })

        # Wrap in span with overflow hidden
        img = make_span(["hide-tail"], [svg_node], options)
        img.style["height"] = make_em(angle_height)
        img_shift = inner.depth + line_weight + clearance

    else:
        # Add horizontal padding
        if "cancel" in label:
            if not is_single_char:
                inner.classes.append("cancel-pad")
        elif label == "angl":
            inner.classes.append("anglpad")
        else:
            inner.classes.append("boxpad")

        # Add vertical padding
        top_pad: float = 0.0
        bottom_pad: float = 0.0
        rule_thickness: float = 0.0

        if "box" in label:
            rule_thickness = max(
                options.font_metrics().get("fboxrule", 0.4),  # default
                options.min_rule_thickness,  # user override
            )
            top_pad = (options.font_metrics().get("fboxsep", 3)
                      +
                      (0 if label == "colorbox" else rule_thickness))
            bottom_pad = top_pad

        elif label == "angl":
            rule_thickness = max(
                options.font_metrics().get("defaultRuleThickness", 0.04),
                options.min_rule_thickness
            )
            top_pad = 4 * rule_thickness  # gap = 3 × line, plus the line itself
            bottom_pad = max(0.0, 0.25 - inner.depth)

        else:
            top_pad = 0.2 if is_single_char else 0.0
            bottom_pad = top_pad

        img = enclose_span(inner, label, top_pad, bottom_pad, options)

        if any(x in label for x in ["fbox", "boxed", "fcolorbox"]):
            img.style["borderStyle"] = "solid"
            img.style["borderWidth"] = make_em(rule_thickness)
        elif label == "angl" and rule_thickness != 0.049:
            img.style["borderTopWidth"] = make_em(rule_thickness)
            img.style["borderRightWidth"] = make_em(rule_thickness)

        img_shift = inner.depth + bottom_pad

        background_color = enclose_group.get("backgroundColor")
        if background_color is not None:
            img.style["backgroundColor"] = background_color
            border_color = enclose_group.get("borderColor")
            if border_color is not None:
                img.style["borderColor"] = border_color

    # Create vlist
    if background_color is not None:
        vlist = make_v_list({
            "positionType": "individualShift",
            "children": [
                # Put color background behind inner
                {"type": "elem", "elem": img, "shift": img_shift},
                {"type": "elem", "elem": inner, "shift": 0},
            ],
        }, options)
    else:
        classes = ["svg-align"] if any(x in label for x in ["cancel", "phase"]) else []
        vlist = make_v_list({
            "positionType": "individualShift",
            "children": [
                # Write the enclosure on top of inner
                {"type": "elem", "elem": inner, "shift": 0},
                {
                    "type": "elem",
                    "elem": img,
                    "shift": img_shift,
                    "wrapperClasses": classes,
                },
            ],
        }, options)

    # Cancel lines don't add height to expression
    if "cancel" in label:
        vlist.height = inner.height
        vlist.depth = inner.depth

    if "cancel" in label and not is_single_char:
        # Cancel doesn't create horizontal space for line extension
        return make_span(["mord", "cancel-lap"], [vlist], options)
    else:
        return make_span(["mord"], [vlist], options)


def mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for enclosure commands."""
    from .. import build_mathml as mml

    enclose_group = cast("EncloseParseNode", group)
    label = enclose_group["label"]
    node = MathNode(
        "mpadded" if "colorbox" in label else "menclose",
        [mml.build_group(enclose_group["body"], options)]
    )

    if label == "\\cancel":
        node.set_attribute("notation", "updiagonalstrike")
    elif label == "\\bcancel":
        node.set_attribute("notation", "downdiagonalstrike")
    elif label == "\\phase":
        node.set_attribute("notation", "phasorangle")
    elif label == "\\sout":
        node.set_attribute("notation", "horizontalstrike")
    elif label == "\\fbox":
        node.set_attribute("notation", "box")
    elif label == "\\angl":
        node.set_attribute("notation", "actuarial")
    elif label in ["\\fcolorbox", "\\colorbox"]:
        # menclose doesn't have good notation, use mpadded
        fboxsep = (options.font_metrics().get("fboxsep", 3) *
                  options.font_metrics().get("ptPerEm", 10))
        node.set_attribute("width", f"+{2 * fboxsep}pt")
        node.set_attribute("height", f"+{2 * fboxsep}pt")
        node.set_attribute("lspace", f"{fboxsep}pt")
        node.set_attribute("voffset", f"{fboxsep}pt")

        if label == "\\fcolorbox":
            thk = max(
                options.font_metrics().get("fboxrule", 0.4),  # default
                options.min_rule_thickness,  # user override
            )
            border_color = enclose_group.get("borderColor", "black")
            node.set_attribute("style", f"border: {thk}em solid {border_color}")
    elif label == "\\xcancel":
        node.set_attribute("notation", "updiagonalstrike downdiagonalstrike")

    background_color = enclose_group.get("backgroundColor")
    if isinstance(background_color, str):
        node.set_attribute("mathbackground", background_color)

    return node


# Define enclosure functions
define_function({
    "type": "enclose",
    "names": ["\\colorbox"],
    "props": {
        "numArgs": 2,
        "allowedInText": True,
        "argTypes": ["color", "text"],
    },
    "handler": lambda context, args, opt_args: _enclose_handler(context, args, False),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

define_function({
    "type": "enclose",
    "names": ["\\fcolorbox"],
    "props": {
        "numArgs": 3,
        "allowedInText": True,
        "argTypes": ["color", "color", "text"],
    },
    "handler": lambda context, args, opt_args: _enclose_handler(context, args, True),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

define_function({
    "type": "enclose",
    "names": ["\\fbox"],
    "props": {
        "numArgs": 1,
        "argTypes": ["hbox"],
        "allowedInText": True,
    },
    "handler": lambda context, args, opt_args: {
        "type": "enclose",
        "mode": context["parser"].mode,
        "label": "\\fbox",
        "body": args[0],
    },
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

define_function({
    "type": "enclose",
    "names": ["\\cancel", "\\bcancel", "\\xcancel", "\\sout", "\\phase"],
    "props": {
        "numArgs": 1,
    },
    "handler": lambda context, args, opt_args: {
        "type": "enclose",
        "mode": context["parser"].mode,
        "label": context["funcName"],
        "body": args[0],
    },
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

define_function({
    "type": "enclose",
    "names": ["\\angl"],
    "props": {
        "numArgs": 1,
        "argTypes": ["hbox"],
        "allowedInText": False,
    },
    "handler": lambda context, args, opt_args: {
        "type": "enclose",
        "mode": context["parser"].mode,
        "label": "\\angl",
        "body": args[0],
    },
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})


def _enclose_handler(context: Dict[str, Any], args: List[AnyParseNode], has_border_color: bool) -> Dict[str, Any]:
    """Handler for colorbox/fcolorbox commands."""
    if has_border_color:
        border_color = cast("ColorTokenParseNode", assert_node_type(args[0], "color-token"))["color"]
        background_color = cast("ColorTokenParseNode", assert_node_type(args[1], "color-token"))["color"]
        body = args[2]
    else:
        border_color = None
        background_color = cast("ColorTokenParseNode", assert_node_type(args[0], "color-token"))["color"]
        body = args[1]

    return {
        "type": "enclose",
        "mode": context["parser"].mode,
        "label": context["funcName"],
        "backgroundColor": background_color,
        "borderColor": border_color,
        "body": body,
    }
