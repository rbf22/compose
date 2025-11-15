"""Python port of KaTeX's macros.js - built-in macro definitions."""

from __future__ import annotations

from .define_macro import define_macro, _macros

# Import the extracted macro data
try:
    from .macros_data import MACROS_DATA
except ImportError:
    MACROS_DATA = {}

# Export the global macros object (same as _macros from defineMacro)
macros = _macros

# Initialize macros from the extracted data
for macro_name, macro_value in MACROS_DATA.items():
    if macro_value == '<function macro>':
        # For function macros, we'll need to implement them individually
        # For now, skip these complex ones
        continue
    elif macro_value == '<unparsed macro>':
        # Skip unparsed macros
        continue
    else:
        # Simple string macro
        define_macro(macro_name, macro_value)

# Export the macros object as default
__all__ = ["macros"]
