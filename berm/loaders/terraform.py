"""Loader for Terraform plan JSON files."""

import json
from typing import Any, Dict, List

from berm.security import SecurityError, MAX_ARRAY_INDEX


class TerraformPlanLoadError(Exception):
    """Exception raised when Terraform plan loading fails."""

    pass


def load_terraform_plan(plan_path: str, _allow_absolute: bool = False) -> List[Dict[str, Any]]:
    """Load and parse a Terraform plan JSON file.

    Extracts resource changes from the plan and normalizes them for evaluation.
    Only includes resources that are being created or updated (not deleted or no-op).

    Args:
        plan_path: Path to Terraform plan JSON file (output of 'terraform show -json')
        _allow_absolute: Internal parameter for testing - allows absolute paths

    Returns:
        List of resource dictionaries with normalized structure:
        [
            {
                "address": "aws_s3_bucket.example",
                "type": "aws_s3_bucket",
                "name": "example",
                "values": {...}  # Resource configuration
            },
            ...
        ]

    Raises:
        TerraformPlanLoadError: If file doesn't exist, isn't valid JSON,
                               or doesn't have expected structure
    """
    # Validate and sanitize the path (prevents path traversal, checks file size)
    try:
        from berm.security import validate_safe_path, validate_file_size, validate_json_depth, ALLOWED_PLAN_EXTENSIONS

        path = validate_safe_path(
            plan_path,
            must_exist=True,
            allowed_extensions=ALLOWED_PLAN_EXTENSIONS,
            allow_absolute=_allow_absolute,
        )
        validate_file_size(path)
    except (SecurityError, ValueError) as e:
        raise TerraformPlanLoadError(f"Security validation failed: {e}")

    # Load and parse JSON
    try:
        # Use utf-8-sig to handle UTF-8 BOM if present (common in Windows)
        with open(path, "r", encoding="utf-8-sig") as f:
            plan_data = json.load(f)

        # Validate JSON depth to prevent DoS via deeply nested structures
        validate_json_depth(plan_data)
    except json.JSONDecodeError as e:
        raise TerraformPlanLoadError(f"Invalid JSON in plan file: {e}")
    except SecurityError as e:
        raise TerraformPlanLoadError(f"Security validation failed: {e}")
    except Exception as e:
        raise TerraformPlanLoadError(f"Error reading plan file: {e}")

    # Validate plan structure
    if not isinstance(plan_data, dict):
        raise TerraformPlanLoadError("Plan file must contain a JSON object")

    # Extract resource_changes
    resource_changes = plan_data.get("resource_changes", [])

    if not isinstance(resource_changes, list):
        raise TerraformPlanLoadError(
            "Plan file 'resource_changes' must be a list"
        )

    # Normalize resources
    resources = []

    for change in resource_changes:
        try:
            # Skip if not a valid resource change
            if not isinstance(change, dict):
                continue

            # Get action type
            actions = change.get("change", {}).get("actions", [])

            # Skip resources being deleted or no-op
            if not actions or actions == ["delete"] or actions == ["no-op"]:
                continue

            # Extract resource details
            address = change.get("address", "")
            resource_type = change.get("type", "")
            name = change.get("name", "")

            # Get the 'after' values (planned configuration)
            # For creates, this is in 'after'
            # For updates, 'after' contains the new values
            values = change.get("change", {}).get("after", {})

            # If 'after' is None, try 'after_unknown' or 'before'
            if values is None:
                values = change.get("change", {}).get("before", {})

            if values is None:
                values = {}

            # Build normalized resource
            resource = {
                "address": address,
                "type": resource_type,
                "name": name,
                "values": values,
            }

            resources.append(resource)

        except Exception as e:
            # Log warning but continue processing other resources
            # In production, might want proper logging here
            continue

    return resources


def get_resource_by_type(
    resources: List[Dict[str, Any]], resource_type: str
) -> List[Dict[str, Any]]:
    """Filter resources by type.

    Args:
        resources: List of normalized resource dictionaries
        resource_type: Terraform resource type (e.g., 'aws_s3_bucket')

    Returns:
        List of resources matching the specified type
    """
    return [r for r in resources if r["type"] == resource_type]


def get_nested_property(obj: Dict[str, Any], path: str) -> Any:
    """Get a nested property from an object using dot notation.

    Supports accessing nested dictionaries and list indices.
    Returns None if path doesn't exist.

    Args:
        obj: Dictionary to traverse
        path: Dot-notation path (e.g., 'versioning.enabled' or 'rules.0.status')

    Returns:
        Value at the specified path, or None if not found

    Examples:
        >>> obj = {"a": {"b": {"c": 123}}}
        >>> get_nested_property(obj, "a.b.c")
        123

        >>> obj = {"items": [{"name": "first"}, {"name": "second"}]}
        >>> get_nested_property(obj, "items.0.name")
        'first'
    """
    if not obj or not path:
        return None

    # Security: validate path before traversal
    from berm.security import validate_property_path

    try:
        validate_property_path(path)
    except (ValueError, SecurityError):
        # Invalid property path - return None instead of raising
        # This allows graceful handling of malformed rules
        return None

    parts = path.split(".")
    current = obj

    for part in parts:
        if current is None:
            return None

        # Handle list index access (e.g., "0", "1", "2")
        if isinstance(current, list):
            try:
                index = int(part)
                # Security: prevent array index DoS with excessively large indices
                if index < 0 or index >= MAX_ARRAY_INDEX:
                    return None
                if index < len(current):
                    current = current[index]
                else:
                    return None
            except (ValueError, IndexError):
                return None

        # Handle dictionary key access
        elif isinstance(current, dict):
            current = current.get(part)

        else:
            return None

    return current
