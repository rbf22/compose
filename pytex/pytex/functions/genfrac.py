"""Python port of KaTeX's functions/genfrac.js - generalized fraction handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from ..build_common import make_line_span, make_span, make_v_list
from ..define_function import define_function, normalize_argument
from ..mathml_tree import MathNode
from ..parse_error import ParseError
from ..style import Style
from ..units import calculate_size, make_em

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode


def adjust_style(size: str, original_style: Style) -> Style:
    """Adjust style based on fraction size specification."""
    style = original_style
    if size == "display":
        # Get display style as default
        # If incoming style is sub/sup, use style.text() to get correct size
        style = style.text() if style.id >= Style.SCRIPT.id else Style.DISPLAY
    elif size == "text" and style.size == Style.DISPLAY.size:
        # We're in \tfrac but incoming style is displaystyle
        style = Style.TEXT
    elif size == "script":
        style = Style.SCRIPT
    elif size == "scriptscript":
        style = Style.SCRIPTSCRIPT
    return style


def html_builder(group: ParseNode, options: Options):
    """Build HTML for generalized fraction."""
    from .. import build_html as html
    from .. import delimiter

    style = adjust_style(group.get("size", "auto"), options.style)

    nstyle = style.frac_num()
    dstyle = style.frac_den()

    # Build numerator
    new_options = options.having_style(nstyle)
    numerm = html.build_group(group["numer"], new_options, options)

    if group.get("continued"):
        # \cfrac inserts a strut into the numerator
        h_strut = 8.5 / options.font_metrics().get("ptPerEm", 10)
        d_strut = 3.5 / options.font_metrics().get("ptPerEm", 10)
        numerm.height = max(numerm.height, h_strut)
        numerm.depth = max(numerm.depth, d_strut)

    # Build denominator
    new_options = options.having_style(dstyle)
    denomm = html.build_group(group["denom"], new_options, options)

    # Handle fraction bar
    rule = None
    rule_width = 0
    rule_spacing = options.font_metrics().get("defaultRuleThickness", 0.04)

    if group.get("hasBarLine"):
        if group.get("barSize"):
            rule_width = calculate_size(group["barSize"], options)
            rule = make_line_span("frac-line", options, rule_width)
        else:
            rule = make_line_span("frac-line", options)
        rule_width = rule.height
        rule_spacing = rule.height

    # Rule 15b - calculate shifts
    if style.size == Style.DISPLAY.size or group.get("size") == "display":
        num_shift = options.font_metrics().get("num1", 0)
        clearance = 3 * rule_spacing if rule_width > 0 else 7 * rule_spacing
        denom_shift = options.font_metrics().get("denom1", 0)
    else:
        if rule_width > 0:
            num_shift = options.font_metrics().get("num2", 0)
            clearance = rule_spacing
        else:
            num_shift = options.font_metrics().get("num3", 0)
            clearance = 3 * rule_spacing
        denom_shift = options.font_metrics().get("denom2", 0)

    # Build fraction
    if not rule:
        # Rule 15c - no bar line
        candidate_clearance = (num_shift - numerm.depth) - (denomm.height - denom_shift)
        if candidate_clearance < clearance:
            adjustment = 0.5 * (clearance - candidate_clearance)
            num_shift += adjustment
            denom_shift += adjustment

        frac = make_v_list({
            "positionType": "individualShift",
            "children": [
                {"type": "elem", "elem": denomm, "shift": denom_shift},
                {"type": "elem", "elem": numerm, "shift": -num_shift},
            ],
        }, options)
    else:
        # Rule 15d - with bar line
        axis_height = options.font_metrics().get("axisHeight", 0)

        # Ensure minimum clearance above bar
        if (num_shift - numerm.depth) - (axis_height + 0.5 * rule_width) < clearance:
            num_shift += clearance - ((num_shift - numerm.depth) -
                                    (axis_height + 0.5 * rule_width))

        # Ensure minimum clearance below bar
        if (axis_height - 0.5 * rule_width) - (denomm.height - denom_shift) < clearance:
            denom_shift += clearance - ((axis_height - 0.5 * rule_width) -
                                       (denomm.height - denom_shift))

        mid_shift = -(axis_height - 0.5 * rule_width)

        frac = make_v_list({
            "positionType": "individualShift",
            "children": [
                {"type": "elem", "elem": denomm, "shift": denom_shift},
                {"type": "elem", "elem": rule, "shift": mid_shift},
                {"type": "elem", "elem": numerm, "shift": -num_shift},
            ],
        }, options)

    # Account for size changes
    new_options = options.having_style(style)
    frac.height *= new_options.size_multiplier / options.size_multiplier
    frac.depth *= new_options.size_multiplier / options.size_multiplier

    # Rule 15e - delimiters
    if style.size == Style.DISPLAY.size:
        delim_size = options.font_metrics().get("delim1", 0)
    elif style.size == Style.SCRIPTSCRIPT.size:
        delim_size = options.having_style(Style.SCRIPT).font_metrics().get("delim2", 0)
    else:
        delim_size = options.font_metrics().get("delim2", 0)

    # Left delimiter
    if group.get("leftDelim") is None:
        left_delim = html.make_null_delimiter(options, ["mopen"])
    else:
        left_delim = delimiter.make_custom_sized_delim(
            group["leftDelim"], delim_size, True,
            options.having_style(style), group.get("mode", "math"), ["mopen"]
        )

    # Right delimiter
    if group.get("continued"):
        right_delim = make_span([])  # zero width for \cfrac
    elif group.get("rightDelim") is None:
        right_delim = html.make_null_delimiter(options, ["mclose"])
    else:
        right_delim = delimiter.make_custom_sized_delim(
            group["rightDelim"], delim_size, True,
            options.having_style(style), group.get("mode", "math"), ["mclose"]
        )

    return make_span(
        ["mord"] + new_options.sizing_classes(options),
        [left_delim, make_span(["mfrac"], [frac]), right_delim],
        options
    )


def mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for generalized fraction."""
    from .. import build_mathml as mml

    node = MathNode("mfrac", [
        mml.build_group(group["numer"], options),
        mml.build_group(group["denom"], options),
    ])

    if not group.get("hasBarLine", True):
        node.set_attribute("linethickness", "0px")
    elif group.get("barSize"):
        rule_width = calculate_size(group["barSize"], options)
        node.set_attribute("linethickness", make_em(rule_width))

    style = adjust_style(group.get("size", "auto"), options.style)
    if style.size != options.style.size:
        node = MathNode("mstyle", [node])
        is_display = "true" if style.size == Style.DISPLAY.size else "false"
        node.set_attribute("displaystyle", is_display)
        node.set_attribute("scriptlevel", "0")

    if group.get("leftDelim") is not None or group.get("rightDelim") is not None:
        with_delims = []

        if group.get("leftDelim") is not None:
            left_text = group["leftDelim"].replace("\\", "")
            left_op = MathNode("mo", [mml.make_text(left_text, "math", options)])
            left_op.set_attribute("fence", "true")
            with_delims.append(left_op)

        with_delims.append(node)

        if group.get("rightDelim") is not None:
            right_text = group["rightDelim"].replace("\\", "")
            right_op = MathNode("mo", [mml.make_text(right_text, "math", options)])
            right_op.set_attribute("fence", "true")
            with_delims.append(right_op)

        return mml.make_row(with_delims)

    return node


