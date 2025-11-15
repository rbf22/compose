"""Python port of KaTeX's Parser.js - LaTeX expression parsing."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .macro_expander import MacroExpander
from .parse_error import ParseError
from .settings import Settings
from .source_location import SourceLocation
from .token import Token
from .types import ArgType, BreakToken, Mode
from .unicode_sup_or_sub import UNICODE_SUB_REGEX, U_SUBS_AND_SUPS

# Placeholder imports - will be filled in
try:
    from .functions import functions as FUNCTIONS
except ImportError:
    FUNCTIONS = {}

try:
    from .symbols_data import symbols as SYMBOLS
except ImportError:
    SYMBOLS = {}

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
        self.mode: Mode = "math"
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
            self.gullet.macros["\\color"] = "\\textcolor"

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
        break_on_token_text: Optional[BreakToken] = None,
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
            if break_on_infix and FUNCTIONS.get(lex.text, {}).get("infix"):
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
        """Rewrites infix operators like \over with commands like \frac."""
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

    def parse_atom(self, break_on_token_text: Optional[BreakToken] = None) -> Optional[Any]:
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
        break_on_token_text: Optional[BreakToken] = None,
        name: Optional[str] = None,
    ) -> Optional[Any]:
        """Parses an entire function, including its base and all arguments."""
        token = self.fetch()
        func = token.text
        func_data = FUNCTIONS.get(func)
        if not func_data:
            return None
        self.consume()  # consume command token

        if name and name != "atom" and not func_data.get("allowedInArgument"):
            raise ParseError(
                f"Got function '{func}' with no arguments" + (f" as {name}" if name else ""),
                token
            )
        elif self.mode == "text" and not func_data.get("allowedInText"):
            raise ParseError(f"Can't use function '{func}' in text mode", token)
        elif self.mode == "math" and func_data.get("allowedInMath") is False:
            raise ParseError(f"Can't use function '{func}' in math mode", token)

        args, opt_args = self.parse_arguments(func, func_data)
        return self.call_function(func, args, opt_args, token, break_on_token_text)

    def call_function(
        self,
        name: str,
        args: List[Any],
        opt_args: List[Optional[Any]],
        token: Optional[Token] = None,
        break_on_token_text: Optional[BreakToken] = None,
    ) -> Any:
        """Call a function handler with suitable context."""
        context = {
            "funcName": name,
            "parser": self,
            "token": token,
            "breakOnTokenText": break_on_token_text,
        }
        func = FUNCTIONS.get(name)
        if func and func.get("handler"):
            return func["handler"](context, args, opt_args)
        else:
            raise ParseError(f"No function handler for {name}")

    def parse_arguments(
        self, func: str, func_data: Dict[str, Any]
    ) -> tuple[List[Any], List[Optional[Any]]]:
        """Parses the arguments of a function or environment."""
        total_args = func_data.get("numArgs", 0) + func_data.get("numOptionalArgs", 0)
        if total_args == 0:
            return [], []

        args = []
        opt_args = []

        for i in range(total_args):
            arg_types = func_data.get("argTypes", [])
            arg_type = arg_types[i] if i < len(arg_types) else None
            is_optional = i < func_data.get("numOptionalArgs", 0)

            if (
                func_data.get("primitive") and arg_type is None
                or (func_data.get("type") == "sqrt" and i == 1 and opt_args and opt_args[0] is None)
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
        type_: Optional[ArgType],
        optional: bool,
    ) -> Optional[Any]:
        """Parses a group when the mode is changing."""
        if type_ == "color":
            return self.parse_color_group(optional)
        elif type_ == "size":
            return self.parse_size_group(optional)
        elif type_ == "url":
            return self.parse_url_group(optional)
        elif type_ in ("math", "text"):
            return self.parse_argument_group(optional, type_)
        elif type_ == "hbox":
            # hbox argument type wraps the argument in the equivalent of \hbox
            group = self.parse_argument_group(optional, "text")
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
        self, mode_name: ArgType, optional: bool
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
        break_on_token_text: Optional[BreakToken] = None,
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

    # Placeholder methods - will need to be implemented
    def parse_symbol(self) -> Optional[Any]:
        """Parse a symbol."""
        return None

    def parse_size_group(self, optional: bool) -> Optional[Any]:
        """Parse a size specification."""
        return None

    def parse_url_group(self, optional: bool) -> Optional[Any]:
        """Parse an URL."""
        return None


__all__ = ["Parser"]
