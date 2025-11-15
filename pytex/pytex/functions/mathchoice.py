"""Python port of KaTeX's functions/mathchoice.js - style-dependent math choice."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..build_common import make_fragment
from ..define_function import define_function, ordargument
from ..style import Style

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode


def choose_math_style(group: ParseNode, options: Options):
    """Choose the appropriate math expression based on current style."""
    style_size = options.style.size

    if style_size == Style.DISPLAY.size:
        return group["display"]
    elif style_size == Style.TEXT.size:
        return group["text"]
    elif style_size == Style.SCRIPT.size:
        return group["script"]
    elif style_size == Style.SCRIPTSCRIPT.size:
        return group["scriptscript"]
    else:
        return group["text"]


# \mathchoice command for style-dependent expressions
define_function({
    "type": "mathchoice",
    "names": ["\\mathchoice"],
    "props": {
        "numArgs": 4,
        "primitive": True,
    },
    "handler": lambda context, args: {
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


def _mathchoice_html_builder(group: ParseNode, options: Options):
    """Build HTML for mathchoice - choose expression based on style."""
    from .. import build_html as html

    body = choose_math_style(group, options)
    elements = html.build_expression(body, options, False)
    return make_fragment(elements)


def _mathchoice_mathml_builder(group: ParseNode, options: Options):
    """Build MathML for mathchoice - choose expression based on style."""
    from .. import build_mathml as mml

    body = choose_math_style(group, options)
    return mml.build_expression_row(body, options)
