"""Python port of KaTeX's Namespace.js - nameable things management."""

from __future__ import annotations

from typing import Generic, TypeVar

from .parse_error import ParseError

Value = TypeVar('Value')


class Namespace(Generic[Value]):
    """A space of nameable things like macros or lengths."""

    def __init__(
        self,
        builtins: dict[str, Value] | None = None,
        global_macros: dict[str, Value] | None = None
    ):
        self.current: dict[str, Value] = global_macros or {}
        self.builtins: dict[str, Value] = builtins or {}
        self.undef_stack: list[dict[str, Value | None]] = []

    def begin_group(self) -> None:
        """Start a new nested group, affecting future local sets."""
        self.undef_stack.append({})

    def end_group(self) -> None:
        """End current nested group, restoring values before the group began."""
        if not self.undef_stack:
            raise ParseError(
                "Unbalanced namespace destruction: attempt to pop global namespace; "
                "please report this as a bug"
            )
        undefs = self.undef_stack.pop()
        for name, value in undefs.items():
            if value is None:
                self.current.pop(name, None)
            else:
                self.current[name] = value

    def end_groups(self) -> None:
        """Ends all currently nested groups."""
        while self.undef_stack:
            self.end_group()

    def has(self, name: str) -> bool:
        """Detect whether name has a definition."""
        return name in self.current or name in self.builtins

    def get(self, name: str) -> Value | None:
        """Get the current value of a name, or None if there is no value."""
        if name in self.current:
            return self.current[name]
        return self.builtins.get(name)

    def set(self, name: str, value: Value | None, global_: bool = False) -> None:
        """Set the current value of a name, and optionally set it globally too."""
        if global_:
            # Global set is equivalent to setting in all groups
            for undefs in self.undef_stack:
                undefs.pop(name, None)
            if self.undef_stack:
                self.undef_stack[-1][name] = value
        else:
            # Undo this set at end of this group
            if self.undef_stack and name not in self.undef_stack[-1]:
                self.undef_stack[-1][name] = self.current.get(name)

        if value is None:
            self.current.pop(name, None)
        else:
            self.current[name] = value


__all__ = ["Namespace"]
