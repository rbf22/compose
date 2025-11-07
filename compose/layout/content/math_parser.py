# compose/layout/content/math_parser.py
"""
Mathematical expression parser for TeX-style math notation.

This module parses LaTeX-style mathematical expressions into
the internal box representation for layout and rendering.
"""

import re
from typing import List, Optional, Tuple, Union
from ..box_model import MathBox, BoxType, create_atom_box, create_operator_box
from ..font_metrics import default_math_font


class MathExpressionParser:
    """
    Parser for mathematical expressions in LaTeX syntax.
    
    This parser converts LaTeX-style math notation into the internal
    box representation used by the layout engine.
    """
    
    def __init__(self):
        self.font_metrics = default_math_font
        self._setup_symbol_tables()
    
    def _setup_symbol_tables(self):
        """Initialize symbol lookup tables."""
        # Greek letters
        self.greek_letters = {
            'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ',
            'epsilon': 'ε', 'zeta': 'ζ', 'eta': 'η', 'theta': 'θ',
            'iota': 'ι', 'kappa': 'κ', 'lambda': 'λ', 'mu': 'μ',
            'nu': 'ν', 'xi': 'ξ', 'pi': 'π', 'rho': 'ρ',
            'sigma': 'σ', 'tau': 'τ', 'upsilon': 'υ', 'phi': 'φ',
            'chi': 'χ', 'psi': 'ψ', 'omega': 'ω',
            # Uppercase
            'Alpha': 'Α', 'Beta': 'Β', 'Gamma': 'Γ', 'Delta': 'Δ',
            'Epsilon': 'Ε', 'Zeta': 'Ζ', 'Eta': 'Η', 'Theta': 'Θ',
            'Iota': 'Ι', 'Kappa': 'Κ', 'Lambda': 'Λ', 'Mu': 'Μ',
            'Nu': 'Ν', 'Xi': 'Ξ', 'Pi': 'Π', 'Rho': 'Ρ',
            'Sigma': 'Σ', 'Tau': 'Τ', 'Upsilon': 'Υ', 'Phi': 'Φ',
            'Chi': 'Χ', 'Psi': 'Ψ', 'Omega': 'Ω'
        }
        
        # Mathematical operators
        self.operators = {
            'pm': '±', 'mp': '∓', 'times': '×', 'div': '÷',
            'cdot': '·', 'ast': '∗', 'star': '⋆', 'circ': '∘',
            'bullet': '•', 'cap': '∩', 'cup': '∪', 'sqcap': '⊓',
            'sqcup': '⊔', 'vee': '∨', 'wedge': '∧', 'setminus': '∖',
            'wr': '≀', 'diamond': '⋄', 'bigtriangleup': '△',
            'bigtriangledown': '▽', 'triangleleft': '◁', 'triangleright': '▷',
            'lhd': '⊲', 'rhd': '⊳', 'unlhd': '⊴', 'unrhd': '⊵',
            'oplus': '⊕', 'ominus': '⊖', 'otimes': '⊗', 'oslash': '⊘',
            'odot': '⊙', 'bigcirc': '◯', 'dagger': '†', 'ddagger': '‡',
            'amalg': '⨿'
        }
        
        # Relations
        self.relations = {
            'leq': '≤', 'le': '≤', 'geq': '≥', 'ge': '≥',
            'equiv': '≡', 'models': '⊨', 'prec': '≺', 'succ': '≻',
            'sim': '∼', 'perp': '⊥', 'preceq': '⪯', 'succeq': '⪰',
            'simeq': '≃', 'mid': '∣', 'll': '≪', 'gg': '≫',
            'asymp': '≍', 'parallel': '∥', 'subset': '⊂', 'supset': '⊃',
            'approx': '≈', 'bowtie': '⋈', 'subseteq': '⊆', 'supseteq': '⊇',
            'cong': '≅', 'Join': '⋈', 'sqsubset': '⊏', 'sqsupset': '⊐',
            'neq': '≠', 'smile': '⌣', 'sqsubseteq': '⊑', 'sqsupseteq': '⊒',
            'doteq': '≐', 'frown': '⌢', 'in': '∈', 'ni': '∋',
            'propto': '∝', 'vdash': '⊢', 'dashv': '⊣'
        }
        
        # Large operators
        self.large_operators = {
            'sum': '∑', 'prod': '∏', 'coprod': '∐', 'int': '∫',
            'oint': '∮', 'iint': '∬', 'iiint': '∭', 'iiiint': '⨌',
            'bigcap': '⋂', 'bigcup': '⋃', 'bigsqcup': '⊔',
            'bigvee': '⋁', 'bigwedge': '⋀', 'bigodot': '⨀',
            'bigotimes': '⨂', 'bigoplus': '⨁', 'biguplus': '⨄'
        }
        
        # Arrows
        self.arrows = {
            'leftarrow': '←', 'gets': '←', 'rightarrow': '→', 'to': '→',
            'leftrightarrow': '↔', 'uparrow': '↑', 'downarrow': '↓',
            'updownarrow': '↕', 'Leftarrow': '⇐', 'Rightarrow': '⇒',
            'Leftrightarrow': '⇔', 'Uparrow': '⇑', 'Downarrow': '⇓',
            'Updownarrow': '⇕', 'mapsto': '↦', 'longmapsto': '⟼',
            'hookleftarrow': '↩', 'hookrightarrow': '↪',
            'leftharpoonup': '↼', 'rightharpoonup': '⇀',
            'leftharpoondown': '↽', 'rightharpoondown': '⇁',
            'rightleftharpoons': '⇌', 'leadsto': '⇝'
        }
        
        # Delimiters
        self.delimiters = {
            'langle': '⟨', 'rangle': '⟩', 'lceil': '⌈', 'rceil': '⌉',
            'lfloor': '⌊', 'rfloor': '⌋', 'lbrace': '{', 'rbrace': '}',
            'lbrack': '[', 'rbrack': ']', 'vert': '|', 'Vert': '‖'
        }
        
        # Miscellaneous symbols
        self.misc_symbols = {
            'infty': '∞', 'partial': '∂', 'nabla': '∇', 'Box': '□',
            'Diamond': '◊', 'triangle': '△', 'clubsuit': '♣',
            'diamondsuit': '♢', 'heartsuit': '♡', 'spadesuit': '♠',
            'neg': '¬', 'flat': '♭', 'natural': '♮', 'sharp': '♯',
            'wp': '℘', 'Re': 'ℜ', 'Im': 'ℑ', 'mho': '℧',
            'prime': '′', 'emptyset': '∅', 'exists': '∃', 'forall': '∀',
            'complement': '∁', 'ell': 'ℓ', 'hbar': 'ℏ', 'imath': 'ı',
            'jmath': 'ȷ', 'aleph': 'ℵ', 'beth': 'ℶ', 'gimel': 'ℷ'
        }
    
    def parse_expression(self, expression: str) -> MathBox:
        """
        Parse a complete mathematical expression.
        
        This is the main entry point for parsing LaTeX math expressions.
        """
        # Clean up the expression
        expr = expression.strip()
        if expr.startswith('$$') and expr.endswith('$$'):
            expr = expr[2:-2].strip()
        elif expr.startswith('$') and expr.endswith('$'):
            expr = expr[1:-1].strip()
        
        # Tokenize the expression
        tokens = self._tokenize(expr)
        
        # Parse tokens into boxes
        boxes = self._parse_tokens(tokens)
        
        # If single box, return it directly
        if len(boxes) == 1:
            return boxes[0]
        
        # Otherwise, create composite box
        from ..engines.math_engine import MathLayoutEngine
        engine = MathLayoutEngine()
        return engine.layout_expression(boxes)
    
    def parse_atom(self, atom: str) -> MathBox:
        """Parse a single mathematical atom (character, symbol, etc.)."""
        # Check if it's a command
        if atom.startswith('\\'):
            return self._parse_command(atom[1:])
        
        # Single character
        if len(atom) == 1:
            if atom.isalpha():
                # Variables are typically italic
                return create_atom_box(atom, font_size=10.0)
            elif atom.isdigit():
                return create_atom_box(atom, font_size=10.0)
            elif atom in '+-=<>':
                return create_operator_box(atom, font_size=10.0)
            else:
                return create_atom_box(atom, font_size=10.0)
        
        # Multi-character: treat as sequence
        boxes = [self.parse_atom(char) for char in atom]
        from ..engines.math_engine import MathLayoutEngine
        engine = MathLayoutEngine()
        return engine.layout_expression(boxes)
    
    def _tokenize(self, expression: str) -> List[str]:
        """
        Tokenize a mathematical expression into components.
        
        This handles commands, braces, superscripts, subscripts, etc.
        """
        tokens = []
        i = 0
        
        while i < len(expression):
            char = expression[i]
            
            if char == '\\':
                # Command
                i += 1
                cmd_start = i
                while i < len(expression) and expression[i].isalpha():
                    i += 1
                command = expression[cmd_start:i]
                tokens.append('\\' + command)
            
            elif char == '{':
                # Braced group
                brace_count = 1
                i += 1
                group_start = i
                while i < len(expression) and brace_count > 0:
                    if expression[i] == '{':
                        brace_count += 1
                    elif expression[i] == '}':
                        brace_count -= 1
                    i += 1
                group_content = expression[group_start:i-1]
                tokens.append('{' + group_content + '}')
            
            elif char in '^_':
                # Superscript or subscript
                tokens.append(char)
                i += 1
            
            elif char == ' ':
                # Skip whitespace
                i += 1
            
            else:
                # Regular character
                tokens.append(char)
                i += 1
        
        return tokens
    
    def _parse_tokens(self, tokens: List[str]) -> List[MathBox]:
        """Parse a list of tokens into math boxes."""
        boxes = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            if token.startswith('\\'):
                # Command
                box = self._parse_command(token[1:])
                boxes.append(box)
                i += 1
            
            elif token.startswith('{') and token.endswith('}'):
                # Braced group
                group_content = token[1:-1]
                group_box = self.parse_expression(group_content)
                boxes.append(group_box)
                i += 1
            
            elif token == '^':
                # Superscript
                if boxes and i + 1 < len(tokens):
                    base = boxes.pop()
                    sup_token = tokens[i + 1]
                    if sup_token.startswith('{') and sup_token.endswith('}'):
                        sup_content = sup_token[1:-1]
                    else:
                        sup_content = sup_token
                    
                    sup_box = self.parse_expression(sup_content)
                    
                    from ..engines.math_engine import MathLayoutEngine
                    engine = MathLayoutEngine()
                    script_box = engine.layout_superscript(base, sup_box)
                    boxes.append(script_box)
                    i += 2
                else:
                    i += 1
            
            elif token == '_':
                # Subscript
                if boxes and i + 1 < len(tokens):
                    base = boxes.pop()
                    sub_token = tokens[i + 1]
                    if sub_token.startswith('{') and sub_token.endswith('}'):
                        sub_content = sub_token[1:-1]
                    else:
                        sub_content = sub_token
                    
                    sub_box = self.parse_expression(sub_content)
                    
                    from ..engines.math_engine import MathLayoutEngine
                    engine = MathLayoutEngine()
                    script_box = engine.layout_subscript(base, sub_box)
                    boxes.append(script_box)
                    i += 2
                else:
                    i += 1
            
            else:
                # Regular atom
                box = self.parse_atom(token)
                boxes.append(box)
                i += 1
        
        return boxes
    
    def _parse_command(self, command: str) -> MathBox:
        """Parse a LaTeX command into a math box."""
        # Check symbol tables
        if command in self.greek_letters:
            symbol = self.greek_letters[command]
            return create_atom_box(symbol, font_size=10.0)
        
        if command in self.operators:
            symbol = self.operators[command]
            box = create_operator_box(symbol, font_size=10.0)
            box.box_type = BoxType.OPERATOR
            return box
        
        if command in self.relations:
            symbol = self.relations[command]
            box = create_operator_box(symbol, font_size=10.0)
            box.box_type = BoxType.RELATION
            return box
        
        if command in self.large_operators:
            symbol = self.large_operators[command]
            box = create_operator_box(symbol, font_size=12.0)
            box.box_type = BoxType.LARGE_OP
            return box
        
        if command in self.arrows:
            symbol = self.arrows[command]
            box = create_operator_box(symbol, font_size=10.0)
            box.box_type = BoxType.RELATION
            return box
        
        if command in self.delimiters:
            symbol = self.delimiters[command]
            box = create_atom_box(symbol, font_size=10.0)
            if command.startswith('l'):
                box.box_type = BoxType.OPENING
            else:
                box.box_type = BoxType.CLOSING
            return box
        
        if command in self.misc_symbols:
            symbol = self.misc_symbols[command]
            return create_atom_box(symbol, font_size=10.0)
        
        # Special commands
        if command == 'frac':
            # This would need special handling in a full parser
            # For now, return a placeholder
            return create_atom_box('□', font_size=10.0)
        
        if command == 'sqrt':
            # Square root - placeholder for now
            return create_atom_box('√', font_size=10.0)
        
        # Unknown command - return as text
        return create_atom_box(f'\\{command}', font_size=10.0)
