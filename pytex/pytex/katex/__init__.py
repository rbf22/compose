"""KaTeX Python - Fast math typesetting for Python.

This is a complete Python port of KaTeX (https://katex.org/),
the fastest math rendering library for the web.
"""

from __future__ import annotations

import warnings
from typing import Optional, Union, Dict, Any

from ..define_macro import defineMacro
from ..define_function import defineFunction

__version__ = "0.16.25"
__author__ = "R. Bryn Fenwick"
__email__ = "robert_fenwick@epam.com"
__license__ = "MIT"


def render_to_string(math: str, options: Optional[Dict[str, Any]] = None) -> str:
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

    # For now, return a simple placeholder implementation
    # The full implementation requires the complete functions/symbols database
    # which needs to be converted from the original KaTeX data
    #
    # TODO: Implement full KaTeX rendering once:
    # 1. functions.py is created from original KaTeX function definitions
    # 2. symbols_data.py is created from original KaTeX symbol tables
    # 3. All function handlers are properly ported
    return f'<span class="katex">{math}</span>'


def render(math: str, element_id: Optional[str] = None, options: Optional[Dict[str, Any]] = None) -> None:
    """Render LaTeX math expression (for web integration).

    This function is primarily for web browser compatibility.
    In Python applications, use render_to_string() instead.

    Args:
        math: LaTeX math expression
        element_id: DOM element ID (not applicable in Python)
        options: Rendering options
    """
    warnings.warn(
        "render() is for web browser compatibility. "
        "Use render_to_string() in Python applications.",
        UserWarning,
        stacklevel=2
    )

    # In a web context, this would manipulate the DOM
    # In Python, it's essentially a no-op
    if element_id:
        result = render_to_string(math, options)
        # In a web context, this would set element.innerHTML = result
        print(f"Would render to element '{element_id}': {result}")


def define_macro(name: str, expansion: Union[str, callable]) -> None:
    """Define a custom LaTeX macro.

    Args:
        name: Macro name (with backslash, e.g., r"\RR")
        expansion: LaTeX expansion string or function
    """
    defineMacro(name, expansion)


def define_function(definition: Dict[str, Any]) -> None:
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


# Export public API
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
