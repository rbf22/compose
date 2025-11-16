"""Python port of KaTeX's functions/delimsizing.js - delimiter sizing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, cast

from ..build_common import make_span
from ..define_function import define_function
from ..mathml_tree import MathNode
from ..tree import VirtualNode
from ..parse_error import ParseError
from ..parse_node import assert_node_type, check_symbol_node_type
from ..types import Mode
from ..units import make_em

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import (
        AnyParseNode,
        DelimsizingParseNode,
        LeftrightParseNode,
        LeftrightRightParseNode,
        MiddleParseNode,
        ParseNode,
        SymbolParseNode,
    )

# Delimiter size configurations
DELIMITER_SIZES: Dict[str, Dict[str, Union[str, int]]] = {
    "\\bigl": {"mclass": "mopen", "size": 1},
    "\\Bigl": {"mclass": "mopen", "size": 2},
    "\\biggl": {"mclass": "mopen", "size": 3},
    "\\Biggl": {"mclass": "mopen", "size": 4},
    "\\bigr": {"mclass": "mclose", "size": 1},
    "\\Bigr": {"mclass": "mclose", "size": 2},
    "\\biggr": {"mclass": "mclose", "size": 3},
    "\\Biggr": {"mclass": "mclose", "size": 4},
    "\\bigm": {"mclass": "mrel", "size": 1},
    "\\Bigm": {"mclass": "mrel", "size": 2},
    "\\biggm": {"mclass": "mrel", "size": 3},
    "\\Biggm": {"mclass": "mrel", "size": 4},
    "\\big": {"mclass": "mord", "size": 1},
    "\\Big": {"mclass": "mord", "size": 2},
    "\\bigg": {"mclass": "mord", "size": 3},
    "\\Bigg": {"mclass": "mord", "size": 4},
}

# Valid delimiters
DELIMITERS = [
    "(", "\\lparen", ")", "\\rparen",
    "[", "\\lbrack", "]", "\\rbrack",
    "\\{", "\\lbrace", "\\}", "\\rbrace",
    "\\lfloor", "\\rfloor", "\u230a", "\u230b",
    "\\lceil", "\\rceil", "\u2308", "\u2309",
    "<", ">", "\\langle", "\u27e8", "\\rangle", "\u27e9", "\\lt", "\\gt",
    "\\lvert", "\\rvert", "\\lVert", "\\rVert",
    "\\lgroup", "\\rgroup", "\u27ee", "\u27ef",
    "\\lmoustache", "\\rmoustache", "\u23b0", "\u23b1",
    "/", "\\backslash",
    "|", "\\vert", "\\|", "\\Vert",
    "\\uparrow", "\\Uparrow",
    "\\downarrow", "\\Downarrow",
    "\\updownarrow", "\\Updownarrow",
    ".",
]


def _ensure_mode(mode_value: Optional[Union[str, Mode]]) -> Mode:
    """Normalize optional mode values to the Mode enum."""
    if isinstance(mode_value, Mode):
        return mode_value
    if isinstance(mode_value, str):
        try:
            return Mode(mode_value)
        except ValueError:
            return Mode.MATH
    return Mode.MATH


def _size_to_max_height(size: int) -> float:
    from .. import delimiter

    heights = delimiter.SIZE_TO_MAX_HEIGHT
    if not heights:
        return 0.0
    index = max(0, min(size, len(heights) - 1))
    return float(heights[index])


def check_delimiter(delim: AnyParseNode, context: Dict[str, Any]) -> SymbolParseNode:
    """Validate and return delimiter symbol."""
    sym_delim = check_symbol_node_type(delim)
    if sym_delim and sym_delim["text"] in DELIMITERS:
        return sym_delim
    elif sym_delim:
        raise ParseError(
            f"Invalid delimiter '{sym_delim['text']}' after '{context['funcName']}'",
            context.get("token")
        )
    else:
        raise ParseError(
            f"Invalid delimiter type '{delim.get('type', 'unknown')}'",
            context.get("token")
        )


def assert_parsed(group: ParseNode) -> None:
    """Assert that leftright group was fully parsed."""
    if not group.get("body"):
        raise ValueError("Bug: The leftright ParseNode wasn't fully parsed.")


# Delimiter sizing functions
define_function({
    "type": "delimsizing",
    "names": [
        "\\bigl", "\\Bigl", "\\biggl", "\\Biggl",
        "\\bigr", "\\Bigr", "\\biggr", "\\Biggr",
        "\\bigm", "\\Bigm", "\\biggm", "\\Biggm",
        "\\big", "\\Big", "\\bigg", "\\Bigg",
    ],
    "props": {
        "numArgs": 1,
        "argTypes": ["primitive"],
    },
    "handler": lambda context, args: _delimsizing_handler(context, args),
    "html_builder": lambda group, options: _delimsizing_html_builder(group, options),
    "mathml_builder": lambda group, options: _delimsizing_mathml_builder(group, options),
})

# \right delimiter
define_function({
    "type": "leftright-right",
    "names": ["\\right"],
    "props": {
        "numArgs": 1,
        "primitive": True,
    },
    "handler": lambda context, args: _right_handler(context, args),
})

# \left...\right delimiters
define_function({
    "type": "leftright",
    "names": ["\\left"],
    "props": {
        "numArgs": 1,
        "primitive": True,
    },
    "handler": lambda context, args: _left_handler(context, args),
    "html_builder": lambda group, options: _leftright_html_builder(group, options),
    "mathml_builder": lambda group, options: _leftright_mathml_builder(group, options),
})

# \middle delimiters
define_function({
    "type": "middle",
    "names": ["\\middle"],
    "props": {
        "numArgs": 1,
        "primitive": True,
    },
    "handler": lambda context, args: _middle_handler(context, args),
    "html_builder": lambda group, options: _middle_html_builder(group, options),
    "mathml_builder": lambda group, options: _middle_mathml_builder(group, options),
})


def _delimsizing_handler(context: Dict[str, Any], args: List[AnyParseNode]) -> Dict[str, Any]:
    """Handler for delimiter sizing commands."""
    delim = check_delimiter(args[0], context)
    size_info = DELIMITER_SIZES.get(context["funcName"], {"mclass": "mord", "size": 1})

    return {
        "type": "delimsizing",
        "mode": context["parser"].mode,
        "size": size_info["size"],
        "mclass": size_info["mclass"],
        "delim": delim["text"],
    }


def _delimsizing_html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for sized delimiters."""

    delimsizing_group = cast("DelimsizingParseNode", group)
    if delimsizing_group["delim"] == ".":
        # Empty delimiters still count as elements
        return make_span([delimsizing_group["mclass"]])

    # Use delimiter.sizedDelim to generate the delimiter
    from .. import delimiter
    mode = _ensure_mode(delimsizing_group.get("mode"))
    return delimiter.make_sized_delim(
        delimsizing_group["delim"], delimsizing_group["size"], options, mode,
        [delimsizing_group["mclass"]]
    )


