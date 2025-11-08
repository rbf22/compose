# compose/render/math_images.py
"""
Math image generation for HTML rendering.

This module generates SVG images of mathematical expressions using only
Python standard library and provides them for embedding in HTML output.
"""

import os
import hashlib
import base64
import re
from typing import Dict, List, Tuple, Optional, Any
from ..layout.engines.math_engine import MathLayoutEngine, ExpressionLayout
from ..layout.content.math_parser import MathExpressionParser
from ..cache_system import math_cache, performance_monitor
from .large_operators import large_operator_layout, radical_layout, render_large_operator, render_radical
from .latex_nodes import parse_latex_to_nodes, LatexMacroNode, LatexGroupNode, LatexCharsNode
from .latex_specs import latex_to_unicode
from .html_parser import HTMLMathProcessor
from ..layout.tex_boxes import TexLayoutEngine, HBox, CharBox


class MathImageGenerator:
    """
    Generates SVG images of mathematical expressions for HTML embedding.

    Uses the layout engine for processing and creates clean SVG representations
    using only Python standard library.
    """

    def __init__(self):
        self.layout_engine = MathLayoutEngine()
        self.parser = MathExpressionParser()
        self.tex_engine = TexLayoutEngine()  # TeX-style box model
        self.cache: Dict[str, str] = {}  # content -> data_url

    @performance_monitor.time_operation("math_rendering")
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
        cached_result = math_cache.get_rendered_math(content, display_style)
        if cached_result:
            return cached_result

        # Generate new image
        try:
            image_data_url = self._generate_math_image(content, display_style)

            # Cache the result
            math_cache.set_rendered_math(content, display_style, image_data_url)

            return image_data_url
        except Exception as e:
            # Return fallback on error
            return self._create_fallback_svg(str(e), display_style)

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

        # Check for special mathematical constructs
        if self._contains_large_operator(clean_content):
            return self._generate_large_operator_image(clean_content, display_style)
        elif self._contains_radical(clean_content):
            return self._generate_radical_image(clean_content, display_style)
        elif self._contains_matrix(clean_content):
            return self._generate_matrix_image(clean_content, display_style)

        # Generate SVG representation
        return self._create_math_svg(clean_content, display_style)

    def _contains_large_operator(self, content: str) -> bool:
        """Check if content contains large operators."""
        large_ops = ['\\int', '\\sum', '\\prod', '\\coprod', '\\bigcup', '\\bigcap']
        return any(op in content for op in large_ops)

    def _contains_radical(self, content: str) -> bool:
        """Check if content contains radicals."""
        return '\\sqrt' in content or '\\root' in content

    def _generate_large_operator_image(self, content: str, display_style: bool) -> str:
        """Generate image for large operator expressions."""
        try:
            # Parse and extract operator information
            operator_info = self._parse_large_operator(content)
            if operator_info:
                return render_large_operator(**operator_info, display_style=display_style)
            else:
                return self._create_math_svg(content, display_style)
        except Exception as e:
            return self._create_fallback_svg(f"Large operator error: {str(e)[:30]}", display_style)

    def _generate_radical_image(self, content: str, display_style: bool) -> str:
        """Generate image for radical expressions."""
        try:
            # Parse radical expression
            radical_info = self._parse_radical(content)
            if radical_info:
                return render_radical(**radical_info)
            else:
                return self._create_math_svg(content, display_style)
        except Exception as e:
            return self._create_fallback_svg(f"Radical error: {str(e)[:30]}", display_style)

    def _parse_large_operator(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse large operator expression using proper tokenizer."""
        try:
            # Use the proper LaTeX tokenizer instead of regex
            from .latex_tokenizer import tokenize_latex, TokenType

            tokens = tokenize_latex(content)

            # Find the operator command
            operator = None
            for token in tokens:
                if token.type == TokenType.COMMAND:
                    # Extract operator name (remove backslash)
                    op_name = token.value[1:]
                    if op_name in ['int', 'iint', 'iiint', 'oint', 'sum', 'prod', 'coprod', 'bigcup', 'bigcap']:
                        operator = op_name
                        break

            if not operator:
                return None

            # Extract subscript and superscript by parsing token sequence
            subscript = self._extract_script_from_tokens(tokens, TokenType.SUBSCRIPT)
            superscript = self._extract_script_from_tokens(tokens, TokenType.SUPERSCRIPT)

            return {
                'operator': operator,
                'subscript': subscript,
                'superscript': superscript
            }

        except Exception:
            # Fallback to simple regex if tokenizer fails
            return self._parse_large_operator_regex(content)

    def _extract_script_from_tokens(self, tokens, script_type):
        """Extract subscript or superscript content from tokens."""
        from .latex_tokenizer import TokenType

        for i, token in enumerate(tokens):
            if token.type == script_type:
                # Look for content after the script marker
                if i + 1 < len(tokens):
                    next_token = tokens[i + 1]
                    if next_token.type == TokenType.LBRACE:
                        # Find matching closing brace
                        content = self._extract_braced_content(tokens, i + 2)
                        return content
                    elif next_token.type in (TokenType.TEXT, TokenType.COMMAND):
                        # Capture the immediate script token only
                        # If TEXT contains spaces, take the segment before the first space
                        value = next_token.value
                        if next_token.type == TokenType.TEXT and ' ' in value:
                            value = value.split(' ')[0]
                        return value
        return None

    def _extract_braced_content(self, tokens, start_pos):
        """Extract content between matching braces."""
        from .latex_tokenizer import TokenType

        content_parts = []
        brace_level = 1
        pos = start_pos

        while pos < len(tokens) and brace_level > 0:
            token = tokens[pos]

            if token.type == TokenType.LBRACE:
                brace_level += 1
                if brace_level > 1:  # Don't include nested braces
                    content_parts.append(token.value)
            elif token.type == TokenType.RBRACE:
                brace_level -= 1
                if brace_level > 0:  # Don't include the closing brace
                    content_parts.append(token.value)
            else:
                content_parts.append(token.value)

            pos += 1

        return ''.join(content_parts)

    def _parse_large_operator_regex(self, content: str) -> Optional[Dict[str, Any]]:
        """Fallback regex-based parsing for large operators."""
        # Simple regex approach as backup
        patterns = [
            r'\\(int|iint|iiint|oint|sum|prod|coprod|bigcup|bigcap)_(\w+|\{[^}]+\})\^(\w+|\{[^}]+\})',
            r'\\(int|iint|iiint|oint|sum|prod|coprod|bigcup|bigcap)_(\w+|\{[^}]+\})',
            r'\\(int|iint|iiint|oint|sum|prod|coprod|bigcup|bigcap)\^(\w+|\{[^}]+\})'
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                operator = match.group(1)
                if len(match.groups()) >= 3:
                    subscript = match.group(2)
                    superscript = match.group(3)
                elif len(match.groups()) >= 2:
                    if '_' in content[match.start():match.end()]:
                        subscript = match.group(2)
                        superscript = None
                    else:
                        subscript = None
                        superscript = match.group(2)
                else:
                    subscript = None
                    superscript = None

                # Strip braces
                if subscript and subscript.startswith('{') and subscript.endswith('}'):
                    subscript = subscript[1:-1]
                if superscript and superscript.startswith('{') and superscript.endswith('}'):
                    superscript = superscript[1:-1]

                return {
                    'operator': operator,
                    'subscript': subscript,
                    'superscript': superscript
                }

        return None

    def _parse_radical(self, content: str) -> Optional[Dict[str, str]]:
        """Parse radical expression."""
        import re

        # Match \sqrt[index]{content} or \sqrt{content}
        sqrt_pattern = r'\\sqrt(\[([^\]]+)\])?\{([^}]*)\}'
        match = re.search(sqrt_pattern, content)

        if match:
            index = match.group(2) if match.group(2) else None
            radical_content = match.group(3)
            return {
                'content': radical_content,
                'index': index
            }

        return None

    def _contains_matrix(self, content: str) -> bool:
        """Check if content contains matrix expressions."""
        matrix_patterns = [
            r'\\begin\{matrix\}',
            r'\\begin\{pmatrix\}',
            r'\\begin\{bmatrix\}',
            r'\\begin\{Bmatrix\}',
            r'\\begin\{vmatrix\}',
            r'\\begin\{Vmatrix\}'
        ]

        return any(re.search(pattern, content) for pattern in matrix_patterns)

    def _generate_matrix_image(self, content: str, display_style: bool) -> str:
        """Generate image for matrix expressions."""
        try:
            # Parse matrix
            matrix_box = matrix_parser.parse_matrix_expression(content)

            if matrix_box:
                # Render to SVG
                svg_data = matrix_engine.render_matrix_svg(matrix_box)
                return svg_data
            else:
                # Fallback to regular math rendering
                return self._create_math_svg(content, display_style)
        except Exception as e:
            # Fallback on error
            return self._create_fallback_svg(f"Matrix error: {str(e)[:30]}", display_style)

    def _create_math_svg(self, content: str, display_style: bool) -> str:
        """
        Create an SVG representation of mathematical content with proper formatting.
        Parses basic mathematical notation and positions elements correctly.
        """
        # Estimate dimensions
        font_size = 18 if display_style else 16
        padding = 12 if display_style else 8
        
        # Parse and format the mathematical expression
        formatted_content = self._format_math_expression(content, font_size)

        # Estimate width based on content
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
        Uses comprehensive mappings adapted from pylatexenc.
        """
        return latex_to_unicode(latex)

    def _format_math_expression(self, content: str, font_size: int) -> str:
        """
        Format mathematical expression with proper SVG positioning.
        Now uses full LaTeX node parsing to handle complex nested structures.
        """
        try:
            # Parse LaTeX into structured nodes
            nodes = parse_latex_to_nodes(content)

            # Check for integrals with complex limits
            if self._has_integral_with_limits(nodes):
                return self._format_integral_expression_nodes(nodes, font_size)

            # General expression formatting using node structure
            return self._format_nodes_to_svg(nodes, font_size)

        except Exception as e:
            # Fallback to simple token-based parsing
            print(f"Node parsing failed, falling back to tokens: {e}")
            expr = parse_latex_expression(content)
            svg_text = expr.to_svg_text(font_size)
            return f'<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Times New Roman, STIXGeneral, serif" font-size="{font_size}px" font-style="italic" fill="#000000">{svg_text}</text>'

    def _has_integral_with_limits(self, nodes: List) -> bool:
        """Check if nodes contain an integral with limits."""
        for node in nodes:
            if isinstance(node, LatexMacroNode) and node.macroname == 'int':
                # Check if it has sub/super scripts
                return (node.subscript is not None) or (node.superscript is not None)
        return False

    def _format_nodes_to_svg(self, nodes: List, font_size: int) -> str:
        """Format LaTeX nodes into SVG text elements."""
        svg_parts = []

        for node in nodes:
            if isinstance(node, LatexCharsNode):
                # Convert text to Unicode
                text = latex_to_unicode(node.chars)
                svg_parts.append(text)

            elif isinstance(node, LatexMacroNode):
                # Handle macros with sub/super scripts
                if node.macroname:
                    # Regular macro
                    if node.macroname in ['int', 'sum', 'prod', 'infty', 'pi', 'alpha', 'beta', 'gamma']:
                        # Convert known macros to Unicode
                        unicode_symbol = latex_to_unicode(f'\\{node.macroname}')
                        svg_parts.append(unicode_symbol)
                    else:
                        # Unknown macro - show as text
                        svg_parts.append(f'\\{node.macroname}')
                else:
                    # Script macro (subscript/superscript)
                    pass  # Handled below

                # Handle subscripts and superscripts
                if node.subscript:
                    sub_text = latex_to_unicode(node.subscript)
                    svg_parts.append(f'<tspan baseline-shift="sub" font-size="{font_size-4}px">{sub_text}</tspan>')

                if node.superscript:
                    sup_text = latex_to_unicode(node.superscript)
                    svg_parts.append(f'<tspan baseline-shift="super" font-size="{font_size-4}px">{sup_text}</tspan>')

            elif isinstance(node, LatexGroupNode):
                # Handle groups (potentially with sub/super scripts)
                group_content = self._format_nodes_to_svg(node.nodelist, font_size)
                # Remove the outer <text> wrapper if present
                import re
                text_match = re.search(r'<text[^>]*>(.*)</text>', group_content)
                if text_match:
                    group_content = text_match.group(1)
                svg_parts.append(f'<tspan>{group_content}</tspan>')

        full_text = "".join(svg_parts)

        # Apply sub/super script processing (simplified)
        full_text = self._apply_scripts_to_svg(full_text, font_size)

        return f'<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Times New Roman, STIXGeneral, serif" font-size="{font_size}px" font-style="italic" fill="#000000">{full_text}</text>'

    def _apply_scripts_to_svg(self, text: str, font_size: int) -> str:
        """Apply subscript/superscript formatting to SVG text."""
        # Simple pattern-based script handling
        import re

        # Handle subscripts
        text = re.sub(r'_\{([^}]+)\}',
                     f'<tspan baseline-shift="sub" font-size="{font_size-4}px">\\1</tspan>',
                     text)

        # Handle superscripts
        text = re.sub(r'\^\{([^}]+)\}',
                     f'<tspan baseline-shift="super" font-size="{font_size-4}px">\\1</tspan>',
                     text)

        return text

    def _format_integral_expression_nodes(self, nodes: List, font_size: int) -> str:
        """
        Special formatting for integral expressions using enhanced node structure.
        """
        svg_elements = []

        # Find the integral and extract its limits
        for node in nodes:
            if isinstance(node, LatexMacroNode) and node.macroname == 'int':
                # Center the integral symbol
                svg_elements.append(f'<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Times New Roman, STIXGeneral, serif" font-size="{font_size}px" font-style="italic" fill="#000000">∫</text>')

                # Position limits
                limit_x = 70

                # Lower limit (subscript)
                if node.subscript:
                    sub_text = latex_to_unicode(node.subscript)
                    svg_elements.append(f'<text x="{limit_x}" y="58" font-family="Times New Roman, STIXGeneral, serif" font-size="{font_size-4}px" font-style="italic" fill="#000000">{sub_text}</text>')

                # Upper limit (superscript)
                if node.superscript:
                    sup_text = latex_to_unicode(node.superscript)
                    svg_elements.append(f'<text x="{limit_x}" y="42" font-family="Times New Roman, STIXGeneral, serif" font-size="{font_size-4}px" font-style="italic" fill="#000000">{sup_text}</text>')

                # Find remaining nodes after the integral
                integral_index = nodes.index(node)
                remaining_nodes = nodes[integral_index + 1:]

                if remaining_nodes:
                    remaining_svg = self._format_nodes_to_svg(remaining_nodes, font_size)
                    # Extract text content and re-wrap
                    import re
                    text_match = re.search(r'<text[^>]*>(.*)</text>', remaining_svg)
                    if text_match:
                        remaining_text = text_match.group(1)
                        svg_elements.append(f'<text x="85%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Times New Roman, STIXGeneral, serif" font-size="{font_size}px" font-style="italic" fill="#000000">{remaining_text}</text>')

                break

        if not svg_elements:
            # Fallback to regular formatting
            return self._format_nodes_to_svg(nodes, font_size)

        return '\n  '.join(svg_elements)

    def _format_with_tex_boxes(self, content: str, font_size: int) -> str:
        """
        Format mathematical expression using TeX box model for proper layout.
        """
        # Use TeX layout engine
        hbox = self.tex_engine.layout_expression(content)

        # Convert box layout to SVG
        svg_parts = []
        x_offset = 0.0

        for box in hbox.contents:
            if isinstance(box, CharBox):
                svg_parts.append(f'<text x="{x_offset:.1f}" y="50%" dominant-baseline="middle">{box.char}</text>')
                x_offset += box.width
            elif isinstance(box, Glue):
                # Glue provides flexible spacing
                x_offset += box.width

        return '\n  '.join(svg_parts)

    def _nodes_to_text(self, nodes: List) -> str:
        """Convert nodes back to text representation."""
        parts = []
        for node in nodes:
            if isinstance(node, LatexCharsNode):
                parts.append(node.chars)
            elif isinstance(node, LatexMacroNode):
                parts.append(f'\\{node.macroname}')
            elif isinstance(node, LatexGroupNode):
                group_text = self._nodes_to_text(node.nodelist)
                parts.append(f'{{{group_text}}}')
        return ''.join(parts)

    def _format_integral_expression(self, content: str, font_size: int, expr) -> str:
        """
        Special formatting for integral expressions with limits.
        """
        svg_elements = []

        # Center the integral symbol
        svg_elements.append(f'<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Times New Roman, STIXGeneral, serif" font-size="{font_size}px" font-style="italic" fill="#000000">∫</text>')

        # Position limits relative to center
        limit_x = 70  # Position limits to the right of integral

        # Extract limits from the expression (this is a simplified approach)
        # In a full implementation, we'd parse the integral structure properly
        import re
        sub_match = re.search(r'_\{([^}]+)\}', content)
        sup_match = re.search(r'\^\{([^}]+)\}', content)

        if sub_match:
            sub_text = sub_match.group(1)
            # Convert any LaTeX commands in limits
            sub_text = latex_to_unicode(sub_text)
            svg_elements.append(f'<text x="{limit_x}" y="58" font-family="Times New Roman, STIXGeneral, serif" font-size="{font_size-4}px" font-style="italic" fill="#000000">{sub_text}</text>')

        if sup_match:
            sup_text = sup_match.group(1)
            # Convert any LaTeX commands in limits
            sup_text = latex_to_unicode(sup_text)
            svg_elements.append(f'<text x="{limit_x}" y="42" font-family="Times New Roman, STIXGeneral, serif" font-size="{font_size-4}px" font-style="italic" fill="#000000">{sup_text}</text>')

        # Add the rest of the expression to the right
        # Remove the integral with limits part
        rest = re.sub(r'∫_\{[^}]+\}\^\{[^}]+\}', '', content)
        rest = re.sub(r'∫_\{[^}]+\}', '', rest)  # Handle cases with only sub
        rest = re.sub(r'∫\^\{[^}]+\}', '', rest)  # Handle cases with only sup

        if rest.strip():
            # Parse and format the remaining expression
            rest_expr = parse_latex_expression(rest.strip())
            rest_svg = rest_expr.to_svg_text(font_size)
            svg_elements.append(f'<text x="85%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="Times New Roman, STIXGeneral, serif" font-size="{font_size}px" font-style="italic" fill="#000000">{rest_svg}</text>')

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
