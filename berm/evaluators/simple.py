"""Simple property-based rule evaluator."""

import re
from typing import Any, Dict, List

from berm.models.rule import Rule
from berm.models.violation import Violation
from berm.loaders.terraform import get_nested_property


class SimpleEvaluator:
    """Evaluates rules by checking property values against expected values.

    Supports multiple comparison operators:
    - equals: Exact value match
    - greater_than: Numeric comparison (>)
    - greater_than_or_equal: Numeric comparison (>=)
    - less_than: Numeric comparison (<)
    - less_than_or_equal: Numeric comparison (<=)
    - contains: String/list contains check
    - in: Value must be in list
    - regex_match: Regular expression pattern match

    Uses dot notation for nested property access.
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

        # Check if this is a forbidden resource rule
        if rule.resource_forbidden is True:
            # Any instance of this resource type is a violation
            # Note: message formatting without context here; will be sanitized by reporters
            message = rule.format_message(resource_address, output_context="terminal")
            return Violation(
                rule_id=rule.id,
                rule_name=rule.name,
                resource_name=resource_address,
                resource_type=resource_type,
                severity=rule.severity,
                message=message,
            )

        # For property-based rules, get the property value using dot notation
        actual_value = get_nested_property(values, rule.property)

        # Check if property exists
        if actual_value is None:
            # Property doesn't exist - this is a violation
            # Note: message formatting without context here; will be sanitized by reporters
            message = rule.format_message(resource_address, output_context="terminal")
            return Violation(
                rule_id=rule.id,
                rule_name=rule.name,
                resource_name=resource_address,
                resource_type=resource_type,
                severity=rule.severity,
                message=f"{message} (property '{rule.property}' not found)",
            )

        # Determine which comparison to perform
        if rule.equals is not None:
            passes = self._check_equals(actual_value, rule.equals)
            operator_desc = f"equals '{rule.equals}'"
        elif rule.greater_than is not None:
            passes = self._check_greater_than(actual_value, rule.greater_than)
            operator_desc = f"> {rule.greater_than}"
        elif rule.greater_than_or_equal is not None:
            passes = self._check_greater_than_or_equal(
                actual_value, rule.greater_than_or_equal
            )
            operator_desc = f">= {rule.greater_than_or_equal}"
        elif rule.less_than is not None:
            passes = self._check_less_than(actual_value, rule.less_than)
            operator_desc = f"< {rule.less_than}"
        elif rule.less_than_or_equal is not None:
            passes = self._check_less_than_or_equal(actual_value, rule.less_than_or_equal)
            operator_desc = f"<= {rule.less_than_or_equal}"
        elif rule.contains is not None:
            passes = self._check_contains(actual_value, rule.contains)
            operator_desc = f"contains '{rule.contains}'"
        elif rule.in_list is not None:
            passes = self._check_in_list(actual_value, rule.in_list)
            operator_desc = f"in {rule.in_list}"
        elif rule.regex_match is not None:
            passes = self._check_regex_match(actual_value, rule.regex_match)
            operator_desc = f"matches pattern '{rule.regex_match}'"
        else:
            # Should never happen due to model validation
            passes = False
            operator_desc = "unknown"

        if not passes:
            # Note: message formatting without context here; will be sanitized by reporters
            message = rule.format_message(resource_address, output_context="terminal")
            return Violation(
                rule_id=rule.id,
                rule_name=rule.name,
                resource_name=resource_address,
                resource_type=resource_type,
                severity=rule.severity,
                message=f"{message} (expected {operator_desc}, got '{actual_value}')",
            )

        # No violation - resource complies
        return None

    def _check_equals(self, actual: Any, expected: Any) -> bool:
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

    def _check_greater_than(self, actual: Any, expected: int | float) -> bool:
        """Check if actual value is greater than expected.

        Args:
            actual: The actual value from the resource
            expected: The expected threshold value

        Returns:
            True if actual > expected, False otherwise
        """
        try:
            actual_num = float(actual)
            return actual_num > expected
        except (ValueError, TypeError):
            return False

    def _check_greater_than_or_equal(self, actual: Any, expected: int | float) -> bool:
        """Check if actual value is greater than or equal to expected.

        Args:
            actual: The actual value from the resource
            expected: The expected threshold value

        Returns:
            True if actual >= expected, False otherwise
        """
        try:
            actual_num = float(actual)
            return actual_num >= expected
        except (ValueError, TypeError):
            return False

    def _check_less_than(self, actual: Any, expected: int | float) -> bool:
        """Check if actual value is less than expected.

        Args:
            actual: The actual value from the resource
            expected: The expected threshold value

        Returns:
            True if actual < expected, False otherwise
        """
        try:
            actual_num = float(actual)
            return actual_num < expected
        except (ValueError, TypeError):
            return False

    def _check_less_than_or_equal(self, actual: Any, expected: int | float) -> bool:
        """Check if actual value is less than or equal to expected.

        Args:
            actual: The actual value from the resource
            expected: The expected threshold value

        Returns:
            True if actual <= expected, False otherwise
        """
        try:
            actual_num = float(actual)
            return actual_num <= expected
        except (ValueError, TypeError):
            return False

    def _check_contains(self, actual: Any, expected: str) -> bool:
        """Check if actual value contains the expected substring/element.

        Works with strings (substring match) and lists (element match).

        Args:
            actual: The actual value from the resource (string or list)
            expected: The substring/element to search for

        Returns:
            True if actual contains expected, False otherwise
        """
        try:
            if isinstance(actual, str):
                # String substring match
                return expected in actual
            elif isinstance(actual, list):
                # List element match
                return expected in actual
            else:
                # Try converting to string for other types
                return expected in str(actual)
        except (ValueError, TypeError):
            return False

    def _check_in_list(self, actual: Any, expected_list: List[Any]) -> bool:
        """Check if actual value is in the expected list.

        Args:
            actual: The actual value from the resource
            expected_list: The list of allowed values

        Returns:
            True if actual is in expected_list, False otherwise
        """
        try:
            # Direct membership check
            if actual in expected_list:
                return True

            # Try type coercion for common cases
            for expected in expected_list:
                if self._check_equals(actual, expected):
                    return True

            return False
        except (ValueError, TypeError):
            return False

    def _check_regex_match(self, actual: Any, pattern: str) -> bool:
        """Check if actual value matches the regex pattern.

        Args:
            actual: The actual value from the resource
            pattern: The regular expression pattern to match

        Returns:
            True if actual matches pattern, False otherwise
        """
        try:
            # Convert actual to string if needed
            actual_str = str(actual) if not isinstance(actual, str) else actual

            # Compile and match pattern
            regex = re.compile(pattern)
            return regex.search(actual_str) is not None
        except (re.error, ValueError, TypeError):
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
