# compose/model/enhanced_ast.py
"""
Enhanced AST model with relationship metadata for complex document features.
Extends the basic AST with cross-referencing and structural metadata.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from .ast import *


@dataclass
class DocumentStructure:
    """Analyzes and tracks relationships within a document"""

    document: Document

    # Cross-reference tracking
    headings_by_level: Dict[int, List[Heading]] = field(default_factory=lambda: {})
    headings_by_id: Dict[str, Heading] = field(default_factory=dict)

    # Content relationships
    footnotes: List['Footnote'] = field(default_factory=list)
    citations: List['Citation'] = field(default_factory=list)
    references: Dict[str, Any] = field(default_factory=dict)  # label -> target

    # Page/section structure
    sections: List['Section'] = field(default_factory=list)
    page_breaks: List[int] = field(default_factory=list)  # block indices

    def __post_init__(self):
        self._analyze_document()

    def _analyze_document(self):
        """Analyze the document structure and build relationship maps"""
        for i, block in enumerate(self.document.blocks):
            if isinstance(block, Heading):
                # Track headings by level and assign IDs
                level = block.level
                if level not in self.headings_by_level:
                    self.headings_by_level[level] = []
                self.headings_by_level[level].append(block)

                # Generate heading ID if not present
                heading_id = self._generate_heading_id(block, i)
                self.headings_by_id[heading_id] = block

            elif isinstance(block, MathBlock):
                # Check for labels in math content
                self._analyze_math_labels(block)

            elif isinstance(block, Paragraph):
                # Check for citations, footnotes, cross-references
                self._analyze_paragraph_content(block)

    def _generate_heading_id(self, heading: Heading, index: int) -> str:
        """Generate a unique ID for a heading"""
        # Simple ID generation - could be enhanced
        text_content = self._extract_text_content(heading.content)
        return f"heading-{index}-{text_content.lower().replace(' ', '-')}"

    def _analyze_math_labels(self, math_block: MathBlock):
        """Extract labels from math expressions"""
        content = math_block.content
        # Look for \label{...} in LaTeX
        import re
        labels = re.findall(r'\\label\{([^}]+)\}', content)
        for label in labels:
            self.references[label] = math_block

    def _analyze_paragraph_content(self, paragraph: Paragraph):
        """Analyze paragraph for citations, footnotes, etc."""
        # This would analyze inline elements for references
        # Implementation depends on specific features needed
        pass

    def _extract_text_content(self, inline_elements: List[InlineElement]) -> str:
        """Extract plain text from inline elements"""
        result = []
        for element in inline_elements:
            if isinstance(element, Text):
                result.append(element.content)
            elif isinstance(element, (Bold, Italic, Strikethrough)):
                result.append(self._extract_text_content(element.children))
            elif isinstance(element, CodeInline):
                result.append(element.content)
            # Add other element types as needed
        return ''.join(result)

    def get_table_of_contents(self) -> List[Dict[str, Any]]:
        """Generate table of contents from headings"""
        toc = []
        # Process headings in document order, not grouped by level
        for i, block in enumerate(self.document.blocks):
            if isinstance(block, Heading):
                toc.append({
                    'level': block.level,
                    'text': self._extract_text_content(block.content),
                    'id': self._generate_heading_id(block, i)
                })
        return toc

    def _get_heading_id(self, heading: Heading) -> str:
        """Get the ID for a heading"""
        for hid, h in self.headings_by_id.items():
            if h is heading:
                return hid
        return ""

    def _get_all_headings(self) -> List[Heading]:
        """Get all headings in document order."""
        headings = []
        for block in self.document.blocks:
            if isinstance(block, Heading):
                headings.append(block)
        return headings

    def resolve_reference(self, label: str) -> Optional[Any]:
        """Resolve a cross-reference by label"""
        # Check references first (math labels, etc.)
        if label in self.references:
            return self.references[label]

        # Check headings
        if label in self.headings_by_id:
            return self.headings_by_id[label]

        return None


# Enhanced AST nodes with relationship metadata
@dataclass
class EnhancedDocument(Document):
    """Document with structural analysis"""
    structure: DocumentStructure = None

    def __post_init__(self):
        if self.structure is None:
            self.structure = DocumentStructure(self)


@dataclass
class EnhancedHeading(Heading):
    """Heading with cross-reference metadata"""
    id: str = ""
    section_number: str = ""  # e.g., "1.2.3"


@dataclass
class Footnote:
    """Footnote with back-reference"""
    id: str
    content: List[InlineElement]
    referenced_by: List[Any] = field(default_factory=list)  # blocks that reference this


@dataclass
class Citation:
    """Citation with bibliography reference"""
    key: str
    bibliography_entry: Optional['BibliographyEntry'] = None


@dataclass
class BibliographyEntry:
    """Bibliography entry"""
    key: str
    title: str
    authors: List[str]
    year: int
    cited_by: List[Any] = field(default_factory=list)  # elements that cite this


@dataclass
class Section:
    """Document section with hierarchy"""
    heading: Heading
    start_block: int
    end_block: int
    subsections: List['Section'] = field(default_factory=list)
    level: int = 1
