"""Python port of KaTeX's functions/delimsizing.js - delimiter sizing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..build_common import make_span
from ..define_function import define_function
from ..mathml_tree import MathNode
from ..parse_error import ParseError
from ..parse_node import assert_node_type, check_symbol_node_type
from ..units import make_em

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import AnyParseNode, ParseNode, SymbolParseNode
    from ..define_function import FunctionContext

# Delimiter size configurations
DELIMITER_SIZES = {
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


def check_delimiter(delim: AnyParseNode, context: FunctionContext) -> SymbolParseNode:
    """Validate and return delimiter symbol."""
    sym_delim = check_symbol_node_type(delim)
    if sym_delim and sym_delim["text"] in DELIMITERS:
        return sym_delim
    elif sym_delim:
        raise ParseError(
            f"Invalid delimiter '{sym_delim['text']}' after '{context['funcName']}'",
            delim
        )
    else:
        raise ParseError(f"Invalid delimiter type '{delim.get('type', 'unknown')}'", delim)


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


def _delimsizing_handler(context, args):
    """Handler for delimiter sizing commands."""
    delim = check_delimiter(args[0], context)
    size_info = DELIMITER_SIZES[context["funcName"]]

    return {
        "type": "delimsizing",
        "mode": context["parser"].mode,
        "size": size_info["size"],
        "mclass": size_info["mclass"],
        "delim": delim["text"],
    }


def _delimsizing_html_builder(group: ParseNode, options: Options):
    """Build HTML for sized delimiters."""

    if group["delim"] == ".":
        # Empty delimiters still count as elements
        return make_span([group["mclass"]])

    # Use delimiter.sizedDelim to generate the delimiter
    from .. import delimiter
    return delimiter.make_sized_delim(
        group["delim"], group["size"], options, group.get("mode", "math"),
        [group["mclass"]]
    )


def _delimsizing_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for sized delimiters."""
    from .. import build_mathml as mml
    from .. import delimiter

    children = []

    if group["delim"] != ".":
        children.append(mml.make_text(group["delim"], group.get("mode", "math")))

    node = MathNode("mo", children)

    if group["mclass"] in ("mopen", "mclose"):
        # Fence delimiters
        node.set_attribute("fence", "true")
    else:
        # Explicitly disable fencing
        node.set_attribute("fence", "false")

    node.set_attribute("stretchy", "true")
    size = make_em(delimiter.SIZE_TO_MAX_HEIGHT.get(group["size"], 0))
    node.set_attribute("minsize", size)
    node.set_attribute("maxsize", size)

    return node


def _right_handler(context, args):
    """Handler for \right delimiter."""
    color = context["parser"].gullet.macros.get("\\current@color")
    if color and not isinstance(color, str):
        raise ParseError("\\current@color set to non-string in \\right")

    return {
        "type": "leftright-right",
        "mode": context["parser"].mode,
        "delim": check_delimiter(args[0], context)["text"],
        "color": color,  # undefined if not set via \color
    }


def _left_handler(context, args):
    """Handler for \left delimiter."""
    delim = check_delimiter(args[0], context)
    parser = context["parser"]

    # Parse out the implicit body
    parser.leftright_depth += 1
    # parseExpression stops before '\\right'
    body = parser.parse_expression(False)
    parser.leftright_depth -= 1

    # Check the next token
    parser.expect("\\right", False)
    right = assert_node_type(parser.parse_function(), "leftright-right")

    return {
        "type": "leftright",
        "mode": parser.mode,
        "body": body,
        "left": delim["text"],
        "right": right["delim"],
        "rightColor": right.get("color"),
    }


