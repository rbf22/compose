"""
Constraint solver.

Iteratively resolves layout constraints until satisfied.
"""

from typing import List, TYPE_CHECKING, Optional
from .constraint_primitives import LayoutState, Violation, Severity
from .layout_rules import LayoutRule

if TYPE_CHECKING:
    from .layout_generator import LayoutGenerator


class ConstraintSolver:
    """
    Iteratively resolves layout constraints.
    
    Applies rules, detects violations, generates adjustments,
    and regenerates layout until all constraints are satisfied.
    """
    
    def __init__(self, rules: List[LayoutRule], max_iterations: int = 10, 
                 verbose: bool = True):
        """
        Initialize solver.
        
        Args:
            rules: List of layout rules to check
            max_iterations: Maximum iterations before giving up
            verbose: Print progress information
        """
        self.rules = rules
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.iteration_history = []
    
    def solve(self, initial_state: LayoutState, 
             generator: 'LayoutGenerator') -> LayoutState:
        """
        Iteratively solve constraints.
        
        Args:
            initial_state: Initial layout state
            generator: Layout generator for regeneration
            
        Returns:
            Final layout state with constraints satisfied
        """
        current_state = initial_state
        
        for iteration in range(self.max_iterations):
            if self.verbose:
                print(f"\n{'='*60}")
                print(f"Constraint Solving - Iteration {iteration + 1}/{self.max_iterations}")
                print(f"{'='*60}")
            
            # Check all rules
            violations = self._check_all_rules(current_state)
            
            # Record history
            self.iteration_history.append({
                'iteration': iteration,
                'violations': len(violations),
                'details': violations
            })
            
            if not violations:
                if self.verbose:
                    print(f"\n✓ SUCCESS: Layout converged - no violations found")
                return current_state
            
            # Print violations
            if self.verbose:
                self._print_violations(violations)
            
            # Generate adjustments
            adjustments = self._generate_adjustments(violations, current_state)
            
            if not adjustments:
                if self.verbose:
                    print(f"\n⚠ WARNING: No adjustments possible")
                    print(f"  {len(violations)} violations remain")
                return current_state
            
            if self.verbose:
                print(f"\nApplying {len(adjustments)} adjustment(s)...")
            
            # Apply adjustments and regenerate
            current_state = generator.regenerate_with_adjustments(
                current_state,
                adjustments
            )
        
        if self.verbose:
            print(f"\n⚠ WARNING: Max iterations ({self.max_iterations}) reached")
            print(f"  Layout may have unresolved violations")
        
        return current_state
    
    def _check_all_rules(self, state: LayoutState) -> List[Violation]:
        """
        Check all rules against state.
        
        Args:
            state: Layout state to check
            
        Returns:
            List of all violations found
        """
        violations = []
        
        for rule in self.rules:
            rule_violations = rule.check(state)
            violations.extend(rule_violations)
        
        return violations
    
    def _generate_adjustments(self, violations: List[Violation],
                             state: LayoutState) -> List:
        """
        Generate adjustments for violations.
        
        Prioritizes violations by severity and page order.
        
        Args:
            violations: List of violations
            state: Current layout state
            
        Returns:
            List of adjustments to apply
        """
        # Sort by severity (ERROR > WARNING > INFO) and page
        violations.sort(key=lambda v: (
            0 if v.severity == Severity.ERROR else
            1 if v.severity == Severity.WARNING else 2,
            v.page
        ))
        
        adjustments = []
        
        # Fix top violations (don't try to fix everything at once)
        for violation in violations[:3]:
            # Find rule that created this violation
            for rule in self.rules:
                rule_name = rule.__class__.__name__.replace('Rule', '').lower()
                if rule_name in violation.rule_name.lower():
                    suggested = rule.suggest_fix(violation, state)
                    adjustments.extend(suggested)
                    break
        
        return adjustments
    
    def _print_violations(self, violations: List[Violation]):
        """
        Print violations summary.
        
        Args:
            violations: List of violations to print
        """
        print(f"\nFound {len(violations)} violation(s):")
        
        # Group by severity
        by_severity = {}
        for v in violations:
            by_severity.setdefault(v.severity, []).append(v)
        
        # Print by severity
        for severity in [Severity.ERROR, Severity.WARNING, Severity.INFO]:
            if severity in by_severity:
                violations_at_level = by_severity[severity]
                print(f"\n  {severity.value.upper()}: {len(violations_at_level)}")
                
                for v in violations_at_level[:3]:  # Show first 3
                    print(f"    - Page {v.page}: {v.description}")
                
                if len(violations_at_level) > 3:
                    print(f"    ... and {len(violations_at_level) - 3} more")
    
    def print_summary(self):
        """Print summary of solving process"""
        print(f"\n{'='*60}")
        print("Constraint Solving Summary")
        print(f"{'='*60}")
        
        for entry in self.iteration_history:
            iteration = entry['iteration'] + 1
            violations = entry['violations']
            status = "✓" if violations == 0 else "✗"
            print(f"  Iteration {iteration}: {status} {violations} violation(s)")
        
        if self.iteration_history:
            final_violations = self.iteration_history[-1]['violations']
            if final_violations == 0:
                iterations = len(self.iteration_history)
                print(f"\n✓ Converged in {iterations} iteration(s)")
            else:
                print(f"\n⚠ Did not converge - {final_violations} violations remain")
