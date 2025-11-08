# compose/lint/filefinder.py
"""
File finder for the Compose linter.

Discovers Markdown files in directories and validates file paths.
"""

import os
from pathlib import Path
from typing import List


class MarkdownFileFinder:
    """Finds Markdown files in directories"""

    MARKDOWN_EXTENSIONS = {'.md', '.markdown', '.mdown', '.mkd'}

    @staticmethod
    def find_files(path: str) -> List[str]:
        """
        Find all Markdown files in the given path.

        Args:
            path: File or directory path to search

        Returns:
            List of absolute paths to Markdown files
        """
        path_obj = Path(path)

        # If it's a single file, validate and return it
        if path_obj.is_file():
            if MarkdownFileFinder._is_markdown_file(path_obj):
                return [str(path_obj.resolve())]
            else:
                return []

        # If it's a directory, search recursively
        if path_obj.is_dir():
            markdown_files = []
            for root, dirs, files in os.walk(path_obj):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                for file in files:
                    file_path = Path(root) / file
                    if MarkdownFileFinder._is_markdown_file(file_path):
                        markdown_files.append(str(file_path.resolve()))

            return sorted(markdown_files)

        return []

    @staticmethod
    def _is_markdown_file(file_path: Path) -> bool:
        """
        Check if a file is a Markdown file.

        Args:
            file_path: Path to the file

        Returns:
            True if the file is a Markdown file
        """
        # Check extension
        if file_path.suffix.lower() in MarkdownFileFinder.MARKDOWN_EXTENSIONS:
            return True

        # Check if it's a file (not directory)
        if not file_path.is_file():
            return False

        # For files without standard extensions, check the first few lines
        # This is a simple heuristic - could be enhanced
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = []
                for i, line in enumerate(f):
                    if i >= 5:  # Check first 5 lines
                        break
                    first_lines.append(line.strip())

            # Look for Markdown patterns
            has_markdown_patterns = any(
                line.startswith('#') or  # Headings
                line.startswith('- ') or  # Lists
                line.startswith('* ') or
                line.startswith('1. ') or  # Numbered lists
                '![[' in line or  # Images/links
                '](' in line or
                '`' in line  # Inline code
                for line in first_lines
            )

            return has_markdown_patterns

        except (IOError, OSError):
            return False

    @staticmethod
    def validate_paths(paths: List[str]) -> tuple[List[str], List[str]]:
        """
        Validate a list of paths and separate valid from invalid ones.

        Args:
            paths: List of paths to validate

        Returns:
            Tuple of (valid_paths, invalid_paths)
        """
        valid_paths = []
        invalid_paths = []

        for path in paths:
            path_obj = Path(path)
            if path_obj.exists():
                valid_paths.append(path)
            else:
                invalid_paths.append(path)

        return valid_paths, invalid_paths
