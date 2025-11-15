"""Python port of KaTeX's functions/utils/assembleSupSub.js - superscript/subscript assembly utility."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ...build_common import make_v_list
from ...utils import is_character_box
from ...units import make_em

if TYPE_CHECKING:
    from ...options import Options
    from ...style import StyleInterface
    from ...parse_node import AnyParseNode
    from ...dom_tree import DomSpan, SymbolNode


def assembleSupSub(
    base: DomSpan | SymbolNode,
    sup_group: Optional[AnyParseNode],
    sub_group: Optional[AnyParseNode],
    options: Options,
    style: StyleInterface,
    slant: float,
    base_shift: float,
) -> DomSpan:
    """Assemble base, superscript, and subscript into a span for operators with limits."""
    from ...build_common import make_span as make_span_common
    from ... import build_html as html

    base = make_span_common([], [base])
    sub_is_single_character = sub_group and is_character_box(sub_group)

    sup = None
    sub = None

    # Build superscript if present
    if sup_group:
        elem = html.build_group(
            sup_group, options.having_style(style.sup()), options
        )

        sup = {
            "elem": elem,
            "kern": max(
                options.font_metrics().get("bigOpSpacing1", 0),
                options.font_metrics().get("bigOpSpacing3", 0) - elem.depth
            ),
        }

    # Build subscript if present
    if sub_group:
        elem = html.build_group(
            sub_group, options.having_style(style.sub()), options
        )

        sub = {
            "elem": elem,
            "kern": max(
                options.font_metrics().get("bigOpSpacing2", 0),
                options.font_metrics().get("bigOpSpacing4", 0) - elem.height
            ),
        }

    # Build the final group as a vlist
    if sup and sub:
        # Both superscript and subscript
        bottom = (options.font_metrics().get("bigOpSpacing5", 0) +
                 sub["elem"].height + sub["elem"].depth +
                 sub["kern"] +
                 base.depth + base_shift)

        final_group = make_v_list({
            "positionType": "bottom",
            "positionData": bottom,
            "children": [
                {"type": "kern", "size": options.font_metrics().get("bigOpSpacing5", 0)},
                {"type": "elem", "elem": sub["elem"], "marginLeft": make_em(-slant)},
                {"type": "kern", "size": sub["kern"]},
                {"type": "elem", "elem": base},
                {"type": "kern", "size": sup["kern"]},
                {"type": "elem", "elem": sup["elem"], "marginLeft": make_em(slant)},
                {"type": "kern", "size": options.font_metrics().get("bigOpSpacing5", 0)},
            ],
        }, options)

    elif sub:
        # Only subscript
        top = base.height - base_shift

        final_group = make_v_list({
            "positionType": "top",
            "positionData": top,
            "children": [
                {"type": "kern", "size": options.font_metrics().get("bigOpSpacing5", 0)},
                {"type": "elem", "elem": sub["elem"], "marginLeft": make_em(-slant)},
                {"type": "kern", "size": sub["kern"]},
                {"type": "elem", "elem": base},
            ],
        }, options)

    elif sup:
        # Only superscript
        bottom = base.depth + base_shift

        final_group = make_v_list({
            "positionType": "bottom",
            "positionData": bottom,
            "children": [
                {"type": "elem", "elem": base},
                {"type": "kern", "size": sup["kern"]},
                {"type": "elem", "elem": sup["elem"], "marginLeft": make_em(slant)},
                {"type": "kern", "size": options.font_metrics().get("bigOpSpacing5", 0)},
            ],
        }, options)

    else:
        # This case shouldn't occur - no superscript or subscript
        return base

    parts = [final_group]

    # Add spacer if needed to avoid overlap
    if sub and slant != 0 and not sub_is_single_character:
        spacer = make_span_common(["mspace"], [], options)
        spacer.style["marginRight"] = make_em(slant)
        parts.insert(0, spacer)

    return make_span_common(["mop", "op-limits"], parts, options)


# Export the function
__all__ = ["assembleSupSub"]
