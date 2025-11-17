"""Python port of KaTeX's macros.js - built-in macro definitions."""

from __future__ import annotations

from typing import List

from .define_macro import MacroExpansion, MacroContextInterface, define_macro, _macros
from .parse_error import ParseError
from .token import Token

# Import the extracted macro data
try:
    from .macros_data import MACROS_DATA
except ImportError:  # pragma: no cover - generator/runtime mismatch
    MACROS_DATA = {}

try:
    from .symbols_data import symbols as _SYMBOLS
except ImportError:  # pragma: no cover - generator/runtime mismatch
    _SYMBOLS = {}

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

def _text_or_math(context: MacroContextInterface) -> MacroExpansion:
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


def _noexpand(context: MacroContextInterface) -> MacroExpansion:
    """Implementation of KaTeX's \noexpand.

    The expansion is the next token itself; if that token would normally be
    expandable, mark it so that it is treated as ``\relax`` instead.
    """

    tok = context.popToken()
    if context.isExpandable(tok.text):
        tok.noexpand = True
        tok.treat_as_relax = True
    return MacroExpansion(tokens=[tok], num_args=0)


def _expandafter(context: MacroContextInterface) -> MacroExpansion:
    """Implementation of KaTeX's \expandafter.

    Pop the next token *t*, expand the following token once, then reinsert *t*.
    """

    tok = context.popToken()
    # Expand only an expandable token; undefined control sequences error.
    context.expandOnce(True)
    return MacroExpansion(tokens=[tok], num_args=0)


def _first_of_two(context: MacroContextInterface) -> MacroExpansion:
    """LaTeX's \@firstoftwo{#1}{#2} expands to #1, skipping #2."""

    args = context.consumeArgs(2)
    return MacroExpansion(tokens=args[0], num_args=0)


def _second_of_two(context: MacroContextInterface) -> MacroExpansion:
    """LaTeX's \@secondoftwo{#1}{#2} expands to #2, skipping #1."""

    args = context.consumeArgs(2)
    return MacroExpansion(tokens=args[1], num_args=0)


def _ifnextchar(context: MacroContextInterface) -> MacroExpansion:
    """Implementation of KaTeX's \@ifnextchar.

    \@ifnextchar{<symbol>}{<then>}{<else>} looks ahead to the next
    (unexpanded) non-space token.  If it matches the given symbol token, it
    expands to the <then> branch; otherwise to the <else> branch.
    """

    args = context.consumeArgs(3)  # symbol, then, else
    context.consumeSpaces()
    next_tok = context.future()

    symbol_tokens: List[Token] = args[0]
    if len(symbol_tokens) == 1 and symbol_tokens[0].text == next_tok.text:
        return MacroExpansion(tokens=args[1], num_args=0)
    return MacroExpansion(tokens=args[2], num_args=0)


_DIGIT_TO_NUMBER = {
    "0": 0,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "a": 10,
    "A": 10,
    "b": 11,
    "B": 11,
    "c": 12,
    "C": 12,
    "d": 13,
    "D": 13,
    "e": 14,
    "E": 14,
    "f": 15,
    "F": 15,
}


def _char_macro(context: MacroContextInterface) -> str:
    r"""Implementation of KaTeX's \char macro.

    Parses TeX's \char forms and forwards to \@char{<codepoint>} which is
    implemented in ``functions/char.py``.
    """

    token = context.popToken()
    base: int | None
    number: int | None = None

    if token.text == "'":
        base = 8
        token = context.popToken()
    elif token.text == '"':
        base = 16
        token = context.popToken()
    elif token.text == "`":
        token = context.popToken()
        if token.text.startswith("\\"):
            if len(token.text) < 2:
                raise ParseError("\\char` missing argument")
            number = ord(token.text[1])
        elif token.text == "EOF":
            raise ParseError("\\char` missing argument")
        else:
            number = ord(token.text[0])
        base = None
    else:
        base = 10

    if base is not None:
        digit = _DIGIT_TO_NUMBER.get(token.text)
        if digit is None or digit >= base:
            raise ParseError(f"Invalid base-{base} digit {token.text}")
        number = digit
        while True:
            next_tok = context.future()
            digit = _DIGIT_TO_NUMBER.get(next_tok.text)
            if digit is None or digit >= base:
                break
            number = number * base + digit
            context.popToken()

    assert number is not None
    return f"\\@char{{{number}}}"


