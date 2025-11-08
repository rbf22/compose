# compose/render/mermaid_parser.py
"""
Robust Mermaid diagram parser using tokenization instead of regex.
Provides better error handling and maintainability than regex-based parsing.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class TokenType(Enum):
    """Token types for Mermaid parsing"""
    GRAPH = "graph"
    DIRECTION = "direction"
    IDENTIFIER = "identifier"
    LBRACKET = "lbracket"
    RBRACKET = "rbracket"
    LPAREN = "lparen"
    RPAREN = "rparen"
    LBRACE = "lbrace"
    RBRACE = "rbrace"
    ARROW = "arrow"
    DASH = "dash"
    PIPE = "pipe"
    STRING = "string"
    EOF = "eof"


class Token:
    """Token representation"""
    def __init__(self, type_: TokenType, value: str, position: int = 0):
        self.type = type_
        self.value = value
        self.position = position

    def __repr__(self):
        return f"Token({self.type.value}, {repr(self.value)}, {self.position})"


class MermaidTokenizer:
    """Tokenizer for Mermaid diagram syntax"""

    def __init__(self, input_text: str):
        self.input = input_text
        self.position = 0
        self.current_char = self.input[0] if self.input else None

    def tokenize(self) -> List[Token]:
        """Tokenize the input into a list of tokens"""
        tokens = []

        while self.current_char is not None:
            if self.current_char.isspace():
                self.advance()
                continue
            elif self.current_char.isalpha():
                tokens.append(self.identifier())
            elif self.current_char == '[':
                tokens.append(Token(TokenType.LBRACKET, '[', self.position))
                self.advance()
            elif self.current_char == ']':
                tokens.append(Token(TokenType.RBRACKET, ']', self.position))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TokenType.LPAREN, '(', self.position))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TokenType.RPAREN, ')', self.position))
                self.advance()
            elif self.current_char == '{':
                tokens.append(Token(TokenType.LBRACE, '{', self.position))
                self.advance()
            elif self.current_char == '}':
                tokens.append(Token(TokenType.RBRACE, '}', self.position))
                self.advance()
            elif self.current_char == '-':
                tokens.append(self.arrow_or_dash())
            elif self.current_char == '|':
                tokens.append(Token(TokenType.PIPE, '|', self.position))
                self.advance()
            elif self.current_char == '"':
                tokens.append(self.string())
            else:
                # Skip unknown characters or handle them
                self.advance()

        tokens.append(Token(TokenType.EOF, "", self.position))
        return tokens

    def advance(self):
        """Move to the next character"""
        self.position += 1
        if self.position >= len(self.input):
            self.current_char = None
        else:
            self.current_char = self.input[self.position]

    def peek(self) -> Optional[str]:
        """Look at the next character without advancing"""
        peek_pos = self.position + 1
        if peek_pos >= len(self.input):
            return None
        return self.input[peek_pos]

    def identifier(self) -> Token:
        """Parse an identifier (letters, numbers, underscores)"""
        start_pos = self.position
        result = ""

        while (self.current_char is not None and
               (self.current_char.isalnum() or self.current_char == '_')):
            result += self.current_char
            self.advance()

        # Check for keywords
        if result.lower() == "graph":
            return Token(TokenType.GRAPH, result, start_pos)
        elif result.upper() in ["TD", "TB", "BT", "RL", "LR"]:
            return Token(TokenType.DIRECTION, result, start_pos)

        return Token(TokenType.IDENTIFIER, result, start_pos)

    def arrow_or_dash(self) -> Token:
        """Parse arrow (-->) or dash (-)"""
        start_pos = self.position
        result = self.current_char
        self.advance()

        # Check for arrow pattern -->
        if self.current_char == '-' and self.peek() == '>':
            result += self.current_char
            self.advance()
            result += self.current_char
            self.advance()
            return Token(TokenType.ARROW, result, start_pos)

        return Token(TokenType.DASH, result, start_pos)

    def string(self) -> Token:
        """Parse a quoted string"""
        start_pos = self.position
        result = ""
        self.advance()  # Skip opening quote

        while self.current_char is not None and self.current_char != '"':
            result += self.current_char
            self.advance()

        if self.current_char == '"':
            self.advance()  # Skip closing quote

        return Token(TokenType.STRING, result, start_pos)


class MermaidParser:
    """Parser for Mermaid flowchart syntax using tokenized input"""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0
        self.current_token = self.tokens[0] if self.tokens else Token(TokenType.EOF, "")

    def parse(self) -> Tuple[Dict[str, Dict], List[Dict]]:
        """
        Parse tokens into nodes and connections.

        Returns:
            Tuple of (nodes_dict, connections_list)
        """
        nodes = {}
        connections = []

        # Find all node definitions first
        for i, token in enumerate(self.tokens):
            if (token.type == TokenType.IDENTIFIER and
                i + 1 < len(self.tokens) and
                self.tokens[i + 1].type in [TokenType.LBRACKET, TokenType.LPAREN, TokenType.LBRACE]):
                # This is a node definition
                node_id = token.value
                bracket_type = self.tokens[i + 1].type
                node_text = token.value + self.tokens[i + 1].value  # Include the opening bracket
                
                # Find the matching closing bracket
                bracket_count = 0
                label_tokens = []
                j = i + 2  # Skip ID and opening bracket

                closing_types = {
                    TokenType.LBRACKET: TokenType.RBRACKET,
                    TokenType.LPAREN: TokenType.RPAREN,
                    TokenType.LBRACE: TokenType.RBRACE
                }
                closing_type = closing_types[bracket_type]

                while j < len(self.tokens):
                    t = self.tokens[j]
                    if t.type in [TokenType.LBRACKET, TokenType.LPAREN, TokenType.LBRACE]:
                        bracket_count += 1
                    elif t.type == closing_type:
                        if bracket_count == 0:
                            node_text += t.value  # Include the closing bracket
                            break
                        bracket_count -= 1
                    else:
                        label_tokens.append(t.value)
                    j += 1

                label = ' '.join(label_tokens).strip()

                # Determine shape from the bracket type
                if bracket_type == TokenType.LPAREN:
                    shape = 'round'
                elif bracket_type == TokenType.LBRACE:
                    shape = 'hexagon'
                else:
                    shape = 'rectangle'

                nodes[node_id] = {
                    'id': node_id,
                    'label': label,
                    'shape': shape
                }

        # Find all connections - simplified approach
        # Look for arrows and find adjacent node IDs
        for i, token in enumerate(self.tokens):
            if token.type == TokenType.ARROW:
                # Find from node (immediately before arrow, skipping brackets)
                from_id = None
                j = i - 1
                while j >= 0:
                    if self.tokens[j].type == TokenType.IDENTIFIER:
                        # Check if this is followed by [ (node ID) or preceded by ] (end of label)
                        if (j + 1 < len(self.tokens) and self.tokens[j + 1].type == TokenType.LBRACKET) or \
                           (j > 0 and self.tokens[j - 1].type == TokenType.RBRACKET):
                            from_id = self.tokens[j].value
                            break
                    j -= 1

                # Find to node (immediately after arrow, skipping brackets)
                to_id = None
                j = i + 1
                while j < len(self.tokens):
                    if self.tokens[j].type == TokenType.IDENTIFIER:
                        # Check if this is followed by [ (node ID)
                        if j + 1 < len(self.tokens) and self.tokens[j + 1].type == TokenType.LBRACKET:
                            to_id = self.tokens[j].value
                            break
                    j += 1

                if from_id and to_id and from_id in nodes and to_id in nodes:
                    connections.append({
                        'from': from_id,
                        'to': to_id,
                        'label': '',
                        'directed': True
                    })

        return nodes, connections

    def parse_statement(self, nodes: Dict[str, Dict], connections: List[Dict]):
        """Parse a single statement (node definition or connection)"""
        # Try to parse as a connection first (most common)
        if self.try_parse_connection(nodes, connections):
            return

        # Try to parse as a node definition
        if self.try_parse_node_definition(nodes):
            return

        # Skip unknown tokens
        self.advance()

    def try_parse_connection(self, nodes: Dict[str, Dict], connections: List[Dict]) -> bool:
        """Try to parse a connection statement"""
        start_pos = self.position

        # Parse from node (identifier)
        from_id = None
        if self.current_token.type == TokenType.IDENTIFIER:
            from_id = self.current_token.value
            self.advance()

        # Look for arrow
        if self.current_token.type == TokenType.ARROW:
            self.advance()

            # Parse to node
            to_id = None
            if self.current_token.type == TokenType.IDENTIFIER:
                to_id = self.current_token.value
                self.advance()

                # Check if node definition follows (inline node definition)
                if self.current_token.type == TokenType.LBRACKET:
                    # Parse the inline node definition
                    self.try_parse_node_definition_for_id(nodes, to_id)

            if from_id and to_id:
                connections.append({
                    'from': from_id,
                    'to': to_id,
                    'label': '',
                    'directed': True
                })
                return True

        # Reset position if parsing failed
        self.position = start_pos
        self.current_token = self.tokens[self.position]
        return False

    def try_parse_node_definition_for_id(self, nodes: Dict[str, Dict], expected_id: str) -> bool:
        """Parse a node definition for a specific ID (used for inline definitions)"""
        if self.current_token.type == TokenType.LBRACKET:
            self.consume(TokenType.LBRACKET)

            # Parse label until closing bracket
            label_parts = []
            while self.current_token.type not in [TokenType.RBRACKET, TokenType.EOF]:
                if self.current_token.type == TokenType.STRING:
                    label_parts.append(self.current_token.value)
                elif self.current_token.type == TokenType.IDENTIFIER:
                    label_parts.append(self.current_token.value)
                else:
                    label_parts.append(self.current_token.value)
                self.advance()

            if self.current_token.type == TokenType.RBRACKET:
                self.consume(TokenType.RBRACKET)

            label = ' '.join(label_parts)

            # Determine shape
            shape = 'rectangle'  # Default
            if '(' in label or ')' in label:
                shape = 'round'
            elif '{' in label or '}' in label:
                shape = 'hexagon'

            nodes[expected_id] = {
                'id': expected_id,
                'label': label,
                'shape': shape
            }
            return True

        return False

    def try_parse_node_definition(self, nodes: Dict[str, Dict]) -> bool:
        """Try to parse a node definition like A[Label]"""
        if self.current_token.type != TokenType.IDENTIFIER:
            return False

        node_id = self.current_token.value
        self.consume(TokenType.IDENTIFIER)

        if self.current_token.type == TokenType.LBRACKET:
            self.consume(TokenType.LBRACKET)

            # Parse label until closing bracket
            label_parts = []
            while self.current_token.type not in [TokenType.RBRACKET, TokenType.EOF]:
                if self.current_token.type == TokenType.STRING:
                    label_parts.append(self.current_token.value)
                elif self.current_token.type == TokenType.IDENTIFIER:
                    label_parts.append(self.current_token.value)
                else:
                    label_parts.append(self.current_token.value)
                self.advance()

            if self.current_token.type == TokenType.RBRACKET:
                self.consume(TokenType.RBRACKET)

            label = ' '.join(label_parts)

            # Determine shape
            shape = 'rectangle'  # Default
            if label_parts and ('(' in label or ')' in label):
                shape = 'round'
            elif label_parts and ('{' in label or '}' in label):
                shape = 'hexagon'

            nodes[node_id] = {
                'id': node_id,
                'label': label,
                'shape': shape
            }
            return True

        return False

    def consume(self, token_type: TokenType) -> Token:
        """Consume a token of the expected type"""
        if self.current_token.type == token_type:
            token = self.current_token
            self.advance()
            return token
        else:
            raise ValueError(f"Expected {token_type.value}, got {self.current_token.type.value}")

    def advance(self):
        """Move to the next token"""
        self.position += 1
        if self.position >= len(self.tokens):
            self.current_token = Token(TokenType.EOF, "")
        else:
            self.current_token = self.tokens[self.position]

    def peek(self) -> Token:
        """Look at the next token without advancing"""
        peek_pos = self.position + 1
        if peek_pos >= len(self.tokens):
            return Token(TokenType.EOF, "")
        return self.tokens[peek_pos]


def parse_mermaid_flowchart(code: str) -> Tuple[Dict[str, Dict], List[Dict]]:
    """
    Parse Mermaid flowchart code into nodes and connections.

    Args:
        code: Mermaid flowchart code as string

    Returns:
        Tuple of (nodes_dict, connections_list)
    """
    # Tokenize
    tokenizer = MermaidTokenizer(code)
    tokens = tokenizer.tokenize()

    # Parse
    parser = MermaidParser(tokens)
    nodes, connections = parser.parse()

    return nodes, connections


# Test the new parser
def test_tokenizer():
    """Test the tokenizer"""
    code = 'graph TD A[Start] --> B[Process] B --> C[End]'
    tokenizer = MermaidTokenizer(code)
    tokens = tokenizer.tokenize()

    print("Tokens:")
    for token in tokens:
        print(f"  {token}")

    print("\nParsing:")
    nodes, connections = parse_mermaid_flowchart(code)
    print(f"Nodes: {nodes}")
    print(f"Connections: {connections}")


if __name__ == "__main__":
    test_tokenizer()
