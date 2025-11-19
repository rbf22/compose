"""Python port of KaTeX's Parser.js - LaTeX expression parsing."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, cast

from .lexer import COMBINING_DIACRITICAL_MARKS_END_REGEX
from .macro_expander import MacroExpander
from .parse_error import ParseError
from .settings import Settings
from .source_location import SourceLocation
from .token import Token
from .types import Mode
from .unicode_accents import ACCENTS
from .unicode_scripts import supported_codepoint
from .unicode_sup_or_sub import UNICODE_SUB_REGEX, U_SUBS_AND_SUPS
from .unicode_symbols import UNICODE_SYMBOLS
from .units import valid_unit

# Functions map imported from define_function as FunctionSpec dataclasses.
from .define_function import FUNCTIONS, FunctionSpec

try:
    from .symbols_data_generated import symbols as SYMBOLS, ATOMS
except ImportError:
    SYMBOLS = {}
    ATOMS = {}

IMPLICIT_COMMANDS = {
    "^": True,           # Parser.js
    "_": True,           # Parser.js
    "\\limits": True,    # Parser.js
    "\\nolimits": True,  # Parser.js
}


class Parser:
    """Main LaTeX parser class."""

    def __init__(self, input_: str, settings: Settings):
        # Start in math mode
        self.mode: Mode = Mode.MATH
        # Create a new macro expander
        self.gullet = MacroExpander(input_, settings, self.mode)
        # Store the settings for use in parsing
        self.settings = settings
        # Count leftright depth (for \middle errors)
        self.leftright_depth = 0
        self.next_token: Optional[Token] = None

    def expect(self, text: str, consume: bool = True) -> None:
        """Checks a result to make sure it has the right type."""
        if self.fetch().text != text:
            raise ParseError(
                f"Expected '{text}', got '{self.fetch().text}'", self.fetch()
            )
        if consume:
            self.consume()

    def consume(self) -> None:
        """Discards the current lookahead token."""
        self.next_token = None

    def fetch(self) -> Token:
        """Return the current lookahead token."""
        if self.next_token is None:
            self.next_token = self.gullet.expand_next_token()
        return self.next_token

    def switch_mode(self, new_mode: Mode) -> None:
        """Switches between 'text' and 'math' modes."""
        self.mode = new_mode
        self.gullet.switch_mode(new_mode)

    def parse(self) -> List[Any]:
        """Main parsing function, which parses an entire input."""
        if not self.settings.global_group:
            # Create a group namespace for the math expression
            self.gullet.begin_group()

        # Use old \color behavior (same as LaTeX's \textcolor) if requested
        if self.settings.color_is_text_color:
            # Install alias in the macro namespace
            self.gullet.macros.set("\\color", "\\textcolor", global_=True)

        try:
            # Try to parse the input
            parse = self.parse_expression(False)

            # If we succeeded, make sure there's an EOF at the end
            self.expect("EOF")

            # End the group namespace for the expression
            if not self.settings.global_group:
                self.gullet.end_group()

            return parse

        finally:
            # Close any leftover groups in case of a parse error
            self.gullet.end_groups()

    def subparse(self, tokens: List[Token]) -> List[Any]:
        """Fully parse a separate sequence of tokens."""
        # Save the next token from the current job
        old_token = self.next_token
        self.consume()

        # Run the new job, terminating it with an excess '}'
        self.gullet.push_token(Token("}"))
        self.gullet.push_tokens(tokens)
        parse = self.parse_expression(False)
        self.expect("}")

        # Restore the next token from the current job
        self.next_token = old_token

        return parse

    END_OF_EXPRESSION = ["}", "\\endgroup", "\\end", "\\right", "&"]

    def parse_expression(
        self,
        break_on_infix: bool,
        break_on_token_text: Optional[str] = None,
    ) -> List[Any]:
        """Parses an 'expression', a list of atoms."""
        body = []
        # Keep adding atoms to the body until we can't parse any more atoms
        while True:
            # Ignore spaces in math mode
            if self.mode == "math":
                self.consume_spaces()
            lex = self.fetch()
            if lex.text in self.END_OF_EXPRESSION:
                break
            if break_on_token_text and lex.text == break_on_token_text:
                break
            func_spec = FUNCTIONS.get(lex.text)
            if break_on_infix and func_spec and func_spec.infix:
                break
            atom = self.parse_atom(break_on_token_text)
            if atom is None:
                break
            if atom.get("type") == "internal":
                continue
            body.append(atom)

        if self.mode == "text":
            self.form_ligatures(body)
        return self.handle_infix_nodes(body)

    def handle_infix_nodes(self, body: List[Any]) -> List[Any]:
        r"""Rewrites infix operators like \over with commands like \frac."""
        over_index = -1
        func_name = None

        for i, node in enumerate(body):
            if node.get("type") == "infix":
                if over_index != -1:
                    raise ParseError("only one infix operator per group", node["token"])
                over_index = i
                func_name = node.get("replaceWith")

        if over_index != -1 and func_name:
            numer_body = body[:over_index]
            denom_body = body[over_index + 1:]

            if len(numer_body) == 1 and numer_body[0].get("type") == "ordgroup":
                numer_node = numer_body[0]
            else:
                numer_node = {"type": "ordgroup", "mode": self.mode, "body": numer_body}

            if len(denom_body) == 1 and denom_body[0].get("type") == "ordgroup":
                denom_node = denom_body[0]
            else:
                denom_node = {"type": "ordgroup", "mode": self.mode, "body": denom_body}

            node = self.call_function(func_name, [numer_node, denom_node], [])
            return [node]
        else:
            return body

    def handle_sup_subscript(self, name: str) -> Any:
        """Handle a subscript or superscript with nice errors."""
        symbol_token = self.fetch()
        symbol = symbol_token.text
        self.consume()
        self.consume_spaces()  # ignore spaces before sup/subscript argument

        # Skip over allowed internal nodes such as \relax
        group = None
        while True:
            group = self.parse_group(name)
            if not group or group.get("type") != "internal":
                break

        if not group:
            raise ParseError(f"Expected group after '{symbol}'", symbol_token)

        return group

    def format_unsupported_cmd(self, text: str) -> Dict[str, Any]:
        """Format unsupported command as colored text."""
        textord_array = [
            {"type": "textord", "mode": "text", "text": char} for char in text
        ]

        text_node = {
            "type": "text",
            "mode": self.mode,
            "body": textord_array,
        }

        color_node = {
            "type": "color",
            "mode": self.mode,
            "color": self.settings.error_color,
            "body": [text_node],
        }

        return color_node

    def parse_atom(self, break_on_token_text: Optional[str] = None) -> Optional[Any]:
        """Parses a group with optional super/subscripts."""
        # The body of an atom is an implicit group
        base = self.parse_group("atom", break_on_token_text)

        # Internal nodes cannot support super/subscripts
        if base and base.get("type") == "internal":
            return base

        # In text mode, we don't have superscripts or subscripts
        if self.mode == "text":
            return base

        superscript = None
        subscript = None
        while True:
            # Guaranteed in math mode, so eat any spaces first
            self.consume_spaces()

            # Lex the first token
            lex = self.fetch()

            if lex.text in ("\\limits", "\\nolimits"):
                # We got a limit control
                if base and base.get("type") == "op":
                    limits = lex.text == "\\limits"
                    base["limits"] = limits
                    base["alwaysHandleSupSub"] = True
                elif base and base.get("type") == "operatorname":
                    if base.get("alwaysHandleSupSub"):
                        base["limits"] = lex.text == "\\limits"
                else:
                    raise ParseError("Limit controls must follow a math operator", lex)
                self.consume()
            elif lex.text == "^":
                # We got a superscript start
                if superscript:
                    raise ParseError("Double superscript", lex)
                superscript = self.handle_sup_subscript("superscript")
            elif lex.text == "_":
                # We got a subscript start
                if subscript:
                    raise ParseError("Double subscript", lex)
                subscript = self.handle_sup_subscript("subscript")
            elif lex.text == "'":
                # We got a prime
                if superscript:
                    raise ParseError("Double superscript", lex)
                prime = {"type": "textord", "mode": self.mode, "text": "\\prime"}

                # Many primes can be grouped together
                primes = [prime]
                self.consume()
                # Keep lexing tokens until we get something that's not a prime
                while self.fetch().text == "'":
                    primes.append(prime)
                    self.consume()
                # If there's a superscript following the primes, combine it
                if self.fetch().text == "^":
                    primes.append(self.handle_sup_subscript("superscript"))
                # Put everything into an ordgroup as the superscript
                superscript = {"type": "ordgroup", "mode": self.mode, "body": primes}
            elif lex.text in U_SUBS_AND_SUPS:
                # A Unicode subscript or superscript character
                is_sub = UNICODE_SUB_REGEX.search(lex.text) is not None
                subsup_tokens = []
                subsup_tokens.append(Token(U_SUBS_AND_SUPS[lex.text]))
                self.consume()
                # Continue fetching tokens to fill out the string
                while True:
                    token_text = self.fetch().text
                    if token_text not in U_SUBS_AND_SUPS:
                        break
                    if (UNICODE_SUB_REGEX.search(token_text) is not None) != is_sub:
                        break
                    subsup_tokens.insert(0, Token(U_SUBS_AND_SUPS[token_text]))
                    self.consume()
                # Now create a (sub|super)script
                body = self.subparse(subsup_tokens)
                if is_sub:
                    subscript = {"type": "ordgroup", "mode": "math", "body": body}
                else:
                    superscript = {"type": "ordgroup", "mode": "math", "body": body}
            else:
                # If it wasn't ^, _, or ', stop parsing super/subscripts
                break

        # Base must be set if superscript or subscript are set per logic above
        if superscript or subscript:
            # If we got either a superscript or subscript, create a supsub
            return {
                "type": "supsub",
                "mode": self.mode,
                "base": base,
                "sup": superscript,
                "sub": subscript,
            }
        else:
            # Otherwise return the original body
            return base

    def parse_function(
        self,
        break_on_token_text: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[Any]:
        """Parses an entire function, including its base and all arguments."""
        token = self.fetch()
        func = token.text
        func_data = FUNCTIONS.get(func)
        if func == "\\custom":
            try:
                print(
                    "[DEBUG] parse_function func=", repr(func),
                    "in FUNCTIONS?", func in FUNCTIONS,
                    "func_data is None?", func_data is None,
                )
            except Exception:
                pass
        if not func_data:
            return None
        self.consume()  # consume command token

        if name and name != "atom" and not func_data.allowed_in_argument:
            raise ParseError(
                f"Got function '{func}' with no arguments" + (f" as {name}" if name else ""),
                token
            )
        elif self.mode == "text" and not func_data.allowed_in_text:
            raise ParseError(f"Can't use function '{func}' in text mode", token)
        elif self.mode == "math" and func_data.allowed_in_math is False:
            raise ParseError(f"Can't use function '{func}' in math mode", token)

        args, opt_args = self.parse_arguments(func, func_data)
        return self.call_function(func, args, opt_args, token, break_on_token_text)

    def call_function(
        self,
        name: str,
        args: List[Any],
        opt_args: List[Optional[Any]],
        token: Optional[Token] = None,
        break_on_token_text: Optional[str] = None,
    ) -> Any:
        """Call a function handler with suitable context."""
        context = {
            "funcName": name,
            "parser": self,
            "token": token,
            "breakOnTokenText": break_on_token_text,
        }
        func = FUNCTIONS.get(name)
        if func and func.handler:
            handler = func.handler

            # All function handlers in the port follow KaTeX's calling
            # convention: handler(context, args, optArgs).
            result = handler(context, args, opt_args)  # type: ignore[misc]

            # In KaTeX, a handler is expected to return a parse node.  For the
            # Python port we treat falsy/empty returns (such as "{}" from a
            # user-defined function) as an internal no-op node so that the
            # parser recognises the function name but drops it from the final
            # expression.
            if not result:
                return {
                    "type": "internal",
                    "mode": self.mode,
                }
            return result
        else:
            raise ParseError(f"No function handler for {name}")

    def parse_arguments(
        self, func: str, func_data: "FunctionSpec | Dict[str, Any]"
    ) -> tuple[List[Any], List[Optional[Any]]]:
        """Parses the arguments of a function or environment.

        The *func_data* parameter is normally a FunctionSpec produced by
        define_function, but some call sites (e.g. environment handling)
        pass a lightweight dict with KaTeX-style keys such as
        ``numArgs`` and ``numOptionalArgs``.
        """

        def _num_args(spec: "FunctionSpec | Dict[str, Any]") -> int:
            return spec.num_args if isinstance(spec, FunctionSpec) else int(spec.get("numArgs", 0))

        def _num_optional_args(spec: "FunctionSpec | Dict[str, Any]") -> int:
            return spec.num_optional_args if isinstance(spec, FunctionSpec) else int(spec.get("numOptionalArgs", 0))

        def _arg_types(spec: "FunctionSpec | Dict[str, Any]") -> List[Any]:
            if isinstance(spec, FunctionSpec):
                return list(spec.arg_types or [])
            return list(spec.get("argTypes", []) or [])

        def _primitive(spec: "FunctionSpec | Dict[str, Any]") -> bool:
            return bool(spec.primitive) if isinstance(spec, FunctionSpec) else bool(spec.get("primitive", False))

        def _type_name(spec: "FunctionSpec | Dict[str, Any]") -> Optional[str]:
            return spec.type if isinstance(spec, FunctionSpec) else spec.get("type")

        total_args = _num_args(func_data) + _num_optional_args(func_data)
        if total_args == 0:
            return [], []

        args: List[Any] = []
        opt_args: List[Optional[Any]] = []

        for i in range(total_args):
            arg_types = _arg_types(func_data)
            arg_type = arg_types[i] if i < len(arg_types) else None
            is_optional = i < _num_optional_args(func_data)

            if (
                _primitive(func_data) and arg_type is None
                or (_type_name(func_data) == "sqrt" and i == 1 and opt_args and opt_args[0] is None)
            ):
                arg_type = "primitive"

            arg = self.parse_group_of_type(f"argument to '{func}'", arg_type, is_optional)
            if is_optional:
                opt_args.append(arg)
            elif arg is not None:
                args.append(arg)
            else:
                raise ParseError("Null argument, please report this as a bug")

        return args, opt_args

    def parse_group_of_type(
        self,
        name: str,
        type_: Optional[str],
        optional: bool,
    ) -> Optional[Any]:
        """Parses a group when the mode is changing."""
        if type_ == "color":
            return self.parse_color_group(optional)
        elif type_ == "size":
            return self.parse_size_group(optional)
        elif type_ == "url":
            return self.parse_url_group(optional)
        elif type_ == "math":
            return self.parse_argument_group(optional, Mode.MATH)
        elif type_ == "text":
            return self.parse_argument_group(optional, Mode.TEXT)
        elif type_ == "hbox":
            # hbox argument type wraps the argument in the equivalent of \hbox
            group = self.parse_argument_group(optional, Mode.TEXT)
            if group is not None:
                return {
                    "type": "styling",
                    "mode": group["mode"],
                    "body": [group],
                    "style": "text",  # simulate \textstyle
                }
            return None
        elif type_ == "raw":
            token = self.parse_string_group("raw", optional)
            if token is not None:
                return {
                    "type": "raw",
                    "mode": "text",
                    "string": token.text,
                }
            return None
        elif type_ == "primitive":
            if optional:
                raise ParseError("A primitive argument cannot be optional")
            group = self.parse_group(name)
            if group is None:
                raise ParseError(f"Expected group as {name}", self.fetch())
            return group
        elif type_ in ("original", None):
            return self.parse_argument_group(optional)
        else:
            raise ParseError(f"Unknown group type as {name}", self.fetch())

    def consume_spaces(self) -> None:
        """Discard any space tokens, fetching the next non-space token."""
        while self.fetch().text == " ":
            self.consume()

    def parse_string_group(
        self, mode_name: str, optional: bool
    ) -> Optional[Token]:
        """Parses a group, returning the string formed by brace-enclosed tokens."""
        arg_token = self.gullet.scan_argument(optional)
        if arg_token is None:
            return None
        text = ""
        while (next_token := self.fetch()).text != "EOF":
            text += next_token.text
            self.consume()
        self.consume()  # consume the end of the argument
        arg_token.text = text
        return arg_token

    def parse_color_group(self, optional: bool) -> Optional[Dict[str, Any]]:
        """Parses a color description."""
        res = self.parse_string_group("color", optional)
        if res is None:
            return None
        import re
        match = re.match(
            r"^(#[a-f0-9]{3,4}|#[a-f0-9]{6}|#[a-f0-9]{8}|[a-f0-9]{6}|[a-z]+)$",
            res.text,
            re.IGNORECASE
        )
        if not match:
            raise ParseError(f"Invalid color: '{res.text}'", res)
        color = match.group(0)
        if re.match(r"^[0-9a-f]{6}$", color, re.IGNORECASE):
            # We allow a 6-digit HTML color spec without a leading "#"
            color = "#" + color
        return {
            "type": "color-token",
            "mode": self.mode,
            "color": color,
        }

    def parse_argument_group(self, optional: bool, mode: Optional[Mode] = None) -> Optional[Dict[str, Any]]:
        """Parses an argument with the mode specified."""
        arg_token = self.gullet.scan_argument(optional)
        if arg_token is None:
            return None
        outer_mode = self.mode
        if mode:  # Switch to specified mode
            self.switch_mode(mode)

        self.gullet.begin_group()
        expression = self.parse_expression(False, "EOF")
        self.expect("EOF")  # expect the end of the argument
        self.gullet.end_group()
        result = {
            "type": "ordgroup",
            "mode": self.mode,
            "loc": arg_token.loc,
            "body": expression,
        }

        if mode:  # Switch mode back
            self.switch_mode(outer_mode)
        return result

    def parse_group(
        self,
        name: str,
        break_on_token_text: Optional[str] = None,
    ) -> Optional[Any]:
        """Parses an ordinary group."""
        first_token = self.fetch()
        text = first_token.text

        result = None
        # Try to parse an open brace or \begingroup
        if text in ("{", "\\begingroup"):
            self.consume()
            group_end = "}" if text == "{" else "\\endgroup"

            self.gullet.begin_group()
            # If we get a brace, parse an expression
            expression = self.parse_expression(False, group_end)
            last_token = self.fetch()
            self.expect(group_end)  # Check that we got a matching closing brace
            self.gullet.end_group()
            result = {
                "type": "ordgroup",
                "mode": self.mode,
                "loc": SourceLocation.range(first_token, last_token),
                "body": expression,
                # A group formed by \begingroup...\endgroup is a semi-simple group
                "semisimple": text == "\\begingroup",
            }
        else:
            # If there exists a function with this name, parse the function
            # Otherwise, just return a nucleus
            result = self.parse_function(break_on_token_text, name) or self.parse_symbol()
            if result is None and text.startswith("\\") and text not in IMPLICIT_COMMANDS:
                if self.settings.throw_on_error:
                    raise ParseError(f"Undefined control sequence: {text}", first_token)
                result = self.format_unsupported_cmd(text)
                self.consume()

        return result

    def form_ligatures(self, group: List[Any]) -> None:
        """Form ligature-like combinations of characters for text mode."""
        n = len(group) - 1
        i = 0
        while i < n:
            a = group[i]
            v = a.get("text", "")
            if v == "-" and group[i + 1].get("text") == "-":
                if i + 1 < n and group[i + 2].get("text") == "-":
                    group[i:i+3] = [{
                        "type": "textord",
                        "mode": "text",
                        "loc": SourceLocation.range(a, group[i + 2]),
                        "text": "---",
                    }]
                    n -= 2
                else:
                    group[i:i+2] = [{
                        "type": "textord",
                        "mode": "text",
                        "loc": SourceLocation.range(a, group[i + 1]),
                        "text": "--",
                    }]
                    n -= 1
            i += 1
    
    def parse_regex_group(self, regex: "re.Pattern[str]", mode_name: str) -> Token:
        """Parse a regex-delimited group as a single token.

        This mirrors KaTeX's Parser.parseRegexGroup helper and is used by
        parse_size_group when scanning dimension-like arguments.
        """
        first_token = self.fetch()
        last_token = first_token
        text = ""
        while True:
            next_token = self.fetch()
            if next_token.text == "EOF" or not regex.match(text + next_token.text):
                break
            last_token = next_token
            text += last_token.text
            self.consume()
        if text == "":
            raise ParseError(f"Invalid {mode_name}: '{first_token.text}'", first_token)
        return first_token.range(last_token, text)

    def parse_symbol(self) -> Optional[Any]:
        """Parse a single symbol or \verb, including Unicode accents.

        This closely follows KaTeX's Parser.parseSymbol.
        """
        nucleus = self.fetch()
        text = nucleus.text

        # \verb handling: \verb<delim>...<delim>, optional leading *.
        if re.match(r"^\\verb[^a-zA-Z]", text):
            self.consume()
            arg = text[5:]
            star = arg.startswith("*")
            if star:
                arg = arg[1:]
            # tokenRegex guarantees matching first/last delimiter characters
            if len(arg) < 2 or arg[0] != arg[-1]:
                raise ParseError(
                    "\\verb assertion failed -- please report what input caused this bug",
                    nucleus,
                )
            body = arg[1:-1]
            return {
                "type": "verb",
                "mode": "text",
                "loc": nucleus.loc,
                "body": body,
                "star": star,
            }

        # At this point we should have a symbol, possibly with accents.
        # First expand any precomposed accented Unicode symbol.
        if text and text[0] in UNICODE_SYMBOLS and not SYMBOLS.get(self.mode, {}).get(text[0]):
            if self.settings.strict and self.mode == Mode.MATH:
                self.settings.report_nonstrict(
                    "unicodeTextInMathMode",
                    f"Accented Unicode text character \"{text[0]}\" used in math mode",
                    nucleus,
                )
            text = UNICODE_SYMBOLS[text[0]] + text[1:]

        # Strip off trailing combining diacritical marks (accents).
        match = COMBINING_DIACRITICAL_MARKS_END_REGEX.search(text)
        accents = ""
        if match:
            base = text[: match.start()]
            accents = text[match.start():]
            if base == "i":
                base = "\u0131"  # dotless i
            elif base == "j":
                base = "\u0237"  # dotless j
            text = base

        symbol: Optional[Dict[str, Any]]
        mode_symbols = SYMBOLS.get(self.mode.value if isinstance(self.mode, Mode) else self.mode, {})
        info = mode_symbols.get(text)

        if info is not None:
            group = info.get("group")
            loc = nucleus.loc
            if group in ATOMS:
                # Atom families (bin, rel, open, close, etc.) are represented
                # as a dedicated "atom" node with a family field.
                symbol = {
                    "type": "atom",
                    "mode": self.mode,
                    "loc": loc,
                    "family": group,
                    "text": text,
                }
            else:
                symbol = {
                    "type": group,
                    "mode": self.mode,
                    "loc": loc,
                    "text": text,
                }
        elif text and ord(text[0]) >= 0x80:
            codepoint = ord(text[0])
            if self.settings.strict and not supported_codepoint(codepoint):
                self.settings.report_nonstrict(
                    "unknownSymbol",
                    f"Unrecognized Unicode character \"{text[0]}\" ({codepoint})",
                    nucleus,
                )
            elif self.settings.strict and self.mode == Mode.MATH:
                self.settings.report_nonstrict(
                    "unicodeTextInMathMode",
                    f"Unicode text character \"{text[0]}\" used in math mode",
                    nucleus,
                )
            # Render all nonmathematical Unicode characters as if in text mode.
            symbol = {
                "type": "textord",
                "mode": "text",
                "loc": nucleus.loc,
                "text": text,
            }
        elif text and text != "EOF":
            # Basic ASCII characters (e.g. letters, digits) that are not
            # present in the symbol tables are treated as ordinary symbols.
            # This mirrors KaTeX's behaviour of producing mathord/textord
            # nodes for unknown characters instead of failing the parse.
            symbol = {
                "type": "mathord" if self.mode == Mode.MATH else "textord",
                "mode": self.mode,
                "loc": nucleus.loc,
                "text": text,
            }
        else:
            # Internal EOF sentinel (or truly empty text) – no symbol.
            return None

        self.consume()

        # Transform combining characters into explicit accent nodes.
        if accents:
            for accent in accents:
                mapping = ACCENTS.get(accent)
                if not mapping:
                    raise ParseError(f"Unknown accent '{accent}'", nucleus)
                command = mapping.get(self.mode.value if isinstance(self.mode, Mode) else str(self.mode)) or mapping.get("text")
                if not command:
                    raise ParseError(
                        f"Accent {accent} unsupported in {self.mode} mode",
                        nucleus,
                    )
                symbol = {
                    "type": "accent",
                    "mode": self.mode,
                    "loc": nucleus.loc,
                    "label": command,
                    "isStretchy": False,
                    "isShifty": True,
                    "base": symbol,
                }

        return symbol

    def parse_size_group(self, optional: bool) -> Optional[Any]:
        """Parse a size specification (magnitude + unit).

        This mirrors KaTeX's Parser.parseSizeGroup and returns a SizeParseNode
        with a Measurement-like payload.
        """
        self.gullet.consume_spaces()  # don't expand before parse_string_group

        if not optional and self.gullet.future().text != "{":
            token = self.parse_regex_group(
                re.compile(r"^[-+]? *(?:$|\d+|\d+\.\d*|\.\d*) *[a-z]{0,2} *$"),
                "size",
            )
        else:
            token = self.parse_string_group("size", optional)

        if token is None:
            return None

        text = token.text
        is_blank = False

        if not optional and text == "":
            # For mandatory size arguments like \above{} and \genfrac.
            text = "0pt"
            is_blank = True

        match = re.search(r"([-+]?) *(\d+(?:\.\d*)?|\.\d+) *([a-z]{2})", text)
        if not match:
            raise ParseError(f"Invalid size: '{text}'", token)

        number = float((match.group(1) or "") + match.group(2))
        unit = match.group(3)
        if not valid_unit(unit):
            raise ParseError(f"Invalid unit: '{unit}'", token)

        measurement = {"number": number, "unit": unit}
        return {
            "type": "size",
            "mode": self.mode,
            "value": measurement,
            "isBlank": is_blank,
        }

    def parse_url_group(self, optional: bool) -> Optional[Any]:
        """Parse a URL argument, handling escapes and catcodes.

        This ports KaTeX's Parser.parseUrlGroup, including temporary catcode
        changes for '%' and '~' to match hyperref-like behaviour.
        """
        # Treat '%' as active and '~' as an ordinary character while scanning.
        self.gullet.lexer.set_catcode("%", 13)
        self.gullet.lexer.set_catcode("~", 12)
        token = self.parse_string_group("url", optional)
        # Restore default catcodes.
        self.gullet.lexer.set_catcode("%", 14)
        self.gullet.lexer.set_catcode("~", 13)

        if token is None:
            return None

        # Unescape a limited set of characters inside URLs.
        url = re.sub(r"\\([#$%&~_^{}])", r"\1", token.text)

        return {
            "type": "url",
            "mode": self.mode,
            "loc": token.loc,
            "url": url,
        }


__all__ = ["Parser"]
