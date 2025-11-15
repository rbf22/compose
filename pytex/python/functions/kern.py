"""Python port of KaTeX's functions/kern.js - horizontal spacing commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..build_common import make_glue
from ..define_function import define_function
from ..mathml_tree import SpaceNode
from ..parse_node import assert_node_type
from ..units import calculate_size

if TYPE_CHECKING:
    from ..parse_node import ParseNode


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
    "handler": lambda context, args: _kern_handler(context, args),
    "html_builder": lambda group, options: make_glue(group["dimension"], options),
    "mathml_builder": lambda group, options: SpaceNode(calculate_size(group["dimension"], options)),
})


def _kern_handler(context, args) -> ParseNode:
    """Handler for kern/spacing commands."""
    size = assert_node_type(args[0], "size")

    func_name = context["funcName"]
    parser = context["parser"]

    # Strict mode validation
    if parser.settings.strict:
        math_function = func_name[1] == 'm'  # \mkern, \mskip
        mu_unit = size["value"]["unit"] == 'mu'

        if math_function:
            if not mu_unit:
                parser.settings.report_nonstrict(
                    "mathVsTextUnits",
                    f"LaTeX's {func_name} supports only mu units, not {size['value']['unit']} units"
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
        "dimension": size["value"],
    }
