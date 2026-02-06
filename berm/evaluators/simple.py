"""Simple property-based rule evaluator."""

from typing import Any, Dict, List

from berm.models.rule import Rule
from berm.models.violation import Violation
from berm.loaders.terraform import get_nested_property


class SimpleEvaluator:
    """Evaluates rules by checking property values against expected values.

    This evaluator supports basic equality checks on resource properties
    using dot notation for nested access.
    """

    def evaluate(
        self, rule: Rule, resources: List[Dict[str, Any]]
    ) -> List[Violation]:
        """Evaluate a rule against a list of resources.

        Args:
            rule: The policy rule to evaluate
            resources: List of normalized resource dictionaries from Terraform plan

        Returns:
            List of violations found (empty if all resources comply)
        """
        violations = []

        # Filter resources by type
        matching_resources = [
            r for r in resources if r["type"] == rule.resource_type
        ]

        # Evaluate each matching resource
        for resource in matching_resources:
            violation = self._check_resource(rule, resource)
            if violation:
                violations.append(violation)

        return violations

    def _check_resource(
        self, rule: Rule, resource: Dict[str, Any]
    ) -> Violation | None:
        """Check a single resource against a rule.

        Args:
            rule: The policy rule to check
            resource: Normalized resource dictionary

        Returns:
            Violation if rule is violated, None if resource complies
        """
        resource_address = resource.get("address", "unknown")
        resource_type = resource.get("type", "unknown")
        values = resource.get("values", {})

        # Get the property value using dot notation
        actual_value = get_nested_property(values, rule.property)

        # Check if property exists
        if actual_value is None:
            # Property doesn't exist - this is a violation
            message = rule.format_message(resource_address)
            return Violation(
                rule_id=rule.id,
                rule_name=rule.name,
                resource_name=resource_address,
                resource_type=resource_type,
                severity=rule.severity,
                message=f"{message} (property '{rule.property}' not found)",
            )

        # Compare actual value to expected value
        if not self._values_match(actual_value, rule.equals):
            message = rule.format_message(resource_address)
            return Violation(
                rule_id=rule.id,
                rule_name=rule.name,
                resource_name=resource_address,
                resource_type=resource_type,
                severity=rule.severity,
                message=f"{message} (expected '{rule.equals}', got '{actual_value}')",
            )

        # No violation - resource complies
        return None

    def _values_match(self, actual: Any, expected: Any) -> bool:
        """Compare two values for equality.

        Handles type coercion for common cases (e.g., "true" vs True).

        Args:
            actual: The actual value from the resource
            expected: The expected value from the rule

        Returns:
            True if values match, False otherwise
        """
        # Direct equality check
        if actual == expected:
            return True

        # Handle boolean string comparisons
        if isinstance(expected, bool) and isinstance(actual, str):
            if expected is True and actual.lower() in ("true", "yes", "1"):
                return True
            if expected is False and actual.lower() in ("false", "no", "0"):
                return True

        if isinstance(actual, bool) and isinstance(expected, str):
            if actual is True and expected.lower() in ("true", "yes", "1"):
                return True
            if actual is False and expected.lower() in ("false", "no", "0"):
                return True

        # Handle numeric string comparisons
        if isinstance(expected, (int, float)) and isinstance(actual, str):
            try:
                return float(actual) == float(expected)
            except (ValueError, TypeError):
                pass

        if isinstance(actual, (int, float)) and isinstance(expected, str):
            try:
                return float(actual) == float(expected)
            except (ValueError, TypeError):
                pass

        # Values don't match
        return False

    def evaluate_all(
        self, rules: List[Rule], resources: List[Dict[str, Any]]
    ) -> List[Violation]:
        """Evaluate all rules against all resources.

        Args:
            rules: List of policy rules to evaluate
            resources: List of normalized resource dictionaries

        Returns:
            Combined list of all violations found
        """
        all_violations = []

        for rule in rules:
            violations = self.evaluate(rule, resources)
            all_violations.extend(violations)

        return all_violations