def _delimsizing_mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for sized delimiters."""
    from .. import build_mathml as mml

    delimsizing_group = cast("DelimsizingParseNode", group)
    children: List[VirtualNode] = []

    mode = _ensure_mode(delimsizing_group.get("mode"))
    if delimsizing_group["delim"] != ".":
        children.append(mml.make_text(delimsizing_group["delim"], mode))

    node = MathNode("mo", children)

    if delimsizing_group["mclass"] in ("mopen", "mclose"):
        # Fence delimiters
        node.set_attribute("fence", "true")
    else:
        # Explicitly disable fencing
        node.set_attribute("fence", "false")

    node.set_attribute("stretchy", "true")
    size_value = _size_to_max_height(delimsizing_group["size"])
    size_em = make_em(size_value)
    node.set_attribute("minsize", size_em)
    node.set_attribute("maxsize", size_em)

    return node


def _right_handler(context: Dict[str, Any], args: List[AnyParseNode]) -> Dict[str, Any]:
    r"""Handler for \right delimiter."""
    color = context["parser"].gullet.macros.get("\\current@color")
    if color and not isinstance(color, str):
        raise ParseError("\\current@color set to non-string in \\right")

    return {
        "type": "leftright-right",
        "mode": context["parser"].mode,
        "delim": check_delimiter(args[0], context)["text"],
        "color": color,  # undefined if not set via \color
    }


def _left_handler(context: Dict[str, Any], args: List[AnyParseNode]) -> Dict[str, Any]:
    r"""Handler for \left delimiter."""
    delim = check_delimiter(args[0], context)
    parser = context["parser"]

    # Parse out the implicit body
    parser.leftright_depth += 1
    # parseExpression stops before '\\right'
    body = parser.parse_expression(False)
    parser.leftright_depth -= 1

    # Check the next token
    parser.expect("\\right", False)
    right = cast("LeftrightRightParseNode", assert_node_type(parser.parse_function(), "leftright-right"))

    return {
        "type": "leftright",
        "mode": parser.mode,
        "body": body,
        "left": delim["text"],
        "right": right["delim"],
        "rightColor": right.get("color"),
    }


def _leftright_html_builder(group: ParseNode, options: "Options") -> Any:
    r"""Build HTML for \left...\right delimiters."""
    from .. import build_html as html

    leftright_group = cast("LeftrightParseNode", group)
    assert_parsed(leftright_group)

    # Build the inner expression
    inner = html.build_expression(leftright_group["body"], options, True, ["mopen", "mclose"])

    inner_height: float = 0.0
    inner_depth: float = 0.0
    had_middle = False

    # Calculate height and depth
    for item in inner:
        middle_info = getattr(item, "is_middle", None)
        if middle_info:
            had_middle = True
        else:
            inner_height = max(item.height, inner_height)
            inner_depth = max(item.depth, inner_depth)

    # Scale based on size multiplier
    inner_height *= options.size_multiplier
    inner_depth *= options.size_multiplier

    # Left delimiter
    from .. import delimiter
    if leftright_group["left"] == ".":
        left_delim = html.make_null_delimiter(options, ["mopen"])
    else:
        mode = _ensure_mode(leftright_group.get("mode"))
        left_delim = delimiter.make_left_right_delim(
            leftright_group["left"], inner_height, inner_depth, options, mode, ["mopen"]
        )
    inner.insert(0, left_delim)

    # Handle middle delimiters
    if had_middle:
        for i in range(1, len(inner)):
            item = inner[i]
            middle_info = getattr(item, "is_middle", None)
            if middle_info:
                # Apply the options that were active when \middle was called
                inner[i] = delimiter.make_left_right_delim(
                    middle_info["delim"], inner_height, inner_depth,
                    middle_info["options"], _ensure_mode(leftright_group.get("mode")), []
                )

    # Right delimiter (with color support)
    if leftright_group["right"] == ".":
        right_delim = html.make_null_delimiter(options, ["mclose"])
    else:
        color_value = leftright_group.get("rightColor")
        color_options = options.with_color(color_value) if color_value else options
        right_delim = delimiter.make_left_right_delim(
            leftright_group["right"], inner_height, inner_depth, color_options,
            _ensure_mode(leftright_group.get("mode")), ["mclose"]
        )
    inner.append(right_delim)

    return make_span(["minner"], inner, options)


def _leftright_mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    r"""Build MathML for \left...\right delimiters."""
    from .. import build_mathml as mml

    leftright_group = cast("LeftrightParseNode", group)
    assert_parsed(leftright_group)
    inner = mml.build_expression(leftright_group["body"], options)

    mode = _ensure_mode(leftright_group.get("mode"))
    if leftright_group["left"] != ".":
        left_node = MathNode("mo", [mml.make_text(leftright_group["left"], mode)])
        left_node.set_attribute("fence", "true")
        inner.insert(0, left_node)

    if leftright_group["right"] != ".":
        right_node = MathNode("mo", [mml.make_text(leftright_group["right"], mode)])
        right_node.set_attribute("fence", "true")

        right_color = leftright_group.get("rightColor")
        if isinstance(right_color, str):
            right_node.set_attribute("mathcolor", right_color)

        inner.append(right_node)

    return mml.make_row(inner)


def _middle_handler(context: Dict[str, Any], args: List[AnyParseNode]) -> Dict[str, Any]:
    r"""Handler for \middle delimiter."""
    delim = check_delimiter(args[0], context)

    if not context["parser"].leftright_depth:
        raise ParseError("\\middle without preceding \\left", context.get("token"))

    return {
        "type": "middle",
        "mode": context["parser"].mode,
        "delim": delim["text"],
    }


def _middle_html_builder(group: ParseNode, options: "Options") -> Any:
    r"""Build HTML for \middle delimiters."""
    from .. import build_html as html
    from .. import delimiter

    middle_group = cast("MiddleParseNode", group)
    if middle_group["delim"] == ".":
        middle_delim = html.make_null_delimiter(options, [])
    else:
        middle_delim = delimiter.make_sized_delim(
            middle_group["delim"], 1, options, _ensure_mode(middle_group.get("mode")), []
        )

        # Store middle information for later processing
        setattr(middle_delim, "is_middle", {
            "delim": middle_group["delim"],
            "options": options
        })

    return middle_delim


def _middle_mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    r"""Build MathML for \middle delimiters."""
    from .. import build_mathml as mml

    middle_group = cast("MiddleParseNode", group)
    # Use plain "|" instead of \vert for Firefox compatibility
    if middle_group["delim"] in ("\\vert", "|"):
        text_node = mml.make_text("|", Mode.TEXT)
    else:
        text_node = mml.make_text(middle_group["delim"], _ensure_mode(middle_group.get("mode")))

    middle_node = MathNode("mo", [text_node])
    middle_node.set_attribute("fence", "true")
    # MathML gives 5/18em spacing, but \middle should get delimiter spacing
    middle_node.set_attribute("lspace", "0.05em")
    middle_node.set_attribute("rspace", "0.05em")

    return middle_node
