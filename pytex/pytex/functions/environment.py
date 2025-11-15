r"""Python port of KaTeX's functions/environment.js - environment commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Dict, List, Sequence, cast

from ..define_environment import ENVIRONMENTS, EnvSpec
from ..define_function import define_function
from ..parse_error import ParseError
from ..parse_node import AnyParseNode, assert_node_type

if TYPE_CHECKING:
    from ..parser import Parser


EnvHandler = Callable[[Dict[str, Any], Sequence[AnyParseNode], Sequence[Any]], AnyParseNode]


# Define \begin and \end commands
define_function({
    "type": "environment",
    "names": ["\\begin", "\\end"],
    "props": {
        "numArgs": 1,
        "argTypes": ["text"],
    },
    "handler": lambda context, args: _environment_handler(context, args),
})


r"""Handler implementations for \begin and \end."""


def _environment_handler(context: Dict[str, Any], args: List[AnyParseNode]) -> AnyParseNode:
    parser: Parser = context["parser"]
    name_group = assert_node_type(args[0], "ordgroup")
    body_nodes = cast(List[AnyParseNode], name_group.get("body", []))
    env_name_parts: List[str] = []
    for node in body_nodes:
        text_node = assert_node_type(node, "textord")
        env_name_parts.append(str(text_node.get("text", "")))
    env_name = "".join(env_name_parts)

    if context["funcName"] == "\\begin":
        # Validate environment exists
        if env_name not in ENVIRONMENTS:
            raise ParseError(f"No such environment: {env_name}", parser.next_token)

        # Get environment definition
        env = ENVIRONMENTS[env_name]

        # Parse arguments
        args_result, opt_args = parser.parse_arguments(
            f"\\begin{{{env_name}}}", _env_spec_to_dict(env)
        )

        # Create context for handler
        env_context = {
            "mode": parser.mode,
            "envName": env_name,
            "parser": parser,
        }

        # Call environment handler
        handler = cast(EnvHandler, env.handler)
        result = handler(env_context, args_result, opt_args)

        # Expect \end
        parser.expect("\\end", False)
        end_name_token = parser.next_token
        end = assert_node_type(parser.parse_function(), "environment")
        end_dict = cast(Dict[str, Any], end)

        if end_dict.get("name") != env_name:
            raise ParseError(
                f"Mismatch: \\begin{{{env_name}}} matched by \\end{{{end_dict.get('name')}}}",
                end_name_token
            )

        return result

    else:  # \end
        return cast(AnyParseNode, {
            "type": "environment",
            "mode": parser.mode,
            "name": env_name,
            "nameGroup": name_group,
        })


def _env_spec_to_dict(env: EnvSpec) -> Dict[str, Any]:
    return {
        "numArgs": env.num_args,
        "allowedInText": env.allowed_in_text,
        "numOptionalArgs": env.num_optional_args,
        "handler": env.handler,
    }
