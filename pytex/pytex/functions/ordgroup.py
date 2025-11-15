"""Python port of KaTeX's functions/ordgroup.js - ordinary group handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..build_common import make_fragment, make_span
from ..define_function import define_function_builders

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import ParseNode


# Ordinary group builders
define_function_builders({
    "type": "ordgroup",
    "html_builder": lambda group, options: _ordgroup_html_builder(group, options),
    "mathml_builder": lambda group, options: _ordgroup_mathml_builder(group, options),
})


def _ordgroup_html_builder(group: ParseNode, options: Options):
    """Build HTML for ordgroup."""
    from .. import build_html as html

    if group.get("semisimple"):
        return make_fragment(html.build_expression(group["body"], options, False))
    else:
        return make_span(["mord"],
                        html.build_expression(group["body"], options, True),
                        options)


def _ordgroup_mathml_builder(group: ParseNode, options: Options):
    """Build MathML for ordgroup."""
    from .. import build_mathml as mml

    return mml.build_expression_row(group["body"], options, True)
