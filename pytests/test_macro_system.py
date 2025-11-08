# tests/test_macro_system.py
"""Tests for LaTeX macro system"""

import pytest
from compose.render.macro_system import (
    MacroDefinition, MacroExpander, NewcommandParser,
    MacroProcessor, expand_latex_macros, define_latex_macro
)


class TestMacroDefinition:
    """Test macro definition functionality"""

    def test_macro_definition_creation(self):
        """Test creating a macro definition"""
        macro = MacroDefinition('test', 2, 'result #1 and #2')

        assert macro.name == 'test'
        assert macro.parameters == 2
        assert macro.body == 'result #1 and #2'

    def test_macro_expansion_no_params(self):
        """Test expanding macro with no parameters"""
        macro = MacroDefinition('alpha', 0, 'α')

        result = macro.expand([])
        assert result == 'α'

    def test_macro_expansion_with_params(self):
        """Test expanding macro with parameters"""
        macro = MacroDefinition('frac', 2, '\\frac{#1}{#2}')

        result = macro.expand(['a', 'b'])
        assert result == '\\frac{a}{b}'

    def test_macro_expansion_wrong_args(self):
        """Test macro expansion with wrong number of arguments"""
        macro = MacroDefinition('test', 2, 'result')

        result = macro.expand(['arg1'])  # Only 1 arg, needs 2
        assert result == '\\test'  # Return unexpanded


class TestMacroExpander:
    """Test macro expander functionality"""

    def test_expander_initialization(self):
        """Test creating macro expander"""
        expander = MacroExpander()
        assert len(expander.macros) > 0  # Should have built-in macros

        # Check some built-in macros
        assert 'alpha' in expander.macros
        assert 'pi' in expander.macros

    def test_expand_builtin_macros(self):
        """Test expanding built-in macros"""
        expander = MacroExpander()

        result = expander.expand_macros(r'\alpha + \beta = \gamma')
        assert 'α' in result
        assert 'β' in result
        assert 'γ' in result

    def test_define_custom_macro(self):
        """Test defining custom macros"""
        expander = MacroExpander()

        expander.define_macro('RR', 0, '\\mathbb{R}')

        result = expander.expand_macros(r'f: \RR \to \RR')
        assert '\\mathbb{R}' in result

    def test_define_parameterized_macro(self):
        """Test defining macros with parameters"""
        expander = MacroExpander()

        expander.define_macro('frac', 2, '\\frac{#1}{#2}')

        result = expander.expand_macros(r'\frac{a}{b} + \frac{c}{d}')
        assert '\\frac{a}{b}' in result
        assert '\\frac{c}{d}' in result

    def test_nested_macro_expansion(self):
        """Test nested macro expansion"""
        expander = MacroExpander()

        expander.define_macro('num', 0, '42')
        expander.define_macro('answer', 0, 'The answer is \\num')

        result = expander.expand_macros(r'\answer')
        assert 'The answer is 42' == result

    def test_macro_removal(self):
        """Test removing macro definitions"""
        expander = MacroExpander()

        expander.define_macro('test', 0, 'value')
        assert 'test' in expander.macros

        removed = expander.remove_macro('test')
        assert removed == True
        assert 'test' not in expander.macros

        # Try removing non-existent macro
        removed = expander.remove_macro('nonexistent')
        assert removed == False

    def test_expansion_depth_limit(self):
        """Test that expansion depth is limited to prevent infinite loops"""
        expander = MacroExpander()

        # Create a macro that references itself
        expander.define_macro('loop', 0, '\\loop')

        result = expander.expand_macros(r'\loop', max_depth=3)
        # Should stop expanding after max_depth
        assert result == r'\loop'

    def test_complex_macro_expansion(self):
        """Test complex macro expansion with multiple parameters"""
        expander = MacroExpander()

        # Define a complex macro
        expander.define_macro('vector', 3, '(#1, #2, #3)')

        result = expander.expand_macros(r'\vector{x}{y}{z}')
        assert result == '(x, y, z)'


