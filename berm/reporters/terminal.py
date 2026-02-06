"""Terminal reporter with rich formatting."""

from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from berm.models.violation import Violation


class TerminalReporter:
    """Reports violations to the terminal with colored output.

    Uses the Rich library for beautiful terminal formatting with
    colors, tables, and clear visual hierarchy.
    """

    def __init__(self) -> None:
        """Initialize the terminal reporter."""
        self.console = Console()

    def report(self, violations: List[Violation]) -> None:
        """Report violations to the terminal.

        Args:
            violations: List of violations to report
        """
        if not violations:
            self._report_success()
            return

        # Separate errors and warnings
        errors = [v for v in violations if v.is_error()]
        warnings = [v for v in violations if v.is_warning()]

        # Print errors
        if errors:
            self._print_violations(errors, "Errors", "red")

        # Print warnings
        if warnings:
            self._print_violations(warnings, "Warnings", "yellow")

        # Print summary
        self._print_summary(errors, warnings)

    def _report_success(self) -> None:
        """Report successful validation with no violations."""
        success_text = Text()
        success_text.append("✓", style="bold green")
        success_text.append(" All policy checks passed!", style="bold green")

        panel = Panel(
            success_text,
            border_style="green",
            padding=(1, 2),
        )
        self.console.print()
        self.console.print(panel)
        self.console.print()

    def _print_violations(
        self, violations: List[Violation], title: str, color: str
    ) -> None:
        """Print a list of violations with formatting.

        Args:
            violations: List of violations to print
            title: Section title (e.g., "Errors", "Warnings")
            color: Color to use for styling
        """
        self.console.print()
        self.console.print(f"[bold {color}]{title} ({len(violations)}):[/bold {color}]")
        self.console.print()

        # Create table
        table = Table(
            show_header=True,
            header_style=f"bold {color}",
            border_style=color,
            padding=(0, 1),
        )

        table.add_column("Resource", style="cyan", no_wrap=False)
        table.add_column("Rule", style="white", no_wrap=False)
        table.add_column("Message", style="white", no_wrap=False)

        # Add rows
        for violation in violations:
            table.add_row(
                violation.resource_name,
                violation.rule_name,
                violation.message,
            )

        self.console.print(table)

    def _print_summary(self, errors: List[Violation], warnings: List[Violation]) -> None:
        """Print summary of violations.

        Args:
            errors: List of error violations
            warnings: List of warning violations
        """
        self.console.print()

        summary_text = Text()
        summary_text.append("Summary: ", style="bold")

        if errors:
            summary_text.append(f"{len(errors)} error(s)", style="bold red")
        else:
            summary_text.append("0 errors", style="green")

        summary_text.append(", ")

        if warnings:
            summary_text.append(f"{len(warnings)} warning(s)", style="bold yellow")
        else:
            summary_text.append("0 warnings", style="green")

        self.console.print(summary_text)
        self.console.print()
