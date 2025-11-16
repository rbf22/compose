"""Python port of KaTeX's Lexer.js - LaTeX tokenization."""

from __future__ import annotations

import re
from typing import Dict

from .parse_error import ParseError
from .settings import Settings
from .source_location import SourceLocation
from .token import Token


# Regex patterns for tokenization
SPACE_REGEX_STRING = r"[ \r\n\t]"
CONTROL_WORD_REGEX_STRING = r"\\[a-zA-Z@]+"
CONTROL_SYMBOL_REGEX_STRING = r"\\[^\uD800-\uDFFF]"
CONTROL_WORD_WHITESPACE_REGEX_STRING = f"({CONTROL_WORD_REGEX_STRING}){SPACE_REGEX_STRING}*"
CONTROL_SPACE_REGEX_STRING = r"\\(\n|[ \r\t]+\n?)[ \r\t]*"
COMBINING_DIACRITICAL_MARK_STRING = r"[\u0300-\u036f]"

COMBINING_DIACRITICAL_MARKS_END_REGEX = re.compile(f"{COMBINING_DIACRITICAL_MARK_STRING}+$")

TOKEN_REGEX_STRING = (
    f"({SPACE_REGEX_STRING}+)|"  # whitespace
    f"{CONTROL_SPACE_REGEX_STRING}|"  # \whitespace
    r"([!-\\[\\]-\u2027\u202A-\uD7FF\uF900-\uFFFF]"  # single codepoint
    f"{COMBINING_DIACRITICAL_MARK_STRING}*"  # ...plus accents
    r"|[\uD800-\uDBFF][\uDC00-\uDFFF]"  # surrogate pair
    f"{COMBINING_DIACRITICAL_MARK_STRING}*"  # ...plus accents
    r"|\\verb\*([^]).*?\4"  # \verb*
    r"|\\verb([^*a-zA-Z]).*?\5"  # \verb unstarred
    f"|{CONTROL_WORD_WHITESPACE_REGEX_STRING}"  # \macroName + spaces
    f"|{CONTROL_SYMBOL_REGEX_STRING})"  # \\, \', etc.
)


class Lexer:
    """Main Lexer class for tokenizing LaTeX input."""

    def __init__(self, input_: str, settings: Settings):
        # Separate accents from characters
        self.input = input_
        self.settings = settings
        self.token_regex = re.compile(TOKEN_REGEX_STRING, re.MULTILINE)
        # Track current position explicitly; Pattern.lastindex is not available.
        self._pos = 0
        # Category codes. The lexer only supports comment characters (14) for now.
        # MacroExpander additionally distinguishes active (13).
        self.catcodes: Dict[str, int] = {
            "%": 14,  # comment character
            "~": 13,  # active character
        }

    def set_catcode(self, char: str, code: int) -> None:
        """Set category code for a character."""
        self.catcodes[char] = code

    def lex(self) -> Token:
        """Lex a single token."""
        input_ = self.input
        pos = self._pos

        if pos == len(input_):
            return Token("EOF", SourceLocation(self, pos, pos))

        match = self.token_regex.search(input_, pos)
        if match is None or match.start() != pos:
            char = input_[pos] if pos < len(input_) else "EOF"
            raise ParseError(
                f"Unexpected character: '{char}'",
                Token(char, SourceLocation(self, pos, pos + 1))
            )

        # Extract token text
        if match.group(6):  # control word
            text = match.group(6)
        elif match.group(3):  # regular token
            text = match.group(3)
        elif match.group(2):  # control space
            text = "\\ "
        else:  # whitespace
            text = " "

        if self.catcodes.get(text) == 14:  # comment character
            nl_index = input_.find('\n', match.end())
            if nl_index == -1:
                self._pos = len(input_)  # EOF
                self.settings.report_nonstrict(
                    "commentAtEnd",
                    "% comment has no terminating newline; LaTeX would "
                    "fail because of commenting the end of math mode (e.g. $)"
                )
            else:
                self._pos = nl_index + 1
            return self.lex()

        # Advance position to end of this match
        self._pos = match.end()
        return Token(text, SourceLocation(self, pos, self._pos))


__all__ = ["Lexer", "COMBINING_DIACRITICAL_MARKS_END_REGEX"]
