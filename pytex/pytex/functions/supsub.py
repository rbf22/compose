"""Python port of KaTeX's functions/supsub.js - superscript/subscript handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..build_common import make_span, make_v_list
from ..dom_tree import SymbolNode
from ..mathml_tree import MathNode
from ..style import Style
from ..units import make_em
from ..define_function import define_function_builders
from ..utils import is_character_box

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode, SupsubParseNode


def html_builder_delegate(group: ParseNode, options: "Options") -> Any:
    """Check if inner group should handle sup/sub itself."""
    supsub_group = cast("SupsubParseNode", group)
    base = supsub_group.get("base")
    if not base:
        return None
    elif base.get("type") == "op":
        # Operators handle supsubs differently when they have limits
        delegate = (base.get("limits") and
                   (options.style.size == Style.DISPLAY.size or
                    base.get("alwaysHandleSupSub")))
        return delegate  # Would return op.html_builder if implemented
    elif base.get("type") == "operatorname":
        delegate = (base.get("alwaysHandleSupSub") and
                   (options.style.size == Style.DISPLAY.size or base.get("limits")))
        return delegate  # Would return operatorname.html_builder if implemented
    elif base.get("type") == "accent":
        return is_character_box(base.get("base"))  # Would return accent.html_builder
    elif base.get("type") == "horizBrace":
        is_sup = not supsub_group.get("sub")
        return is_sup == base.get("isOver")  # Would return horizBrace.html_builder
    else:
        return None


def html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for superscript/subscript group."""
    from .. import build_html as html

    supsub_group = cast("SupsubParseNode", group)
    # Check if inner group should handle sup/sub itself
    builder_delegate = html_builder_delegate(supsub_group, options)
    if builder_delegate:
        # Would delegate to appropriate builder
        pass

    value_base = supsub_group.get("base")
    value_sup = supsub_group.get("sup")
    value_sub = supsub_group.get("sub")

    base = html.build_group(value_base, options)
    supm = None
    subm = None

    metrics = options.font_metrics()

    # Rule 18a
    sup_shift = 0
    sub_shift = 0

    is_character_box_base = value_base and is_character_box(value_base)

    if value_sup:
        new_options = options.having_style(options.style.sup())
        supm = html.build_group(value_sup, new_options, options)
        if not is_character_box_base:
            sup_shift = (base.height - new_options.font_metrics().get("supDrop", 0)
                        * new_options.size_multiplier / options.size_multiplier)

    if value_sub:
        new_options = options.having_style(options.style.sub())
        subm = html.build_group(value_sub, new_options, options)
        if not is_character_box_base:
            sub_shift = (base.depth + new_options.font_metrics().get("subDrop", 0)
                        * new_options.size_multiplier / options.size_multiplier)

    # Rule 18c
    if options.style == Style.DISPLAY:
        min_sup_shift = metrics.get("sup1", 0)
    elif options.style.cramped:
        min_sup_shift = metrics.get("sup3", 0)
    else:
        min_sup_shift = metrics.get("sup2", 0)

    # Scriptspace is font-size-independent
    multiplier = options.size_multiplier
    margin_right = make_em((0.5 / metrics.get("ptPerEm", 10)) / multiplier)

    margin_left = None
    if subm:
        # Handle italic correction for subscripts
        is_oiint = (supsub_group.get("base") and
                   supsub_group["base"].get("type") == "op" and
                   supsub_group["base"].get("name") and
                   supsub_group["base"]["name"] in ("\\oiint", "\\oiiint"))
        if isinstance(base, SymbolNode) or is_oiint:
            margin_left = make_em(-base.italic)

    if supm and subm:
        # Both superscript and subscript
        sup_shift = max(sup_shift, min_sup_shift,
                       supm.depth + 0.25 * metrics.get("xHeight", 0))
        sub_shift = max(sub_shift, metrics.get("sub2", 0))

        rule_width = metrics.get("defaultRuleThickness", 0.04)

        # Rule 18e - ensure minimum separation
        max_width = 4 * rule_width
        if (sup_shift - supm.depth) - (subm.height - sub_shift) < max_width:
            sub_shift = max_width - (sup_shift - supm.depth) + subm.height
            psi = 0.8 * metrics.get("xHeight", 0) - (sup_shift - supm.depth)
            if psi > 0:
                sup_shift += psi
                sub_shift -= psi

        vlist_elem = [
            {"type": "elem", "elem": subm, "shift": sub_shift,
             "marginRight": margin_right, "marginLeft": margin_left},
            {"type": "elem", "elem": supm, "shift": -sup_shift,
             "marginRight": margin_right},
        ]

        supsub = make_v_list({
            "positionType": "individualShift",
            "children": vlist_elem,
        }, options)

    elif subm:
        # Subscript only - Rule 18b
        sub_shift = max(sub_shift, metrics.get("sub1", 0),
                       subm.height - 0.8 * metrics.get("xHeight", 0))

        vlist_elem = [{"type": "elem", "elem": subm,
                      "marginLeft": margin_left, "marginRight": margin_right}]

        supsub = make_v_list({
            "positionType": "shift",
            "positionData": sub_shift,
            "children": vlist_elem,
        }, options)

    elif supm:
        # Superscript only - Rule 18c, d
        sup_shift = max(sup_shift, min_sup_shift,
                       supm.depth + 0.25 * metrics.get("xHeight", 0))

        supsub = make_v_list({
            "positionType": "shift",
            "positionData": -sup_shift,
            "children": [{"type": "elem", "elem": supm, "marginRight": margin_right}],
        }, options)
    else:
        raise ValueError("supsub must have either sup or sub.")

    # Wrap in span.msupsub to reset text-align
    mclass = html.get_type_of_dom_tree(base, "right") or "mord"
    return make_span([mclass],
                    [base, make_span(["msupsub"], [supsub])],
                    options)


def mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for superscript/subscript group."""
    from .. import build_mathml as mml

    supsub_group = cast("SupsubParseNode", group)
    # Check for horizontal brace
    is_brace = False
    is_over = None
    is_sup = None

    if supsub_group.get("base") and supsub_group["base"].get("type") == "horizBrace":
        is_sup = bool(supsub_group.get("sup"))
        if is_sup == supsub_group["base"].get("isOver"):
            is_brace = True
            is_over = supsub_group["base"]["isOver"]

    # Mark parent relationship
    if supsub_group.get("base") and supsub_group["base"].get("type") in ("op", "operatorname"):
        supsub_group["base"]["parentIsSupSub"] = True

    children = [mml.build_group(supsub_group["base"], options)]

    if supsub_group.get("sub"):
        children.append(mml.build_group(supsub_group["sub"], options))

    if supsub_group.get("sup"):
        children.append(mml.build_group(supsub_group["sup"], options))

    # Determine MathML node type
    if is_brace:
        node_type = "mover" if is_over else "munder"
    elif not supsub_group.get("sub"):
        base = supsub_group.get("base")
        if (base and base.get("type") == "op" and base.get("limits") and
            (options.style == Style.DISPLAY or base.get("alwaysHandleSupSub"))):
            node_type = "mover"
        elif (base and base.get("type") == "operatorname" and
              base.get("alwaysHandleSupSub") and
              (base.get("limits") or options.style == Style.DISPLAY)):
            node_type = "mover"
        else:
            node_type = "msup"
    elif not supsub_group.get("sup"):
        base = supsub_group.get("base")
        if (base and base.get("type") == "op" and base.get("limits") and
            (options.style == Style.DISPLAY or base.get("alwaysHandleSupSub"))):
            node_type = "munder"
        elif (base and base.get("type") == "operatorname" and
              base.get("alwaysHandleSupSub") and
              (base.get("limits") or options.style == Style.DISPLAY)):
            node_type = "munder"
        else:
            node_type = "msub"
    else:
        base = supsub_group.get("base")
        if (base and base.get("type") == "op" and base.get("limits") and
            options.style == Style.DISPLAY):
            node_type = "munderover"
        elif (base and base.get("type") == "operatorname" and
              base.get("alwaysHandleSupSub") and
              (options.style == Style.DISPLAY or base.get("limits"))):
            node_type = "munderover"
        else:
            node_type = "msubsup"

    return MathNode(node_type, children)


# Register the builders

define_function_builders({
    "type": "supsub",
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})
