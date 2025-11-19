"""Python port of KaTeX's functions/symbolsOp.js - operator symbol handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from ..build_common import mathsym
from ..define_function import define_function_builders
from ..mathml_tree import MathNode

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import AtomParseNode, ParseNode


# Atom (operator) symbols
define_function_builders({
    "type": "atom",
    "html_builder": lambda group, options: mathsym(
        group["text"], group["mode"], options, [f"m{group['family']}"]
    ),
    "mathml_builder": lambda group, options: _atom_mathml_builder(group, options),
})


def _atom_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for atom (operator) symbols."""
    from .. import build_mathml as mml

    atom_group = cast("AtomParseNode", group)
    node = MathNode("mo", [mml.make_text(atom_group["text"], atom_group["mode"])])

    family = atom_group.get("family", "")

    if family == "bin":
        variant = mml.get_variant(atom_group, options)
        if variant == "bold-italic":
            node.set_attribute("mathvariant", variant)
    elif family == "punct":
        node.set_attribute("separator", "true")
    elif family in ("open", "close"):
        # Delims built here should not stretch vertically
        # See delimsizing.js for stretchy delims
        node.set_attribute("stretchy", "false")

    return node
