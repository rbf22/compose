# compose/parser/ast_parser.py
"""Clean AST-based markdown parser"""

import re
from typing import List, Dict, Any
from ..model.ast import *

class MarkdownParser:
    """Clean markdown parser that builds a consistent AST"""

    def parse(self, content: str) -> Document:
        """Parse markdown content into a Document AST"""
        lines = content.split('\n')
        blocks: List[BlockElement] = []
        frontmatter = self._extract_frontmatter(lines)

        i = 0
        while i < len(lines):
            # Skip empty lines at the beginning of blocks
            while i < len(lines) and lines[i].strip() == '':
                i += 1

            if i >= len(lines):
                break

            # Try to parse different block types
            block, consumed = self._parse_block(lines, i)
            if block:
                blocks.append(block)
                i += consumed
            else:
                i += 1

        return Document(blocks=blocks, frontmatter=frontmatter)

    def _extract_frontmatter(self, lines: List[str]) -> Dict[str, Any]:
        """Extract TOML frontmatter"""
        if len(lines) >= 3 and lines[0].strip() == '+++':
            # Find closing +++
            for i in range(1, len(lines)):
                if lines[i].strip() == '+++':
                    frontmatter_lines = lines[1:i]
                    return self._parse_toml_simple('\n'.join(frontmatter_lines))
        return {}

    def _parse_toml_simple(self, content: str) -> Dict[str, Any]:
        """Simple TOML parser for frontmatter"""
        result = {}
        for line in content.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                result[key] = value
        return result

    def _parse_block(self, lines: List[str], start: int) -> tuple[BlockElement, int]:
        """Parse a block element"""
        line = lines[start]

        # Headings
        if line.startswith('#'):
            return self._parse_heading(line)

        # Code blocks
        if line.strip().startswith('```'):
            return self._parse_code_block(lines, start)

        # Math blocks
        if line.strip().startswith('$$'):
            return self._parse_math_block(lines, start)

        # Tables
        if '|' in line and start + 1 < len(lines) and '|' in lines[start + 1]:
            return self._parse_table(lines, start)

        # Blockquotes
        if line.strip().startswith('>'):
            return self._parse_blockquote(lines, start)

        # Lists
        if self._is_list_item(line):
            return self._parse_list(lines, start)

        # Horizontal rule
        if line.strip() in ['---', '***', '___']:
            return HorizontalRule(), 1

        # Mermaid diagrams
        if line.strip() == '```mermaid':
            return self._parse_mermaid_block(lines, start)

        # Default to paragraph
        return self._parse_paragraph(lines, start)

    def _parse_heading(self, line: str) -> tuple[Heading, int]:
        """Parse a heading"""
        level = len(line) - len(line.lstrip('#'))
        text = line[level:].strip()
        content = self._parse_inline(text)
        return Heading(level=level, content=content), 1

    def _parse_paragraph(self, lines: List[str], start: int) -> tuple[Paragraph, int]:
        """Parse a paragraph"""
        content_lines = []
        i = start

        while i < len(lines):
            line = lines[i]
            # Stop at empty lines or other block elements
            if line.strip() == '' or self._is_block_start(line):
                break
            content_lines.append(line)
            i += 1

        text = ' '.join(content_lines)
        content = self._parse_inline(text)
        return Paragraph(content=content), i - start

    def _parse_code_block(self, lines: List[str], start: int) -> tuple[CodeBlock, int]:
        """Parse a code block"""
        # Get language from first line
        first_line = lines[start]
        language = first_line[3:].strip() if len(first_line) > 3 else None

        # Collect content until closing ```
        content_lines = []
        i = start + 1
        while i < len(lines):
            if lines[i].strip() == '```':
                break
            content_lines.append(lines[i])
            i += 1

        content = '\n'.join(content_lines)
        return CodeBlock(content=content, language=language), i - start + 1

    def _parse_math_block(self, lines: List[str], start: int) -> tuple[MathBlock, int]:
        """Parse a math block"""
        content_lines = []
        i = start

        # Check if single line
        line = lines[i]
        if line.count('$$') >= 2:
            # Single line math block
            start_pos = line.find('$$')
            end_pos = line.find('$$', start_pos + 2)
            if end_pos != -1:
                content = line[start_pos + 2:end_pos]
                return MathBlock(content=content), 1

        # Multi-line math block
        first_line = line.strip()[2:].strip()
        if first_line:
            content_lines.append(first_line)
        i += 1

        while i < len(lines):
            line = lines[i]
            if '$$' in line:
                end_pos = line.find('$$')
                if end_pos > 0:
                    content_lines.append(line[:end_pos])
                break
            content_lines.append(line)
            i += 1

        content = '\n'.join(content_lines)
        return MathBlock(content=content), i - start + 1

    def _parse_table(self, lines: List[str], start: int) -> tuple[Table, int]:
        """Parse a table"""
        headers_line = lines[start]
        separator_line = lines[start + 1]

        # Parse headers
        headers_raw = [cell.strip() for cell in headers_line.split('|')[1:-1]]
        headers = [self._parse_inline(cell) for cell in headers_raw]

        # Parse rows
        rows = []
        i = start + 2
        while i < len(lines) and '|' in lines[i]:
            row_raw = [cell.strip() for cell in lines[i].split('|')[1:-1]]
            row = [self._parse_inline(cell) for cell in row_raw]
            rows.append(row)
            i += 1

        return Table(headers=headers, rows=rows), i - start

    def _parse_blockquote(self, lines: List[str], start: int) -> tuple[Blockquote, int]:
        """Parse a blockquote"""
        quote_lines = []
        i = start

        while i < len(lines):
            line = lines[i]
            if not line.strip().startswith('>'):
                break

            # Remove the > prefix
            quote_line = line.lstrip('>')
            if quote_line.startswith(' '):
                quote_line = quote_line[1:]
            quote_lines.append(quote_line)
            i += 1

        # Parse the content recursively
        quote_content = '\n'.join(quote_lines)
        # Create a temporary parser for the nested content
        nested_doc = MarkdownParser().parse(quote_content)
        return Blockquote(content=nested_doc.blocks), i - start

    def _parse_list(self, lines: List[str], start: int) -> tuple[ListBlock, int]:
        """Parse a list"""
        items = []
        i = start
        ordered = False

        while i < len(lines):
            line = lines[i]
            if not self._is_list_item(line):
                break

            # Check if ordered
            if re.match(r'\d+\.', line.strip()):
                ordered = True

            # Parse list item content
            if ordered:
                # Remove "1. " etc.
                content = re.sub(r'^\d+\.\s*', '', line)
            else:
                # Remove "- " or "* "
                content = line[2:].strip()

            # Check for task list
            checked = None
            task_match = re.match(r'\[([ xX])\]\s*(.+)', content)
            if task_match:
                checkbox = task_match.group(1).lower()
                checked = checkbox == 'x'
                content = task_match.group(2)

            item_content = self._parse_inline(content)
            items.append(ListItem(content=item_content, checked=checked))
            i += 1

        return ListBlock(items=items, ordered=ordered), i - start

    def _parse_mermaid_block(self, lines: List[str], start: int) -> tuple[MermaidDiagram, int]:
        """Parse a Mermaid diagram block"""
        content_lines = []
        i = start + 1

        while i < len(lines):
            if lines[i].strip() == '```':
                break
            content_lines.append(lines[i])
            i += 1

        content = '\n'.join(content_lines)
        return MermaidDiagram(content=content), i - start + 1

    def _is_list_item(self, line: str) -> bool:
        """Check if line is a list item"""
        return re.match(r'^(\s*[-*]|\s*\d+\.)\s', line.strip()) is not None

    def _is_block_start(self, line: str) -> bool:
        """Check if line starts a new block"""
        return (line.startswith('#') or
                line.strip().startswith('```') or
                line.strip().startswith('$$') or
                ('|' in line and len(line.split('|')) > 2) or
                line.strip().startswith('>') or
                self._is_list_item(line) or
                line.strip() in ['---', '***', '___'])

    def _parse_inline(self, text: str) -> List[InlineElement]:
        """Parse inline formatting"""
        if not text:
            return [Text(content="")]

        # Handle inline code first (highest priority)
        elements = self._parse_inline_code(text)

        # Apply other inline formatting
        result = []
        for element in elements:
            if isinstance(element, Text):
                # Parse formatting within text
                result.extend(self._parse_text_formatting(element.content))
            else:
                result.append(element)

        return result

    def _parse_inline_code(self, text: str) -> List[InlineElement]:
        """Parse inline code blocks"""
        elements = []
        last_end = 0

        # Find all `...` sequences
        for match in re.finditer(r'`([^`]*)`', text):
            # Add text before
            if match.start() > last_end:
                elements.append(Text(content=text[last_end:match.start()]))

            # Add code element
            elements.append(CodeInline(content=match.group(1)))
            last_end = match.end()

        # Add remaining text
        if last_end < len(text):
            elements.append(Text(content=text[last_end:]))

        return elements if elements else [Text(content=text)]

    def _parse_inline(self, text: str) -> List[InlineElement]:
        """Parse inline formatting with proper markdown syntax handling"""
        if not text:
            return [Text(content="")]

        # Parse inline code first (highest priority)
        elements = self._parse_inline_code(text)

        # Apply other inline formatting
        result = []
        for element in elements:
            if isinstance(element, Text):
                # Parse formatting within text
                result.extend(self._parse_text_formatting(element.content))
            else:
                result.append(element)

        return result

    def _parse_text_formatting(self, text: str) -> List[InlineElement]:
        """Parse bold, italic, strikethrough, links, images, math in text"""
        if not text:
            return []

        # Apply smart typography first
        text = self._apply_smart_typography(text)

        elements = []

        # Handle bold (**text**)
        while '**' in text:
            start = text.find('**')
            if start == -1:
                break

            # Add text before
            if start > 0:
                elements.extend(self._parse_text_formatting(text[:start]))

            # Find closing **
            end = text.find('**', start + 2)
            if end == -1:
                # No closing, treat as literal
                elements.append(Text(content=text[start:]))
                return elements

            # Extract bold content
            bold_content = text[start + 2:end]
            inner_elements = self._parse_text_formatting(bold_content)
            elements.append(Bold(children=inner_elements))

            # Continue with remaining text
            text = text[end + 2:]

        # Handle italic (*text*)
        while '*' in text:
            start = text.find('*')
            if start == -1:
                break

            # Skip if this might be part of bold
            if start + 1 < len(text) and text[start + 1] == '*':
                # This is actually bold, skip
                start = text.find('*', start + 2)
                if start == -1:
                    break
                continue

            # Add text before
            if start > 0:
                elements.extend(self._parse_text_formatting(text[:start]))

            # Find closing *
            end = text.find('*', start + 1)
            if end == -1:
                # No closing, treat as literal
                elements.append(Text(content=text[start:]))
                return elements

            # Make sure it's not part of bold
            if end + 1 < len(text) and text[end + 1] == '*':
                # This closing * is actually part of bold, skip
                continue

            # Extract italic content
            italic_content = text[start + 1:end]
            inner_elements = self._parse_text_formatting(italic_content)
            elements.append(Italic(children=inner_elements))

            # Continue with remaining text
            text = text[end + 1:]

        # Handle strikethrough (~~text~~)
        while '~~' in text:
            start = text.find('~~')
            if start == -1:
                break

            # Add text before
            if start > 0:
                elements.extend(self._parse_text_formatting(text[:start]))

            # Find closing ~~
            end = text.find('~~', start + 2)
            if end == -1:
                # No closing, treat as literal
                elements.append(Text(content=text[start:]))
                return elements

            # Extract strikethrough content
            strike_content = text[start + 2:end]
            inner_elements = self._parse_text_formatting(strike_content)
            elements.append(Strikethrough(children=inner_elements))

            # Continue with remaining text
            text = text[end + 2:]

        # Handle math ($text$)
        while '$' in text:
            start = text.find('$')
            if start == -1:
                break

            # Add text before
            if start > 0:
                elements.extend(self._parse_text_formatting(text[:start]))

            # Find closing $ (but not $$)
            end = text.find('$', start + 1)
            if end == -1 or (end + 1 < len(text) and text[end + 1] == '$'):
                # No closing or it's $$, treat as literal
                elements.append(Text(content=text[start:]))
                return elements

            # Extract math content
            math_content = text[start + 1:end]
            elements.append(MathInline(content=math_content))

            # Continue with remaining text
            text = text[end + 1:]

        # Handle images ![alt](url)
        while '![' in text:
            start = text.find('![')
            if start == -1:
                break

            # Add text before
            if start > 0:
                elements.extend(self._parse_text_formatting(text[:start]))

            # Parse image
            match = re.match(r'!\[([^\]]*)\]\(([^)"\s]+)(?:\s*"([^"]*)")?\)', text[start:])
            if not match:
                # Malformed, treat as literal
                elements.append(Text(content=text[start:]))
                return elements

            alt, url = match.groups()[:2]
            elements.append(Image(alt=alt, url=url))

            # Continue with remaining text
            text = text[start + match.end():]

        # Handle links [text](url)
        while '[' in text:
            start = text.find('[')
            if start == -1:
                break

            # Check if this is actually an image
            if start > 0 and text[start - 1] == '!':
                # This is an image, already handled above
                break

            # Add text before
            if start > 0:
                elements.extend(self._parse_text_formatting(text[:start]))

            # Parse link
            match = re.match(r'\[([^\]]+)\]\(([^)"\s]+)(?:\s*"([^"]*)")?\)', text[start:])
            if not match:
                # Malformed, treat as literal
                elements.append(Text(content=text[start:]))
                return elements

            link_text, url = match.groups()[:2]
            # Parse inline formatting in link text
            link_elements = self._parse_text_formatting(link_text)
            elements.append(Link(text=link_text, url=url))

            # Continue with remaining text
            text = text[start + match.end():]

        # Add remaining plain text
        if text.strip():
            elements.append(Text(content=text))

        return elements

    def _apply_smart_typography(self, text: str) -> str:
        """Apply smart typography transformations"""
        # Apply longer patterns first to avoid conflicts
        # Smart dashes (em dash before en dash)
        text = text.replace('---', '—')  # em dash
        text = text.replace('--', '–')   # en dash

        # Smart quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace("'", "'").replace("'", "'")

        # Smart ellipses
        text = text.replace('...', '…')

        return text
