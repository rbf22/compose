"""Python port of KaTeX's Lexer.js - LaTeX tokenization."""

from __future__ import annotations

import re

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
    # Simplified \\verb/\\verb* handling: we no longer rely on numeric
    # backreferences (\\4, \\5), which can cause re.PatternError on
    # some Python versions if group numbering diverges from the original
    # JavaScript regex.  The lexer still recognises \\verb tokens as a
    # whole, but does not enforce matching delimiters at the regex level.
    r"|\\verb\*([^]).*?"  # \\verb*
    r"|\\verb([^*a-zA-Z]).*?"  # \\verb unstarred
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
        self.catcodes: dict[str, int] = {
            "%": 14,  # comment character
            "~": 13,  # active character
        }

    def set_catcode(self, char: str, code: int) -> None:
        """Set category code for a character."""
        self.catcodes[char] = code

    def lex(self) -> Token:
        """Lex a single token.

        This implementation mirrors KaTeX's tokenisation semantics but
        avoids relying on complex regex group numbering, which proved
        brittle across Python versions.
        """

        input_ = self.input
        length = len(input_)
        pos = self._pos

        # End of input
        if pos >= length:
            return Token("EOF", SourceLocation(self, pos, pos))

        ch = input_[pos]

        # -----------------------------------------------------------------
        # Whitespace: collapse runs of spaces/newlines into a single " "
        # token, as in KaTeX.
        # -----------------------------------------------------------------
        if ch in " \r\n\t":
            start = pos
            while pos < length and input_[pos] in " \r\n\t":
                pos += 1
            self._pos = pos
            return Token(" ", SourceLocation(self, start, pos))

        # -----------------------------------------------------------------
        # Control sequences starting with backslash: control space,
        # \verb / \verb*, control words (\\alpha), and control symbols
        # (\\%, \\&, etc.).
        # -----------------------------------------------------------------
        if ch == "\\":
            start = pos
            # Control space: "\\" followed by whitespace/newline.
            if pos + 1 < length and input_[pos + 1] in " \r\n\t":
                pos += 2
                # Consume the rest of the whitespace sequence.
                while pos < length and input_[pos] in " \r\n\t":
                    pos += 1
                self._pos = pos
                return Token("\\ ", SourceLocation(self, start, pos))

            # \verb and \verb* handling.  We expect "\\verb" followed by a
            # non-letter delimiter (optionally preceded by "*").  We then
            # consume up to the next occurrence of that delimiter.
            if input_.startswith("\\verb", pos):
                dpos = pos + 5
                if dpos < length and not input_[dpos].isalpha():
                    # Optional star
                    if input_[dpos] == "*":
                        dpos += 1
                    if dpos >= length:
                        # Degenerate, but treat as a bare backslash.
                        self._pos = start + 1
                        return Token("\\", SourceLocation(self, start, start + 1))
                    delim = input_[dpos]
                    end = input_.find(delim, dpos + 1)
                    if end == -1:
                        end = length - 1
                    text = input_[start : end + 1]
                    self._pos = end + 1
                    return Token(text, SourceLocation(self, start, self._pos))

            # Control word: backslash followed by letters/@.
            if pos + 1 < length and (input_[pos + 1].isalpha() or input_[pos + 1] == "@"):  # type: ignore[str-bytes-safe]
                pos += 2
                while pos < length and (input_[pos].isalpha() or input_[pos] == "@"):  # type: ignore[str-bytes-safe]
                    pos += 1
                # Consume trailing spaces/newlines (TeX behaviour).
                while pos < length and input_[pos] in " \r\n\t":
                    pos += 1
                text = input_[start:pos]
                self._pos = pos
                return Token(text, SourceLocation(self, start, pos))

            # Control symbol: backslash plus the next character.
            if pos + 1 < length:
                text = input_[pos : pos + 2]
                self._pos = pos + 2
            else:
                text = "\\"
                self._pos = pos + 1

            # Comment character (%) is handled via catcodes below.
            token = Token(text, SourceLocation(self, start, self._pos))
            if self.catcodes.get(text) == 14:  # pragma: no cover - safety
                # Treat as comment; fall through to comment handling.
                ch = "%"
            else:
                return token

        # -----------------------------------------------------------------
        # Comment character (%): skip to end of line and recurse.
        # -----------------------------------------------------------------
        if ch == "%" and self.catcodes.get("%") == 14:
            nl_index = input_.find("\n", pos + 1)
            if nl_index == -1:
                # Comment to EOF.
                self._pos = length
                self.settings.report_nonstrict(
                    "commentAtEnd",
                    "% comment has no terminating newline; LaTeX would "
                    "fail because of commenting the end of math mode (e.g. $)",
                )
            else:
                self._pos = nl_index + 1
            return self.lex()

        # -----------------------------------------------------------------
        # Ordinary character (including Unicode) plus optional combining
        # diacritical marks.
        # -----------------------------------------------------------------
        start = pos
        pos += 1
        # Consume trailing combining marks U+0300..U+036F.
        while pos < length and "\u0300" <= input_[pos] <= "\u036F":
            pos += 1

        text = input_[start:pos]
        self._pos = pos
        return Token(text, SourceLocation(self, start, pos))


__all__ = ["Lexer", "COMBINING_DIACRITICAL_MARKS_END_REGEX"]
