"""Python port of KaTeX's functions/sizing.js - font sizing commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, cast

from ..build_common import make_fragment
from ..define_function import define_function
from ..mathml_tree import MathNode
from ..units import make_em

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import AnyParseNode, ParseNode, SizingParseNode
    from ..dom_tree import HtmlDomNode


def sizing_group(
    value: List[AnyParseNode],
    options: "Options",
    base_options: "Options",
) -> HtmlDomNode:
    """Create a sizing group with proper scaling."""
    from .. import build_html as html

    inner = html.build_expression(value, options, False)
    multiplier = options.size_multiplier / base_options.size_multiplier

    # Add size-resetting classes and scale dimensions
    for item in inner:
        pos = -1
        try:
            pos = item.classes.index("sizing")
        except ValueError:
            pass

        if pos < 0:
            item.classes.extend(options.sizing_classes(base_options))
        elif pos + 1 < len(item.classes) and item.classes[pos + 1] == f"reset-size{options.size}":
            # Nested size change - override old size
            item.classes[pos + 1] = f"reset-size{base_options.size}"

        item.height *= multiplier
        item.depth *= multiplier

    return make_fragment(inner)


# Size function names
SIZE_FUNCS = [
    "\\tiny", "\\sixptsize", "\\scriptsize", "\\footnotesize", "\\small",
    "\\normalsize", "\\large", "\\Large", "\\LARGE", "\\huge", "\\Huge",
]

def html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for sizing commands."""
    sizing_group_node = cast("SizingParseNode", group)
    new_options = options.having_size(sizing_group_node["size"])
    return sizing_group(sizing_group_node["body"], new_options, options)


def mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for sizing commands."""
    from .. import build_mathml as mml

    sizing_group_node = cast("SizingParseNode", group)
    new_options = options.having_size(sizing_group_node["size"])
    inner = mml.build_expression(sizing_group_node["body"], new_options)

    node = MathNode("mstyle", inner)
    # Set mathsize attribute
    node.set_attribute("mathsize", make_em(new_options.size_multiplier))

    return node


# Define sizing functions
define_function({
    "type": "sizing",
    "names": SIZE_FUNCS,
    "props": {
        "numArgs": 0,
        "allowedInText": True,
    },
    "handler": lambda context, args: {
        "type": "sizing",
        "mode": context["parser"].mode,
        "size": SIZE_FUNCS.index(context["funcName"]) + 1,  # Size is 1-indexed
        "body": context["parser"].parse_expression(False, context.get("breakOnTokenText")),
    },
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})