class TestNewcommandParser:
    """Test newcommand parsing functionality"""

    def test_newcommand_parser_initialization(self):
        """Test creating newcommand parser"""
        expander = MacroExpander()
        parser = NewcommandParser(expander)
        assert parser.expander is expander

    def test_parse_simple_newcommand(self):
        """Test parsing simple newcommand without parameters"""
        expander = MacroExpander()
        parser = NewcommandParser(expander)

        text = r'\newcommand{\RR}{\mathbb{R}}'
        result = parser.parse_newcommand(text)

        # Should define the macro
        assert 'RR' in expander.macros
        assert expander.macros['RR'].body == r'\mathbb{R}'
        assert expander.macros['RR'].parameters == 0

        # Should remove the definition from text
        assert r'\newcommand' not in result

    def test_parse_newcommand_with_params(self):
        """Test parsing newcommand with parameters"""
        expander = MacroExpander()
        parser = NewcommandParser(expander)

        text = r'\newcommand{\frac}[2]{\frac{#1}{#2}}'
        result = parser.parse_newcommand(text)

        assert 'frac' in expander.macros
        assert expander.macros['frac'].parameters == 2
        assert expander.macros['frac'].body == r'\frac{#1}{#2}'

    def test_parse_multiple_newcommands(self):
        """Test parsing multiple newcommand definitions"""
        expander = MacroExpander()
        parser = NewcommandParser(expander)

        text = r'''
        \newcommand{\RR}{\mathbb{R}}
        \newcommand{\abs}[1]{|#1|}
        \newcommand{\norm}[1]{\left\|#1\right\|}
        '''

        result = parser.parse_newcommand(text)

        assert 'RR' in expander.macros
        assert 'abs' in expander.macros
        assert 'norm' in expander.macros
        assert expander.macros['abs'].parameters == 1
        assert expander.macros['norm'].parameters == 1


class TestMacroProcessor:
    """Test high-level macro processor"""

    def test_macro_processor_initialization(self):
        """Test creating macro processor"""
        processor = MacroProcessor()
        assert hasattr(processor, 'expander')
        assert hasattr(processor, 'newcommand_parser')

    def test_process_document(self):
        """Test processing entire document with macros"""
        processor = MacroProcessor()

        document = r'''
        \newcommand{\RR}{\mathbb{R}}
        \newcommand{\abs}[1]{|#1|}

        Let $f: \RR \to \RR$ be a function such that $\abs{f(x)} \leq 1$.
        '''

        result = processor.process_document(document)

        # Should expand the macros
        assert r'\mathbb{R}' in result
        assert r'|f(x)|' in result

        # Should remove newcommand definitions
        assert r'\newcommand' not in result

    def test_process_math_expression(self):
        """Test processing math expressions with macros"""
        processor = MacroProcessor()

        # Define a macro
        processor.expander.define_macro('RR', 0, '\\mathbb{R}')

        math_expr = r'f: \RR \to \RR'
        result = processor.process_math_expression(math_expr)

        assert r'\mathbb{R}' in result

    def test_define_preamble_macros(self):
        """Test processing LaTeX preamble"""
        processor = MacroProcessor()

        preamble = r'''
        \newcommand{\RR}{\mathbb{R}}
        \newcommand{\CC}{\mathbb{C}}
        \newcommand{\NN}{\mathbb{N}}
        '''

        processor.define_preamble_macros(preamble)

        # Should have defined the macros
        assert 'RR' in processor.expander.macros
        assert 'CC' in processor.expander.macros
        assert 'NN' in processor.expander.macros


class TestMacroConvenienceFunctions:
    """Test convenience functions"""

    def test_expand_latex_macros(self):
        """Test the convenience macro expansion function"""
        define_latex_macro('test', 0, 'TEST')

        result = expand_latex_macros(r'This is a \test macro.')
        assert 'This is a TEST macro.' == result

    def test_define_latex_macro(self):
        """Test the convenience macro definition function"""
        define_latex_macro('my_macro', 1, 'My #1 macro')

        result = expand_latex_macros(r'\my_macro{test}')
        assert 'My test macro' == result
