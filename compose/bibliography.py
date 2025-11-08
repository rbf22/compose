# compose/bibliography.py
"""
Bibliography and citation management for Compose documents.

Supports various citation styles (APA, MLA, Chicago, IEEE) and automatic
formatting of references and bibliographies.
"""

from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass
import re


class CitationStyle(Enum):
    """Supported citation styles"""
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    IEEE = "ieee"
    HARVARD = "harvard"


@dataclass
class CitationSource:
    """Represents a bibliographic source"""
    key: str
    entry_type: str  # book, article, inproceedings, etc.
    fields: Dict[str, str]

    def __post_init__(self):
        # Ensure key is clean
        self.key = re.sub(r'[^\w\-]', '', self.key)


class BibliographyManager:
    """
    Manages bibliographic sources and generates formatted citations.

    Supports multiple citation styles and automatic bibliography generation.
    """

    def __init__(self, style: CitationStyle = CitationStyle.APA):
        self.style = style
        self.sources: Dict[str, CitationSource] = {}
        self.citations: List[Dict[str, Any]] = []  # Track citation usage
        self.citation_counter = 0

    def add_source(self, source: CitationSource):
        """Add a bibliographic source"""
        self.sources[source.key] = source

    def add_source_from_dict(self, key: str, entry_type: str, fields: Dict[str, str]):
        """Add a source from dictionary data"""
        source = CitationSource(key=key, entry_type=entry_type, fields=fields)
        self.add_source(source)

    def add_source_from_bibtex(self, bibtex_entry: str):
        """Parse and add a source from BibTeX format"""
        # Basic BibTeX parsing (simplified)
        lines = bibtex_entry.strip().split('\n')
        if not lines:
            return

        # Parse entry type and key
        first_line = lines[0].strip()
        match = re.match(r'@\w+\{([^,]+),', first_line)
        if not match:
            return

        key = match.group(1)
        match = re.match(r'@(\w+)\{', first_line)
        if not match:
            return

        entry_type = match.group(1).lower()

        # Parse fields
        fields = {}
        for line in lines[1:]:
            line = line.strip()
            if line == '}':
                break
            if '=' in line:
                field_match = re.match(r'(\w+)\s*=\s*["{]([^"}]*)["}]', line)
                if field_match:
                    field_name, field_value = field_match.groups()
                    fields[field_name] = field_value

        self.add_source_from_dict(key, entry_type, fields)

    def cite(self, key: str, page: Optional[str] = None) -> str:
        """
        Generate an in-text citation for a source.

        Args:
            key: Source key
            page: Optional page reference

        Returns:
            Formatted citation text
        """
        if key not in self.sources:
            return f"[?? {key}]"

        source = self.sources[key]

        # Record citation usage
        self.citations.append({
            'key': key,
            'page': page,
            'number': len([c for c in self.citations if c['key'] == key]) + 1
        })

        # Generate citation based on style
        if self.style == CitationStyle.APA:
            return self._cite_apa(source, page)
        elif self.style == CitationStyle.MLA:
            return self._cite_mla(source, page)
        elif self.style == CitationStyle.CHICAGO:
            return self._cite_chicago(source, page)
        elif self.style == CitationStyle.IEEE:
            return self._cite_ieee(source, page)
        else:
            return self._cite_default(source, page)

    def generate_bibliography(self) -> str:
        """
        Generate a formatted bibliography.

        Returns:
            Formatted bibliography text
        """
        if not self.sources:
            return ""

        # Sort sources (by author, then title)
        sorted_sources = sorted(self.sources.values(),
                              key=lambda s: (s.fields.get('author', ''),
                                            s.fields.get('title', '')))

        lines = ["\nBibliography\n"]
        lines.append("=" * 50)

        for source in sorted_sources:
            citation = self._format_bibliography_entry(source)
            if citation:
                lines.append(f"\n{citation}")

        return "\n".join(lines)

    def export_to_bibtex(self) -> str:
        """Export sources to BibTeX format"""
        bibtex_entries = []
        for source in self.sources.values():
            fields_str = ",\n".join(f"  {k} = {{{v}}}" for k, v in source.fields.items())
            entry = f"""@{source.entry_type}{{{source.key},
{fields_str}
}}"""
            bibtex_entries.append(entry)

        return "\n\n".join(bibtex_entries)

    def _cite_apa(self, source: CitationSource, page: Optional[str]) -> str:
        """Generate APA-style citation"""
        authors = source.fields.get('author', 'Unknown')
        year = source.fields.get('year', 'n.d.')

        # Simplify author formatting (would be more complex in real implementation)
        author_parts = authors.split(' and ')[0]  # Take first author
        if ',' in author_parts:
            last, first = author_parts.split(',', 1)
            citation = f"({last}, {year})"
        else:
            citation = f"({authors}, {year})"

        if page:
            citation = citation.rstrip(')') + f", p. {page})"

        return citation

    def _cite_mla(self, source: CitationSource, page: Optional[str]) -> str:
        """Generate MLA-style citation"""
        authors = source.fields.get('author', 'Unknown')
        page_ref = f" {page}" if page else ""
        return f"({authors}{page_ref})"

    def _cite_chicago(self, source: CitationSource, page: Optional[str]) -> str:
        """Generate Chicago-style citation"""
        authors = source.fields.get('author', 'Unknown')
        year = source.fields.get('year', 'n.d.')
        page_ref = f", {page}" if page else ""
        return f"({authors} {year}{page_ref})"

    def _cite_ieee(self, source: CitationSource, page: Optional[str]) -> str:
        """Generate IEEE-style citation"""
        # IEEE uses numbers, find the citation number
        citation_nums = [c['number'] for c in self.citations if c['key'] == source.key]
        num = citation_nums[0] if citation_nums else 1
        return f"[{num}]"

    def _cite_default(self, source: CitationSource, page: Optional[str]) -> str:
        """Generate default citation format"""
        return f"[{source.key}]"

    def _format_bibliography_entry(self, source: CitationSource) -> str:
        """Format a bibliography entry"""
        if self.style == CitationStyle.APA:
            return self._format_apa_entry(source)
        elif self.style == CitationStyle.MLA:
            return self._format_mla_entry(source)
        elif self.style == CitationStyle.CHICAGO:
            return self._format_chicago_entry(source)
        elif self.style == CitationStyle.IEEE:
            return self._format_ieee_entry(source)
        else:
            return self._format_default_entry(source)

    def _format_apa_entry(self, source: CitationSource) -> str:
        """Format APA bibliography entry"""
        authors = source.fields.get('author', 'Unknown')
        year = source.fields.get('year', '')
        title = source.fields.get('title', 'Untitled')
        journal = source.fields.get('journal', '')
        volume = source.fields.get('volume', '')
        pages = source.fields.get('pages', '')

        # Simplified APA formatting
        entry = f"{authors} ({year}). {title}."
        if journal and volume:
            entry += f" {journal}, {volume}"
            if pages:
                entry += f", {pages}"

        return entry

    def _format_mla_entry(self, source: CitationSource) -> str:
        """Format MLA bibliography entry"""
        authors = source.fields.get('author', 'Unknown')
        title = source.fields.get('title', 'Untitled')
        publisher = source.fields.get('publisher', '')
        year = source.fields.get('year', '')

        entry = f'{authors}. "{title}."'
        if publisher and year:
            entry += f" {publisher}, {year}."

        return entry

    def _format_chicago_entry(self, source: CitationSource) -> str:
        """Format Chicago bibliography entry"""
        authors = source.fields.get('author', 'Unknown')
        title = source.fields.get('title', 'Untitled')
        publisher = source.fields.get('publisher', '')
        year = source.fields.get('year', '')

        entry = f'{authors}. "{title}." {publisher}, {year}.'

        return entry

    def _format_ieee_entry(self, source: CitationSource) -> str:
        """Format IEEE bibliography entry"""
        # Find citation number
        citation_nums = [i+1 for i, c in enumerate(self.citations) if c['key'] == source.key]
        num = citation_nums[0] if citation_nums else 1

        authors = source.fields.get('author', 'Unknown')
        title = source.fields.get('title', 'Untitled')
        journal = source.fields.get('journal', '')
        year = source.fields.get('year', '')

        entry = f"[{num}] {authors}, \"{title},\" {journal}, {year}."

        return entry

    def _format_default_entry(self, source: CitationSource) -> str:
        """Format default bibliography entry"""
        authors = source.fields.get('author', 'Unknown')
        title = source.fields.get('title', 'Untitled')
        year = source.fields.get('year', '')

        return f"{authors}. {title}. {year}."


# Global bibliography manager
bibliography_manager = BibliographyManager()


def set_citation_style(style: CitationStyle):
    """Set the global citation style"""
    bibliography_manager.style = style


def add_bibliography_source(key: str, entry_type: str, **fields):
    """Add a bibliography source"""
    bibliography_manager.add_source_from_dict(key, entry_type, fields)


def cite(key: str, page: Optional[str] = None) -> str:
    """Generate a citation"""
    return bibliography_manager.cite(key, page)


def bibliography() -> str:
    """Generate the bibliography"""
    return bibliography_manager.generate_bibliography()


# Example usage:
# set_citation_style(CitationStyle.APA)
# add_bibliography_source("smith2023", "article",
#                        author="John Smith",
#                        title="A Great Paper",
#                        journal="Journal of Stuff",
#                        year="2023")
# citation = cite("smith2023")  # (Smith, 2023)
# bib = bibliography()  # Formatted bibliography
