"""Public API implementation for pytex.katex.

This module contains the real implementation of the KaTeX-style
Python API (render_to_string, render, define_macro, define_function).
The package-level __init__.py simply re-exports these symbols so that
`import pytex.katex as katex` continues to work as expected.
"""

from __future__ import annotations

import importlib
import warnings
from collections.abc import Callable
from typing import Any

from ..build_tree import build_tree
from ..define_function import defineFunction
from ..define_macro import defineMacro
from ..font_metrics import load_metrics
from ..font_metrics_data import FONT_METRICS_DATA
from ..parse_tree import parse_tree
from ..settings import Settings

__version__ = "0.16.25"
__author__ = "R. Bryn Fenwick"
__email__ = "robert_fenwick@epam.com"
__license__ = "MIT"


_INITIALIZED = False

# Mapping from user-facing snake_case option names to internal Settings keys.
_PUBLIC_TO_INTERNAL_OPTIONS: dict[str, str] = {
    "display_mode": "display_mode",
    "output": "output",
    "leqno": "leqno",
    "fleqn": "fleqn",
    "throw_on_error": "throw_on_error",
    "error_color": "error_color",
    "macros": "macros",
    "min_rule_thickness": "min_rule_thickness",
    "color_is_text_color": "color_is_text_color",
    "strict": "strict",
    "trust": "trust",
    "max_size": "max_size",
    "max_expand": "max_expand",
    "global_group": "global_group",
}


def _normalize_options(options: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Normalize public API options into Settings-compatible keys."""

    merged: dict[str, Any] = {}
    if options:
        merged.update(options)
    if kwargs:
        merged.update(kwargs)

    normalized: dict[str, Any] = {}
    for key, value in merged.items():
        internal_key = _PUBLIC_TO_INTERNAL_OPTIONS.get(key, key)
        normalized[internal_key] = value
    return normalized


def _ensure_initialized() -> None:
    """Load font metrics and register functions/environments once."""

    global _INITIALIZED
    if _INITIALIZED:
        return

    # Load font metrics used by HTML/MathML builders.
    load_metrics(FONT_METRICS_DATA)

    # Import all function modules so they register with define_function.
    try:
        from ..functions import __all__ as _function_modules
    except Exception:
        _function_modules = ()
    for name in _function_modules:
        try:
            importlib.import_module(f"pytex.functions.{name}")
        except Exception:
            # Some modules may not be present or fully implemented yet.
            continue

    # Import environments so they register with define_environment.
    for env_mod in ("pytex.environments.array", "pytex.environments.cd"):
        try:
            importlib.import_module(env_mod)
        except Exception:
            continue

    _INITIALIZED = True


def render_to_string(
    math: str | None,
    options: dict[str, Any] | None = None,
    **kwargs: Any,
) -> str:
    """Render LaTeX math expression to HTML string.

    Args:
        math: LaTeX math expression string
        options: Rendering options dictionary

    Returns:
        HTML string with rendered math

    Raises:
        ParseError: If the LaTeX expression is invalid and throw_on_error is True
    """

    if options is None:
        options = {}
    if math is None:
        math = ""

    _ensure_initialized()

    settings_options = _normalize_options(options, **kwargs)
    settings = Settings(settings_options)

    # Parse the input into a parse tree, then build a DOM tree and serialize.
    tree = parse_tree(math, settings)
    dom_tree = build_tree(tree, math, settings)
    return dom_tree.to_markup()


def render(math: str, element_id: str | None = None, options: dict[str, Any] | None = None) -> None:
    """Render LaTeX math expression (for web integration).

    This function is primarily for web browser compatibility.
    In Python applications, use render_to_string() instead.
    """

    warnings.warn(
        "render() is for web browser compatibility. "
        "Use render_to_string() in Python applications.",
        UserWarning,
        stacklevel=2,
    )

    # In a web context, this would manipulate the DOM; in Python we simply
    # call render_to_string and print the result when an element_id is given.
    if element_id:
        result = render_to_string(math, options)
        print(f"Would render to element '{element_id}': {result}")


def define_macro(name: str, expansion: str | Callable) -> None:
    r"""Define a custom LaTeX macro.

    Args:
        name: Macro name (with backslash, e.g., r"\RR")
        expansion: LaTeX expansion string or function
    """

    defineMacro(name, expansion)


def define_function(definition: dict[str, Any]) -> None:
    """Define a custom LaTeX function.

    Args:
        definition: Function definition dictionary with keys:
            - type: Function type
            - names: List of function names
            - props: Function properties
            - handler: Handler function
            - html_builder: HTML builder function (optional)
            - mathml_builder: MathML builder function (optional)
    """

    defineFunction(definition)


__all__ = [
    "render_to_string",
    "render",
    "define_macro",
    "define_function",
    "__version__",
    "__author__",
    "__email__",
    "__license__",
]
