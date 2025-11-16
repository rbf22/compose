"""Python port of KaTeX's MacroExpander.js - macro expansion engine."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, cast

from .define_macro import MacroArg, MacroExpansion
from .define_function import FUNCTIONS
from .lexer import Lexer
from .namespace import Namespace
from .parse_error import ParseError
from .settings import Settings
from .source_location import SourceLocation
from .token import Token
from .types import Mode

SymbolTable = Dict[str, Dict[str, Any]]

try:
    from .symbols_data import symbols as _SYMBOLS
except ImportError:
    SYMBOLS: SymbolTable = {}
else:
    SYMBOLS = cast(SymbolTable, _SYMBOLS)

try:
    from .macros import macros as MACROS
except ImportError:
    MACROS = {}

# List of commands that act like macros but aren't defined as a macro,
# function, or symbol.  Used in `isDefined`.
IMPLICIT_COMMANDS = {
    "^": True,           # Parser.js
    "_": True,           # Parser.js
    "\\limits": True,    # Parser.js
    "\\nolimits": True,  # Parser.js
}


class MacroExpander:
    """Macro expansion engine."""

    def __init__(self, input_: str, settings: Settings, mode: Mode):
        self.settings = settings
        self.expansion_count = 0
        self.feed(input_)
        # Make new global namespace
        self.macros = Namespace(MACROS, settings.macros)
        self.mode = mode
        self.stack: List[Token] = []  # contains tokens in REVERSE order

    def feed(self, input_: str) -> None:
        """Feed a new input string."""
        self.lexer = Lexer(input_, self.settings)

    def switch_mode(self, new_mode: Mode) -> None:
        """Switches between 'text' and 'math' modes."""
        self.mode = new_mode

    def begin_group(self) -> None:
        """Start a new group nesting within all namespaces."""
        self.macros.begin_group()

    def end_group(self) -> None:
        """End current group nesting within all namespaces."""
        self.macros.end_group()

    def end_groups(self) -> None:
        """Ends all currently nested groups."""
        self.macros.end_groups()

    def future(self) -> Token:
        """Returns the topmost token on the stack, without expanding it."""
        if not self.stack:
            self.push_token(self.lexer.lex())
        return self.stack[-1]

    def pop_token(self) -> Token:
        """Remove and return the next unexpanded token."""
        self.future()  # ensure non-empty stack
        return self.stack.pop()

    def push_token(self, token: Token) -> None:
        """Add a given token to the token stack."""
        self.stack.append(token)

    def push_tokens(self, tokens: List[Token]) -> None:
        """Append an array of tokens to the token stack."""
        self.stack.extend(tokens)

    def scan_argument(self, is_optional: bool) -> Optional[Token]:
        """Find a macro argument without expanding tokens."""
        if is_optional:
            self.consume_spaces()
            if self.future().text != "[":
                return None
            start = self.pop_token()  # don't include [ in tokens
            arg_result = self.consume_arg(["]"])
            tokens, end = arg_result.tokens, arg_result.end
        else:
            arg_result = self.consume_arg()
            tokens, start, end = arg_result.tokens, arg_result.start, arg_result.end

        # indicate the end of an argument
        self.push_token(Token("EOF", end.loc))
        self.push_tokens(tokens)
        return Token("", SourceLocation.range(start, end))

    def consume_spaces(self) -> None:
        """Consume all following space tokens, without expansion."""
        while True:
            token = self.future()
            if token.text == " ":
                self.stack.pop()
            else:
                break

    def consume_arg(self, delims: Optional[List[str]] = None) -> MacroArg:
        """Consume an argument from the token stream."""
        tokens: List[Token] = []
        is_delimited = delims and len(delims) > 0
        if not is_delimited:
            # Ignore spaces between arguments
            self.consume_spaces()

        start = self.future()
        depth = 0
        match = 0
        while True:
            tok = self.pop_token()
            tokens.append(tok)
            if tok.text == "{":
                depth += 1
            elif tok.text == "}":
                depth -= 1
                if depth == -1:
                    raise ParseError("Extra }", tok)
            elif tok.text == "EOF":
                expected = delims[match] if delims and is_delimited else "}"
                raise ParseError(
                    f"Unexpected end of input in a macro argument, expected '{expected}'", tok
                )

            if delims and is_delimited:
                if ((depth == 0 or (depth == 1 and delims[match] == "{")) and
                    tok.text == delims[match]):
                    match += 1
                    if match == len(delims):
                        # don't include delims in tokens
                        tokens = tokens[:-match]
                        break
                else:
                    match = 0

            if depth == 0 and not is_delimited:
                break

        # If the argument found has the form '{<nested tokens>}',
        # the outermost braces enclosing the argument are removed
        if start.text == "{" and tokens and tokens[-1].text == "}":
            tokens = tokens[1:-1]

        tokens.reverse()  # to fit in with stack order
        return MacroArg(tokens=tokens, start=start, end=tok)

    def consume_args(self, num_args: int, delimiters: Optional[List[List[str]]] = None) -> List[List[Token]]:
        """Consume the specified number of (delimited) arguments."""
        if delimiters:
            if len(delimiters) != num_args + 1:
                raise ParseError("The length of delimiters doesn't match the number of args!")
            delims = delimiters[0]
            for delim in delims:
                tok = self.pop_token()
                if delim != tok.text:
                    raise ParseError("Use of the macro doesn't match its definition", tok)

        args: List[List[Token]] = []
        for i in range(num_args):
            arg_delims: Optional[List[str]] = delimiters[i + 1] if delimiters else None
            args.append(self.consume_arg(arg_delims).tokens)
        return args

    def count_expansion(self, amount: int) -> None:
        """Increment expansionCount by the specified amount."""
        self.expansion_count += amount
        if self.expansion_count > self.settings.maxExpand:
            raise ParseError(
                "Too many expansions: infinite loop or need to increase maxExpand setting"
            )

    def expand_once(self, expandable_only: bool = False) -> Union[int, bool]:
        """Expand the next token only once if possible."""
        top_token = self.pop_token()
        name = top_token.text
        expansion = None if top_token.noexpand else self._get_expansion(name)

        if expansion is None or (expandable_only and getattr(expansion, 'unexpandable', False)):
            if (expandable_only and expansion is None and
                name.startswith("\\") and not self.is_defined(name)):
                raise ParseError(f"Undefined control sequence: {name}")
            self.push_token(top_token)
            return False

        self.count_expansion(1)
        tokens = expansion.tokens
        args = self.consume_args(expansion.num_args, expansion.delimiters)

        if expansion.num_args:
            # paste arguments in place of the placeholders
            tokens = tokens.copy()
            i = len(tokens) - 1
            while i >= 0:
                tok = tokens[i]
                if tok.text == "#":
                    if i == 0:
                        raise ParseError("Incomplete placeholder at end of macro body", tok)
                    tok = tokens[i - 1]  # next token on stack
                    if tok.text == "#":  # ## → #
                        tokens.pop(i)  # drop first #
                        i -= 1
                    elif tok.text.isdigit() and 1 <= int(tok.text) <= 9:
                        # replace the placeholder with the indicated argument
                        arg_num = int(tok.text) - 1
                        tokens[i-1:i+1] = args[arg_num]
                        i -= 1
                    else:
                        raise ParseError("Not a valid argument number", tok)
                i -= 1

        # Concatenate expansion onto top of stack
        self.push_tokens(tokens)
        return len(tokens)

    def expand_after_future(self) -> Token:
        """Expand the next token only once, return resulting top token."""
        self.expand_once()
        return self.future()

    def expand_next_token(self) -> Token:
        """Recursively expand first token, then return first non-expandable token."""
        while True:
            if self.expand_once() is False:  # fully expanded
                token = self.stack.pop()
                # the token after \noexpand is interpreted as if its meaning were '\relax'
                if getattr(token, 'treat_as_relax', False):
                    token.text = "\\relax"
                return token

    def expand_macro(self, name: str) -> Optional[List[Token]]:
        """Fully expand the given macro name."""
        return self.expand_tokens([Token(name)]) if self.macros.has(name) else None

    def expand_tokens(self, tokens: List[Token]) -> List[Token]:
        """Fully expand the given token stream."""
        output: List[Token] = []
        old_stack_length = len(self.stack)
        self.push_tokens(tokens)
        while len(self.stack) > old_stack_length:
            # Expand only expandable tokens
            if self.expand_once(True) is False:  # fully expanded
                token = self.stack.pop()
                if getattr(token, 'treat_as_relax', False):
                    # the expansion of \noexpand is the token itself
                    token.noexpand = False
                    token.treat_as_relax = False
                output.append(token)
        # Count all of these tokens as additional expansions
        self.count_expansion(len(output))
        return output

    def expand_macro_as_text(self, name: str) -> Optional[str]:
        """Fully expand the given macro name and return as string."""
        tokens = self.expand_macro(name)
        return "".join(token.text for token in tokens) if tokens else None

    def _get_expansion(self, name: str) -> Optional[MacroExpansion]:
        """Returns the expanded macro as a reversed array of tokens and a macro argument count."""
        definition = self.macros.get(name)
        if definition is None:  # mainly checking for undefined here
            return definition

        # If a single character has an associated catcode other than 13
        # (active character), then don't expand it.
        if len(name) == 1:
            catcode = getattr(self.lexer, 'catcodes', {}).get(name)
            if catcode is not None and catcode != 13:
                return None

        expansion = definition(self) if callable(definition) else definition
        if isinstance(expansion, str):
            num_args = 0
            if "#" in expansion:
                stripped = expansion.replace("##", "")
                while f"#{num_args + 1}" in stripped:
                    num_args += 1
            body_lexer = Lexer(expansion, self.settings)
            tokens: List[Token] = []
            tok = body_lexer.lex()
            while tok.text != "EOF":
                tokens.append(tok)
                tok = body_lexer.lex()
            tokens.reverse()  # to fit in with stack using push and pop
            return MacroExpansion(tokens=tokens, num_args=num_args)

        return cast(Optional[MacroExpansion], expansion)

    def is_defined(self, name: str) -> bool:
        """Determine whether a command is currently 'defined'."""
        return (self.macros.has(name) or
                name in FUNCTIONS or
                name in SYMBOLS.get("math", {}) or
                name in SYMBOLS.get("text", {}) or
                name in IMPLICIT_COMMANDS)

    def is_expandable(self, name: str) -> bool:
        """Determine whether a command is expandable."""
        macro = self.macros.get(name)
        if macro is not None:
            return (isinstance(macro, str) or
                    callable(macro) or
                    not getattr(macro, 'unexpandable', False))
        func_spec = FUNCTIONS.get(name)
        return bool(func_spec) and not getattr(func_spec, "primitive", False)

    # ------------------------------------------------------------------
    # CamelCase adapter methods for MacroContextInterface compatibility
    # ------------------------------------------------------------------

    def popToken(self) -> Token:
        return self.pop_token()

    def consumeSpaces(self) -> None:
        self.consume_spaces()

    def expandOnce(self, expandableOnly: bool = False) -> Union[int, bool]:
        return self.expand_once(expandableOnly)

    def expandAfterFuture(self) -> Token:
        return self.expand_after_future()

    def expandNextToken(self) -> Token:
        return self.expand_next_token()

    def expandMacro(self, name: str) -> Optional[List[Token]]:
        return self.expand_macro(name)

    def expandMacroAsText(self, name: str) -> Optional[str]:
        return self.expand_macro_as_text(name)

    def expandTokens(self, tokens: List[Token]) -> List[Token]:
        return self.expand_tokens(tokens)

    def consumeArg(self, delims: Optional[List[str]] = None) -> MacroArg:
        return self.consume_arg(delims)

    def consumeArgs(self, numArgs: int) -> List[List[Token]]:
        return self.consume_args(numArgs)

    def isDefined(self, name: str) -> bool:
        return self.is_defined(name)

    def isExpandable(self, name: str) -> bool:
        return self.is_expandable(name)


__all__ = ["MacroExpander", "IMPLICIT_COMMANDS"]
