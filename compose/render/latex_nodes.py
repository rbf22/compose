# compose/render/latex_nodes.py
"""
Core LaTeX node parsing infrastructure.
Adapted from pylatexenc latexnodes module (MIT License).
"""

import re
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum


class LatexTokenType(Enum):
    """Types of LaTeX tokens."""
    TEXT = "text"
    COMMAND = "command"
    BRACE_OPEN = "brace_open"
    BRACE_CLOSE = "brace_close"
    SUBSCRIPT = "subscript"
    SUPERSCRIPT = "superscript"
    SYMBOL = "symbol"


class LatexToken:
    """A token in the LaTeX stream."""

    def __init__(self, tok_type: LatexTokenType, value: str, pos: int):
        self.tok_type = tok_type
        self.value = value
        self.pos = pos

    def __repr__(self):
        return f"LatexToken({self.tok_type.value}, '{self.value}', {self.pos})"


class ParsingState:
    """State for LaTeX parsing."""

    def __init__(self):
        self.math_mode = False
        self.in_group = False
        self.group_level = 0

    def clone(self):
        """Create a copy of this parsing state."""
        new_state = ParsingState()
        new_state.math_mode = self.math_mode
        new_state.in_group = self.in_group
        new_state.group_level = self.group_level
        return new_state


class LatexNode:
    """Base class for LaTeX nodes."""

    def __init__(self, parsing_state: ParsingState = None):
        self.parsing_state = parsing_state or ParsingState()

    def is_node_type(self, node_type_cls):
        """Check if this node is of the given type."""
        return isinstance(self, node_type_cls)


class LatexCharsNode(LatexNode):
    """Node representing plain text characters."""

    def __init__(self, chars: str, parsing_state: ParsingState = None):
        super().__init__(parsing_state)
        self.chars = chars

    def __repr__(self):
        return f"LatexCharsNode('{self.chars}')"


class LatexMacroNode(LatexNode):
    """Node representing a LaTeX macro."""

    def __init__(self, macroname: str, nodeargs: List = None, subscript=None, superscript=None, parsing_state: ParsingState = None):
        super().__init__(parsing_state)
        self.macroname = macroname
        self.nodeargs = nodeargs or []
        self.subscript = subscript
        self.superscript = superscript

    def __repr__(self):
        args = []
        if self.nodeargs:
            args.append(f'args={self.nodeargs}')
        if self.subscript:
            args.append(f'sub={self.subscript}')
        if self.superscript:
            args.append(f'sup={self.superscript}')
        args_str = ', '.join(args) if args else ''
        return f"LatexMacroNode('{self.macroname}'{', ' + args_str if args_str else ''})"


class LatexGroupNode(LatexNode):
    """Node representing a LaTeX group {...}."""

    def __init__(self, nodelist: List[LatexNode], parsing_state: ParsingState = None):
        super().__init__(parsing_state)
        self.nodelist = nodelist

    def __repr__(self):
        return f"LatexGroupNode({self.nodelist})"


class LatexMathNode(LatexNode):
    """Node representing math content."""

    def __init__(self, nodelist: List[LatexNode], displaytype: str = 'inline', parsing_state: ParsingState = None):
        super().__init__(parsing_state)
        self.nodelist = nodelist
        self.displaytype = displaytype

    def __repr__(self):
        return f"LatexMathNode({self.nodelist}, '{self.displaytype}')"


class LatexNodesCollector:
    """
    Collects and processes LaTeX nodes during parsing.
    """

    def __init__(self):
        self.nodes: List[LatexNode] = []
        self.current_parsing_state = ParsingState()

    def add_node(self, node: LatexNode):
        """Add a node to the collection."""
        self.nodes.append(node)

    def add_chars(self, chars: str):
        """Add character content."""
        if chars.strip():  # Only add non-whitespace
            self.add_node(LatexCharsNode(chars, self.current_parsing_state.clone()))

    def add_macro(self, macroname: str, args: List = None):
        """Add a macro node."""
        self.add_node(LatexMacroNode(macroname, args, self.current_parsing_state.clone()))

    def add_group(self, nodelist: List[LatexNode]):
        """Add a group node."""
        self.add_node(LatexGroupNode(nodelist, self.current_parsing_state.clone()))

    def get_nodelist(self) -> List[LatexNode]:
        """Get the collected nodes."""
        return self.nodes.copy()

    def reset(self):
        """Reset the collector."""
        self.nodes = []
        self.current_parsing_state = ParsingState()


