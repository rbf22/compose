"""Python port of KaTeX's functions/op.js - mathematical operators."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..build_common import make_span, make_symbol, make_v_list, mathsym, static_svg
from ..define_function import define_function, ordargument
from ..dom_tree import SymbolNode
from ..mathml_tree import MathNode
from ..style import Style

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode

# Operators that don't have large successors
NO_SUCCESSOR = ["\\smallint"]

def html_builder(group: ParseNode, options: Options):
    """Build HTML for operator group."""
    from .. import build_html as html

    # Handle supsub delegation
    sup_group = None
    sub_group = None
    has_limits = False

    if group.get("type") == "supsub":
        sup_group = group.get("sup")
        sub_group = group.get("sub")
        group = group["base"]  # The op is in the base
        has_limits = True

    style = options.style

    # Determine if operator should be large
    large = (style.size == Style.DISPLAY.size and
            group.get("symbol") and
            group.get("name") not in NO_SUCCESSOR)

    # Build the base operator
    if group.get("symbol"):
        font_name = "Size2-Regular" if large else "Size1-Regular"

        name = group.get("name", "")
        stash = ""

        # Handle special cases for \oiint, \oiiint
        if name in ("\\oiint", "\\oiiint"):
            stash = name[1:]  # Remove backslash
            name = "\\iint" if stash == "oiint" else "\\iiint"

        base = make_symbol(name, font_name, "math", options,
                          ["mop", "op-symbol", "large-op" if large else "small-op"])

        if stash:
            # Overlay the oval for \oiint, \oiiint
            italic = base.italic
            oval = static_svg(f"{stash}Size{'2' if large else '1'}", options)

            base = make_v_list({
                "positionType": "individualShift",
                "children": [
                    {"type": "elem", "elem": base, "shift": 0},
                    {"type": "elem", "elem": oval, "shift": 0.08 if large else 0},
                ],
            }, options)

            name = f"\\{stash}"
            base.classes.insert(0, "mop")
            base.italic = italic

    elif group.get("body"):
        # Operator with body content
        inner = html.build_expression(group["body"], options, True)
        if len(inner) == 1 and isinstance(inner[0], SymbolNode):
            base = inner[0]
            base.classes[0] = "mop"
        else:
            base = make_span(["mop"], inner, options)

    else:
        # Text operator
        name = group.get("name", "")
        output = []
        for i in range(1, len(name)):
            output.append(mathsym(name[i], group.get("mode", "math"), options))
        base = make_span(["mop"], output, options)

    # Calculate base shift and slant
    base_shift = 0
    slant = 0

    if ((isinstance(base, SymbolNode) or
         group.get("name") in ("\\oiint", "\\oiiint")) and
        not group.get("suppressBaseShift", False)):

        # Shift so center lies on axis (rule 13)
        base_shift = (base.height - base.depth) / 2 - options.font_metrics().get("axisHeight", 0)
        slant = base.italic

    if has_limits:
        # Use supsub assembly for limits
        return assemble_sup_sub(base, sup_group, sub_group, options, style, slant, base_shift)
    else:
        # Apply base shift directly
        if base_shift:
            base.style["position"] = "relative"
            base.style["top"] = f"{base_shift}em"
        return base


def mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for operator group."""
    from .. import build_mathml as mml

    if group.get("symbol"):
        # Symbol operator
        node = MathNode("mo", [mml.make_text(group.get("name", ""), group.get("mode", "math"))])
        if group.get("name") in NO_SUCCESSOR:
            node.set_attribute("largeop", "false")

    elif group.get("body"):
        # Operator with body
        node = MathNode("mo", mml.build_expression(group["body"], options))

    else:
        # Text operator
        name = group.get("name", "")
        node = MathNode("mi", [MathNode.TextNode(name[1:])])  # Skip backslash

        # Append ApplyFunction operator
        operator = MathNode("mo", [mml.make_text("\u2061", "text")])
        if group.get("parentIsSupSub"):
            node = MathNode("mrow", [node, operator])
        else:
            # Would need DocumentFragment equivalent
            node = MathNode("mrow", [node, operator])

    return node


