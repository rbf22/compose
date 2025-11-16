"""Python representation of KaTeX's DOM tree helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .parse_error import ParseError
from .unicode_scripts import script_from_codepoint
from .utils import escape, hyphenate
from .units import make_em


def create_class(classes: Iterable[str]) -> str:
    return " ".join(cls for cls in classes if cls)


INVALID_ATTRIBUTE_NAME = re.compile(r"[\s\"'>/\x00-\x1f]")


@dataclass
class DomNode:
    classes: List[str] = field(default_factory=list)
    style: Dict[str, str] = field(default_factory=dict)
    attributes: Dict[str, str] = field(default_factory=dict)
    height: float = 0.0
    depth: float = 0.0
    width: float = 0.0
    max_font_size: float = 0.0

    def add_class(self, class_name: str) -> None:
        if class_name not in self.classes:
            self.classes.append(class_name)

    def has_class(self, class_name: str) -> bool:
        """Return True if the node has the given CSS class."""
        return class_name in self.classes

    def set_attribute(self, key: str, value: str) -> None:
        if INVALID_ATTRIBUTE_NAME.search(key):
            raise ParseError(f"Invalid attribute name '{key}'")
        self.attributes[key] = value

    # ------------------------------------------------------------------
    # Rendering helpers

    def _open_tag(self, tag: str) -> str:
        markup = [f"<{tag}"]
        if self.classes:
            markup.append(f" class=\"{escape(create_class(self.classes))}\"")
        if self.style:
            styles = "".join(f"{hyphenate(k)}:{v};" for k, v in self.style.items())
            if styles:
                markup.append(f" style=\"{escape(styles)}\"")
        for attr, value in self.attributes.items():
            markup.append(f" {attr}=\"{escape(value)}\"")
        markup.append(">")
        return "".join(markup)

    def _close_tag(self, tag: str) -> str:
        return f"</{tag}>"

    def to_markup(self) -> str:
        raise NotImplementedError


@dataclass
class Span(DomNode):
    children: List[DomNode] = field(default_factory=list)

    def to_markup(self) -> str:
        markup = [self._open_tag("span")]
        for child in self.children:
            markup.append(child.to_markup())
        markup.append(self._close_tag("span"))
        return "".join(markup)


# Compatibility alias matching KaTeX's DomSpan class name
DomSpan = Span

# Type alias used throughout HTML builders
HtmlDomNode = DomNode


@dataclass
class SvgSpan(Span):
    """Compatibility subclass used by KaTeX for SVG spans."""
    pass


@dataclass
class Anchor(DomNode):
    children: List[DomNode] = field(default_factory=list)

    def __post_init__(self) -> None:
        if "href" not in self.attributes:
            self.attributes["href"] = "#"

    def to_markup(self) -> str:
        markup = [self._open_tag("a")]
        for child in self.children:
            markup.append(child.to_markup())
        markup.append(self._close_tag("a"))
        return "".join(markup)


@dataclass
class Img(DomNode):
    src: str = ""
    alt: str = ""

    def to_markup(self) -> str:
        markup = ["<img"]
        markup.append(f" src=\"{escape(self.src)}\"")
        markup.append(f" alt=\"{escape(self.alt)}\"")
        if self.style:
            styles = "".join(f"{hyphenate(k)}:{v};" for k, v in self.style.items())
            markup.append(f" style=\"{escape(styles)}\"")
        markup.append("/>")
        return "".join(markup)


@dataclass
class SymbolNode(DomNode):
    text: str = ""
    italic: float = 0.0
    skew: float = 0.0
    width: float = 0.0

    def __post_init__(self) -> None:
        if self.text:
            script = script_from_codepoint(ord(self.text[0]))
            if script:
                self.add_class(f"{script}_fallback")
        if self.italic:
            self.style.setdefault("marginRight", make_em(self.italic))

    def to_markup(self) -> str:
        if self.classes or self.style:
            markup = [self._open_tag("span"), escape(self.text), self._close_tag("span")]
            return "".join(markup)
        return escape(self.text)


@dataclass
class SvgNode(DomNode):
    children: List[DomNode] = field(default_factory=list)

    def to_markup(self) -> str:
        markup = ["<svg xmlns=\"http://www.w3.org/2000/svg\""]
        for attr, value in self.attributes.items():
            markup.append(f" {attr}=\"{escape(value)}\"")
        markup.append(">")
        for child in self.children:
            markup.append(child.to_markup())
        markup.append("</svg>")
        return "".join(markup)


@dataclass
class PathNode(DomNode):
    path_data: str = ""

    def to_markup(self) -> str:
        return f"<path d=\"{escape(self.path_data)}\"/>"


@dataclass
class LineNode(DomNode):
    def to_markup(self) -> str:
        markup = ["<line"]
        for attr, value in self.attributes.items():
            markup.append(f" {attr}=\"{escape(value)}\"")
        markup.append("/>")
        return "".join(markup)


def assert_symbol_dom_node(node: DomNode) -> SymbolNode:
    if isinstance(node, SymbolNode):
        return node
    raise TypeError(f"Expected SymbolNode, got {type(node).__name__}")


def assert_span(node: DomNode) -> Span:
    if isinstance(node, Span):
        return node
    raise TypeError(f"Expected Span, got {type(node).__name__}")


__all__ = [
    "DomNode",
    "HtmlDomNode",
    "Span",
    "DomSpan",
    "SvgSpan",
    "Anchor",
    "Img",
    "SymbolNode",
    "SvgNode",
    "PathNode",
    "LineNode",
    "create_class",
    "assert_symbol_dom_node",
    "assert_span",
]
