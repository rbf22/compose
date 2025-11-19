"""Python port of KaTeX's functions/mathchoice.js - style-dependent math choice."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..build_common import make_fragment
from ..define_function import define_function, ordargument
from ..style import STYLES

# Import style constants for easier access
DISPLAY, DISPLAY_CRAMPED, TEXT, TEXT_CRAMPED, SCRIPT, SCRIPT_CRAMPED, SCRIPTSCRIPT, SCRIPTSCRIPT_CRAMPED = STYLES

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import MathchoiceParseNode, ParseNode


def choose_math_style(group: ParseNode, options: Options) -> list:
    """Choose the appropriate math expression based on current style."""
    mathchoice_group = cast("MathchoiceParseNode", group)
    style_size = options.style.size

    if style_size == DISPLAY.size:
        return mathchoice_group["display"]
    elif style_size == TEXT.size:
        return mathchoice_group["text"]
    elif style_size == SCRIPT.size:
        return mathchoice_group["script"]
    elif style_size == SCRIPTSCRIPT.size:
        return mathchoice_group["scriptscript"]
    else:
        return mathchoice_group["text"]


# \mathchoice command for style-dependent expressions
define_function({
    "type": "mathchoice",
    "names": ["\\mathchoice"],
    "props": {
        "numArgs": 4,
        "primitive": True,
    },
    "handler": lambda context, args, opt_args: {
        "type": "mathchoice",
        "mode": context["parser"].mode,
        "display": ordargument(args[0]),
        "text": ordargument(args[1]),
        "script": ordargument(args[2]),
        "scriptscript": ordargument(args[3]),
    },
    "html_builder": lambda group, options: _mathchoice_html_builder(group, options),
    "mathml_builder": lambda group, options: _mathchoice_mathml_builder(group, options),
})


def _mathchoice_html_builder(group: ParseNode, options: Options) -> Any:
    """Build HTML for mathchoice - choose expression based on style."""
    from .. import build_html as html

    body = choose_math_style(group, options)
    elements = html.build_expression(body, options, False)
    return make_fragment(elements)


def _mathchoice_mathml_builder(group: ParseNode, options: Options) -> Any:
    """Build MathML for mathchoice - choose expression based on style."""
    from .. import build_mathml as mml

    body = choose_math_style(group, options)
    return mml.build_expression_row(body, options)
