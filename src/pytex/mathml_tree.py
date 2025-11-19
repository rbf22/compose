"""MathML tree structures mirroring KaTeX's mathMLTree.js."""

from __future__ import annotations

from dataclasses import dataclass, field

from .tree import DocumentFragment, VirtualNode
from .units import make_em
from .utils import escape

MATH_ML_NS = "http://www.w3.org/1998/Math/MathML"


@dataclass
class TextNode:
    text: str

    def to_markup(self) -> str:
        return escape(self.text)

    def to_text(self) -> str:
        return self.text


@dataclass
class MathNode:
    type: str
    children: list[VirtualNode] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    attributes: dict[str, str] = field(default_factory=dict)

    def set_attribute(self, name: str, value: str) -> None:
        self.attributes[name] = value

    def get_attribute(self, name: str) -> str | None:
        return self.attributes.get(name)

    def to_markup(self) -> str:
        markup = [f"<{self.type}"]
        for attr, value in self.attributes.items():
            markup.append(f" {attr}=\"{escape(value)}\"")
        if self.classes:
            markup.append(f" class=\"{escape(' '.join(self.classes))}\"")
        markup.append(">")
        for child in self.children:
            markup.append(child.to_markup())
        markup.append(f"</{self.type}>")
        return "".join(markup)

    def to_text(self) -> str:
        return "".join(getattr(child, "to_text", lambda: "")() for child in self.children)


@dataclass
class SpaceNode:
    width: float

    def to_markup(self) -> str:
        if 0.05555 <= self.width <= 0.05556:
            return "<mtext>\u200a</mtext>"
        if 0.1666 <= self.width <= 0.1667:
            return "<mtext>\u2009</mtext>"
        return f"<mspace width=\"{make_em(self.width)}\"/>"

    def to_text(self) -> str:
        return " "


__all__ = ["MathNode", "TextNode", "SpaceNode", "DocumentFragment"]
