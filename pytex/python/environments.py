"""Python port of KaTeX's environments.js - environment registry and imports."""

from __future__ import annotations

from .define_environment import _environments

# Export the environments registry
environments = _environments

# Import all environment implementations (these will register themselves)

__all__ = ["environments"]
