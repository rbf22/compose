"""Python utilities mirroring KaTeX's JavaScript helpers.

The original KaTeX implementation exposes a handful of utility helpers from
``src/utils.js``.  These functions are broadly useful across the renderer, so we
port them here with Pythonic signatures while keeping the same semantics.
"""

from __future__ import annotations

import html
import re
from typing import Any, Dict, Iterable, Optional

ParseNode = Dict[str, Any]


def default(value: Optional[Any], fallback: Any) -> Any:
    """Return *value* if it is not ``None``; otherwise return *fallback*.

    The JavaScript version returns the default when a value is strictly
    ``undefined``.  We interpret ``None`` as the same sentinel in Python.
    """

    return fallback if value is None else value


_UPPERCASE = re.compile(r"([A-Z])")


def hyphenate(identifier: str) -> str:
    """Convert *identifier* from camelCase/PascalCase to hyphen-case."""

    return _UPPERCASE.sub(lambda match: "-" + match.group(1).lower(), identifier)


def escape(text: Any) -> str:
    """HTML-escape *text* using ``html.escape``.

    The JavaScript helper coerces arbitrary input to string before escaping; we
    follow the same behaviour.
    """

    return html.escape(str(text), quote=True).replace("'", "&#x27;")


def _single_child(node: ParseNode) -> Optional[ParseNode]:
    body = node.get("body")
    if isinstance(body, Iterable) and not isinstance(body, (str, bytes)):
        children = list(body)
        if len(children) == 1 and isinstance(children[0], dict):
            return children[0]
    return None


def get_base_elem(node: ParseNode) -> ParseNode:
    """Peel away wrapper nodes that simply contain a single child.

    Mirrors ``getBaseElem``: it recursively unwraps ``ordgroup``, ``color``, and
    ``font`` nodes when they contain exactly one element.
    """

    current = node
    while True:
        node_type = current.get("type")
        if node_type in {"ordgroup", "color"}:
            child = _single_child(current)
            if child is None:
                return current
            current = child
            continue
        if node_type == "font":
            child = current.get("body")
            if isinstance(child, dict):
                current = child
                continue
        return current


def is_character_box(node: ParseNode) -> bool:
    """Return ``True`` when *node* ultimately contains a single character."""

    base = get_base_elem(node)
    return base.get("type") in {"mathord", "textord", "atom"}


def assert_non_null(value: Optional[Any]) -> Any:
    """Raise ``ValueError`` if *value* is falsy, mirroring JS ``assert``."""

    if not value:
        raise ValueError(f"Expected non-null value, received {value!r}")
    return value


_PROTOCOL_RE = re.compile(
    r"^[\x00-\x20]*([^/\?#]*?)(:|&#0*58|&#x0*3a|&colon)", re.IGNORECASE
)
_ALLOWED_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+\-.]*$")


def protocol_from_url(url: str) -> Optional[str]:
    """Return the URL scheme or ``"_relative"`` when none is present.

    ``None`` is returned if the URL encodes a colon using HTML entities or
    contains characters outside RFC 3986 scheme grammar.
    """

    match = _PROTOCOL_RE.search(url)
    if not match:
        return "_relative"

    literal_colon = match.group(2)
    if literal_colon != ":":
        return None

    scheme = match.group(1)
    if not _ALLOWED_SCHEME.fullmatch(scheme):
        return None

    return scheme.lower()


__all__ = [
    "default",
    "hyphenate",
    "escape",
    "get_base_elem",
    "is_character_box",
    "assert_non_null",
    "protocol_from_url",
]
