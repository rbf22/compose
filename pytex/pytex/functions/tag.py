"""Python port of KaTeX's functions/tag.js - equation tagging."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..define_function import define_function_builders
from ..mathml_tree import MathNode

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode


def pad():
    """Create a padding table cell."""
    pad_node = MathNode("mtd", [])
    pad_node.set_attribute("width", "50%")
    return pad_node


# Tag builders for equation numbering
define_function_builders({
    "type": "tag",
    "mathml_builder": lambda group, options: _tag_mathml_builder(group, options),
})


def _tag_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for equation tags."""
    from .. import build_mathml as mml

    table = MathNode("mtable", [
        MathNode("mtr", [
            pad(),
            MathNode("mtd", [
                mml.build_expression_row(group["body"], options),
            ]),
            pad(),
            MathNode("mtd", [
                mml.build_expression_row(group["tag"], options),
            ]),
        ]),
    ])
    table.set_attribute("width", "100%")

    # TODO: Left-aligned tags.
    # Currently, the group and options passed here do not contain
    # enough info to set tag alignment. `leqno` is in Settings but it is
    # not passed to Options. On the HTML side, leqno is
    # set by a CSS class applied in buildTree.js. That would have worked
    # in MathML if browsers supported <mlabeledtr>. Since they don't, we
    # need to rewrite the way this function is called.

    return table
