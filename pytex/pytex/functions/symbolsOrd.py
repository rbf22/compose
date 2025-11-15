"""Python port of KaTeX's functions/symbolsOrd.js - ordinary symbol handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..build_common import make_ord
from ..define_function import define_function_builders
from ..mathml_tree import MathNode

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode

# Default variants for MathML elements
DEFAULT_VARIANT = {
    "mi": "italic",
    "mn": "normal",
    "mtext": "normal",
}

# Mathord (mathematical ordinary) symbols
define_function_builders({
    "type": "mathord",
    "html_builder": lambda group, options: make_ord(group, options, "mathord"),
    "mathml_builder": lambda group, options: _mathord_mathml_builder(group, options),
})

# Textord (text ordinary) symbols
define_function_builders({
    "type": "textord",
    "html_builder": lambda group, options: make_ord(group, options, "textord"),
    "mathml_builder": lambda group, options: _textord_mathml_builder(group, options),
})


def _mathord_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for mathord symbols."""
    from .. import build_mathml as mml

    node = MathNode("mi", [mml.make_text(group["text"], group["mode"], options)])

    variant = mml.get_variant(group, options) or "italic"
    if variant != DEFAULT_VARIANT.get(node.type, ""):
        node.set_attribute("mathvariant", variant)

    return node


def _textord_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for textord symbols."""
    from .. import build_mathml as mml
    import re

    text = mml.make_text(group["text"], group["mode"], options)
    variant = mml.get_variant(group, options) or "normal"

    # Determine appropriate MathML element type
    if group["mode"] == 'text':
        node = MathNode("mtext", [text])
    elif re.match(r'[0-9]', group["text"]):
        node = MathNode("mn", [text])
    elif group["text"] == "\\prime":
        node = MathNode("mo", [text])
    else:
        node = MathNode("mi", [text])

    if variant != DEFAULT_VARIANT.get(node.type, ""):
        node.set_attribute("mathvariant", variant)

    return node
