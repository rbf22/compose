"""Shared virtual node abstractions for HTML/Math trees."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol


class VirtualNode(Protocol):
    def to_markup(self) -> str:
        ...


@dataclass
class DocumentFragment:
    children: Sequence[VirtualNode] = field(default_factory=list)
    height: float = 0.0
    depth: float = 0.0
    max_font_size: float = 0.0

    def has_class(self, class_name: str) -> bool:
        return False

    def to_markup(self) -> str:
        return "".join(child.to_markup() for child in self.children)

    def to_text(self) -> str:
        parts: list[str] = []
        for child in self.children:
            to_text = getattr(child, "to_text", None)
            if callable(to_text):
                parts.append(to_text())
        return "".join(parts)


__all__ = ["VirtualNode", "DocumentFragment"]
