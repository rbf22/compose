# compose/render/macro_system.py
"""
LaTeX macro system for Compose.
Provides support for \newcommand and basic macro expansion.
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Callable
from ..cache_system import performance_monitor


class MacroDefinition:
    """Represents a LaTeX macro definition"""

    def __init__(self, name: str, parameters: int, body: str):
        self.name = name
        self.parameters = parameters  # Number of parameters (#1, #2, etc.)
        self.body = body
        self.expanded_body = body  # Cache for expanded version

    def expand(self, args: List[str]) -> str:
        """
        Expand macro with given arguments.

        Args:
            args: List of argument strings

        Returns:
            Expanded macro body
        """
        if len(args) != self.parameters:
            return f"\\{self.name}"  # Return unexpanded if wrong number of args

        result = self.body

        # Replace parameter placeholders #1, #2, etc.
        for i, arg in enumerate(args, 1):
            result = result.replace(f"#{i}", arg)

        return result

    def __repr__(self):
        return f"MacroDefinition({self.name}, {self.parameters} params, '{self.body}')"


class MacroExpander:
    """
    Expands LaTeX macros in text.
    Handles nested macro expansion and parameter substitution.
    """

    def __init__(self):
        self.macros: Dict[str, MacroDefinition] = {}
        self._init_builtin_macros()

    def _init_builtin_macros(self):
        """Initialize some common LaTeX macros"""
        # Add some basic macros that are commonly used
        self.macros['alpha'] = MacroDefinition('alpha', 0, 'α')
        self.macros['beta'] = MacroDefinition('beta', 0, 'β')
        self.macros['gamma'] = MacroDefinition('gamma', 0, 'γ')
        self.macros['delta'] = MacroDefinition('delta', 0, 'δ')
        self.macros['epsilon'] = MacroDefinition('epsilon', 0, 'ε')
        self.macros['pi'] = MacroDefinition('pi', 0, 'π')
        self.macros['infty'] = MacroDefinition('infty', 0, '∞')
        self.macros['int'] = MacroDefinition('int', 0, '∫')
        self.macros['sum'] = MacroDefinition('sum', 0, '∑')
        self.macros['prod'] = MacroDefinition('prod', 0, '∏')

    @performance_monitor.time_operation("macro_expansion")
    def expand_macros(self, text: str, max_depth: int = 10) -> str:
        """
        Expand all macros in the text.

        Args:
            text: Text containing LaTeX macros
            max_depth: Maximum expansion depth to prevent infinite loops

        Returns:
            Text with macros expanded
        """
        result = text
        expanded = False

        for depth in range(max_depth):
            new_result, changed = self._expand_once(result)
            result = new_result
            expanded = expanded or changed

            if not changed:
                break  # No more expansions possible

        return result

    def _expand_once(self, text: str) -> Tuple[str, bool]:
        """
        Perform one pass of macro expansion.

        Returns:
            Tuple of (expanded_text, whether_anything_changed)
        """
        result = text
        changed = False

        # Find all macro calls in the text
        macro_pattern = r'\\(\w+)(\[[^\]]*\])?(\{[^}]*\})*'
        matches = list(re.finditer(macro_pattern, text))

        # Process matches in reverse order to maintain positions
        for match in reversed(matches):
            macro_name = match.group(1)

            if macro_name in self.macros:
                macro = self.macros[macro_name]

                # Extract arguments from the match
                args = self._extract_macro_args(match.group(0))

                # Expand the macro
                if len(args) == macro.parameters:
                    expanded = macro.expand(args)
                    result = result[:match.start()] + expanded + result[match.end():]
                    changed = True

        return result, changed

    def _extract_macro_args(self, macro_call: str) -> List[str]:
        """
        Extract arguments from a macro call.

        Args:
            macro_call: Full macro call like \\macro{arg1}{arg2}

        Returns:
            List of argument strings
        """
        args = []

        # Find all braced arguments
        brace_pattern = r'\{([^}]*)\}'
        brace_matches = re.findall(brace_pattern, macro_call)

        args.extend(brace_matches)

        # Find bracket arguments (optional parameters)
        bracket_pattern = r'\[([^\]]*)\]'
        bracket_matches = re.findall(bracket_pattern, macro_call)

        # Add bracket args first (they come before braces in LaTeX)
        args = bracket_matches + args

        return args

    def define_macro(self, name: str, parameters: int, body: str):
        """
        Define a new macro.

        Args:
            name: Macro name (without backslash)
            parameters: Number of parameters
            body: Macro body
        """
        self.macros[name] = MacroDefinition(name, parameters, body)

    def remove_macro(self, name: str) -> bool:
        """
        Remove a macro definition.

        Args:
            name: Macro name to remove

        Returns:
            True if removed, False if not found
        """
        if name in self.macros:
            del self.macros[name]
            return True
        return False

    def get_macro(self, name: str) -> Optional[MacroDefinition]:
        """Get a macro definition by name"""
        return self.macros.get(name)

    def list_macros(self) -> List[str]:
        """List all defined macro names"""
        return list(self.macros.keys())


class NewcommandParser:
    """
    Parser for \newcommand definitions in LaTeX.
    Handles the standard LaTeX \newcommand syntax.
    """

    def __init__(self, macro_expander: MacroExpander):
        self.expander = macro_expander

    def parse_newcommand(self, text: str) -> str:
        """
        Parse and process \newcommand definitions in text.

        Args:
            text: LaTeX text containing \newcommand definitions

        Returns:
            Text with \newcommand definitions processed and removed
        """
        # Find all \newcommand definitions using a simpler, more robust approach
        newcommand_pattern = r'\\newcommand\{\\(\w+)\}(\[\d+\])?\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'

        def replace_newcommand(match):
            macro_name = match.group(1)
            # Extract number from brackets like "[2]"
            param_match = match.group(2)
            num_params = int(param_match[1:-1]) if param_match else 0
            macro_body = match.group(3)

            # Define the macro
            self.expander.define_macro(macro_name, num_params, macro_body)

            # Remove the definition from text
            return ""

        # Process all newcommand definitions
        result = re.sub(newcommand_pattern, replace_newcommand, text, flags=re.DOTALL)

        return result

    def parse_renewcommand(self, text: str) -> str:
        """
        Parse and process \renewcommand definitions.
        Similar to newcommand but overwrites existing macros.
        """
        # \renewcommand has same syntax as \newcommand
        return self.parse_newcommand(text)


class MacroProcessor:
    """
    High-level macro processing for LaTeX documents.
    Handles macro definitions and expansions throughout a document.
    """

    def __init__(self):
        self.expander = MacroExpander()
        self.newcommand_parser = NewcommandParser(self.expander)

    def process_document(self, text: str) -> str:
        """
        Process an entire LaTeX document for macros.

        Args:
            text: Full LaTeX document text

        Returns:
            Text with all macro definitions processed and expansions performed
        """
        # First, extract and process macro definitions
        text = self.newcommand_parser.parse_newcommand(text)
        text = self.newcommand_parser.parse_renewcommand(text)

        # Then expand all macros
        text = self.expander.expand_macros(text)

        return text

    def process_math_expression(self, math_text: str) -> str:
        """
        Process macros within a mathematical expression.

        Args:
            math_text: Mathematical LaTeX expression

        Returns:
            Expression with macros expanded
        """
        # Math expressions typically don't define new macros,
        # but they can use existing ones
        return self.expander.expand_macros(math_text, max_depth=5)  # Lower depth for math

    def define_preamble_macros(self, preamble_text: str):
        """
        Process a LaTeX preamble to define macros.

        Args:
            preamble_text: LaTeX preamble containing macro definitions
        """
        # Process macro definitions without expanding
        self.newcommand_parser.parse_newcommand(preamble_text)
        self.newcommand_parser.parse_renewcommand(preamble_text)


# Global instances
macro_processor = MacroProcessor()
macro_expander = macro_processor.expander


def expand_latex_macros(text: str) -> str:
    """
    Convenience function to expand LaTeX macros in text.

    Args:
        text: Text containing LaTeX macros

    Returns:
        Text with macros expanded
    """
    return macro_processor.process_document(text)


def define_latex_macro(name: str, parameters: int, body: str):
    """
    Convenience function to define a LaTeX macro.

    Args:
        name: Macro name (without backslash)
        parameters: Number of parameters
        body: Macro body
    """
    macro_processor.expander.define_macro(name, parameters, body)


# Test functions
def test_macro_expansion():
    """Test basic macro expansion functionality"""
    expander = MacroExpander()

    # Test built-in macros
    result = expander.expand_macros(r'\alpha + \beta = \gamma')
    print(f"Built-in macros: {result}")

    # Define a custom macro
    expander.define_macro('RR', 0, '\\mathbb{R}')

    # Test custom macro
    result = expander.expand_macros(r'f: \RR \to \RR')
    print(f"Custom macro: {result}")

    # Test parameterized macro
    expander.define_macro('frac', 2, '\\frac{#1}{#2}')

    result = expander.expand_macros(r'\frac{a}{b} + \frac{c}{d}')
    print(f"Parameterized macro: {result}")


def test_newcommand_parsing():
    """Test parsing of \newcommand definitions"""
    processor = MacroProcessor()

    # Test newcommand parsing
    text = r'''
    \newcommand{\RR}{\mathbb{R}}
    \newcommand{\abs}[1]{|#1|}
    f: \RR \to \RR, x \mapsto \abs{x}
    '''

    result = processor.process_document(text)
    print(f"Newcommand result: {result.strip()}")


if __name__ == "__main__":
    test_macro_expansion()
    test_newcommand_parsing()