class LatexTokenizer:
    """
    Tokenizes LaTeX input into tokens.
    Core of the LaTeX parsing infrastructure.
    """

    def __init__(self):
        # Tokenization patterns
        self.patterns = [
            (r'\\[a-zA-Z]+', LatexTokenType.COMMAND),  # Commands
            (r'\{', LatexTokenType.BRACE_OPEN),         # Open brace
            (r'\}', LatexTokenType.BRACE_CLOSE),        # Close brace
            (r'_', LatexTokenType.SUBSCRIPT),           # Subscript
            (r'\^', LatexTokenType.SUPERSCRIPT),        # Superscript
            (r'[^{}\\\s_^]+', LatexTokenType.TEXT),     # Text content (exclude ^ and _)
            (r'\s+', LatexTokenType.SYMBOL),            # Whitespace
        ]

    def tokenize(self, latex: str) -> List[LatexToken]:
        """
        Tokenize LaTeX string into tokens.

        Args:
            latex: LaTeX source string

        Returns:
            List of LatexToken objects
        """
        tokens = []
        position = 0

        while position < len(latex):
            matched = False

            for pattern, token_type in self.patterns:
                regex = re.compile(pattern)
                match = regex.match(latex, position)

                if match:
                    value = match.group(0)
                    # Skip pure whitespace tokens
                    if token_type != LatexTokenType.SYMBOL or value.strip():
                        tokens.append(LatexToken(token_type, value, position))
                    position = match.end()
                    matched = True
                    break

            if not matched:
                # Skip unknown characters
                position += 1

        return tokens


