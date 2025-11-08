# compose/macro_system.py
"""
Macro system for Compose - LaTeX-style macro expansion and definition.

This implements a scoped macro system similar to LaTeX's \newcommand,
with support for parameter substitution and recursive expansion.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
import re
from dataclasses import dataclass
from enum import Enum


class MacroError(Exception):
    """Macro system error"""
    pass


class MacroScope(Enum):
    """Macro scoping levels"""
    GLOBAL = "global"
    DOCUMENT = "document"
    ENVIRONMENT = "environment"
    LOCAL = "local"


@dataclass
class MacroDefinition:
    """A macro definition with parameters and expansion"""
    name: str
    parameters: int  # Number of parameters (0 for simple macros)
    body: str  # The expansion text
    scope: MacroScope = MacroScope.GLOBAL
    protected: bool = False  # Whether this macro can be redefined


class MacroExpansion:
    """Result of expanding a macro"""

    def __init__(self, original: str, expanded: str, macros_used: List[str] = None):
        self.original = original
        self.expanded = expanded
        self.macros_used = macros_used or []


class MacroProcessor:
    """
    Processes LaTeX-style macros with parameter substitution and scoping.

    Supports:
    - \newcommand{\name}[num_params]{definition}
    - \renewcommand{\name}[num_params]{definition}
    - Parameter substitution (#1, #2, etc.)
    - Recursive macro expansion
    - Scoped definitions
    """

    def __init__(self):
        self.macros: Dict[str, MacroDefinition] = {}
        self.scope_stack: List[Dict[str, MacroDefinition]] = []
        self.expansion_stack: List[str] = []  # Prevent infinite recursion

        # Initialize built-in macros
        self._initialize_builtin_macros()

    def _initialize_builtin_macros(self):
        """Initialize built-in Compose macros"""

        # Text formatting macros
        self.define_macro("\\textbf", 1, "\\mathbf{#1}")
        self.define_macro("\\textit", 1, "\\mathit{#1}")
        self.define_macro("\\texttt", 1, "\\mathtt{#1}")

        # Math operators
        self.define_macro("\\sin", 0, "\\mathop{\\mathrm{sin}}\\nolimits")
        self.define_macro("\\cos", 0, "\\mathop{\\mathrm{cos}}\\nolimits")
        self.define_macro("\\tan", 0, "\\mathop{\\mathrm{tan}}\\nolimits")
        self.define_macro("\\log", 0, "\\mathop{\\mathrm{log}}\\nolimits")
        self.define_macro("\\ln", 0, "\\mathop{\\mathrm{ln}}\\nolimits")

        # Spacing macros
        self.define_macro("\\,", 0, "\\hspace{0.166em}")
        self.define_macro("\\:", 0, "\\hspace{0.222em}")
        self.define_macro("\\;", 0, "\\hspace{0.277em}")
        self.define_macro("\\!", 0, "\\hspace{-0.166em}")

        # Special symbols
        self.define_macro("\\deg", 0, "{}^\\circ")
        self.define_macro("\\infty", 0, "\\infty")
        self.define_macro("\\pi", 0, "\\pi")
        self.define_macro("\\alpha", 0, "\\alpha")

    def define_macro(self, name: str, params: int, body: str,
                    scope: MacroScope = MacroScope.GLOBAL, protected: bool = False) -> None:
        """
        Define a new macro.

        Args:
            name: Macro name (without backslash)
            params: Number of parameters (0 for simple macros)
            body: Expansion body
            scope: Macro scope
            protected: Whether macro can be redefined
        """
        # Remove backslash if present
        clean_name = name.lstrip('\\')

        # Check if macro already exists and is protected
        existing = self._lookup_macro(clean_name)
        if existing and existing.protected:
            raise MacroError(f"Cannot redefine protected macro \\{clean_name}")

        # If a local scope is active, default to placing definitions into the current scope
        # unless an explicit non-local scope was requested.
        effective_scope = scope
        if self.scope_stack and scope == MacroScope.GLOBAL:
            effective_scope = MacroScope.LOCAL

        macro = MacroDefinition(clean_name, params, body, effective_scope, protected)

        # Store based on effective scope
        if effective_scope == MacroScope.GLOBAL:
            self.macros[clean_name] = macro
        else:
            # Store in current (top) scope
            if not self.scope_stack:
                self.scope_stack.append({})
            self.scope_stack[-1][clean_name] = macro

    def process_newcommand(self, command: str) -> None:
        """
        Process a \newcommand or \renewcommand directive.

        Args:
            command: The full command string
        """
        # Parse \newcommand[renew]{\name}[num]{definition}
        pattern = r'\\(new|renew)command(\*)?\{\\([^}]+)\}(\[(\d+)\])?\{([^}]*)\}'
        match = re.match(pattern, command)

        if not match:
            raise MacroError(f"Invalid macro definition: {command}")

        is_renew = match.group(1) == 'renew'
        is_starred = match.group(2) is not None
        name = match.group(3)
        num_params = int(match.group(5)) if match.group(5) else 0
        body = match.group(6)

        # Check if macro exists for renew command
        existing = self._lookup_macro(name)
        if is_renew and not existing:
            raise MacroError(f"Cannot renew non-existent macro \\{name}")
        elif not is_renew and existing:
            raise MacroError(f"Macro \\{name} already exists")

        self.define_macro(name, num_params, body,
                         MacroScope.GLOBAL, is_starred)

    def expand_macros(self, text: str) -> MacroExpansion:
        """
        Expand all macros in the given text.

        Args:
            text: Text containing macro calls

        Returns:
            MacroExpansion with original, expanded text, and macros used
        """
        macros_used = []
        result = text

        # Process newcommand directives first
        result = self._process_newcommands(result)

        # Expand macros iteratively until no more expansions
        # Limit to 2 passes to avoid expanding built-in macros further
        max_iterations = 2
        iteration = 0

        while iteration < max_iterations:
            new_result = self._expand_once(result, macros_used)
            if new_result == result:
                break  # No more expansions
            result = new_result
            iteration += 1

        # If expansion budget used up, return the current result without error

        return MacroExpansion(text, result, macros_used)

    def _process_newcommands(self, text: str) -> str:
        """Process and remove newcommand directives from text"""
        # Find all newcommand patterns
        pattern = r'\\(new|renew)command(\*)?\{\\([^}]+)\}(\[(\d+)\])?\{([^}]*)\}'

        def replace_newcommand(match):
            try:
                self.process_newcommand(match.group(0))
                return ""  # Remove the command from text
            except MacroError as e:
                # Keep the command but add a warning comment
                return f"% ERROR: {e}\n{match.group(0)}"

        return re.sub(pattern, replace_newcommand, text)

    def _expand_once(self, text: str, macros_used: List[str]) -> str:
        """Perform one pass of macro expansion"""
        result = text

        # Find all complete macro calls: \name{param1}{param2}...
        # Simplified regex that matches balanced braces
        macro_pattern = r'\\[a-zA-Z]+\*?(\{(?:[^{}]|\{[^{}]*\})*\})*'

        def replace_macro(match):
            macro_call = match.group(0)
            return self._expand_macro_call_simple(macro_call, macros_used)

        result = re.sub(macro_pattern, replace_macro, result)
        return result

    def _expand_macro_call_simple(self, macro_call: str, macros_used: List[str]) -> str:
        """Expand a macro call by parsing name and parameters"""
        # Extract macro name
        name_match = re.match(r'\\([a-zA-Z]+(?:\*)?)', macro_call)
        if not name_match:
            return macro_call

        macro_name = name_match.group(1)

        # Parse parameters - find all {content} patterns
        param_pattern = r'\{([^{}]*)\}'
        param_matches = re.findall(param_pattern, macro_call)
        # If macro is unknown, leave the call unchanged
        if not self._lookup_macro(macro_name):
            return macro_call

        return self._expand_single_macro(macro_name, param_matches, macros_used)

    def _expand_single_macro(self, name: str, params: List[str], macros_used: List[str]) -> str:
        """Expand a single macro call"""
        # Prevent infinite recursion
        if name in self.expansion_stack:
            raise MacroError(f"Infinite macro recursion detected for \\{name}")

        macro = self._lookup_macro(name)
        if not macro:
            return f"\\{name}"  # Return unchanged if macro not found

        # Check parameter count
        if len(params) != macro.parameters:
            raise MacroError(f"Macro \\{name} expects {macro.parameters} parameters, got {len(params)}")

        # Expand the macro body
        self.expansion_stack.append(name)
        try:
            expanded = self._substitute_parameters(macro.body, params)
            macros_used.append(name)
            return expanded
        finally:
            self.expansion_stack.pop()

    def _substitute_parameters(self, body: str, params: List[str]) -> str:
        """Substitute #1, #2, etc. with actual parameters"""
        result = body

        for i, param in enumerate(params, 1):
            placeholder = f"#{i}"
            result = result.replace(placeholder, param)

        return result

    def _lookup_macro(self, name: str) -> Optional[MacroDefinition]:
        """Look up a macro by name, checking scopes in order"""
        # Check local scopes first (most recent first)
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]

        # Check global macros
        return self.macros.get(name)

    def push_scope(self, scope_type: MacroScope = MacroScope.LOCAL):
        """Push a new scope onto the stack"""
        self.scope_stack.append({})

    def pop_scope(self):
        """Pop the current scope from the stack"""
        if self.scope_stack:
            return self.scope_stack.pop()
        return {}

    def get_defined_macros(self) -> Dict[str, MacroDefinition]:
        """Get all currently defined macros"""
        result = dict(self.macros)  # Start with globals

        # Add scoped macros (later scopes override earlier ones)
        for scope in self.scope_stack:
            result.update(scope)

        return result


# Global macro processor instance
macro_processor = MacroProcessor()


# Convenience functions
def define_macro(name: str, params: int, body: str) -> None:
    """Define a global macro"""
    macro_processor.define_macro(name, params, body)


def expand_macros(text: str) -> MacroExpansion:
    """Expand macros in text"""
    return macro_processor.expand_macros(text)


def process_newcommand(command: str) -> None:
    """Process a newcommand directive"""
    macro_processor.process_newcommand(command)


# Example usage:
# macro_processor.process_newcommand(r"\newcommand{\hello}[1]{Hello, #1!}")
# expansion = macro_processor.expand_macros(r"\hello{World}")
# print(expansion.expanded)  # "Hello, World!"
