# -*- coding: utf-8 -*-
"""
LaTeX to Unicode conversion specifications.
Adapted from pylatexenc library (MIT License).

This module provides comprehensive mappings for converting LaTeX mathematical
commands to their Unicode equivalents for proper mathematical rendering.
"""

import unicodedata


# Mathematical symbols and operators
LATEX_TO_UNICODE_BASE = {
    # Integrals
    r'\int': '∫',
    r'\iint': '∬',
    r'\iiint': '∭',
    r'\oint': '∮',

    # Sums and products
    r'\sum': '∑',
    r'\prod': '∏',
    r'\coprod': '∐',

    # Limits and differentials
    r'\infty': '∞',
    r'\partial': '∂',
    r'\nabla': '∇',

    # Greek letters (lowercase)
    r'\alpha': 'α',
    r'\beta': 'β',
    r'\gamma': 'γ',
    r'\delta': 'δ',
    r'\epsilon': 'ε',
    r'\zeta': 'ζ',
    r'\eta': 'η',
    r'\theta': 'θ',
    r'\iota': 'ι',
    r'\kappa': 'κ',
    r'\lambda': 'λ',
    r'\mu': 'μ',
    r'\nu': 'ν',
    r'\xi': 'ξ',
    r'\omicron': 'ο',
    r'\pi': 'π',
    r'\rho': 'ρ',
    r'\sigma': 'σ',
    r'\tau': 'τ',
    r'\upsilon': 'υ',
    r'\phi': 'φ',
    r'\chi': 'χ',
    r'\psi': 'ψ',
    r'\omega': 'ω',

    # Greek letters (uppercase)
    r'\Alpha': 'Α',
    r'\Beta': 'Β',
    r'\Gamma': 'Γ',
    r'\Delta': 'Δ',
    r'\Epsilon': 'Ε',
    r'\Zeta': 'Ζ',
    r'\Eta': 'Η',
    r'\Theta': 'Θ',
    r'\Iota': 'Ι',
    r'\Kappa': 'Κ',
    r'\Lambda': 'Λ',
    r'\Mu': 'Μ',
    r'\Nu': 'Ν',
    r'\Xi': 'Ξ',
    r'\Omicron': 'Ο',
    r'\Pi': 'Π',
    r'\Rho': 'Ρ',
    r'\Sigma': 'Σ',
    r'\Tau': 'Τ',
    r'\Upsilon': 'Υ',
    r'\Phi': 'Φ',
    r'\Chi': 'Χ',
    r'\Psi': 'Ψ',
    r'\Omega': 'Ω',

    # Mathematical constants and symbols
    r'\pi': 'π',
    r'\hbar': 'ℏ',
    r'\ell': 'ℓ',
    r'\forall': '∀',
    r'\complement': '∁',
    r'\exists': '∃',
    r'\nexists': '∄',
    r'\varnothing': '∅',
    r'\emptyset': '∅',
    r'\aleph': 'ℵ',

    # Set theory
    r'\in': '∈',
    r'\notin': '∉',
    r'\ni': '∋',
    r'\setminus': '∖',
    r'\smallsetminus': '∖',

    # Relations
    r'\sim': '∼',
    r'\backsim': '∽',
    r'\simeq': '≃',
    r'\approx': '≈',
    r'\neq': '≠',
    r'\equiv': '≡',
    r'\le': '≤',
    r'\ge': '≥',
    r'\leq': '≤',
    r'\geq': '≥',
    r'\leqslant': '⩽',
    r'\geqslant': '⩾',
    r'\leqq': '≦',
    r'\geqq': '≧',
    r'\lneqq': '≨',
    r'\gneqq': '≩',
    r'\ll': '≪',
    r'\gg': '≫',
    r'\nless': '≮',
    r'\ngtr': '≯',
    r'\nleq': '≰',
    r'\ngeq': '≱',
    r'\lesssim': '≲',
    r'\gtrsim': '≳',
    r'\lessgtr': '≶',
    r'\gtrless': '≷',
    r'\prec': '≺',
    r'\succ': '≻',
    r'\preceq': '⪯',
    r'\succeq': '⪰',
    r'\precsim': '≾',
    r'\succsim': '≿',
    r'\nprec': '⊀',
    r'\nsucc': '⊁',
    r'\subset': '⊂',
    r'\supset': '⊃',
    r'\subseteq': '⊆',
    r'\supseteq': '⊇',
    r'\nsubseteq': '⊈',
    r'\nsupseteq': '⊉',
    r'\subsetneq': '⊊',
    r'\supsetneq': '⊋',

    # Arithmetic operators
    r'\cdot': '⋅',
    r'\times': '×',
    r'\otimes': '⊗',
    r'\oplus': '⊕',
    r'\bigotimes': '⊗',
    r'\bigoplus': '⊕',
    r'\pm': '±',
    r'\mp': '∓',

    # Functions
    r'\cos': 'cos',
    r'\sin': 'sin',
    r'\tan': 'tan',
    r'\arccos': 'arccos',
    r'\arcsin': 'arcsin',
    r'\arctan': 'arctan',
    r'\cosh': 'cosh',
    r'\sinh': 'sinh',
    r'\tanh': 'tanh',
    r'\arccosh': 'arccosh',
    r'\arcsinh': 'arcsinh',
    r'\arctanh': 'arctanh',
    r'\ln': 'ln',
    r'\log': 'log',
    r'\exp': 'exp',
    r'\max': 'max',
    r'\min': 'min',
    r'\sup': 'sup',
    r'\inf': 'inf',
    r'\lim': 'lim',
    r'\limsup': 'lim sup',
    r'\liminf': 'lim inf',

    # Square roots
    r'\sqrt': '√',

    # Fractions and spacing
    r'\prime': "'",
    r'\dag': '†',
    r'\dagger': '†',
    r'\ddag': '‡',
    r'\ddagger': '‡',

    # Arrows
    r'\leftarrow': '←',
    r'\rightarrow': '→',
    r'\to': '→',
    r'\uparrow': '↑',
    r'\downarrow': '↓',
    r'\leftrightarrow': '↔',
    r'\updownarrow': '↕',
    r'\nwarrow': '↖',
    r'\nearrow': '↗',
    r'\searrow': '↘',
    r'\swarrow': '↙',
    r'\nleftarrow': '↚',
    r'\nrightarrow': '↛',
    r'\arrowwaveleft': '↜',
    r'\arrowwaveright': '↝',
    r'\twoheadleftarrow': '↞',
    r'\twoheadrightarrow': '↠',
    r'\leftarrowtail': '↢',
    r'\rightarrowtail': '↣',
    r'\mapsto': '↦',
    r'\hookleftarrow': '↩',
    r'\hookrightarrow': '↪',
    r'\looparrowleft': '↫',
    r'\looparrowright': '↬',
    r'\leftrightsquigarrow': '↭',
    r'\nleftrightarrow': '↮',
    r'\Lsh': '↰',
    r'\Rsh': '↱',
    r'\curvearrowleft': '↶',
    r'\curvearrowright': '↷',
    r'\circlearrowleft': '↺',
    r'\circlearrowright': '↻',

    # Delimiters
    r'\langle': '⟨',
    r'\rangle': '⟩',
    r'\lvert': '|',
    r'\rvert': '|',
    r'\vert': '|',
    r'\lVert': '‖',
    r'\rVert': '‖',
    r'\Vert': '‖',
    r'\mid': '|',
    r'\nmid': '∤',

    # Quantum mechanics / Dirac notation
    r'\ket': '|%s⟩',
    r'\bra': '⟨%s|',
    r'\braket': '⟨%s|%s⟩',
    r'\ketbra': '|%s⟩⟨%s|',

    # Spacing and punctuation
    r',': ' ',
    r';': ' ',
    r':': ' ',
    r' ': ' ',
    r'!': '',
    r'\quad': '  ',
    r'\qquad': '    ',

    # Dots and ellipses
    r'\ldots': '…',
    r'\cdots': '⋯',
    r'\ddots': '⋱',
    r'\iddots': '⋰',
    r'\vdots': '⋮',
    r'\dots': '…',
    r'\dotsc': '…',
    r'\dotsb': '…',
    r'\dotsm': '…',
    r'\dotsi': '…',
    r'\dotso': '…',
}