class LatexWalker:
    """
    Walks through LaTeX tokens and builds node tree.
    Core parsing engine.
    """

    def __init__(self, s: str):
        self.s = s
        self.tokenizer = LatexTokenizer()
        self.tokens = self.tokenizer.tokenize(s)
        self.pos = 0

    def parse_content(self) -> List[LatexNode]:
        """
        Parse the full LaTeX content into nodes.

        Returns:
            List of LatexNode objects
        """
        collector = LatexNodesCollector()
        self._parse_nodes(collector)
        return collector.get_nodelist()

    def _parse_nodes(self, collector: LatexNodesCollector):
        """Parse tokens into nodes."""
        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]

            if token.tok_type == LatexTokenType.TEXT:
                collector.add_chars(token.value)
                self.pos += 1

            elif token.tok_type == LatexTokenType.COMMAND:
                self._parse_macro(collector)
                self.pos += 1

            elif token.tok_type == LatexTokenType.SUPERSCRIPT:
                self._parse_script(collector, "superscript")
                self.pos += 1

            elif token.tok_type == LatexTokenType.SUBSCRIPT:
                self._parse_script(collector, "subscript")
                self.pos += 1

            elif token.tok_type == LatexTokenType.BRACE_OPEN:
                self._parse_group(collector)
                self.pos += 1

            elif token.tok_type == LatexTokenType.BRACE_CLOSE:
                # End of current group
                break

            else:
                self.pos += 1

    def _parse_script(self, collector: LatexNodesCollector, script_type: str):
        """Parse superscript or subscript."""
        # Look for content after the script marker
        if self.pos + 1 < len(self.tokens):
            next_token = self.tokens[self.pos + 1]

            if next_token.tok_type == LatexTokenType.BRACE_OPEN:
                # Braced content
                self.pos += 1  # Skip the opening brace
                script_content = self._parse_braced_content()
                collector.add_node(LatexMacroNode("", [], script_content if script_type == "subscript" else None, script_content if script_type == "superscript" else None))
            elif next_token.tok_type == LatexTokenType.TEXT and len(next_token.value) == 1:
                # Single character
                collector.add_node(LatexMacroNode("", [], next_token.value if script_type == "subscript" else None, next_token.value if script_type == "superscript" else None))
                self.pos += 1
        # If no valid content, just skip

    def _parse_macro(self, collector: LatexNodesCollector):
        """Parse a macro and its arguments, including sub/super scripts."""
        token = self.tokens[self.pos]
        macroname = token.value[1:]  # Remove backslash

        # Check for subscript/superscript after the macro
        subscript = None
        superscript = None

        # Look ahead for subscript
        if self.pos + 1 < len(self.tokens):
            next_token = self.tokens[self.pos + 1]
            if next_token.tok_type == LatexTokenType.SUBSCRIPT:
                self.pos += 1  # Consume the subscript token
                if self.pos + 1 < len(self.tokens):
                    script_token = self.tokens[self.pos + 1]
                    if script_token.tok_type == LatexTokenType.BRACE_OPEN:
                        self.pos += 1  # Consume the brace
                        subscript = self._parse_braced_content()
                    elif script_token.tok_type == LatexTokenType.TEXT:
                        # Single character subscript
                        subscript = script_token.value
                        self.pos += 1

        # Look ahead for superscript
        if self.pos + 1 < len(self.tokens):
            next_token = self.tokens[self.pos + 1]
            if next_token.tok_type == LatexTokenType.SUPERSCRIPT:
                self.pos += 1  # Consume the superscript token
                if self.pos + 1 < len(self.tokens):
                    script_token = self.tokens[self.pos + 1]
                    if script_token.tok_type == LatexTokenType.BRACE_OPEN:
                        self.pos += 1  # Consume the brace
                        superscript = self._parse_braced_content()
                    elif script_token.tok_type == LatexTokenType.TEXT:
                        # Single character superscript
                        superscript = script_token.value
                        self.pos += 1

        # Create macro node with scripts
        collector.add_node(LatexMacroNode(macroname, [], subscript, superscript, collector.current_parsing_state.clone()))

    def _parse_braced_content(self) -> str:
        """Parse content within braces and return as string."""
        content_parts = []
        brace_level = 1
        self.pos += 1  # Skip opening brace

        while self.pos < len(self.tokens) and brace_level > 0:
            token = self.tokens[self.pos]

            if token.tok_type == LatexTokenType.BRACE_OPEN:
                brace_level += 1
                content_parts.append(token.value)
            elif token.tok_type == LatexTokenType.BRACE_CLOSE:
                brace_level -= 1
                if brace_level > 0:  # Don't include the final closing brace
                    content_parts.append(token.value)
            else:
                content_parts.append(token.value)

            self.pos += 1

        return ''.join(content_parts)

    def _parse_group(self, collector: LatexNodesCollector):
        """Parse a braced group."""
        # Skip the opening brace
        self.pos += 1

        # Parse content until closing brace
        group_collector = LatexNodesCollector()
        self._parse_nodes(group_collector)

        # The _parse_nodes should stop at closing brace
        collector.add_group(group_collector.get_nodelist())


def parse_latex_to_nodes(latex: str) -> List[LatexNode]:
    """
    Convenience function to parse LaTeX to nodes.

    Args:
        latex: LaTeX source string

    Returns:
        List of LatexNode objects
    """
    walker = LatexWalker(latex)
    return walker.parse_content()


# Test the parsing infrastructure
def test_latex_parsing():
    """Test the LaTeX parsing infrastructure."""
    test_cases = [
        "Hello world",
        r"\int x dx",
        r"x^{a+b}",
        r"{grouped text}",
        r"\alpha + \beta",
    ]

    print("Testing LaTeX Node Parsing:")
    print("=" * 40)

    for latex in test_cases:
        print(f"\nLaTeX: {latex}")
        try:
            nodes = parse_latex_to_nodes(latex)
            print(f"Nodes: {[str(n) for n in nodes]}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    test_latex_parsing()
