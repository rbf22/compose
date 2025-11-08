# compose/render/html_parser.py
"""
Simple, targeted HTML processing for math expressions.
Uses reliable regex patterns instead of complex HTML parsing.
"""

import re
from typing import Dict


class HTMLMathProcessor:
    """
    Processes HTML to replace math placeholders with images.
    Uses targeted regex patterns that are much simpler and more reliable
    than the original complex patterns.
    """

    def __init__(self):
        from .math_images import MathImageGenerator
        from .macro_system import macro_processor
        self.image_generator = MathImageGenerator()
        self.macro_processor = macro_processor

    def process_html(self, html_content: str) -> str:
        """
        Replace math placeholders in HTML with image tags using targeted regex.

        Args:
            html_content: HTML string containing math expressions

        Returns:
            HTML string with math expressions replaced by images
        """
        # Extract math expressions using targeted patterns
        math_expressions = self._extract_math_expressions(html_content)

        # IMPORTANT: Keep keys consistent with replacement lookups.
        # Do NOT macro-expand here; use extracted LaTeX content directly
        # so that unicode_to_latex(...) in the replacement path matches keys.
        processed_expressions = math_expressions

        # Generate images for all expressions
        math_images = self.image_generator.get_all_math_images(processed_expressions)

        # Replace expressions with images
        html_content = self._replace_math_expressions(html_content, math_images)

        return html_content

    def _extract_math_expressions(self, html_content: str) -> list:
        """
        Extract math expressions from HTML using targeted regex patterns.

        Returns:
            List of (content, is_display) tuples
        """
        expressions = []

        # Inline math: <span class="math">[content]</span>
        # Much simpler pattern than the original complex one
        inline_pattern = r'<span[^>]*class="[^"]*math[^"]*"[^>]*>\[([^\]]+)\]</span>'
        for match in re.finditer(inline_pattern, html_content, re.IGNORECASE):
            expressions.append((match.group(1), False))  # inline

        # Block math: extract from math-placeholder divs within math-block divs
        block_pattern = r'<div[^>]*class="[^"]*math-block[^"]*"[^>]*>.*?<div[^>]*class="[^"]*math-placeholder[^"]*"[^>]*>(.*?)</div>.*?</div>'
        for match in re.finditer(block_pattern, html_content, re.DOTALL | re.IGNORECASE):
            content = match.group(1).strip()
            # Extract just the math content (before <br> tag)
            math_content = content.split('<br>')[0].strip()

            # Use proper LaTeX parsing - convert Unicode back to LaTeX for processing
            try:
                from .latex_specs import unicode_to_latex
                latex_content = unicode_to_latex(math_content)
            except Exception:
                # Fallback to original content if parsing fails
                latex_content = math_content

            expressions.append((latex_content, True))  # display

        return expressions

    def _replace_math_expressions(self, html_content: str, math_images: Dict[str, str]) -> str:
        """
        Replace math expressions in HTML with image tags.

        Args:
            html_content: Original HTML
            math_images: Dict mapping expression content to image URLs

        Returns:
            HTML with expressions replaced by images
        """
        # Replace inline math
        def replace_inline_math(match):
            content = match.group(1)
            image_url = math_images.get(content, "")
            if image_url:
                return f'<img src="{image_url}" alt="{content}" class="math-image math-inline" style="vertical-align: middle; margin: 0 2px;">'
            return match.group(0)

        inline_pattern = r'<span[^>]*class="[^"]*math[^"]*"[^>]*>\[([^\]]+)\]</span>'
        html_content = re.sub(inline_pattern, replace_inline_math, html_content, flags=re.IGNORECASE)

        # Replace block math
        def replace_block_math(match):
            content = match.group(1).strip()
            math_content = content.split('<br>')[0].strip()
            from .latex_specs import unicode_to_latex
            latex_content = unicode_to_latex(math_content)
            image_url = math_images.get(latex_content, "")
            if image_url:
                return f'<div class="math-image-container" style="text-align: center; margin: 1em 0;"><img src="{image_url}" alt="{latex_content}" class="math-image math-block" style="max-width: 100%;"></div>'
            return match.group(0)

        block_pattern = r'<div[^>]*class="[^"]*math-block[^"]*"[^>]*>.*?<div[^>]*class="[^"]*math-placeholder[^"]*"[^>]*>(.*?)</div>.*?</div>'
        html_content = re.sub(block_pattern, replace_block_math, html_content, flags=re.DOTALL | re.IGNORECASE)

        return html_content
