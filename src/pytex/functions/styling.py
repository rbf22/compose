"""Python port of KaTeX's functions/styling.js - style changing commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..define_function import define_function
from ..mathml_tree import MathNode
from ..style import Style
from ..tree import VirtualNode

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import AnyParseNode, ParseNode, StylingParseNode
    from ..tree import DocumentFragment

# Import sizingGroup from sizing
try:
    from .sizing import sizing_group
except ImportError:
    def sizing_group(
        value: list[AnyParseNode],
        options: Options,
        base_options: Options,
    ) -> DocumentFragment:
        """Fallback sizing group function when sizing module is unavailable."""
        raise RuntimeError("sizing module is required for styling commands")

# Style mapping
STYLE_MAP = {
    "display": Style.DISPLAY,
    "text": Style.TEXT,
    "script": Style.SCRIPT,
    "scriptscript": Style.SCRIPTSCRIPT,
}

# Style attributes for MathML
STYLE_ATTRIBUTES = {
    "display": ["0", "true"],
    "text": ["0", "false"],
    "script": ["1", "false"],
    "scriptscript": ["2", "false"],
}


# Style changing commands
define_function({
    "type": "styling",
    "names": [
        "\\displaystyle", "\\textstyle", "\\scriptstyle",
        "\\scriptscriptstyle",
    ],
    "props": {
        "numArgs": 0,
        "allowedInText": True,
        "primitive": True,
    },
    "handler": lambda context, args, opt_args: _styling_handler(context, args),
    "html_builder": lambda group, options: _styling_html_builder(group, options),
    "mathml_builder": lambda group, options: _styling_mathml_builder(group, options),
})


def _styling_handler(context: dict[str, Any], args: Any) -> dict[str, Any]:
    """Handler for style changing commands."""
    # Parse out the implicit body
    body = context["parser"].parse_expression(True, context.get("breakOnTokenText"))

    # Extract style from function name (remove \ and style)
    func_name = context["funcName"]
    style = func_name[1:-5]  # Remove \ and style

    return {
        "type": "styling",
        "mode": context["parser"].mode,
        "style": style,
        "body": body,
    }


def _styling_html_builder(group: ParseNode, options: Options) -> Any:
    """Build HTML for style changes."""
    styling_group = cast("StylingParseNode", group)
    new_style = STYLE_MAP[styling_group["style"]]
    new_options = options.having_style(new_style).with_font('')
    return sizing_group(styling_group["body"], new_options, options)


def _styling_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for style changes."""
    from .. import build_mathml as mml

    styling_group = cast("StylingParseNode", group)
    new_style = STYLE_MAP[styling_group["style"]]
    new_options = options.having_style(new_style)

    inner = mml.build_expression(styling_group["body"], new_options)

    node = MathNode("mstyle", cast(list[VirtualNode], inner))

    attr = STYLE_ATTRIBUTES[styling_group["style"]]
    node.set_attribute("scriptlevel", attr[0])
    node.set_attribute("displaystyle", attr[1])

    return node
