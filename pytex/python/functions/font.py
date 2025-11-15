"""Python port of KaTeX's functions/font.js - font handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..define_function import define_function, normalize_argument
from ..utils import is_character_box

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode

# Import binrelClass from mclass
try:
    from .mclass import binrelClass
except ImportError:
    def binrelClass(body):
        """Fallback binrel class function."""
        return "mord"  # Default


def html_builder(group: ParseNode, options: Options):
    """Build HTML for font group."""
    from .. import build_html as html

    font = group["font"]
    new_options = options.with_font(font)
    return html.build_group(group["body"], new_options)


def mathml_builder(group: ParseNode, options: Options):
    """Build MathML for font group."""
    from .. import build_mathml as mml

    font = group["font"]
    new_options = options.with_font(font)
    return mml.build_group(group["body"], new_options)


# Font aliases
FONT_ALIASES = {
    "\\Bbb": "\\mathbb",
    "\\bold": "\\mathbf",
    "\\frak": "\\mathfrak",
    "\\bm": "\\boldsymbol",
}

# Main font functions
define_function({
    "type": "font",
    "names": [
        # styles
        "\\mathrm", "\\mathit", "\\mathbf", "\\mathnormal", "\\mathsfit",

        # families
        "\\mathbb", "\\mathcal", "\\mathfrak", "\\mathscr", "\\mathsf",
        "\\mathtt",

        # aliases
        "\\Bbb", "\\bold", "\\frak",
    ],
    "props": {
        "numArgs": 1,
        "allowedInArgument": True,
    },
    "handler": lambda context, args: _font_handler(context, args, False),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# Bold functions with mclass handling
define_function({
    "type": "mclass",
    "names": ["\\boldsymbol", "\\bm"],
    "props": {
        "numArgs": 1,
    },
    "handler": lambda context, args: {
        "type": "mclass",
        "mode": context["parser"].mode,
        "mclass": binrelClass(args[0]),
        "body": [{
            "type": "font",
            "mode": context["parser"].mode,
            "font": "boldsymbol",
            "body": args[0],
        }],
        "isCharacterBox": is_character_box(args[0]),
    },
})

# Old-style font commands
define_function({
    "type": "font",
    "names": ["\\rm", "\\sf", "\\tt", "\\bf", "\\it", "\\cal"],
    "props": {
        "numArgs": 0,
        "allowedInText": True,
    },
    "handler": lambda context, args: _old_font_handler(context, args),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})


def _font_handler(context, args, is_old_style=False):
    """Handler for font commands."""
    body = normalize_argument(args[0]) if not is_old_style else args[0]

    func = context["funcName"]
    if func in FONT_ALIASES:
        func = FONT_ALIASES[func]

    return {
        "type": "font",
        "mode": context["parser"].mode,
        "font": func[1:],  # Remove backslash
        "body": body,
    }


def _old_font_handler(context, args):
    """Handler for old-style font commands."""
    mode = context["parser"].mode
    body = context["parser"].parse_expression(True, context.get("breakOnTokenText"))

    func_name = context["funcName"]
    style = f"math{func_name[1:]}"  # Remove backslash and add 'math' prefix

    return {
        "type": "font",
        "mode": mode,
        "font": style,
        "body": {
            "type": "ordgroup",
            "mode": mode,
            "body": body,
        },
    }
