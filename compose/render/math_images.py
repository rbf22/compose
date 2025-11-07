# compose/render/math_images.py
"""
Math image generation for HTML rendering.

This module generates SVG images of mathematical expressions using only
Python standard library and provides them for embedding in HTML output.
"""

import os
import hashlib
import base64
from typing import Dict, List, Tuple
from ..layout.engines.math_engine import MathLayoutEngine, ExpressionLayout
from ..layout.content.math_parser import MathExpressionParser


class MathImageGenerator:
    """
    Generates SVG images of mathematical expressions for HTML embedding.

    Uses the layout engine for processing and creates clean SVG representations
    using only Python standard library.
    """

    def __init__(self):
        self.layout_engine = MathLayoutEngine()
        self.parser = MathExpressionParser()
        self.cache: Dict[str, str] = {}  # content -> data_url

    def get_math_image(self, content: str, display_style: bool = False) -> str:
        """
        Generate a data URL for a mathematical expression image.

        Args:
            content: LaTeX math content (without delimiters)
            display_style: True for block math, False for inline

        Returns:
            Data URL string for embedding in HTML
        """
        # Check cache first
        cache_key = f"{content}:{display_style}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Generate proper math image
        image_data_url = self._generate_math_image(content, display_style)
        self.cache[cache_key] = image_data_url

        return image_data_url

    def _generate_math_image(self, content: str, display_style: bool) -> str:
        """
        Generate a high-quality SVG image of mathematical expressions.
        Creates proper mathematical typography using only standard library.
        """
        # Clean the content
        clean_content = content.strip()
        if clean_content.startswith('$$') and clean_content.endswith('$$'):
            clean_content = clean_content[2:-2].strip()
        elif clean_content.startswith('$') and clean_content.endswith('$'):
            clean_content = clean_content[1:-1].strip()

        # Generate SVG representation
        return self._create_math_svg(clean_content, display_style)

    def _create_math_svg(self, content: str, display_style: bool) -> str:
        """
        Create an SVG representation of mathematical content with proper formatting.
        Parses basic mathematical notation and positions elements correctly.
        """
        # Convert LaTeX commands to Unicode symbols first
        content = self._latex_to_unicode(content)
        
        # Estimate dimensions
        font_size = 18 if display_style else 16
        padding = 12 if display_style else 8
        
        # Parse and format the mathematical expression
        formatted_content = self._format_math_expression(content, font_size)
        
        width = max(80, len(content) * 12)  # Estimate width
        height = font_size + (padding * 2)

        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="#ffffff" stroke="#e9ecef" stroke-width="1" rx="6"/>
  {formatted_content}
