"""Python port of KaTeX's functions/def.js - macro definition and assignment."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, cast

from ..define_function import define_function
from ..parse_error import ParseError
from ..parse_node import assert_node_type

if TYPE_CHECKING:
    pass

# Global map for prefix handling
GLOBAL_MAP = {
    "\\global": "\\global",
    "\\long": "\\\\globallong",
    "\\\\globallong": "\\\\globallong",
    "\\def": "\\gdef",
    "\\gdef": "\\gdef",
    "\\edef": "\\xdef",
    "\\xdef": "\\xdef",
    "\\let": "\\\\globallet",
    "\\futurelet": "\\\\globalfuture",
}


def check_control_sequence(tok: Dict[str, Any]) -> str:
    """Validate control sequence token."""
    name = str(tok["text"])
    if name in ["\\", "{", "}", "$", "&", "#", "^", "_", "EOF"]:
        raise ParseError("Expected a control sequence", tok)
    return name


def get_rhs(parser: Any) -> Dict[str, Any]:
    """Get right-hand side token, consuming optional equals and space."""
    tok = parser.gullet.pop_token()
    if tok["text"] == "=":
        tok = parser.gullet.pop_token()
        if tok["text"] == " ":
            tok = parser.gullet.pop_token()
    return cast(Dict[str, Any], tok)


def let_command(parser: Any, name: str, tok: Dict[str, Any], global_flag: bool) -> None:
    r"""Execute \let command."""
    macro = parser.gullet.macros.get(tok["text"])
    if macro is None:
        # Don't expand it later
        tok["noexpand"] = True
        macro = {
            "tokens": [tok],
            "numArgs": 0,
            "unexpandable": not parser.gullet.is_expandable(tok["text"]),
        }
    parser.gullet.macros.set(name, macro, global_flag)


# Global/long prefixes
define_function({
    "type": "internal",
    "names": ["\\global", "\\long", "\\\\globallong"],
    "props": {
        "numArgs": 0,
        "allowedInText": True,
    },
    "handler": lambda context, args, opt_args: _prefix_handler(context),
})

# Macro definitions
define_function({
    "type": "internal",
    "names": ["\\def", "\\gdef", "\\edef", "\\xdef"],
    "props": {
        "numArgs": 0,
        "allowedInText": True,
        "primitive": True,
    },
    "handler": lambda context, args, opt_args: _def_handler(context),
})

# Let assignments
define_function({
    "type": "internal",
    "names": ["\\let", "\\\\globallet"],
    "props": {
        "numArgs": 0,
        "allowedInText": True,
        "primitive": True,
    },
    "handler": lambda context, args, opt_args: _let_handler(context),
})

# Futurelet assignments
define_function({
    "type": "internal",
    "names": ["\\futurelet", "\\\\globalfuture"],
    "props": {
        "numArgs": 0,
        "allowedInText": True,
        "primitive": True,
    },
    "handler": lambda context, args, opt_args: _futurelet_handler(context),
})


def _prefix_handler(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handler for global/long prefixes."""
    parser = context["parser"]
    func_name = context["funcName"]

    parser.consume_spaces()
    token = parser.fetch()

    if token["text"] in GLOBAL_MAP:
        # KaTeX doesn't have \par, so ignore \long
        if func_name in ["\\global", "\\\\globallong"]:
            token["text"] = GLOBAL_MAP[token["text"]]
        node = assert_node_type(parser.parse_function(), "internal")
        return cast(Dict[str, Any], node)

    raise ParseError("Invalid token after macro prefix", token)


def _def_handler(context: Dict[str, Any]) -> Dict[str, Any]:
    r"""Handler for macro definitions (\def, \gdef, \edef, \xdef)."""
    parser = context["parser"]
    func_name = context["funcName"]

    tok = parser.gullet.pop_token()
    name = tok["text"]

    if name in ["\\", "{", "}", "$", "&", "#", "^", "_", "EOF"]:
        raise ParseError("Expected a control sequence", tok)

    num_args = 0
    insert = None
    delimiters: List[List[str]] = [[]]

    # Parse parameter text
    while parser.gullet.future()["text"] != "{":
        tok = parser.gullet.pop_token()

        if tok["text"] == "#":
            if parser.gullet.future()["text"] == "{":
                insert = parser.gullet.future()
                delimiters[num_args].append("{")
                break

            # Parameter specification
            tok = parser.gullet.pop_token()
            if not tok["text"].isdigit() or not (1 <= int(tok["text"]) <= 9):
                raise ParseError(f'Invalid argument number "{tok["text"]}"')

            if int(tok["text"]) != num_args + 1:
                raise ParseError(f'Argument number "{tok["text"]}" out of order')

            num_args += 1
            delimiters.append([])

        elif tok["text"] == "EOF":
            raise ParseError("Expected a macro definition")
        else:
            delimiters[num_args].append(tok["text"])

    # Parse replacement text
    result = parser.gullet.consume_arg()
    tokens = result["tokens"]

    if insert:
        tokens.insert(0, insert)

    # Expand if needed (\edef, \xdef)
    if func_name in ["\\edef", "\\xdef"]:
        tokens = parser.gullet.expand_tokens(tokens)
        tokens.reverse()  # Match stack order

    # Register the macro
    parser.gullet.macros.set(name, {
        "tokens": tokens,
        "numArgs": num_args,
        "delimiters": delimiters,
    }, func_name == GLOBAL_MAP[func_name])

    return {
        "type": "internal",
        "mode": parser.mode,
    }


def _let_handler(context: Dict[str, Any]) -> Dict[str, Any]:
    r"""Handler for \let assignments."""
    parser = context["parser"]
    func_name = context["funcName"]

    name = check_control_sequence(parser.gullet.pop_token())
    parser.gullet.consume_spaces()
    tok = get_rhs(parser)

    let_command(parser, name, tok, func_name == "\\\\globallet")

    return {
        "type": "internal",
        "mode": parser.mode,
    }


def _futurelet_handler(context: Dict[str, Any]) -> Dict[str, Any]:
    r"""Handler for \futurelet assignments."""
    parser = context["parser"]
    func_name = context["funcName"]

    name = check_control_sequence(parser.gullet.pop_token())
    middle = parser.gullet.pop_token()
    tok = parser.gullet.pop_token()

    let_command(parser, name, tok, func_name == "\\\\globalfuture")

    # Push tokens back in reverse order
    parser.gullet.push_token(tok)
    parser.gullet.push_token(middle)

    return {
        "type": "internal",
        "mode": parser.mode,
    }