def _leftright_html_builder(group: ParseNode, options: Options):
    """Build HTML for \left...\right delimiters."""
    from .. import build_html as html

    assert_parsed(group)

    # Build the inner expression
    inner = html.build_expression(group["body"], options, True, ["mopen", "mclose"])

    inner_height = 0
    inner_depth = 0
    had_middle = False

    # Calculate height and depth
    for item in inner:
        if hasattr(item, 'is_middle') and item.is_middle:
            had_middle = True
        else:
            inner_height = max(item.height, inner_height)
            inner_depth = max(item.depth, inner_depth)

    # Scale based on size multiplier
    inner_height *= options.size_multiplier
    inner_depth *= options.size_multiplier

    # Left delimiter
    from .. import delimiter
    if group["left"] == ".":
        left_delim = html.make_null_delimiter(options, ["mopen"])
    else:
        left_delim = delimiter.make_left_right_delim(
            group["left"], inner_height, inner_depth, options,
            group.get("mode", "math"), ["mopen"]
        )
    inner.insert(0, left_delim)

    # Handle middle delimiters
    if had_middle:
        for i in range(1, len(inner)):
            item = inner[i]
            if hasattr(item, 'is_middle') and item.is_middle:
                # Apply the options that were active when \middle was called
                middle_info = item.is_middle
                inner[i] = delimiter.make_left_right_delim(
                    middle_info["delim"], inner_height, inner_depth,
                    middle_info["options"], group.get("mode", "math"), []
                )

    # Right delimiter (with color support)
    if group["right"] == ".":
        right_delim = html.make_null_delimiter(options, ["mclose"])
    else:
        color_options = (options.with_color(group["rightColor"])
                        if group.get("rightColor") else options)
        right_delim = delimiter.make_left_right_delim(
            group["right"], inner_height, inner_depth, color_options,
            group.get("mode", "math"), ["mclose"]
        )
    inner.append(right_delim)

    return make_span(["minner"], inner, options)


def _leftright_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for \left...\right delimiters."""
    from .. import build_mathml as mml

    assert_parsed(group)
    inner = mml.build_expression(group["body"], options)

    if group["left"] != ".":
        left_node = MathNode("mo", [mml.make_text(group["left"], group.get("mode", "math"))])
        left_node.set_attribute("fence", "true")
        inner.insert(0, left_node)

    if group["right"] != ".":
        right_node = MathNode("mo", [mml.make_text(group["right"], group.get("mode", "math"))])
        right_node.set_attribute("fence", "true")

        if group.get("rightColor"):
            right_node.set_attribute("mathcolor", group["rightColor"])

        inner.append(right_node)

    return mml.make_row(inner)


def _middle_handler(context, args):
    """Handler for \middle delimiter."""
    delim = check_delimiter(args[0], context)

    if not context["parser"].leftright_depth:
        raise ParseError("\\middle without preceding \\left", delim)

    return {
        "type": "middle",
        "mode": context["parser"].mode,
        "delim": delim["text"],
    }


def _middle_html_builder(group: ParseNode, options: Options):
    """Build HTML for \middle delimiters."""
    from .. import build_html as html
    from .. import delimiter

    if group["delim"] == ".":
        middle_delim = html.make_null_delimiter(options, [])
    else:
        middle_delim = delimiter.make_sized_delim(
            group["delim"], 1, options, group.get("mode", "math"), []
        )

        # Store middle information for later processing
        middle_delim.is_middle = {
            "delim": group["delim"],
            "options": options
        }

    return middle_delim


def _middle_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for \middle delimiters."""
    from .. import build_mathml as mml

    # Use plain "|" instead of \vert for Firefox compatibility
    if group["delim"] in ("\\vert", "|"):
        text_node = mml.make_text("|", "text")
    else:
        text_node = mml.make_text(group["delim"], group.get("mode", "math"))

    middle_node = MathNode("mo", [text_node])
    middle_node.set_attribute("fence", "true")
    # MathML gives 5/18em spacing, but \middle should get delimiter spacing
    middle_node.set_attribute("lspace", "0.05em")
    middle_node.set_attribute("rspace", "0.05em")

    return middle_node
