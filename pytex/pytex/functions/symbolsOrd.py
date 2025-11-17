"""Python port of KaTeX's functions/symbolsOrd.js - ordinary symbol handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from ..build_common import make_ord
from ..define_function import define_function_builders
from ..mathml_tree import MathNode

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import MathordParseNode, ParseNode, TextordParseNode


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


def _mathord_mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for mathord symbols."""
    from .. import build_mathml as mml
    import re

    mathord_group = cast("MathordParseNode", group)
    text = mathord_group["text"]

    # KaTeX emits digits as <mn> rather than <mi>.  For identifiers we keep
    # <mi> with italic default, but for numbers we use <mn> with normal
    # variant and avoid an explicit mathvariant attribute unless it differs
    # from the default for that node type.
    node_type = "mn" if re.match(r"^[0-9]+$", text) else "mi"
    node = MathNode(node_type, [mml.make_text(text, mathord_group["mode"], options)])

    default_variant = DEFAULT_VARIANT.get(node_type, "")
    variant = mml.get_variant(mathord_group, options) or default_variant
    if variant != default_variant:
        node.set_attribute("mathvariant", variant)

    return node


def _textord_mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for textord symbols."""
    from .. import build_mathml as mml
    import re

    textord_group = cast("TextordParseNode", group)
    text = mml.make_text(textord_group["text"], textord_group["mode"], options)
    variant = mml.get_variant(textord_group, options) or "normal"

    # Determine appropriate MathML element type
    if textord_group["mode"] == 'text':
        node = MathNode("mtext", [text])
    elif re.match(r'[0-9]', textord_group["text"]):
        node = MathNode("mn", [text])
    elif textord_group["text"] == "\\prime":
        node = MathNode("mo", [text])
    else:
        node = MathNode("mi", [text])

    if variant != DEFAULT_VARIANT.get(node.type, ""):
        node.set_attribute("mathvariant", variant)

    return node
