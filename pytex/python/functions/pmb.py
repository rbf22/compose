"""Python port of KaTeX's functions/pmb.js - poor man's bold."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..build_common import make_span
from ..define_function import define_function, ordargument
from ..mathml_tree import MathNode

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode

# Import binrelClass from mclass
try:
    from .mclass import binrel_class
except ImportError:
    def binrel_class(arg):
        """Fallback binrel class function."""
        return "mord"


# \pmb - poor man's bold (simulates bold using text-shadow)
define_function({
    "type": "pmb",
    "names": ["\\pmb"],
    "props": {
        "numArgs": 1,
        "allowedInText": True,
    },
    "handler": lambda context, args: {
        "type": "pmb",
        "mode": context["parser"].mode,
        "mclass": binrel_class(args[0]),
        "body": ordargument(args[0]),
    },
    "html_builder": lambda group, options: _pmb_html_builder(group, options),
    "mathml_builder": lambda group, options: _pmb_mathml_builder(group, options),
})


def _pmb_html_builder(group: ParseNode, options: Options):
    """Build HTML for pmb (poor man's bold)."""
    from .. import build_html as html

    elements = html.build_expression(group["body"], options, True)
    node = make_span([group["mclass"]], elements, options)

    # Simulate bold using CSS text-shadow
    node.style["textShadow"] = "0.02em 0.01em 0.04px"

    return node


def _pmb_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for pmb (poor man's bold)."""
    from .. import build_mathml as mml

    inner = mml.build_expression(group["body"], options)

    # Wrap with mstyle element
    node = MathNode("mstyle", inner)
    node.set_attribute("style", "text-shadow: 0.02em 0.01em 0.04px")

    return node