</svg>'''

        svg_base64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{svg_base64}"

    def _latex_to_unicode(self, latex: str) -> str:
        """
        Convert LaTeX commands to Unicode symbols for SVG display.
        """
        # Math symbol conversions
        conversions = {
            r'\int': '∫',
            r'\infty': '∞',
            r'\pi': 'π',
            r'\alpha': 'α',
            r'\beta': 'β',
            r'\gamma': 'γ',
            r'\delta': 'δ',
            r'\epsilon': 'ε',
            r'\theta': 'θ',
            r'\lambda': 'λ',
            r'\mu': 'μ',
            r'\sigma': 'σ',
            r'\phi': 'φ',
            r'\omega': 'ω',
            r'\sqrt': '√',
            r'\sum': '∑',
            r'\prod': '∏',
            r'\partial': '∂',
            r'\nabla': '∇',
            r'\leq': '≤',
            r'\geq': '≥',
            r'\neq': '≠',
            r'\approx': '≈',
            r'\rightarrow': '→',
            r'\leftarrow': '←',
            r'\Rightarrow': '⇒',
            r'\Leftarrow': '⇐',
        }
        
        result = latex
        for latex_cmd, unicode_sym in conversions.items():
            result = result.replace(latex_cmd, unicode_sym)
        
        return result

    def _format_math_expression(self, content: str, font_size: int) -> str:
        """
        Format mathematical expression with proper SVG positioning.
        Handles basic superscripts, subscripts, and symbols.
        """
        import re
        
        # Start with base text positioning
        x_pos = 50  # Center horizontally
        y_pos = 50  # Center vertically
        
        svg_elements = []
        
        # Simple parsing - split by operators and format each part
        # This is a basic implementation - could be enhanced significantly
        
        # Handle integrals with limits
        if '∫' in content and ('_{-' in content or '^{' in content or '_∞' in content or '^∞' in content):
            # Parse integral with limits using Unicode symbols
            # Center the integral symbol
            svg_elements.append(f'<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Times New Roman, STIXGeneral, serif" font-size="{font_size}px" font-style="italic" fill="#000000">∫</text>')
            
            # Position limits relative to center
            limit_x = 70  # Position limits to the right of integral
            
            # Find limits using Unicode braces
            sub_match = re.search(r'_\{([^}]+)\}', content)
            sup_match = re.search(r'\^\{([^}]+)\}', content)
            
            if sub_match:
                sub_text = sub_match.group(1)
                # Convert Unicode symbols in limits
                sub_text = sub_text.replace('∞', '∞').replace('π', 'π')
                svg_elements.append(f'<text x="{limit_x}" y="58" font-family="Times New Roman, STIXGeneral, serif" font-size="{font_size-4}px" font-style="italic" fill="#000000">{sub_text}</text>')
            
            if sup_match:
                sup_text = sup_match.group(1)
                # Convert Unicode symbols in limits
                sup_text = sup_text.replace('∞', '∞').replace('π', 'π')
                svg_elements.append(f'<text x="{limit_x}" y="42" font-family="Times New Roman, STIXGeneral, serif" font-size="{font_size-4}px" font-style="italic" fill="#000000">{sup_text}</text>')
            
            # Add the rest of the expression to the right
            rest = re.sub(r'∫_\{[^}]+\}\^\{[^}]+\}', '', content)
            if rest.strip():
                # Clean up the rest and format superscripts/subscripts
                rest = re.sub(r'_\{([^}]+)\}', f'<tspan baseline-shift="sub" font-size="{font_size-4}px">\\1</tspan>', rest)
                rest = re.sub(r'\^\{([^}]+)\}', f'<tspan baseline-shift="super" font-size="{font_size-4}px">\\1</tspan>', rest)
                rest = re.sub(r'\^2', '²', rest)
                rest = re.sub(r'\^3', '³', rest)
                svg_elements.append(f'<text x="85%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Times New Roman, STIXGeneral, serif" font-size="{font_size}px" font-style="italic" fill="#000000">{rest}</text>')
        
        else:
            # Simple formatting for other expressions
            display_text = content
            display_text = re.sub(r'_\{([^}]+)\}', f'<tspan baseline-shift="sub" font-size="{font_size-4}px">\\1</tspan>', display_text)
            display_text = re.sub(r'\^\{([^}]+)\}', f'<tspan baseline-shift="super" font-size="{font_size-4}px">\\1</tspan>', display_text)
            display_text = re.sub(r'\^2', '²', display_text)
            display_text = re.sub(r'\^3', '³', display_text)
            
            svg_elements.append(f'<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Times New Roman, STIXGeneral, serif" font-size="{font_size}px" font-style="italic" fill="#000000">{display_text}</text>')
        
        return '\n  '.join(svg_elements)

    def _create_fallback_svg(self, content: str, display_style: bool) -> str:
        """
        Create a fallback SVG when math rendering fails.
        """
        font_size = 16 if not display_style else 18
        padding = 8 if not display_style else 12
        width = max(50, len(content) * 8)
        height = font_size + (padding * 2)

        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="#fff3cd" stroke="#ffeeba" stroke-width="1" rx="4"/>
  <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle"
        font-family="Times New Roman, serif" font-size="{font_size}px" fill="#856404">
    {content[:30]}{"..." if len(content) > 30 else ""}
  </text>
</svg>'''

        svg_base64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{svg_base64}"

    def get_all_math_images(self, math_expressions: List[Tuple[str, bool]]) -> Dict[str, str]:
        """
        Generate images for all math expressions at once.

        Args:
            math_expressions: List of (content, display_style) tuples

        Returns:
            Dict mapping content to data URLs
        """
        result = {}
        for content, display_style in math_expressions:
            result[content] = self.get_math_image(content, display_style)
        return result


