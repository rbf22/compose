"""Python port of KaTeX's functions/environment.js - environment commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..define_function import define_function
from ..parse_error import ParseError
from ..parse_node import assert_node_type

if TYPE_CHECKING:
    from ..parse_node import ParseNode


# Import environments registry
try:
    from ..environments import environments
except ImportError:
    environments = {}


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


def _environment_handler(context, args) -> ParseNode:
    """Handler for \begin and \end commands."""
    name_group = args[0]
    if name_group.get("type") != "ordgroup":
        raise ParseError("Invalid environment name", name_group)

    env_name = ""
    for node in name_group["body"]:
        env_name += assert_node_type(node, "textord")["text"]

    if context["funcName"] == "\\begin":
        # Validate environment exists
        if env_name not in environments:
            raise ParseError(f"No such environment: {env_name}", name_group)

        # Get environment definition
        env = environments[env_name]

        # Parse arguments
        args_result, opt_args = context["parser"].parse_arguments(f"\\begin{{{env_name}}}", env)

        # Create context for handler
        env_context = {
            "mode": context["parser"].mode,
            "envName": env_name,
            "parser": context["parser"],
        }

        # Call environment handler
        result = env["handler"](env_context, args_result, opt_args)

        # Expect \end
        context["parser"].expect("\\end", False)
        end_name_token = context["parser"].next_token
        end = assert_node_type(context["parser"].parse_function(), "environment")

        if end["name"] != env_name:
            raise ParseError(
                f"Mismatch: \\begin{{{env_name}}} matched by \\end{{{end['name']}}}",
                end_name_token
            )

        return result

    else:  # \end
        return {
            "type": "environment",
            "mode": context["parser"].mode,
            "name": env_name,
            "nameGroup": name_group,
        }
