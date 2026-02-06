"""Loader for policy rule files."""

import json
from pathlib import Path
from typing import List

from pydantic import ValidationError

from berm.models.rule import Rule
from berm.security import (
    MAX_FILE_SIZE,
    SecurityError,
    validate_file_size,
    validate_json_depth,
    validate_safe_directory,
    validate_safe_path,
)


class RuleLoadError(Exception):
    """Exception raised when rule loading fails."""

    pass


def load_rules(rules_path: str, _allow_absolute: bool = False) -> List[Rule]:
    """Load and validate all rules from a directory.

    Recursively discovers all .json files in the specified directory,
    parses them, and validates them against the Rule schema.

    Args:
        rules_path: Path to directory containing rule JSON files
        _allow_absolute: Internal parameter for testing - allows absolute paths

    Returns:
        List of validated Rule objects

    Raises:
        RuleLoadError: If rules_path doesn't exist, isn't a directory,
                      or if any rule fails validation
    """
    # Validate and sanitize the directory path (prevents path traversal)
    try:
        path = validate_safe_directory(
            rules_path,
            must_exist=True,
            allow_absolute=_allow_absolute,
        )
    except (SecurityError, ValueError) as e:
        raise RuleLoadError(f"Security validation failed: {e}")

    # Find all JSON files recursively
    rule_files = list(path.rglob("*.json"))

    if not rule_files:
        raise RuleLoadError(f"No rule files (*.json) found in: {rules_path}")

    # Load and validate each rule
    rules = []
    errors = []

    for rule_file in rule_files:
        try:
            # Validate each rule file is within the rules directory
            # and check file size to prevent DoS
            try:
                validate_safe_path(
                    str(rule_file),
                    base_dir=str(path),
                    must_exist=True,
                    allowed_extensions={".json"},
                    allow_absolute=_allow_absolute,
                )
                validate_file_size(rule_file, max_size=MAX_FILE_SIZE)
            except (SecurityError, ValueError) as e:
                errors.append(f"{rule_file}: Security validation failed - {e}")
                continue

            with open(rule_file, "r", encoding="utf-8") as f:
                rule_data = json.load(f)

            # Validate JSON depth to prevent DoS
            validate_json_depth(rule_data)

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


def load_single_rule(rule_file_path: str, _allow_absolute: bool = False) -> Rule:
    """Load and validate a single rule file.

    Args:
        rule_file_path: Path to a single rule JSON file
        _allow_absolute: Internal parameter for testing - allows absolute paths

    Returns:
        Validated Rule object

    Raises:
        RuleLoadError: If file doesn't exist or validation fails
    """
    # Validate and sanitize the file path
    try:
        path = validate_safe_path(
            rule_file_path,
            must_exist=True,
            allowed_extensions={".json"},
            allow_absolute=_allow_absolute,
        )
        validate_file_size(path, max_size=MAX_FILE_SIZE)
    except (SecurityError, ValueError) as e:
        raise RuleLoadError(f"Security validation failed: {e}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            rule_data = json.load(f)

        # Validate JSON depth to prevent DoS
        validate_json_depth(rule_data)

        return Rule(**rule_data)

    except json.JSONDecodeError as e:
        raise RuleLoadError(f"Invalid JSON in {rule_file_path}: {e}")

    except ValidationError as e:
        raise RuleLoadError(f"Rule validation failed for {rule_file_path}: {e}")

    except Exception as e:
        raise RuleLoadError(f"Error loading rule from {rule_file_path}: {e}")
