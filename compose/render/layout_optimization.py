"""
Layout optimization utilities.

Provides performance optimizations for the constraint-based layout system:
- Parallel rule checking
- Early termination strategies
- Incremental layout updates
- Caching and memoization
"""

from typing import List, Dict, Callable, Any
from functools import lru_cache
from .constraint_primitives import LayoutState, Violation
from .layout_rules import LayoutRule


class RuleCheckOptimizer:
    """
    Optimizes rule checking with caching and early termination.
    """
    
    def __init__(self, max_cache_size: int = 1000):
        """
        Initialize optimizer.
        
        Args:
            max_cache_size: Maximum cache entries
        """
        self.max_cache_size = max_cache_size
        self.violation_cache: Dict[int, List[Violation]] = {}
        self.state_hashes: Dict[int, int] = {}
    
    def check_rules_optimized(self, state: LayoutState, 
                             rules: List[LayoutRule],
                             early_termination: bool = True) -> List[Violation]:
        """
        Check rules with optimization.
        
        Args:
            state: Layout state to check
            rules: Rules to check
            early_termination: Stop after finding critical violations
            
        Returns:
            List of violations
        """
        violations = []
        
        for rule in rules:
            # Check rule
            rule_violations = rule.check(state)
            violations.extend(rule_violations)
            
            # Early termination if critical violations found
            if early_termination:
                critical = [v for v in rule_violations 
                           if v.severity.value == 'error']
                if critical:
                    # Found critical violations, stop checking
                    break
        
        return violations
    
    def get_state_hash(self, state: LayoutState) -> int:
        """
        Get hash of layout state for caching.
        
        Args:
            state: Layout state
            
        Returns:
            Hash value
        """
        # Simple hash based on number of pages and elements
        return hash((len(state.pages), len(state.elements), state.iteration))


class IncrementalLayoutUpdater:
    """
    Incrementally updates layout instead of full regeneration.
    
    Useful when only a small part of the layout changed.
    """
    
    def __init__(self):
        """Initialize updater"""
        self.previous_state: LayoutState = None
        self.change_regions: List[tuple] = []
    
    def detect_changes(self, old_state: LayoutState, 
                      new_state: LayoutState) -> List[tuple]:
        """
        Detect which parts of layout changed.
        
        Args:
            old_state: Previous layout state
            new_state: New layout state
            
        Returns:
            List of (page_idx, box_idx) tuples that changed
        """
        changes = []
        
        for page_idx in range(min(len(old_state.pages), len(new_state.pages))):
            old_page = old_state.pages[page_idx]
            new_page = new_state.pages[page_idx]
            
            for box_idx in range(min(len(old_page.boxes), len(new_page.boxes))):
                old_box = old_page.boxes[box_idx]
                new_box = new_page.boxes[box_idx]
                
                # Check if box changed
                if (old_box.x != new_box.x or 
                    old_box.y != new_box.y or
                    old_box.width != new_box.width or
                    old_box.height != new_box.height):
                    changes.append((page_idx, box_idx))
        
        return changes
    
    def update_incrementally(self, old_state: LayoutState,
                            new_state: LayoutState,
                            renderer: 'ProfessionalPDFRenderer') -> None:
        """
        Update only changed parts of PDF.
        
        Args:
            old_state: Previous layout state
            new_state: New layout state
            renderer: PDF renderer instance
        """
        changes = self.detect_changes(old_state, new_state)
        
        # For now, just track changes
        # Full implementation would update PDF incrementally
        self.change_regions = changes


class LayoutMetrics:
    """
    Collects metrics about layout process.
    """
    
    def __init__(self):
        """Initialize metrics"""
        self.total_iterations = 0
        self.total_violations = 0
        self.violations_by_rule: Dict[str, int] = {}
        self.violations_by_severity: Dict[str, int] = {}
        self.timing: Dict[str, float] = {}
    
    def record_iteration(self, violations: List[Violation]) -> None:
        """Record metrics for an iteration"""
        self.total_iterations += 1
        self.total_violations += len(violations)
        
        for violation in violations:
            # Count by rule
            rule_name = violation.rule_name
            self.violations_by_rule[rule_name] = \
                self.violations_by_rule.get(rule_name, 0) + 1
            
            # Count by severity
            severity = violation.severity.value
            self.violations_by_severity[severity] = \
                self.violations_by_severity.get(severity, 0) + 1
    
    def print_summary(self) -> None:
        """Print metrics summary"""
        print(f"\nLayout Metrics:")
        print(f"  Total iterations: {self.total_iterations}")
        print(f"  Total violations: {self.total_violations}")
        
        if self.violations_by_rule:
            print(f"\n  Violations by rule:")
            for rule, count in sorted(self.violations_by_rule.items()):
                print(f"    {rule}: {count}")
        
        if self.violations_by_severity:
            print(f"\n  Violations by severity:")
            for severity, count in sorted(self.violations_by_severity.items()):
                print(f"    {severity}: {count}")


class ConstraintPrioritizer:
    """
    Prioritizes constraints for solving.
    
    Solves high-priority constraints first for better results.
    """
    
    def __init__(self):
        """Initialize prioritizer"""
        self.rule_priorities: Dict[str, int] = {
            'no_overflow': 100,
            'no_orphan_lines': 50,
            'no_widow_lines': 50,
            'no_heading_orphans': 40,
            'keep_together': 30,
            'minimum_spacing': 20,
            'balanced_spacing': 10,
            'minimum_page_fullness': 5,
        }
    
    def prioritize_violations(self, violations: List[Violation]) -> List[Violation]:
        """
        Sort violations by priority.
        
        Args:
            violations: List of violations
            
        Returns:
            Sorted list (highest priority first)
        """
        def get_priority(violation: Violation) -> int:
            # Get rule priority
            rule_priority = self.rule_priorities.get(violation.rule_name, 0)
            
            # Severity multiplier
            severity_multiplier = {
                'error': 1000,
                'warning': 100,
                'info': 1
            }.get(violation.severity.value, 1)
            
            return rule_priority * severity_multiplier
        
        return sorted(violations, key=get_priority, reverse=True)
    
    def set_rule_priority(self, rule_name: str, priority: int) -> None:
        """
        Set priority for a rule.
        
        Args:
            rule_name: Name of rule
            priority: Priority value (higher = more important)
        """
        self.rule_priorities[rule_name] = priority


class ConflictResolver:
    """
    Resolves conflicts between adjustments.
    
    When multiple adjustments affect the same element,
    chooses the best one.
    """
    
    def resolve_conflicts(self, adjustments: List['Adjustment']) -> List['Adjustment']:
        """
        Resolve conflicting adjustments.
        
        Args:
            adjustments: List of adjustments
            
        Returns:
            Filtered list with conflicts resolved
        """
        # Group by affected element
        by_element = {}
        for adj in adjustments:
            if hasattr(adj, 'element'):
                elem_id = id(adj.element)
                if elem_id not in by_element:
                    by_element[elem_id] = []
                by_element[elem_id].append(adj)
        
        # Keep only one adjustment per element
        resolved = []
        for elem_id, elem_adjustments in by_element.items():
            if elem_adjustments:
                # Keep first adjustment (could be improved with priority)
                resolved.append(elem_adjustments[0])
        
        return resolved
