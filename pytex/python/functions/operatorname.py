"""Python port of KaTeX's functions/operatorname.js - operator name handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..build_common import make_span
from ..define_function import define_function, ordargument
from ..define_macro import define_macro
from ..mathml_tree import MathNode, TextNode
from ..parse_node import assert_node_type

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode


def html_builder(group: ParseNode, options: Options):
    """Build HTML for operatorname command."""
    from .. import build_html as html

    # Handle supsub delegation
    sup_group = None
    sub_group = None
    has_limits = False

    if group.get("type") == "supsub":
        sup_group = group.get("sup")
        sub_group = group.get("sub")
        group = assert_node_type(group["base"], "operatorname")
        has_limits = True

    # Build the operator name
    if group.get("body") and len(group["body"]) > 0:
        # Convert body to textord nodes and consolidate
        body = []
        for child in group["body"]:
            child_text = child.get("text")
            if isinstance(child_text, str):
                body.append({
                    "type": "textord",
                    "mode": child.get("mode", "math"),
                    "text": child_text,
                })
            else:
                body.append(child)

        # Build expression with roman font
        expression = html.build_expression(body, options.with_font("mathrm"), True)

        # Replace minus and asterisk symbols
        for child in expression:
            if hasattr(child, 'text'):
                child.text = (child.text.replace('\u2212', '-')
                             .replace('\u2217', '*'))

        base = make_span(["mop"], expression, options)
    else:
        base = make_span(["mop"], [], options)

    if has_limits:
        # Use supsub assembly for limits
        return assemble_sup_sub(base, sup_group, sub_group, options,
                               options.style, 0, 0)
    else:
        return base


def mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for operatorname command."""
    from .. import build_mathml as mml
    from ..mathml_tree import SpaceNode

    expression = mml.build_expression(group["body"], options.with_font("mathrm"))

    # Check if all elements are strings
    is_all_string = True
    for node in expression:
        if isinstance(node, SpaceNode):
            continue
        elif isinstance(node, MathNode):
            if node.type in ("mi", "mn", "ms", "mspace", "mtext"):
                continue
            elif node.type == "mo":
                child = node.children[0] if node.children else None
                if (len(node.children) == 1 and
                    isinstance(child, TextNode)):
                    child.text = (child.text.replace('\u2212', '-')
                                 .replace('\u2217', '*'))
                else:
                    is_all_string = False
            else:
                is_all_string = False
        else:
            is_all_string = False

    if is_all_string:
        # Consolidate into single text node
        word = "".join(node.to_text() for node in expression)
        expression = [TextNode(word)]

    identifier = MathNode("mi", expression)
    identifier.set_attribute("mathvariant", "normal")

    # ApplyFunction operator
    operator = MathNode("mo", [mml.make_text("\u2061", "text")])

    if group.get("parentIsSupSub"):
        return MathNode("mrow", [identifier, operator])
    else:
        # Would need DocumentFragment equivalent
        return MathNode("mrow", [identifier, operator])


# Operator name functions
define_function({
    "type": "operatorname",
    "names": ["\\operatorname@", "\\operatornamewithlimits"],
    "props": {
        "numArgs": 1,
    },
    "handler": lambda context, args: {
        "type": "operatorname",
        "mode": context["parser"].mode,
        "body": ordargument(args[0]),
        "alwaysHandleSupSub": (context["funcName"] == "\\operatornamewithlimits"),
        "limits": False,
        "parentIsSupSub": False,
    },
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# \operatorname macro with star support
define_macro("\\operatorname", "\\@ifstar\\operatornamewithlimits\\operatorname@")


# Import assembleSupSub utility
try:
    from .utils.assembleSupSub import assembleSupSub as assemble_sup_sub
except ImportError:
    # Fallback if utils not available
    def assemble_sup_sub(base, sup_group, sub_group, options, style, slant, base_shift):
        """Fallback assembly for sup/sub on operators."""
        return base
