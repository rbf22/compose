"""Python port of KaTeX's functions/ordgroup.js - ordinary group handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..build_common import make_fragment, make_span
from ..define_function import define_function_builders

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import OrdgroupParseNode, ParseNode


# Ordinary group builders
define_function_builders({
    "type": "ordgroup",
    "html_builder": lambda group, options: _ordgroup_html_builder(group, options),
    "mathml_builder": lambda group, options: _ordgroup_mathml_builder(group, options),
})


def _ordgroup_html_builder(group: ParseNode, options: Options) -> Any:
    """Build HTML for ordgroup."""
    from .. import build_html as html

    ordgroup = cast("OrdgroupParseNode", group)
    if ordgroup.get("semisimple"):
        return make_fragment(html.build_expression(ordgroup["body"], options, False))
    else:
        return make_span(["mord"],
                        html.build_expression(ordgroup["body"], options, True),
                        options)


def _ordgroup_mathml_builder(group: ParseNode, options: Options) -> Any:
    """Build MathML for ordgroup."""
    from .. import build_mathml as mml

    ordgroup = cast("OrdgroupParseNode", group)
    return mml.build_expression_row(ordgroup["body"], options, True)
