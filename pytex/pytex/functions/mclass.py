"""Python port of KaTeX's functions/mclass.js - math class handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from ..build_common import make_span
from ..define_function import define_function, ordargument
from ..mathml_tree import MathNode
from ..utils import is_character_box

if TYPE_CHECKING:
    from ..options import Options
    from ..parse_node import AnyParseNode, MclassParseNode, ParseNode


def html_builder(group: ParseNode, options: "Options") -> Any:
    """Build HTML for math class groups."""
    from .. import build_html as html

    mclass_group = cast("MclassParseNode", group)
    elements = html.build_expression(mclass_group["body"], options, True)
    return make_span([mclass_group["mclass"]], elements, options)


def mathml_builder(group: ParseNode, options: "Options") -> MathNode:
    """Build MathML for math class groups."""
    from .. import build_mathml as mml

    mclass_group = cast("MclassParseNode", group)
    inner = mml.build_expression(mclass_group["body"], options)

    if mclass_group["mclass"] == "minner":
        node = MathNode("mpadded", inner)
    elif mclass_group["mclass"] == "mord":
        if mclass_group.get("isCharacterBox"):
            node = inner[0]
            node.type = "mi"
        else:
            node = MathNode("mi", inner)
    else:
        # mbin, mrel, mopen, mclose, mpunct
        if mclass_group.get("isCharacterBox"):
            node = inner[0]
            node.type = "mo"
        else:
            node = MathNode("mo", inner)

        # Set spacing attributes based on math class
        if mclass_group["mclass"] == "mbin":
            node.set_attribute("lspace", "0.22em")  # medium space
            node.set_attribute("rspace", "0.22em")
        elif mclass_group["mclass"] == "mpunct":
            node.set_attribute("lspace", "0em")
            node.set_attribute("rspace", "0.17em")  # thinspace
        elif mclass_group["mclass"] in ("mopen", "mclose"):
            node.set_attribute("lspace", "0em")
            node.set_attribute("rspace", "0em")
        elif mclass_group["mclass"] == "minner":
            node.set_attribute("lspace", "0.0556em")  # 1 mu
            node.set_attribute("width", "+0.1111em")

    return node


def binrel_class(arg: AnyParseNode) -> str:
    """Determine math class for binrel operations."""
    # Get the atom from ordgroup or directly
    atom = arg["body"][0] if (arg.get("type") == "ordgroup" and arg.get("body")) else arg

    if (atom.get("type") == "atom" and
        atom.get("family") in ("bin", "rel")):
        return f"m{atom['family']}"
    else:
        return "mord"


# Math class commands
define_function({
    "type": "mclass",
    "names": [
        "\\mathord", "\\mathbin", "\\mathrel", "\\mathopen",
        "\\mathclose", "\\mathpunct", "\\mathinner",
    ],
    "props": {
        "numArgs": 1,
        "primitive": True,
    },
    "handler": lambda context, args: {
        "type": "mclass",
        "mode": context["parser"].mode,
        "mclass": f"m{context['funcName'][5:]}",  # Remove "\math" prefix
        "body": ordargument(args[0]),
        "isCharacterBox": is_character_box(args[0]),
    },
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# \@binrel command
define_function({
    "type": "mclass",
    "names": ["\\@binrel"],
    "props": {
        "numArgs": 2,
    },
    "handler": lambda context, args: {
        "type": "mclass",
        "mode": context["parser"].mode,
        "mclass": binrel_class(args[0]),
        "body": ordargument(args[1]),
        "isCharacterBox": is_character_box(args[1]),
    },
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})

# Stacked operators: \stackrel, \overset, \underset
define_function({
    "type": "mclass",
    "names": ["\\stackrel", "\\overset", "\\underset"],
    "props": {
        "numArgs": 2,
    },
    "handler": lambda context, args: _stacked_handler(context, args),
    "html_builder": html_builder,
    "mathml_builder": mathml_builder,
})


def _stacked_handler(context, args):
    """Handler for stacked operators like \\stackrel, \\overset, \\underset."""
    base_arg = args[1]
    shifted_arg = args[0]
    func_name = context["funcName"]

    # Determine math class
    if func_name != "\\stackrel":
        # LaTeX applies \binrel spacing to \overset and \underset
        mclass = binrel_class(base_arg)
    else:
        mclass = "mrel"  # for \stackrel

    # Create base operator
    base_op = {
        "type": "op",
        "mode": base_arg.get("mode", context["parser"].mode),
        "limits": True,
        "alwaysHandleSupSub": True,
        "parentIsSupSub": False,
        "symbol": False,
        "suppressBaseShift": func_name != "\\stackrel",
        "body": ordargument(base_arg),
    }

    # Create supsub structure
    supsub = {
        "type": "supsub",
        "mode": shifted_arg.get("mode", context["parser"].mode),
        "base": base_op,
        "sup": None if func_name == "\\underset" else shifted_arg,
        "sub": shifted_arg if func_name == "\\underset" else None,
    }

    return {
        "type": "mclass",
        "mode": context["parser"].mode,
        "mclass": mclass,
        "body": [supsub],
        "isCharacterBox": is_character_box(supsub),
    }


# Export binrel_class for use by other modules
__all__ = ["binrel_class"]
