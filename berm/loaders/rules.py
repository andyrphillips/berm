"""Loader for policy rule files."""

import json
from pathlib import Path
from typing import List

from pydantic import ValidationError

from berm.models.rule import Rule


class RuleLoadError(Exception):
    """Exception raised when rule loading fails."""

    pass


def load_rules(rules_path: str) -> List[Rule]:
    """Load and validate all rules from a directory.

    Recursively discovers all .json files in the specified directory,
    parses them, and validates them against the Rule schema.

    Args:
        rules_path: Path to directory containing rule JSON files

    Returns:
        List of validated Rule objects

    Raises:
        RuleLoadError: If rules_path doesn't exist, isn't a directory,
                      or if any rule fails validation
    """
    path = Path(rules_path)

    # Validate path exists and is a directory
    if not path.exists():
        raise RuleLoadError(f"Rules path does not exist: {rules_path}")

    if not path.is_dir():
        raise RuleLoadError(f"Rules path is not a directory: {rules_path}")

    # Find all JSON files recursively
    rule_files = list(path.rglob("*.json"))

    if not rule_files:
        raise RuleLoadError(f"No rule files (*.json) found in: {rules_path}")

    # Load and validate each rule
    rules = []
    errors = []

    for rule_file in rule_files:
        try:
            with open(rule_file, "r", encoding="utf-8") as f:
                rule_data = json.load(f)

            # Validate against Rule schema
            rule = Rule(**rule_data)
            rules.append(rule)

        except json.JSONDecodeError as e:
            errors.append(f"{rule_file}: Invalid JSON - {e}")

        except ValidationError as e:
            errors.append(f"{rule_file}: Validation failed - {e}")

        except Exception as e:
            errors.append(f"{rule_file}: Unexpected error - {e}")

    # If any rules failed to load, raise error with all details
    if errors:
        error_msg = "Failed to load one or more rules:\n" + "\n".join(errors)
        raise RuleLoadError(error_msg)

    # Sort rules by ID for consistent ordering
    rules.sort(key=lambda r: r.id)

    return rules


def load_single_rule(rule_file_path: str) -> Rule:
    """Load and validate a single rule file.

    Args:
        rule_file_path: Path to a single rule JSON file

    Returns:
        Validated Rule object

    Raises:
        RuleLoadError: If file doesn't exist or validation fails
    """
    path = Path(rule_file_path)

    if not path.exists():
        raise RuleLoadError(f"Rule file does not exist: {rule_file_path}")

    if not path.is_file():
        raise RuleLoadError(f"Rule path is not a file: {rule_file_path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            rule_data = json.load(f)

        return Rule(**rule_data)

    except json.JSONDecodeError as e:
        raise RuleLoadError(f"Invalid JSON in {rule_file_path}: {e}")

    except ValidationError as e:
        raise RuleLoadError(f"Rule validation failed for {rule_file_path}: {e}")

    except Exception as e:
        raise RuleLoadError(f"Error loading rule from {rule_file_path}: {e}")
