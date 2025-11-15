"""Python port of KaTeX's functions/hbox.js - horizontal box."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..build_common import make_fragment
from ..define_function import define_function, ordargument
from ..mathml_tree import MathNode

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode


# \hbox - horizontal box (prevents soft line breaks)
# Provided for compatibility with LaTeX \vcenter
# \vcenter can act only on a box, as in:
# \vcenter{\hbox{$\frac{a+b}{\dfrac{c}{d}}$}}
# This function prevents soft line breaks but doesn't do much else
define_function({
    "type": "hbox",
    "names": ["\\hbox"],
    "props": {
        "numArgs": 1,
        "argTypes": ["text"],
        "allowedInText": True,
        "primitive": True,
    },
    "handler": lambda context, args: {
        "type": "hbox",
        "mode": context["parser"].mode,
        "body": ordargument(args[0]),
    },
    "html_builder": lambda group, options: _hbox_html_builder(group, options),
    "mathml_builder": lambda group, options: _hbox_mathml_builder(group, options),
})


def _hbox_html_builder(group: ParseNode, options: Options):
    """Build HTML for hbox."""
    from .. import build_html as html

    elements = html.build_expression(group["body"], options, False)
    return make_fragment(elements)


def _hbox_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for hbox."""
    from .. import build_mathml as mml

    return MathNode("mrow", mml.build_expression(group["body"], options))
