"""Python port of KaTeX's functions/font.js - font handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Mapping, cast

from ..build_common import make_span
from ..define_function import define_function, normalize_argument
from ..utils import is_character_box

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import AnyParseNode, FontParseNode, ParseNode


FontGroup = Mapping[str, Any]


def _as_font_name(font_command: str) -> str:
    return font_command.lstrip("\\")


# Import binrelClass from mclass
try:
    from .mclass import binrel_class
except ImportError:  # pragma: no cover - fallback for partial ports
    def _binrel_class(arg: AnyParseNode) -> str:
        """Fallback binrel class function."""
        return "mord"

    binrel_class = _binrel_class


def html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for font group."""
    from .. import build_html as html

    font_group = cast("FontParseNode", group)
    font_name = font_group.get("font", "")
    new_options = options.with_font(font_name)

    body = font_group.get("body")
    if isinstance(body, list):
        expr = body
    elif body is None:
        expr = []
    else:
        expr = [body]

    elements = html.build_expression(expr, new_options, True)
    # Wrap the expression in a single span so callers receive a single
    # HtmlDomNode rather than a raw list.
    return make_span(["mord"], elements, new_options)


def mathml_builder(group: ParseNode, options: "Options") -> Any:
    """Build MathML for font group."""
    from .. import build_mathml as mml

    font_group = cast("FontParseNode", group)
    font_name = font_group.get("font", "")
    new_options = options.with_font(font_name)

    body = font_group.get("body")
    if isinstance(body, list):
        expr = body
    elif body is None:
        expr = []
    else:
        expr = [body]

    nodes = mml.build_expression(expr, new_options)
    # build_expression returns a list of MathNode objects; callers of
    # mathml_builder expect a single MathNode, so wrap in an <mrow> when
    # needed, mirroring other builders like mclass.
    if len(nodes) == 1:
        return nodes[0]
    return mml.make_row(nodes)


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
        "\\mathrm", "\\mathit", "\\mathbf", "\\mathnormal", "\\mathsfit",
        "\\mathbb", "\\mathcal", "\\mathfrak", "\\mathscr", "\\mathsf",
        "\\mathtt",
        "\\Bbb", "\\bold", "\\frak",
    ],
    "props": {
        "numArgs": 1,
        "allowedInArgument": True,
    },
    "handler": lambda context, args, opt_args: _font_handler(context, args, False),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# Bold functions with mclass handling
define_function({
    "type": "mclass",
    "names": ["\\boldsymbol", "\\bm"],
    "props": {"numArgs": 1},
    "handler": lambda context, args, opt_args: _boldsymbol_handler(context, args),
})

# Old-style font commands
define_function({
    "type": "font",
    "names": ["\\rm", "\\sf", "\\tt", "\\bf", "\\it", "\\cal"],
    "props": {
        "numArgs": 0,
        "allowedInText": True,
    },
    "handler": lambda context, args, opt_args: _old_font_handler(context),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})


def _font_handler(context: Dict[str, Any], args: List[AnyParseNode], is_old_style: bool = False) -> Dict[str, Any]:
    body: AnyParseNode = args[0] if is_old_style else normalize_argument(args[0])
    func = context["funcName"]
    func = FONT_ALIASES.get(func, func)
    return {
        "type": "font",
        "mode": context["parser"].mode,
        "font": _as_font_name(func),
        "body": body,
    }


def _old_font_handler(context: Dict[str, Any]) -> Dict[str, Any]:
    parser = context["parser"]
    mode = parser.mode
    body = parser.parse_expression(True, context.get("breakOnTokenText"))
    func_name = context["funcName"]
    style = f"math{func_name.lstrip('\\')}"
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


def _boldsymbol_handler(context: Dict[str, Any], args: List[AnyParseNode]) -> Dict[str, Any]:
    parser = context["parser"]
    body = args[0]
    body_dict = cast(Dict[str, Any], body)
    return {
        "type": "mclass",
        "mode": parser.mode,
        "mclass": binrel_class(body),
        "body": [{
            "type": "font",
            "mode": parser.mode,
            "font": "boldsymbol",
            "body": body,
        }],
        "isCharacterBox": is_character_box(body_dict),
    }
