# compose/render/latex_tokenizer.py
"""
Simple LaTeX tokenizer for parsing mathematical expressions.
Replaces regex patterns with proper token-based parsing for subscripts/superscripts.
"""

import re
from typing import List, Tuple, Optional
from enum import Enum


class TokenType(Enum):
    TEXT = "text"
    SUBSCRIPT = "subscript"
    SUPERSCRIPT = "superscript"
    LBRACE = "lbrace"
    RBRACE = "rbrace"
    COMMAND = "command"
    SYMBOL = "symbol"


class Token:
    """A token in the LaTeX stream."""
    def __init__(self, type_: TokenType, value: str, position: int):
        self.type = type_
        self.value = value
        self.position = position

    def __repr__(self):
        return f"Token({self.type.value}, '{self.value}', {self.position})"


class LatexTokenizer:
    """
    Simple tokenizer for LaTeX mathematical expressions.
    Focuses on parsing subscripts, superscripts, and braces.
    """

    def __init__(self):
        # Patterns for tokenization
        self.patterns = [
            (r'\\[a-zA-Z]+', TokenType.COMMAND),  # LaTeX commands
            (r'_', TokenType.SUBSCRIPT),          # Subscript marker
            (r'\^', TokenType.SUPERSCRIPT),       # Superscript marker
            (r'\{', TokenType.LBRACE),            # Left brace
            (r'\}', TokenType.RBRACE),            # Right brace
            (r'[^{}^_\\{}]+', TokenType.TEXT),    # Regular text
        ]

    def tokenize(self, latex: str) -> List[Token]:
        """
        Tokenize LaTeX string into tokens.

        Args:
            latex: LaTeX mathematical expression

        Returns:
            List of Token objects
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
                    tokens.append(Token(token_type, value, position))
                    position = match.end()
                    matched = True
                    break

            if not matched:
                # Skip unknown characters
                position += 1

        return tokens

    def parse_expression(self, latex: str) -> 'MathExpression':
        """
        Parse LaTeX expression into structured representation.

        Args:
            latex: LaTeX mathematical expression

        Returns:
            MathExpression object
        """
        tokens = self.tokenize(latex)
        return self._parse_tokens(tokens)

    def _parse_tokens(self, tokens: List[Token]) -> 'MathExpression':
        """Parse tokens into MathExpression tree."""
        if not tokens:
            return MathExpression([])

        result = MathExpression([])
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.type in (TokenType.SUBSCRIPT, TokenType.SUPERSCRIPT):
                # Look for braced content or single character
                script_type = "sub" if token.type == TokenType.SUBSCRIPT else "super"

                if i + 1 < len(tokens):
                    next_token = tokens[i + 1]
                    if next_token.type == TokenType.LBRACE:
                        # Find matching closing brace
                        brace_content, end_pos = self._find_matching_brace(tokens, i + 2)
                        if brace_content:
                            result.add_script(script_type, brace_content)
                            i = end_pos
                        else:
                            # Malformed - skip
                            i += 1
                    else:
                        # Single character script
                        result.add_script(script_type, [next_token])
                        i += 2
                else:
                    i += 1
            else:
                result.add_text(token)
                i += 1

        return result

    def _find_matching_brace(self, tokens: List[Token], start_pos: int) -> Tuple[Optional[List[Token]], int]:
        """Find content between matching braces."""
        brace_level = 1
        content = []
        pos = start_pos

        while pos < len(tokens) and brace_level > 0:
            token = tokens[pos]

            if token.type == TokenType.LBRACE:
                brace_level += 1
            elif token.type == TokenType.RBRACE:
                brace_level -= 1
                if brace_level == 0:
                    return content, pos + 1
            else:
                content.append(token)

            pos += 1

        return None, pos  # Malformed - no matching brace


class MathExpression:
    """Structured representation of mathematical expression."""

    def __init__(self, elements: List):
        self.elements = elements  # List of tokens and scripts

    def add_text(self, token: Token):
        """Add regular text token."""
        self.elements.append({"type": "text", "token": token})

    def add_script(self, script_type: str, content):
        """Add subscript or superscript."""
        self.elements.append({
            "type": script_type,
            "content": content
        })

    def to_svg_text(self, font_size: int) -> str:
        """
        Convert to SVG text with proper formatting.

        Args:
            font_size: Base font size for the text

        Returns:
            SVG text element string
        """
        parts = []

        for element in self.elements:
            if element["type"] == "text":
                token = element["token"]
                # Convert LaTeX commands to Unicode
                from . import latex_specs
                text = latex_specs.latex_to_unicode(token.value)
                parts.append(text)

            elif element["type"] in ("sub", "super"):
                baseline_shift = "sub" if element["type"] == "sub" else "super"
                script_size = font_size - 4

                # Convert content tokens to text
                content_parts = []
                for token in element["content"]:
                    from . import latex_specs
                    content_parts.append(latex_specs.latex_to_unicode(token.value))

                content_text = "".join(content_parts)
                parts.append(f'<tspan baseline-shift="{baseline_shift}" font-size="{script_size}px">{content_text}</tspan>')

        return "".join(parts)


def tokenize_latex(latex: str) -> List[Token]:
    """
    Convenience function to tokenize LaTeX expression.

    Args:
        latex: LaTeX mathematical expression

    Returns:
        List of Token objects
    """
    tokenizer = LatexTokenizer()
    return tokenizer.tokenize(latex)


def parse_latex_expression(latex: str) -> MathExpression:
    """
    Convenience function to parse LaTeX expression.

    Args:
        latex: LaTeX mathematical expression

    Returns:
        MathExpression object
    """
    tokenizer = LatexTokenizer()
    return tokenizer.parse_expression(latex)


# Test functions
def test_tokenizer():
    """Test the tokenizer with various expressions."""
    test_cases = [
        "x^2",
        "x_{sub}",
        "∫_{-∞}^{∞} f(x) dx",
        "\\alpha + \\beta",
        "x^{2n}",
        "a_{i,j}",
    ]

    tokenizer = LatexTokenizer()

    print("Testing LaTeX Tokenizer:")
    print("=" * 50)

    for latex in test_cases:
        print(f"\nLaTeX: {latex}")
        tokens = tokenizer.tokenize(latex)
        print(f"Tokens: {[str(t) for t in tokens]}")

        expr = tokenizer.parse_expression(latex)
        svg_text = expr.to_svg_text(16)
        print(f"SVG: {svg_text}")


if __name__ == "__main__":
    test_tokenizer()
