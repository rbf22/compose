"""Python port of KaTeX's macros.js - built-in macro definitions."""

from __future__ import annotations

from .define_macro import MacroExpansion, define_macro, _macros

# Import the extracted macro data
try:
    from .macros_data import MACROS_DATA
except ImportError:
    MACROS_DATA = {}

# Export the global macros object (same as _macros from defineMacro)
macros = _macros

def _expand_as_tokens(body: str) -> MacroExpansion:
    """Utility to turn a raw macro body string into a MacroExpansion.

    This mirrors the logic in MacroExpander._get_expansion when it
    receives a string macro: we lex the body into a reversed token list
    and compute num_args by scanning for placeholders.  Centralising this
    here keeps simple function-style macros easy to define.
    """
    from .lexer import Lexer
    from .settings import Settings

    # Count placeholders (#1, #2, ...) while respecting escaped ##
    num_args = 0
    stripped = body.replace("##", "")
    while f"#{num_args + 1}" in stripped:
        num_args += 1

    lexer = Lexer(body, Settings({}))
    tokens = []
    tok = lexer.lex()
    while tok.text != "EOF":
        tokens.append(tok)
        tok = lexer.lex()
    tokens.reverse()

    return MacroExpansion(tokens=tokens, num_args=num_args)


def _define_function_like_macro(name: str, body: str) -> None:
    """Define a function-style macro that expands using MacroExpansion.

    The *body* string may contain #1..#9 placeholders; arity is inferred
    automatically and the resulting MacroExpansion is marked as
    unexpandable to avoid re-parsing it as a further string macro.
    """
    expansion = _expand_as_tokens(body)
    expansion.unexpandable = True
    define_macro(name, expansion)


# Core functional macros implemented manually

def _text_or_math(context: "MacroContextInterface") -> MacroExpansion:
    """Implementation of KaTeX's \TextOrMath helper.

    Usage pattern (from macros_data):

        \TextOrMath{<text-branch>}{<math-branch>}

    In the port we look at context.mode and expand only the
    branch appropriate for the current mode, mirroring KaTeX’s
    behaviour well enough for spacing macros like \, to work.
    """
    # Consume the two arguments as raw token lists
    args = context.consumeArgs(2)
    text_branch_tokens, math_branch_tokens = args[0], args[1]

    chosen = text_branch_tokens if context.mode == "text" else math_branch_tokens
    # We return a MacroExpansion directly with these tokens.  num_args=0
    # because all arguments have already been substituted.
    return MacroExpansion(tokens=list(reversed(chosen)), num_args=0)


# Register \TextOrMath as a callable macro
define_macro("\\TextOrMath", _text_or_math)


def _canonical_name(name: str) -> str:
    """Normalise KaTeX-style macro names to the parser's single-\\ form.

    The auto-generated macros_data keys often contain an extra leading
    backslash (e.g. "\\\\," in source representing the TeX command
    "\\,").  The lexer and parser, however, see control sequences with a
    single leading backslash.  To bridge this, we register both the raw
    name from MACROS_DATA and a canonical single-\\ form when applicable.
    """

    if name.startswith("\\\\") and not name.startswith("\\\\\\"):
        return name[1:]
    return name


# Initialize macros from the extracted data
for macro_name, macro_value in MACROS_DATA.items():
    if macro_value == '<function macro>':
        # Provide small Python implementations for selected helpers.
        if macro_name == "\\TextOrMath":
            # Already defined above
            continue
        # Other function-style macros are currently unsupported; skip.
        continue
    elif macro_value == '<unparsed macro>':
        # Skip unparsed macros
        continue
    else:
        # Simple string macro – define under both the original and
        # canonicalised names so that the parser's single-\\ sequences
        # resolve correctly.
        define_macro(macro_name, macro_value)
        canon = _canonical_name(macro_name)
        if canon != macro_name:
            define_macro(canon, macro_value)

# Export the macros object as default
__all__ = ["macros"]
