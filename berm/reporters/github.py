"""GitHub Actions reporter for workflow annotations."""

from typing import List

from berm.models.violation import Violation
from berm.security import sanitize_for_output


class GitHubReporter:
    """Reports violations as GitHub Actions annotations.

    Outputs violations in the GitHub Actions workflow command format
    so they appear as annotations in pull requests and workflow runs.

    Format: ::error file={file},line={line},title={title}::{message}
    """

    def report(self, violations: List[Violation]) -> None:
        """Report violations as GitHub Actions annotations.

        Args:
            violations: List of violations to report
        """
        if not violations:
            print("✓ All policy checks passed!")
            return

        # Separate errors and warnings
        errors = [v for v in violations if v.is_error()]
        warnings = [v for v in violations if v.is_warning()]

        # Output errors
        for violation in errors:
            self._print_annotation("error", violation)

        # Output warnings
        for violation in warnings:
            self._print_annotation("warning", violation)

        # Output summary
        self._print_summary(errors, warnings)

    def _print_annotation(self, level: str, violation: Violation) -> None:
        """Print a single GitHub Actions annotation.

        Args:
            level: 'error' or 'warning'
            violation: The violation to annotate
        """
        # GitHub Actions annotation format
        # ::{level} file={file},line={line},title={title}::{message}

        # For Terraform plan violations, we don't have file/line info yet
        # (that would come from HCL parsing in future versions)
        # So we just use the resource name as the title

        # Sanitize for GitHub context to prevent workflow command injection
        title = sanitize_for_output(violation.rule_name, context="github")
        rule_id = sanitize_for_output(violation.rule_id, context="github")
        resource_name = sanitize_for_output(violation.resource_name, context="github")
        message_text = sanitize_for_output(violation.message, context="github")
        message = f"[{rule_id}] [{resource_name}] {message_text}"

        print(f"::{level} title={title}::{message}")

    def _print_summary(self, errors: List[Violation], warnings: List[Violation]) -> None:
        """Print summary using GitHub Actions format.

        Args:
            errors: List of error violations
            warnings: List of warning violations
        """
        error_count = len(errors)
        warning_count = len(warnings)

        summary = f"Policy check found {error_count} error(s) and {warning_count} warning(s)"

        if error_count > 0:
            print(f"::error::{summary}")
        else:
            print(f"::notice::{summary}")
