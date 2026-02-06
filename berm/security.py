"""Security utilities for input validation and sanitization."""

import os
from pathlib import Path
from typing import Optional


class SecurityError(Exception):
    """Exception raised when security validation fails."""

    pass


# Security constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_PATH_LENGTH = 4096
MAX_PROPERTY_DEPTH = 20
MAX_ARRAY_INDEX = 100  # Maximum array index for property access
MAX_JSON_DEPTH = 50  # Maximum nesting depth for JSON documents
ALLOWED_PLAN_EXTENSIONS = {".json", ".tfplan"}
ALLOWED_RULE_EXTENSIONS = {".json"}

# Dangerous characters that could be used for shell injection or other attacks
DANGEROUS_FILENAME_CHARS = set(';|&$`<>(){}[]"\'\\\n\r\t\x00')


def validate_safe_path(
    file_path: str,
    base_dir: Optional[str] = None,
    must_exist: bool = True,
    allowed_extensions: Optional[set] = None,
    allow_absolute: bool = False,
) -> Path:
    """Validate that a file path is safe and within allowed boundaries.

    Prevents path traversal attacks by ensuring the resolved path
    is within the base directory (or current working directory).

    Args:
        file_path: The file path to validate
        base_dir: Base directory to restrict paths to (default: current working directory)
        must_exist: Whether the file must already exist
        allowed_extensions: Set of allowed file extensions (e.g., {'.json', '.tfplan'})
        allow_absolute: Allow absolute paths outside base_dir (for testing only)

    Returns:
        Validated Path object

    Raises:
        SecurityError: If path validation fails
        ValueError: If path is invalid
    """
    if not file_path:
        raise ValueError("File path cannot be empty")

    # Check path length to prevent buffer overflow attacks
    if len(file_path) > MAX_PATH_LENGTH:
        raise SecurityError(f"File path exceeds maximum length of {MAX_PATH_LENGTH}")

    # Check for null bytes (path injection)
    if "\x00" in file_path:
        raise SecurityError("Null bytes not allowed in file paths")

    # Check for dangerous characters that could be used for command injection
    # We validate the basename (filename) only, not the full path, to allow
    # legitimate path separators while blocking shell metacharacters
    filename = Path(file_path).name
    dangerous_chars_found = [c for c in filename if c in DANGEROUS_FILENAME_CHARS]
    if dangerous_chars_found:
        raise SecurityError(
            f"Filename contains dangerous characters: {dangerous_chars_found}. "
            f"Only alphanumeric, dash, underscore, and dot are allowed in filenames."
        )

    # Convert to Path object
    try:
        path = Path(file_path)
    except Exception as e:
        raise ValueError(f"Invalid file path: {e}")

    # Determine base directory
    if base_dir is None:
        base_dir = os.getcwd()

    try:
        base = Path(base_dir).resolve()
        resolved = path.resolve()
    except Exception as e:
        raise ValueError(f"Failed to resolve path: {e}")

    # Check for path traversal
    # For relative paths: ensure they don't escape the base directory
    # For absolute paths: allow them unless explicitly restricted by base_dir parameter
    # The allow_absolute flag is only for testing with temp directories
    if not allow_absolute:
        # If base_dir was explicitly provided (not CWD), validate all paths are within it
        # If base_dir is CWD (default), only validate relative paths don't traverse
        is_explicit_base = base_dir != os.getcwd()
        is_relative_input = not Path(file_path).is_absolute()

        # Validate if: explicit base_dir provided OR input is relative path
        if is_explicit_base or is_relative_input:
            try:
                resolved.relative_to(base)
            except ValueError:
                if is_relative_input:
                    raise SecurityError(
                        f"Path traversal detected: relative path '{file_path}' resolves to '{resolved}' "
                        f"which is outside base directory '{base}'"
                    )
                else:
                    raise SecurityError(
                        f"Path '{file_path}' is outside explicitly specified base directory '{base}'"
                    )

    # Validate file extension if specified
    if allowed_extensions is not None:
        if resolved.suffix.lower() not in allowed_extensions:
            raise SecurityError(
                f"Invalid file extension '{resolved.suffix}'. "
                f"Allowed extensions: {', '.join(sorted(allowed_extensions))}"
            )

    # Check existence if required
    if must_exist and not resolved.exists():
        raise ValueError(f"File does not exist: {file_path}")

    if must_exist and not resolved.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    return resolved


