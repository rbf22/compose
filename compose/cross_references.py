# compose/cross_references.py
"""
Cross-reference system for Compose documents.

Provides automatic numbering and linking for figures, tables, sections,
equations, and other referenceable elements.
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum


class ReferenceType(Enum):
    """Types of referenceable elements"""
    FIGURE = "figure"
    TABLE = "table"
    EQUATION = "equation"
    SECTION = "section"
    LISTING = "listing"
    FOOTNOTE = "footnote"


class ReferenceStyle(Enum):
    """Numbering styles for references"""
    DECIMAL = "decimal"        # 1, 2, 3, ...
    ALPHABETIC = "alphabetic"  # a, b, c, ... or A, B, C, ...
    ROMAN = "roman"           # i, ii, iii, ... or I, II, III, ...


class CrossReferenceManager:
    """
    Manages cross-references throughout a document.

    Tracks referenceable elements, assigns numbers, and resolves references.
    """

    def __init__(self):
        self._counters: Dict[ReferenceType, int] = {}
        self._references: Dict[str, Dict[str, Any]] = {}
        self._pending_refs: List[Dict[str, Any]] = []
        self._style = ReferenceStyle.DECIMAL

    def reset_counters(self):
        """Reset all reference counters"""
        self._counters.clear()

    def set_numbering_style(self, style: ReferenceStyle):
        """Set the numbering style for references"""
        self._style = style

    def register_reference(self, ref_type: ReferenceType, label: str,
                          title: str = "", location: Any = None) -> str:
        """
        Register a new referenceable element.

        Args:
            ref_type: Type of reference (figure, table, etc.)
            label: Unique identifier for the reference
            title: Human-readable title/caption
            location: Location information (page, position, etc.)

        Returns:
            The assigned reference number as a string
        """
        # Increment counter for this type
        if ref_type not in self._counters:
            self._counters[ref_type] = 0
        self._counters[ref_type] += 1

        number = self._counters[ref_type]
        number_str = self._format_number(number)

        # Store reference information
        self._references[label] = {
            'type': ref_type,
            'number': number,
            'number_str': number_str,
            'label': label,
            'title': title,
            'location': location
        }

        return number_str

    def resolve_reference(self, label: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a reference by label.

        Args:
            label: The reference label to resolve

        Returns:
            Reference information, or None if not found
        """
        return self._references.get(label)

    def get_reference_text(self, label: str, include_type: bool = True) -> str:
        """
        Get the formatted reference text for a label.

        Args:
            label: Reference label
            include_type: Whether to include the type prefix (e.g., "Figure 1")

        Returns:
            Formatted reference text
        """
        ref = self.resolve_reference(label)
        if not ref:
            return f"[?? {label}]"

        if include_type:
            type_name = ref['type'].value.capitalize()
            return f"{type_name} {ref['number_str']}"
        else:
            return ref['number_str']

    def add_pending_reference(self, label: str, context: str = ""):
        """
        Add a pending reference that will be resolved later.

        Args:
            label: The reference label
            context: Context information for error reporting
        """
        self._pending_refs.append({
            'label': label,
            'context': context,
            'resolved': False
        })

    def resolve_pending_references(self) -> List[str]:
        """
        Resolve all pending references and return any errors.

        Returns:
            List of error messages for unresolved references
        """
        errors = []
        for pending in self._pending_refs:
            if not self.resolve_reference(pending['label']):
                errors.append(f"Unresolved reference '{pending['label']}' in {pending['context']}")

        # Clear pending refs
        self._pending_refs.clear()
        return errors

    def get_all_references(self, ref_type: Optional[ReferenceType] = None) -> List[Dict[str, Any]]:
        """
        Get all registered references, optionally filtered by type.

        Args:
            ref_type: Optional type filter

        Returns:
            List of reference dictionaries
        """
        refs = list(self._references.values())
        if ref_type:
            refs = [r for r in refs if r['type'] == ref_type]
        return sorted(refs, key=lambda x: x['number'])

    def get_reference_list(self, ref_type: ReferenceType) -> str:
        """
        Generate a formatted list of all references of a given type.

        Args:
            ref_type: Type of references to list

        Returns:
            Formatted reference list as a string
        """
        refs = self.get_all_references(ref_type)
        if not refs:
            return ""

        lines = [f"{ref_type.value.capitalize()} List:"]
        for ref in refs:
            lines.append(f"  {ref['number_str']}: {ref['title']}")

        return "\n".join(lines)

    def _format_number(self, number: int) -> str:
        """Format a number according to the current style"""
        if self._style == ReferenceStyle.DECIMAL:
            return str(number)
        elif self._style == ReferenceStyle.ALPHABETIC:
            return self._number_to_alpha(number).lower()
        elif self._style == ReferenceStyle.ROMAN:
            return self._number_to_roman(number).lower()
        else:
            return str(number)

    def _number_to_alpha(self, n: int) -> str:
        """Convert number to alphabetic representation (A, B, C, ..., AA, AB, etc.)"""
        result = ""
        while n > 0:
            n -= 1  # Adjust for 0-based indexing
            result = chr(65 + (n % 26)) + result
            n //= 26
        return result

    def _number_to_roman(self, n: int) -> str:
        """Convert number to Roman numerals"""
        roman_numerals = [
            (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
            (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
            (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
        ]

        result = ""
        for value, symbol in roman_numerals:
            while n >= value:
                result += symbol
                n -= value

        return result

    def export_references(self) -> Dict[str, Any]:
        """
        Export reference data for serialization or debugging.

        Returns:
            Dictionary containing all reference information
        """
        return {
            'counters': {k.value: v for k, v in self._counters.items()},
            'references': self._references.copy(),
            'style': self._style.value,
            'pending_count': len(self._pending_refs)
        }

    def import_references(self, data: Dict[str, Any]):
        """
        Import reference data from a previous export.

        Args:
            data: Reference data from export_references()
        """
        self._counters = {ReferenceType(k): v for k, v in data.get('counters', {}).items()}
        self._references = data.get('references', {})
        self._style = ReferenceStyle(data.get('style', 'decimal'))


# Global instance for document-wide reference management
cross_ref_manager = CrossReferenceManager()


def register_figure(label: str, caption: str = "") -> str:
    """Register a figure and return its reference number"""
    return cross_ref_manager.register_reference(ReferenceType.FIGURE, label, caption)


def register_table(label: str, caption: str = "") -> str:
    """Register a table and return its reference number"""
    return cross_ref_manager.register_reference(ReferenceType.TABLE, label, caption)


def register_equation(label: str, title: str = "") -> str:
    """Register an equation and return its reference number"""
    return cross_ref_manager.register_reference(ReferenceType.EQUATION, label, title)


def ref(label: str, include_type: bool = True) -> str:
    """Get reference text for a label"""
    return cross_ref_manager.get_reference_text(label, include_type)


def list_of_figures() -> str:
    """Generate a list of all figures"""
    return cross_ref_manager.get_reference_list(ReferenceType.FIGURE)


def list_of_tables() -> str:
    """Generate a list of all tables"""
    return cross_ref_manager.get_reference_list(ReferenceType.TABLE)


# Example usage in document processing
def process_cross_references(document) -> List[str]:
    """
    Process cross-references in a document and return any errors.

    Args:
        document: Document AST to process

    Returns:
        List of error messages for unresolved references
    """
    # Reset for new document
    cross_ref_manager.reset_counters()

    # First pass: register all referenceable elements
    _register_all_elements(document)

    # Second pass: resolve all references
    _resolve_all_references(document)

    # Return any unresolved reference errors
    return cross_ref_manager.resolve_pending_references()


def _register_all_elements(document):
    """Register all referenceable elements in the document"""
    # This would traverse the document AST and register figures, tables, etc.
    # Implementation depends on the document structure
    pass


def _resolve_all_references(document):
    """Resolve all cross-references in the document"""
    # This would traverse the document and replace reference placeholders
    # with actual reference text
    pass