def delim_from_value(delim_string: str) -> Union[str, None]:
    """Convert delimiter string to delimiter value."""
    if len(delim_string) > 0:
        delim = delim_string
        return None if delim == "." else delim
    return None


# Define the fraction functions
define_function({
    "type": "genfrac",
    "names": [
        "\\dfrac", "\\frac", "\\tfrac",
        "\\dbinom", "\\binom", "\\tbinom",
        "\\\\atopfrac",  # can't be entered directly
        "\\\\bracefrac", "\\\\brackfrac",  # ditto
    ],
    "props": {
        "numArgs": 2,
        "allowedInArgument": True,
    },
    "handler": lambda context, args: _genfrac_handler(context, args, False),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

def _genfrac_handler(context, args, continued):
    """Handler for basic fraction commands."""
    parser = context["parser"]
    func_name = context["funcName"]
    numer = args[0]
    denom = args[1]

    has_bar_line = True
    left_delim = None
    right_delim = None
    size = "auto"

    if func_name in ("\\dfrac", "\\frac", "\\tfrac"):
        has_bar_line = True
    elif func_name == "\\\\atopfrac":
        has_bar_line = False
    elif func_name in ("\\dbinom", "\\binom", "\\tbinom"):
        has_bar_line = False
        left_delim = "("
        right_delim = ")"
    elif func_name == "\\\\bracefrac":
        has_bar_line = False
        left_delim = "\\{"
        right_delim = "\\}"
    elif func_name == "\\\\brackfrac":
        has_bar_line = False
        left_delim = "["
        right_delim = "]"
    else:
        raise ParseError(f"Unrecognized genfrac command: {func_name}")

    if func_name in ("\\dfrac", "\\dbinom"):
        size = "display"
    elif func_name in ("\\tfrac", "\\tbinom"):
        size = "text"

    return {
        "type": "genfrac",
        "mode": parser.mode,
        "continued": continued,
        "numer": numer,
        "denom": denom,
        "hasBarLine": has_bar_line,
        "leftDelim": left_delim,
        "rightDelim": right_delim,
        "size": size,
        "barSize": None,
    }


def _infix_genfrac_handler(context):
    """Handler for infix fraction commands."""
    func_name = context["funcName"]
    token = context["token"]

    replace_map = {
        "\\over": "\\frac",
        "\\choose": "\\binom",
        "\\atop": "\\\\atopfrac",
        "\\brace": "\\\\bracefrac",
        "\\brack": "\\\\brackfrac",
    }

    if func_name not in replace_map:
        raise ParseError(f"Unrecognized infix genfrac command: {func_name}")

    return {
        "type": "infix",
        "mode": context["parser"].mode,
        "replaceWith": replace_map[func_name],
        "token": token,
    }


def _genfrac_full_handler(context, args):
    """Handler for \genfrac command."""
    from ..parse_node import assert_node_type

    parser = context["parser"]
    numer = args[4]
    denom = args[5]

    # Parse delimiters
    left_node = normalize_argument(args[0])
    left_delim = (delim_from_value(left_node["text"])
                  if left_node.get("type") == "atom" and left_node.get("family") == "open"
                  else None)

    right_node = normalize_argument(args[1])
    right_delim = (delim_from_value(right_node["text"])
                   if right_node.get("type") == "atom" and right_node.get("family") == "close"
                   else None)

    # Parse bar size
    bar_node = assert_node_type(args[2], "size")
    if bar_node.get("isBlank"):
        has_bar_line = True
        bar_size = None
    else:
        bar_size = bar_node.get("value")
        has_bar_line = bar_size and bar_size.get("number", 0) > 0

    # Parse style
    styl_array = ["display", "text", "script", "scriptscript"]
    size = "auto"
    styl = args[3]

    if styl.get("type") == "ordgroup" and styl.get("body"):
        text_ord = assert_node_type(styl["body"][0], "textord")
        size_index = int(text_ord["text"])
        size = styl_array[size_index] if 0 <= size_index < len(styl_array) else "auto"
    else:
        styl = assert_node_type(styl, "textord")
        size_index = int(styl["text"])
        size = styl_array[size_index] if 0 <= size_index < len(styl_array) else "auto"

    return {
        "type": "genfrac",
        "mode": parser.mode,
        "numer": numer,
        "denom": denom,
        "continued": False,
        "hasBarLine": has_bar_line,
        "barSize": bar_size,
        "leftDelim": left_delim,
        "rightDelim": right_delim,
        "size": size,
    }


def _above_handler(context, args):
    """Handler for \above command."""
    from ..parse_node import assert_node_type

    return {
        "type": "infix",
        "mode": context["parser"].mode,
        "replaceWith": "\\\\abovefrac",
        "size": assert_node_type(args[0], "size")["value"],
        "token": context["token"],
    }


def _abovefrac_handler(context, args):
    """Handler for \\abovefrac command."""
    from ..parse_node import assert_node_type

    numer = args[0]
    bar_size = assert_node_type(args[1], "infix")["size"]
    denom = args[2]

    has_bar_line = bar_size and bar_size.get("number", 0) > 0

    return {
        "type": "genfrac",
        "mode": context["parser"].mode,
        "numer": numer,
        "denom": denom,
        "continued": False,
        "hasBarLine": has_bar_line,
        "barSize": bar_size,
        "leftDelim": None,
        "rightDelim": None,
        "size": "auto",
    }


# Define the fraction functions
define_function({
    "type": "genfrac",
    "names": [
        "\\dfrac", "\\frac", "\\tfrac",
        "\\dbinom", "\\binom", "\\tbinom",
        "\\\\atopfrac",  # can't be entered directly
        "\\\\bracefrac", "\\\\brackfrac",  # ditto
    ],
    "props": {
        "numArgs": 2,
        "allowedInArgument": True,
    },
    "handler": lambda context, args: _genfrac_handler(context, args, False),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

define_function({
    "type": "genfrac",
    "names": ["\\cfrac"],
    "props": {
        "numArgs": 2,
    },
    "handler": lambda context, args: _genfrac_handler(context, args, True),
})

# Infix generalized fractions
define_function({
    "type": "infix",
    "names": ["\\over", "\\choose", "\\atop", "\\brace", "\\brack"],
    "props": {
        "numArgs": 0,
        "infix": True,
    },
    "handler": _infix_genfrac_handler,
})

# \genfrac function
define_function({
    "type": "genfrac",
    "names": ["\\genfrac"],
    "props": {
        "numArgs": 6,
        "allowedInArgument": True,
        "argTypes": ["math", "math", "size", "text", "math", "math"],
    },
    "handler": _genfrac_full_handler,
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# \above function
define_function({
    "type": "infix",
    "names": ["\\above"],
    "props": {
        "numArgs": 1,
        "argTypes": ["size"],
        "infix": True,
    },
    "handler": _above_handler,
})

define_function({
    "type": "genfrac",
    "names": ["\\\\abovefrac"],
    "props": {
        "numArgs": 3,
        "argTypes": ["math", "size", "math"],
    },
    "handler": _abovefrac_handler,
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})
