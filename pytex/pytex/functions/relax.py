"""Python port of KaTeX's functions/relax.js - relax command."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..define_function import define_function

if TYPE_CHECKING:
    pass


# \relax - TeX command that does nothing
define_function({
    "type": "internal",
    "names": ["\\relax"],
    "props": {
        "numArgs": 0,
        "allowedInText": True,
        "allowedInArgument": True,
    },
    "handler": lambda context, args, opt_args: {
        "type": "internal",
        "mode": context["parser"].mode,
    },
})
