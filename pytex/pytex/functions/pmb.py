"""Python port of KaTeX's functions/pmb.js - poor man's bold."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Mapping, cast

from ..build_common import make_span
from ..define_function import define_function, ordargument
from ..dom_tree import DomSpan
from ..mathml_tree import MathNode

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode, PmbParseNode

# Import binrelClass from mclass
try:
    from .mclass import binrel_class
except ImportError:  # pragma: no cover - fallback for partial ports
    def binrel_class(arg: "ParseNode") -> str:
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
    "handler": lambda context, args: _pmb_handler(context, args),
    "html_builder": lambda group, options: _pmb_html_builder(group, options),
    "mathml_builder": lambda group, options: _pmb_mathml_builder(group, options),
})


def _pmb_handler(context: Dict[str, Any], args: List["ParseNode"]) -> Dict[str, Any]:
    parser = context["parser"]
    return {
        "type": "pmb",
        "mode": parser.mode,
        "mclass": binrel_class(args[0]),
        "body": ordargument(args[0]),
    }


def _pmb_html_builder(group: Mapping[str, Any], options: "Options") -> DomSpan:
    """Build HTML for pmb (poor man's bold)."""
    from .. import build_html as html

    pmb_group = cast("PmbParseNode", group)
    elements = html.build_expression(pmb_group["body"], options, True)
    node = make_span([pmb_group["mclass"]], elements, options)

    # Simulate bold using CSS text-shadow
    node.style["textShadow"] = "0.02em 0.01em 0.04px"

    return node


def _pmb_mathml_builder(group: Mapping[str, Any], options: "Options") -> MathNode:
    """Build MathML for pmb (poor man's bold)."""
    from .. import build_mathml as mml

    pmb_group = cast("PmbParseNode", group)
    inner = mml.build_expression(pmb_group["body"], options)

    # Wrap with mstyle element
    node = MathNode("mstyle", inner)
    node.set_attribute("style", "text-shadow: 0.02em 0.01em 0.04px")

    return node