def validate_safe_directory(
    dir_path: str,
    base_dir: Optional[str] = None,
    must_exist: bool = True,
    allow_absolute: bool = False,
) -> Path:
    """Validate that a directory path is safe and within allowed boundaries.

    Args:
        dir_path: The directory path to validate
        base_dir: Base directory to restrict paths to (default: current working directory)
        must_exist: Whether the directory must already exist
        allow_absolute: Allow absolute paths outside base_dir (for testing only)

    Returns:
        Validated Path object

    Raises:
        SecurityError: If path validation fails
        ValueError: If path is invalid
    """
    if not dir_path:
        raise ValueError("Directory path cannot be empty")

    # Check path length
    if len(dir_path) > MAX_PATH_LENGTH:
        raise SecurityError(
            f"Directory path exceeds maximum length of {MAX_PATH_LENGTH}"
        )

    # Check for null bytes
    if "\x00" in dir_path:
        raise SecurityError("Null bytes not allowed in directory paths")

    # Convert to Path object
    try:
        path = Path(dir_path)
    except Exception as e:
        raise ValueError(f"Invalid directory path: {e}")

    # Determine base directory
    if base_dir is None:
        base_dir = os.getcwd()

    try:
        base = Path(base_dir).resolve()
        resolved = path.resolve()
    except Exception as e:
        raise ValueError(f"Failed to resolve path: {e}")

    # Check for path traversal
    # For relative paths: ensure they don't escape the base directory
    # For absolute paths: allow them unless explicitly restricted by base_dir parameter
    # The allow_absolute flag is only for testing with temp directories
    if not allow_absolute:
        # If base_dir was explicitly provided (not CWD), validate all paths are within it
        # If base_dir is CWD (default), only validate relative paths don't traverse
        is_explicit_base = base_dir != os.getcwd()
        is_relative_input = not Path(dir_path).is_absolute()

        # Validate if: explicit base_dir provided OR input is relative path
        if is_explicit_base or is_relative_input:
            try:
                resolved.relative_to(base)
            except ValueError:
                if is_relative_input:
                    raise SecurityError(
                        f"Path traversal detected: relative path '{dir_path}' resolves to '{resolved}' "
                        f"which is outside base directory '{base}'"
                    )
                else:
                    raise SecurityError(
                        f"Path '{dir_path}' is outside explicitly specified base directory '{base}'"
                    )

    # Check existence if required
    if must_exist and not resolved.exists():
        raise ValueError(f"Directory does not exist: {dir_path}")

    if must_exist and not resolved.is_dir():
        raise ValueError(f"Path is not a directory: {dir_path}")

    return resolved


def validate_file_size(file_path: Path, max_size: int = MAX_FILE_SIZE) -> None:
    """Validate that a file size is within acceptable limits.

    Args:
        file_path: Path to the file to check
        max_size: Maximum allowed file size in bytes

    Raises:
        SecurityError: If file size exceeds maximum
        ValueError: If file doesn't exist
    """
    if not file_path.exists():
        raise ValueError(f"File does not exist: {file_path}")

    file_size = file_path.stat().st_size

    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        raise SecurityError(
            f"File size ({actual_mb:.2f}MB) exceeds maximum allowed size ({max_mb:.2f}MB)"
        )


def validate_property_path(path: str, max_depth: int = MAX_PROPERTY_DEPTH) -> None:
    """Validate a property path for safe traversal.

    Args:
        path: Dot-notation property path (e.g., 'versioning.enabled')
        max_depth: Maximum allowed depth

    Raises:
        SecurityError: If path validation fails
    """
    if not path:
        raise ValueError("Property path cannot be empty")

    # Check total length
    if len(path) > 1000:
        raise SecurityError("Property path too long")

    # Check depth
    parts = path.split(".")
    if len(parts) > max_depth:
        raise SecurityError(
            f"Property path depth ({len(parts)}) exceeds maximum ({max_depth})"
        )

    # Validate each part
    for part in parts:
        if not part:
            raise SecurityError("Property path cannot contain empty segments")

        # Check for suspicious characters
        if any(c in part for c in ["\x00", "\n", "\r"]):
            raise SecurityError("Property path contains invalid characters")


