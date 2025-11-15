"""Python port of KaTeX's functions.js - function registry and imports."""

from __future__ import annotations

from .define_function import _functions

# Export the functions registry
functions = _functions

# Import all function implementations (these will register themselves)
# TODO: Convert individual function files from functions/ directory
# import .functions.accent
# import .functions.accentunder
# import .functions.arrow
# import .functions.pmb
# import .environments.cd  # This might be misplaced in the original
# import .functions.char
# import .functions.color
# import .functions.cr
# import .functions.def
# import .functions.delimsizing
# import .functions.enclose
# import .functions.environment
# import .functions.font
# import .functions.genfrac
# import .functions.horizBrace
# import .functions.href
# import .functions.hbox
# import .functions.html
# import .functions.htmlmathml
# import .functions.includegraphics
# import .functions.kern
# import .functions.lap
# import .functions.math
# import .functions.mathchoice
# import .functions.mclass
# import .functions.operatorname
# import .functions.ordgroup
# import .functions.overline
# import .functions.phantom
# import .functions.raisebox
# import .functions.relax
# import .functions.rule
# import .functions.sizing
# import .functions.smash
# import .functions.sqrt
# import .functions.styling
# import .functions.supsub
# import .functions.symbolsOp
# import .functions.symbolsOrd
# import .functions.symbolsSpacing
# import .functions.tag
# import .functions.text
# import .functions.underline
# import .functions.vcenter
# import .functions.verb

__all__ = ["functions"]