def _make_greek_letters():
    """Generate Greek letter mappings using unicodedata."""
    greek_letters = {}

    # Lowercase Greek letters
    lowercase_greek = [
        ('alpha', 'α'), ('beta', 'β'), ('gamma', 'γ'), ('delta', 'δ'),
        ('epsilon', 'ε'), ('zeta', 'ζ'), ('eta', 'η'), ('theta', 'θ'),
        ('iota', 'ι'), ('kappa', 'κ'), ('lambda', 'λ'), ('mu', 'μ'),
        ('nu', 'ν'), ('xi', 'ξ'), ('omicron', 'ο'), ('pi', 'π'),
        ('rho', 'ρ'), ('sigma', 'σ'), ('tau', 'τ'), ('upsilon', 'υ'),
        ('phi', 'φ'), ('chi', 'χ'), ('psi', 'ψ'), ('omega', 'ω')
    ]

    # Uppercase Greek letters
    uppercase_greek = [
        ('Alpha', 'Α'), ('Beta', 'Β'), ('Gamma', 'Γ'), ('Delta', 'Δ'),
        ('Epsilon', 'Ε'), ('Zeta', 'Ζ'), ('Eta', 'Η'), ('Theta', 'Θ'),
        ('Iota', 'Ι'), ('Kappa', 'Κ'), ('Lambda', 'Λ'), ('Mu', 'Μ'),
        ('Nu', 'Ν'), ('Xi', 'Ξ'), ('Omicron', 'Ο'), ('Pi', 'Π'),
        ('Rho', 'Ρ'), ('Sigma', 'Σ'), ('Tau', 'Τ'), ('Upsilon', 'Υ'),
        ('Phi', 'Φ'), ('Chi', 'Χ'), ('Psi', 'Ψ'), ('Omega', 'Ω')
    ]

    # Add lowercase mappings
    for name, symbol in lowercase_greek:
        greek_letters[f'\\{name}'] = symbol
        greek_letters[f'\\up{name}'] = symbol  # up-greek variant

    # Add uppercase mappings
    for name, symbol in uppercase_greek:
        greek_letters[f'\\{name}'] = symbol
        greek_letters[f'\\Up{name}'] = symbol  # up-greek variant

    # Add variant forms
    greek_letters[r'\varepsilon'] = 'ε'  # lunate epsilon
    greek_letters[r'\vartheta'] = 'ϑ'     # variant theta
    greek_letters[r'\varpi'] = 'ϖ'        # variant pi
    greek_letters[r'\varrho'] = 'ϱ'       # variant rho
    greek_letters[r'\varsigma'] = 'ς'     # final sigma
    greek_letters[r'\varphi'] = 'ϕ'       # variant phi

    # up-greek variants for variants
    greek_letters[r'\upvarepsilon'] = 'ε'
    greek_letters[r'\upvartheta'] = 'ϑ'
    greek_letters[r'\upvarpi'] = 'ϖ'
    greek_letters[r'\upvarrho'] = 'ϱ'
    greek_letters[r'\upvarsigma'] = 'ς'
    greek_letters[r'\upvarphi'] = 'ϕ'

    return greek_letters