class HTMLMathProcessor:
    """
    Processes HTML to replace math placeholders with images.
    """

    def __init__(self):
        self.image_generator = MathImageGenerator()

    def process_html(self, html_content: str) -> str:
        """
        Replace math placeholders in HTML with image tags.

        Looks for patterns like:
        - <span class="math math-enhanced">[content]</span>
        - <div class="math-placeholder">content</div>
        """
        import re

        # Find all math expressions
        math_expressions = []

        # Pattern for inline math - more specific to avoid false matches
        # Only match spans that start with [ and end with ] and don't contain HTML
        inline_pattern = r'<span class="math[^"]*"[^>]*>\[([^\]<>]+)\]</span>'
        for match in re.finditer(inline_pattern, html_content):
            content = match.group(1)
            math_expressions.append((content, False))  # inline

        # Pattern for block math placeholders - extract from math-placeholder div
        block_pattern = r'<div class="math-placeholder">\s*([^<]+?)\s*<br>'
        for match in re.finditer(block_pattern, html_content, re.DOTALL):
            content = match.group(1).strip()
            # Convert back from ASCII to LaTeX for processing
            latex_content = self._ascii_to_latex(content)
            math_expressions.append((latex_content, True))  # display

        # Generate images for all expressions
        math_images = self.image_generator.get_all_math_images(math_expressions)

        # Replace inline math
        def replace_inline_math(match):
            content = match.group(1)
            image_url = math_images.get(content, "")
            if image_url:
                return f'<img src="{image_url}" alt="{content}" class="math-image math-inline" style="vertical-align: middle; margin: 0 2px;">'
            return match.group(0)

        html_content = re.sub(inline_pattern, replace_inline_math, html_content)

        # Replace block math - match the full math-block div structure
        block_replace_pattern = r'<div class="math-block"[^>]*>.*?<div class="math-placeholder">\s*([^<]+?)\s*<br><small>\([^<]+\)</small>\s*</div>\s*</div>'
        def replace_block_math(match):
            content = match.group(1).strip()
            latex_content = self._ascii_to_latex(content)
            image_url = math_images.get(latex_content, "")
            if image_url:
                return f'<div class="math-image-container" style="text-align: center; margin: 1em 0;"><img src="{image_url}" alt="{latex_content}" class="math-image math-block" style="max-width: 100%;"></div>'
            return match.group(0)

        html_content = re.sub(block_replace_pattern, replace_block_math, html_content, flags=re.DOTALL)

        return html_content

    def _ascii_to_latex(self, ascii_content: str) -> str:
        """
        Convert ASCII math symbols back to LaTeX format for processing.
        This is needed because the HTML renderer converts LaTeX to ASCII.
        """
        # Basic conversions - expand as needed
        latex = ascii_content
        latex = latex.replace('∫', '\\int')
        latex = latex.replace('∞', '\\infty')
        latex = latex.replace('π', '\\pi')
        latex = latex.replace('√', '\\sqrt')
        latex = latex.replace('²', '^2')
        latex = latex.replace('³', '^3')
        latex = latex.replace('α', '\\alpha')
        latex = latex.replace('β', '\\beta')
        latex = latex.replace('γ', '\\gamma')
        latex = latex.replace('δ', '\\delta')
        latex = latex.replace('ε', '\\epsilon')
        latex = latex.replace('θ', '\\theta')
        latex = latex.replace('λ', '\\lambda')
        latex = latex.replace('μ', '\\mu')
        latex = latex.replace('σ', '\\sigma')
        latex = latex.replace('φ', '\\phi')
        latex = latex.replace('ω', '\\omega')
        
        # Handle subscripts and superscripts
        # Convert _{content} back to _{content} (already in LaTeX format)
        # The ASCII renderer uses _{content} format, which is already LaTeX
        # But we need to make sure the content inside is properly converted
        
        return latex
