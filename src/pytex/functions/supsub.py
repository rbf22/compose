"""Python port of KaTeX's functions/supsub.js - superscript/subscript handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..build_common import make_span, make_v_list
from ..define_function import define_function_builders
from ..dom_tree import SymbolNode
from ..mathml_tree import MathNode
from ..style import Style
from ..tree import VirtualNode
from ..units import make_em
from ..utils import is_character_box

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import OperatornameParseNode, OpParseNode, ParseNode, SupsubParseNode


def _is_character_box_node(node: Any | None) -> bool:
    return isinstance(node, dict) and is_character_box(node)


def html_builder_delegate(group: ParseNode, options: Options) -> Any:
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
        return _is_character_box_node(base.get("base"))  # Would return accent.html_builder
    elif base.get("type") == "horizBrace":
        is_sup = not supsub_group.get("sub")
        return is_sup == base.get("isOver")  # Would return horizBrace.html_builder
    else:
        return None


def html_builder(group: ParseNode, options: Options) -> Any:
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
    sup_shift = 0.0
    sub_shift = 0.0

    is_character_box_base = _is_character_box_node(value_base)

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
        base_node = supsub_group.get("base")
        is_oiint = (
            isinstance(base_node, dict)
            and base_node.get("type") == "op"
            and bool(base_node.get("name"))
            and base_node.get("name") in ("\\oiint", "\\oiiint")
        )
        italic_corr = 0.0
        if isinstance(base, SymbolNode):
            italic_corr = base.italic
        elif is_oiint:
            # Integral-with-circle symbols get a small italic correction in KaTeX;
            # we approximate with zero here for layout simplicity.
            italic_corr = 0.0
        if italic_corr:
            margin_left = make_em(-italic_corr)

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


def mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for superscript/subscript group."""
    from .. import build_mathml as mml

    supsub_group = cast("SupsubParseNode", group)
    # Check for horizontal brace
    is_brace = False
    is_over = None
    is_sup = None

    base_node = supsub_group.get("base")
    base_dict = cast(dict | None, base_node) if isinstance(base_node, dict) else None

    if base_dict and base_dict.get("type") == "horizBrace":
        is_sup = bool(supsub_group.get("sup"))
        if is_sup == base_dict.get("isOver"):
            is_brace = True
            is_over = base_dict.get("isOver")

    # Mark parent relationship
    if base_dict and base_dict.get("type") == "op":
        base_op = cast("OpParseNode", base_dict)
        base_op["parentIsSupSub"] = True
    elif base_dict and base_dict.get("type") == "operatorname":
        op_name_node = cast("OperatornameParseNode", base_dict)
        op_name_node["parentIsSupSub"] = True

    children: list[VirtualNode] = []
    if base_node is not None:
        children.append(mml.build_group(base_node, options))

    sub_node = supsub_group.get("sub")
    if sub_node is not None:
        children.append(mml.build_group(sub_node, options))

    sup_node = supsub_group.get("sup")
    if sup_node is not None:
        children.append(mml.build_group(sup_node, options))

    # Determine MathML node type
    if is_brace:
        node_type = "mover" if is_over else "munder"
    elif sup_node is None:
        base = base_dict
        if (base and base.get("type") == "op" and base.get("limits") and
            (options.style == Style.DISPLAY or base.get("alwaysHandleSupSub"))) or (base and base.get("type") == "operatorname" and
              base.get("alwaysHandleSupSub") and
              (base.get("limits") or options.style == Style.DISPLAY)):
            node_type = "munder"
        else:
            node_type = "msub"
    elif sub_node is None:
        base = base_dict
        if (base and base.get("type") == "op" and base.get("limits") and
            (options.style == Style.DISPLAY or base.get("alwaysHandleSupSub"))) or (base and base.get("type") == "operatorname" and
              base.get("alwaysHandleSupSub") and
              (base.get("limits") or options.style == Style.DISPLAY)):
            node_type = "mover"
        else:
            node_type = "msup"
    else:
        base = base_dict
        if (base and base.get("type") == "op" and base.get("limits") and
            options.style == Style.DISPLAY) or (base and base.get("type") == "operatorname" and
              base.get("alwaysHandleSupSub") and
              (base.get("limits") or options.style == Style.DISPLAY)):
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
