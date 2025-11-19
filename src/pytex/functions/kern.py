"""Python port of KaTeX's functions/kern.js - horizontal spacing commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..build_common import make_glue
from ..define_function import define_function
from ..mathml_tree import MathNode, TextNode
from ..parse_node import assert_node_type
from ..units import Measurement, calculate_size, make_em

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import KernParseNode, ParseNode, SizeParseNode


# Define kern/spacing commands
define_function({
    "type": "kern",
    "names": ["\\kern", "\\mkern", "\\hskip", "\\mskip"],
    "props": {
        "numArgs": 1,
        "argTypes": ["size"],
        "primitive": True,
        "allowedInText": True,
    },
    "handler": lambda context, args, opt_args: _kern_handler(context, args),
    "html_builder": lambda group, options: _kern_html_builder(group, options),
    "mathml_builder": lambda group, options: _kern_mathml_builder(group, options),
})


def _kern_handler(context: dict[str, Any], args: list[SizeParseNode]) -> KernParseNode:
    """Handler for kern/spacing commands."""
    size_node = cast("SizeParseNode", assert_node_type(args[0], "size"))
    dimension: Measurement = size_node["value"]

    func_name = context["funcName"]
    parser = context["parser"]

    # Strict mode validation
    if parser.settings.strict:
        math_function = func_name[1] == 'm'  # \mkern, \mskip
        mu_unit = dimension["unit"] == 'mu'

        if math_function:
            if not mu_unit:
                parser.settings.report_nonstrict(
                    "mathVsTextUnits",
                    f"LaTeX's {func_name} supports only mu units, not {dimension['unit']} units"
                )
            if parser.mode != "math":
                parser.settings.report_nonstrict(
                    "mathVsTextUnits",
                    f"LaTeX's {func_name} works only in math mode"
                )
        else:  # not math function
            if mu_unit:
                parser.settings.report_nonstrict(
                    "mathVsTextUnits",
                    f"LaTeX's {func_name} doesn't support mu units"
                )

    return {
        "type": "kern",
        "mode": parser.mode,
        "loc": None,
        "dimension": dimension,
    }


def _kern_html_builder(group: ParseNode, options: Options) -> Any:
    kern_group = cast("KernParseNode", group)
    dimension: Measurement = kern_group["dimension"]
    # dimension is already a Measurement
    return make_glue(dimension, options)


def _kern_mathml_builder(group: ParseNode, options: Options) -> MathNode:
    kern_group = cast("KernParseNode", group)
    dimension: Measurement = kern_group["dimension"]
    size = calculate_size(dimension, options)

    # Match KaTeX's MathML encoding for kerns:
    # - Very thin spaces (~1mu) → U+200A hair space in <mtext>.
    # - Thin spaces (~3mu)     → U+2009 thin space in <mtext>.
    # - Other kerns            → <mspace width="..."/>.

    if 0.05555 <= size <= 0.05556:
        return MathNode("mtext", [TextNode("\u200a")])
    if 0.1666 <= size <= 0.1667:
        return MathNode("mtext", [TextNode("\u2009")])

    node = MathNode("mspace")
    node.set_attribute("width", make_em(size))
    return node
