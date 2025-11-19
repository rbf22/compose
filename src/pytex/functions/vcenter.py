"""Python port of KaTeX's functions/vcenter.js - vertical centering."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..build_common import make_v_list
from ..define_function import define_function
from ..mathml_tree import MathNode

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode, VcenterParseNode


# \vcenter - vertically center argument on math axis
define_function({
    "type": "vcenter",
    "names": ["\\vcenter"],
    "props": {
        "numArgs": 1,
        "argTypes": ["original"],  # In LaTeX, \vcenter acts only on a box
        "allowedInText": False,
    },
    "handler": lambda context, args, opt_args: {
        "type": "vcenter",
        "mode": context["parser"].mode,
        "body": args[0],
    },
    "html_builder": lambda group, options: _vcenter_html_builder(group, options),
    "mathml_builder": lambda group, options: _vcenter_mathml_builder(group, options),
})


def _vcenter_html_builder(group: ParseNode, options: Options) -> Any:
    """Build HTML for \vcenter command."""
    from .. import build_html as html

    vcenter_group = cast("VcenterParseNode", group)
    body = html.build_group(vcenter_group["body"], options)
    axis_height = options.font_metrics().get("axisHeight", 0.25)

    # Calculate vertical shift to center on math axis
    dy = 0.5 * ((body.height - axis_height) - (body.depth + axis_height))

    return make_v_list({
        "positionType": "shift",
        "positionData": dy,
        "children": [{"type": "elem", "elem": body}],
    }, options)


def _vcenter_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    """Build MathML for \vcenter command."""
    from .. import build_mathml as mml

    vcenter_group = cast("VcenterParseNode", group)
    # MathML doesn't have direct vertical centering
    # Add a class as breadcrumb for post-processors
    return MathNode(
        "mpadded", [mml.build_group(vcenter_group["body"], options)], ["vcenter"]
    )
