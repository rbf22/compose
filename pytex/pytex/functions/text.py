"""Python port of KaTeX's functions/text.js - text command handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..build_common import make_span
from ..define_function import define_function, ordargument

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode, TextParseNode

# Text font families
TEXT_FONT_FAMILIES = {
    "\\text": None,
    "\\textrm": "textrm",
    "\\textsf": "textsf",
    "\\texttt": "texttt",
    "\\textnormal": "textrm",
}

# Text font weights
TEXT_FONT_WEIGHTS = {
    "\\textbf": "textbf",
    "\\textmd": "textmd",
}

# Text font shapes
TEXT_FONT_SHAPES = {
    "\\textit": "textit",
    "\\textup": "textup",
}


def options_with_font(group: ParseNode, options: "Options") -> "Options":
    """Create options with appropriate font settings."""
    text_group = cast("TextParseNode", group)
    font = text_group.get("font")
    if not font:
        return options
    elif font in TEXT_FONT_FAMILIES:
        family = TEXT_FONT_FAMILIES[font]
        if family:
            return options.with_text_font_family(family)
        return options
    elif font in TEXT_FONT_WEIGHTS:
        return options.with_text_font_weight(TEXT_FONT_WEIGHTS[font])
    elif font == "\\emph":
        # Toggle between italic and upright
        return (options.with_text_font_shape("textup")
                if options.font_shape == "textit"
                else options.with_text_font_shape("textit"))

    return options.with_text_font_shape(TEXT_FONT_SHAPES.get(font, "textup"))


# Text commands
define_function({
    "type": "text",
    "names": [
        # Font families
        "\\text", "\\textrm", "\\textsf", "\\texttt", "\\textnormal",
        # Font weights
        "\\textbf", "\\textmd",
        # Font shapes
        "\\textit", "\\textup", "\\emph",
    ],
    "props": {
        "numArgs": 1,
        "argTypes": ["text"],
        "allowedInArgument": True,
        "allowedInText": True,
    },
    "handler": lambda context, args, opt_args: {
        "type": "text",
        "mode": context["parser"].mode,
        "body": ordargument(args[0]),
        "font": context["funcName"],
    },
    "html_builder": lambda group, options: _text_html_builder(group, options),
    "mathml_builder": lambda group, options: _text_mathml_builder(group, options),
})


def _text_html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for text commands."""
    from .. import build_html as html

    text_group = cast("TextParseNode", group)
    new_options = options_with_font(text_group, options)
    inner = html.build_expression(text_group["body"], new_options, True)
    return make_span(["mord", "text"], inner, new_options)


def _text_mathml_builder(group: ParseNode, options: "Options") -> Any:
    """Build MathML for text commands."""
    from .. import build_mathml as mml

    text_group = cast("TextParseNode", group)
    new_options = options_with_font(text_group, options)
    return mml.build_expression_row(text_group["body"], new_options)