# Combine all mappings
LATEX_TO_UNICODE = {}
LATEX_TO_UNICODE.update(LATEX_TO_UNICODE_BASE)
LATEX_TO_UNICODE.update(_make_greek_letters())


def unicode_to_latex(text):
    """
    Convert Unicode mathematical symbols back to LaTeX commands.

    Args:
        text (str): Text containing Unicode mathematical symbols

    Returns:
        str: Text with Unicode symbols converted to LaTeX commands
    """
    result = text

    # Only replace actual Unicode mathematical symbols, not regular text
    replacements = {
        '∫': '\\int',
        '∑': '\\sum',
        '∏': '\\prod',
        '√': '\\sqrt',
        '∞': '\\infty',
        'α': '\\alpha',
        'β': '\\beta',
        'γ': '\\gamma',
        'δ': '\\delta',
        'π': '\\pi',
        'σ': '\\sigma',
        'ω': '\\omega',
        '≤': '\\leq',
        '≥': '\\geq',
        '≠': '\\neq',
        '≈': '\\approx',
        '≡': '\\equiv',
        '→': '\\rightarrow',
        '←': '\\leftarrow',
        '↑': '\\uparrow',
        '↓': '\\downarrow',
    }

    for unicode_sym, latex_cmd in replacements.items():
        result = result.replace(unicode_sym, latex_cmd)

    return result


def latex_to_unicode(text):
    """
    Convert LaTeX mathematical commands to Unicode symbols.

    Args:
        text (str): LaTeX text containing mathematical commands

    Returns:
        str: Text with LaTeX commands converted to Unicode symbols
    """
    result = text
    # Sort by length (longest first) to avoid partial replacements
    sorted_items = sorted(LATEX_TO_UNICODE.items(), key=lambda x: len(x[0]), reverse=True)
    for latex_cmd, unicode_sym in sorted_items:
        result = result.replace(latex_cmd, unicode_sym)
    return result


def test_latex_conversion():
    """Test function to verify LaTeX conversions work correctly."""
    test_cases = [
        (r'\int_{-\infty}^{\infty} e^{-x^2} dx', '∫_{-∞}^{∞} e^{-x²} dx'),
        (r'\alpha + \beta = \gamma', 'α + β = γ'),
        (r'\sqrt{x^2 + y^2}', '√{x² + y²}'),
        (r'\sum_{i=1}^{n} x_i', '∑_{i=1}^{n} x_i'),
    ]

    print("Testing LaTeX to Unicode conversion:")
    for latex, expected in test_cases:
        result = latex_to_unicode(latex)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{latex}' -> '{result}'")
        if result != expected:
            print(f"   Expected: '{expected}'")


if __name__ == '__main__':
    test_latex_conversion()
