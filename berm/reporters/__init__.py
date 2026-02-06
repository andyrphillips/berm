"""Output formatters for policy violations."""

from berm.reporters.terminal import TerminalReporter
from berm.reporters.github import GitHubReporter
from berm.reporters.json_reporter import JSONReporter

__all__ = ["TerminalReporter", "GitHubReporter", "JSONReporter"]


def get_reporter(format: str):
    """Factory function to get reporter by format name.

    Args:
        format: One of 'terminal', 'github', or 'json'

    Returns:
        Reporter instance

    Raises:
        ValueError: If format is not supported
    """
    reporters = {
        "terminal": TerminalReporter,
        "github": GitHubReporter,
        "json": JSONReporter,
    }

    if format not in reporters:
        raise ValueError(
            f"Unsupported format: {format}. Choose from: {', '.join(reporters.keys())}"
        )

    return reporters[format]()