_DOTS_BY_TOKEN = {
    ",": "\\dotsc",
    "\\not": "\\dotsb",
    "+": "\\dotsb",
    "=": "\\dotsb",
    "<": "\\dotsb",
    ">": "\\dotsb",
    "-": "\\dotsb",
    "*": "\\dotsb",
    ":": "\\dotsb",
    "\\DOTSB": "\\dotsb",
    "\\coprod": "\\dotsb",
    "\\bigvee": "\\dotsb",
    "\\bigwedge": "\\dotsb",
    "\\biguplus": "\\dotsb",
    "\\bigcap": "\\dotsb",
    "\\bigcup": "\\dotsb",
    "\\prod": "\\dotsb",
    "\\sum": "\\dotsb",
    "\\bigotimes": "\\dotsb",
    "\\bigoplus": "\\dotsb",
    "\\bigodot": "\\dotsb",
    "\\bigsqcup": "\\dotsb",
    "\\And": "\\dotsb",
    "\\longrightarrow": "\\dotsb",
    "\\Longrightarrow": "\\dotsb",
    "\\longleftarrow": "\\dotsb",
    "\\Longleftarrow": "\\dotsb",
    "\\longleftrightarrow": "\\dotsb",
    "\\Longleftrightarrow": "\\dotsb",
    "\\mapsto": "\\dotsb",
    "\\longmapsto": "\\dotsb",
    "\\hookrightarrow": "\\dotsb",
    "\\doteq": "\\dotsb",
    "\\mathbin": "\\dotsb",
    "\\mathrel": "\\dotsb",
    "\\relbar": "\\dotsb",
    "\\Relbar": "\\dotsb",
    "\\xrightarrow": "\\dotsb",
    "\\xleftarrow": "\\dotsb",
    "\\DOTSI": "\\dotsi",
    "\\int": "\\dotsi",
    "\\oint": "\\dotsi",
    "\\iint": "\\dotsi",
    "\\iiint": "\\dotsi",
    "\\iiiint": "\\dotsi",
    "\\idotsint": "\\dotsi",
    "\\DOTSX": "\\dotsx",
}


_SPACE_AFTER_DOTS = {
    ")": True,
    "]": True,
    "\\rbrack": True,
    "\\}": True,
    "\\rbrace": True,
    "\\rangle": True,
    "\\rceil": True,
    "\\rfloor": True,
    "\\rgroup": True,
    "\\rmoustache": True,
    "\\right": True,
    "\\bigr": True,
    "\\biggr": True,
    "\\Bigr": True,
    "\\Biggr": True,
    "$": True,
    ";": True,
    ".": True,
    ",": True,
}


def _dots(context: MacroContextInterface) -> str:
    """Implementation of KaTeX's automatic \dots macro."""

    thedots = "\\dotso"
    next_tok = context.expandAfterFuture()
    nxt = next_tok.text

    if nxt in _DOTS_BY_TOKEN:
        thedots = _DOTS_BY_TOKEN[nxt]
    elif nxt.startswith("\\not"):
        thedots = "\\dotsb"
    else:
        math_symbols = _SYMBOLS.get("math", {}) if isinstance(_SYMBOLS, dict) else {}
        info = math_symbols.get(nxt)
        if info and info.get("group") in {"bin", "rel"}:
            thedots = "\\dotsb"
    return thedots


def _dotso(context: MacroContextInterface) -> str:
    """Implementation of KaTeX's \dotso macro."""

    next_tok = context.future()
    nxt = next_tok.text
    if nxt in _SPACE_AFTER_DOTS:
        return "\\ldots\\,"
    return "\\ldots"


def _dotsc(context: MacroContextInterface) -> str:
    """Implementation of KaTeX's \dotsc macro."""

    next_tok = context.future()
    nxt = next_tok.text
    if nxt in _SPACE_AFTER_DOTS and nxt != ",":
        return "\\ldots\\,"
    return "\\ldots"


def _cdots(context: MacroContextInterface) -> str:
    """Implementation of KaTeX's \cdots macro."""

    next_tok = context.future()
    nxt = next_tok.text
    if nxt in _SPACE_AFTER_DOTS:
        return "\\@cdots\\,"
    return "\\@cdots"


# Register core function-style macros implemented in Python.
define_macro("\\TextOrMath", _text_or_math)
define_macro("\\noexpand", _noexpand)
define_macro("\\expandafter", _expandafter)
define_macro("\\@firstoftwo", _first_of_two)
define_macro("\\@secondoftwo", _second_of_two)
define_macro("\\@ifnextchar", _ifnextchar)
define_macro("\\char", _char_macro)
define_macro("\\dots", _dots)
define_macro("\\dotso", _dotso)
define_macro("\\dotsc", _dotsc)
define_macro("\\cdots", _cdots)


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


# Initialize macros from the extracted data.  Function-style macros that have
# dedicated Python implementations above are marked as "<function macro>" in
# MACROS_DATA and are skipped here.
for macro_name, macro_value in MACROS_DATA.items():
    if macro_value == '<function macro>':
        # Implemented manually in this module (e.g. \TextOrMath, \noexpand,
        # \expandafter, \@firstoftwo, \@secondoftwo, \@ifnextchar, \dots,
        # \dotso, \dotsc, \cdots, \char).
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


# ---------------------------------------------------------------------------
# Targeted overrides for spacing macros
# ---------------------------------------------------------------------------

# In math mode, KaTeX's \, behaves like a 3mu math thinspace.  Route it
# through \mskip so that the kern/mskip function handlers and MathML
# SpaceNode logic (which maps 3mu → U+2009 thin space) are exercised.
_THINSPACE_EXPANSION = _expand_as_tokens(r"\mskip3mu")
define_macro("\\,", _THINSPACE_EXPANSION)
define_macro("\\thinspace", _THINSPACE_EXPANSION)


# Export the macros object as default
__all__ = ["macros"]