# Single character big operators mapping
SINGLE_CHAR_BIG_OPS = {
    "\u220F": "\\prod",
    "\u2210": "\\coprod",
    "\u2211": "\\sum",
    "\u22c0": "\\bigwedge",
    "\u22c1": "\\bigvee",
    "\u22c2": "\\bigcap",
    "\u22c3": "\\bigcup",
    "\u2a00": "\\bigodot",
    "\u2a01": "\\bigoplus",
    "\u2a02": "\\bigotimes",
    "\u2a04": "\\biguplus",
    "\u2a06": "\\bigsqcup",
}

# Single character integrals mapping
SINGLE_CHAR_INTEGRALS = {
    "\u222b": "\\int",
    "\u222c": "\\iint",
    "\u222d": "\\iiint",
    "\u222e": "\\oint",
    "\u222f": "\\oiint",
    "\u2230": "\\oiiint",
}

# Big operators (limits, symbols)
define_function({
    "type": "op",
    "names": [
        "\\coprod", "\\bigvee", "\\bigwedge", "\\biguplus", "\\bigcap",
        "\\bigcup", "\\intop", "\\prod", "\\sum", "\\bigotimes",
        "\\bigoplus", "\\bigodot", "\\bigsqcup", "\\smallint",
        "\u220F", "\u2210", "\u2211", "\u22c0", "\u22c1", "\u22c2", "\u22c3",
        "\u2a00", "\u2a01", "\u2a02", "\u2a04", "\u2a06",
    ],
    "props": {
        "numArgs": 0,
    },
    "handler": lambda context, args: _op_handler(context, args, limits=True, symbol=True),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# Mathop command
define_function({
    "type": "op",
    "names": ["\\mathop"],
    "props": {
        "numArgs": 1,
        "primitive": True,
    },
    "handler": lambda context, args: {
        "type": "op",
        "mode": context["parser"].mode,
        "limits": False,
        "parentIsSupSub": False,
        "symbol": False,
        "body": ordargument(args[0]),
    },
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# No limits, not symbols (function names)
define_function({
    "type": "op",
    "names": [
        "\\arcsin", "\\arccos", "\\arctan", "\\arctg", "\\arcctg",
        "\\arg", "\\ch", "\\cos", "\\cosec", "\\cosh", "\\cot", "\\cotg",
        "\\coth", "\\csc", "\\ctg", "\\cth", "\\deg", "\\dim", "\\exp",
        "\\hom", "\\ker", "\\lg", "\\ln", "\\log", "\\sec", "\\sin",
        "\\sinh", "\\sh", "\\tan", "\\tanh", "\\tg", "\\th",
    ],
    "props": {
        "numArgs": 0,
    },
    "handler": lambda context, args: _op_handler(context, args, limits=False, symbol=False),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# Limits, not symbols (operators like lim, max, etc.)
define_function({
    "type": "op",
    "names": [
        "\\det", "\\gcd", "\\inf", "\\lim", "\\max", "\\min", "\\Pr", "\\sup",
    ],
    "props": {
        "numArgs": 0,
    },
    "handler": lambda context, args: _op_handler(context, args, limits=True, symbol=False),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# No limits, symbols (integrals)
define_function({
    "type": "op",
    "names": [
        "\\int", "\\iint", "\\iiint", "\\oint", "\\oiint", "\\oiiint",
        "\u222b", "\u222c", "\u222d", "\u222e", "\u222f", "\u2230",
    ],
    "props": {
        "numArgs": 0,
    },
    "handler": lambda context, args: _op_handler(context, args, limits=False, symbol=True),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})


def _op_handler(context, args, limits: bool, symbol: bool):
    """Common handler for operator functions."""
    func_name = context["funcName"]

    # Handle single character operators
    if len(func_name) == 1:
        if symbol and limits:
            func_name = SINGLE_CHAR_BIG_OPS.get(func_name, func_name)
        elif symbol and not limits:
            func_name = SINGLE_CHAR_INTEGRALS.get(func_name, func_name)

    return {
        "type": "op",
        "mode": context["parser"].mode,
        "limits": limits,
        "parentIsSupSub": False,
        "symbol": symbol,
        "name": func_name,
    }


# Import assembleSupSub utility
try:
    from .utils.assembleSupSub import assembleSupSub as assemble_sup_sub
except ImportError:
    # Fallback if utils not available
    def assemble_sup_sub(base, sup_group, sub_group, options, style, slant, base_shift):
        """Fallback assembly for sup/sub on operators."""
        # This would need the full implementation from utils/assembleSupSub.js
        # For now, just return the base
        return base