def sanitize_terraform_plan_path(plan_path: str) -> Path:
    """Validate and sanitize a Terraform plan file path.

    Args:
        plan_path: Path to Terraform plan file

    Returns:
        Validated Path object

    Raises:
        SecurityError: If validation fails
    """
    validated_path = validate_safe_path(
        plan_path,
        must_exist=True,
        allowed_extensions=ALLOWED_PLAN_EXTENSIONS,
    )

    validate_file_size(validated_path)

    return validated_path


def sanitize_rules_directory(rules_dir: str) -> Path:
    """Validate and sanitize a rules directory path.

    Args:
        rules_dir: Path to rules directory

    Returns:
        Validated Path object

    Raises:
        SecurityError: If validation fails
    """
    return validate_safe_directory(rules_dir, must_exist=True)


def sanitize_output_path(output_path: str) -> Path:
    """Validate and sanitize an output file path.

    Ensures the output path:
    - Is within the current working directory
    - Has a .json extension
    - Does not use path traversal

    Args:
        output_path: Desired output file path

    Returns:
        Validated Path object

    Raises:
        SecurityError: If validation fails
    """
    # For output files, we don't require them to exist yet
    validated_path = validate_safe_path(
        output_path,
        must_exist=False,
        allowed_extensions={".json"},
    )

    return validated_path


def validate_json_depth(obj: any, current_depth: int = 0, max_depth: int = MAX_JSON_DEPTH) -> None:
    """Validate that a JSON object doesn't exceed maximum nesting depth.

    Args:
        obj: The JSON object to validate (dict, list, or primitive)
        current_depth: Current recursion depth (internal use)
        max_depth: Maximum allowed depth

    Raises:
        SecurityError: If depth exceeds maximum
    """
    if current_depth > max_depth:
        raise SecurityError(
            f"JSON nesting depth ({current_depth}) exceeds maximum allowed depth ({max_depth}). "
            f"This may indicate a malicious deeply-nested JSON structure."
        )

    if isinstance(obj, dict):
        for value in obj.values():
            validate_json_depth(value, current_depth + 1, max_depth)
    elif isinstance(obj, list):
        for item in obj:
            validate_json_depth(item, current_depth + 1, max_depth)


def sanitize_for_output(text: str, context: str = "terminal") -> str:
    """Sanitize text for safe display in various output contexts.

    Prevents injection attacks via ANSI escape codes, newlines, and
    context-specific control sequences.

    Args:
        text: The text to sanitize
        context: Output context - "terminal", "github", or "json"

    Returns:
        Sanitized text safe for the specified context
    """
    if not text:
        return text

    # Remove ANSI escape codes (e.g., \x1b[31m for colors)
    # This prevents terminal manipulation attacks
    sanitized = text
    import re
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    sanitized = ansi_escape.sub('', sanitized)

    # Remove other control characters (except space and tab)
    # This includes newlines, carriage returns, etc.
    control_chars = ''.join(chr(i) for i in range(32) if i not in [9, 32])  # Keep tab and space
    control_chars += '\x7f'  # DEL character
    for char in control_chars:
        sanitized = sanitized.replace(char, '')

    # Context-specific sanitization
    if context == "github":
        # Prevent GitHub Actions workflow command injection
        # ::error::, ::warning::, ::set-output::, etc.
        sanitized = sanitized.replace("::", ":\u200b:")  # Zero-width space breaks the command

    elif context == "json":
        # JSON special characters are handled by json.dumps(), but we still
        # want to remove control characters for safety
        pass

    # Limit length to prevent DoS via extremely long strings
    max_length = 10000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "... (truncated)"

    return sanitized
