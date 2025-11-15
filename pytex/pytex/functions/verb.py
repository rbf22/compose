"""Python port of KaTeX's functions/verb.js - verbatim text."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..build_common import make_span, make_symbol, try_combine_chars
from ..define_function import define_function
from ..mathml_tree import MathNode, TextNode
from ..parse_error import ParseError

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode, VerbParseNode


def make_verb(group: ParseNode) -> str:
    """Convert verb group into body string."""
    verb_group = cast("VerbParseNode", group)
    # \verb* replaces spaces with open box \u2423
    # \verb replaces spaces with no-break space \xA0
    return verb_group["body"].replace(' ', '\u2423' if verb_group.get("star") else '\xA0')


# \verb command for verbatim text
define_function({
    "type": "verb",
    "names": ["\\verb"],
    "props": {
        "numArgs": 0,
        "allowedInText": True,
    },
    "handler": lambda context, args, opt_args: _verb_handler(context, args, opt_args),
    "html_builder": lambda group, options: _verb_html_builder(group, options),
    "mathml_builder": lambda group, options: _verb_mathml_builder(group, options),
})


def _verb_handler(context, args, opt_args) -> Any:
    """Handler for \verb command."""
    # \verb and \verb* are handled directly in Parser.js
    # If we get here, it's due to a parsing failure
    raise ParseError("\\verb ended by end of line instead of matching delimiter")


def _verb_html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for verb command."""
    verb_group = cast("VerbParseNode", group)
    text = make_verb(verb_group)
    body = []

    # \verb enters text mode and is sized like \textstyle
    new_options = options.having_style(options.style.text())

    for c in text:
        if c == '~':
            c = '\\textasciitilde'
        body.append(make_symbol(c, "Typewriter-Regular", verb_group["mode"], new_options,
                              ["mord", "texttt"]))

    return make_span(
        ["mord", "text"] + new_options.sizing_classes(options),
        try_combine_chars(body),
        new_options
    )


def _verb_mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for verb command."""
    verb_group = cast("VerbParseNode", group)
    text = TextNode(make_verb(verb_group))
    node = MathNode("mtext", [text])
    node.set_attribute("mathvariant", "monospace")
    return node
