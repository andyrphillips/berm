"""Violation model for policy check results."""

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class Violation:
    """Represents a policy rule violation found during evaluation.

    A violation occurs when a resource doesn't meet the requirements
    specified in a policy rule.

    Attributes:
        rule_id: Unique identifier of the violated rule
        rule_name: Human-readable name of the violated rule
        resource_name: Name/address of the resource that violated the rule
        resource_type: Type of the resource (e.g., 'aws_s3_bucket')
        severity: Severity level ('error' or 'warning')
        message: Formatted error message explaining the violation
        location: Optional file location (for future use with HCL parsing)
    """

    rule_id: str
    rule_name: str
    resource_name: str
    resource_type: str
    severity: Literal["error", "warning"]
    message: str
    location: Optional[str] = None

    def is_error(self) -> bool:
        """Check if this violation is an error (not just a warning).

        Returns:
            True if severity is 'error', False if 'warning'
        """
        return self.severity == "error"

    def is_warning(self) -> bool:
        """Check if this violation is a warning (not an error).

        Returns:
            True if severity is 'warning', False if 'error'
        """
        return self.severity == "warning"

    def format_compact(self) -> str:
        """Format violation as a compact single-line string.

        Returns:
            Compact representation for logging or simple output
        """
        severity_prefix = "ERROR" if self.is_error() else "WARN"
        return f"[{severity_prefix}] {self.resource_name} ({self.resource_type}): {self.message}"

    def format_detailed(self) -> str:
        """Format violation with detailed information.

        Returns:
            Multi-line detailed representation
        """
        lines = [
            f"Severity: {self.severity.upper()}",
            f"Rule: {self.rule_name} ({self.rule_id})",
            f"Resource: {self.resource_name} ({self.resource_type})",
            f"Message: {self.message}",
        ]
        if self.location:
            lines.append(f"Location: {self.location}")
        return "\n".join(lines)

    def __str__(self) -> str:
        """String representation using compact format."""
        return self.format_compact()

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"Violation(rule_id='{self.rule_id}', resource_name='{self.resource_name}', "
            f"severity='{self.severity}')"
        )
