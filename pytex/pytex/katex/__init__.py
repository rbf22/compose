"""KaTeX Python - Fast math typesetting for Python.

This package exposes a KaTeX-compatible public API via ``pytex.katex``.
The actual implementation lives in :mod:`pytex.katex.api`; this
``__init__`` file is a thin wrapper that re-exports the public symbols so
``import pytex.katex as katex`` continues to work as expected.
"""

from __future__ import annotations

from .api import (
    __author__,
    __email__,
    __license__,
    __version__,
    define_function,
    define_macro,
    render,
    render_to_string,
)

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
