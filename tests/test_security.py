"""Security tests for input validation and sanitization."""

import os
import tempfile
from pathlib import Path

import pytest

from berm.security import (
    MAX_FILE_SIZE,
    MAX_PROPERTY_DEPTH,
    SecurityError,
    sanitize_output_path,
    sanitize_rules_directory,
    sanitize_terraform_plan_path,
    validate_file_size,
    validate_property_path,
    validate_safe_directory,
    validate_safe_path,
)


class TestPathValidation:
    """Test path validation and sanitization."""

    def test_safe_path_within_cwd(self, tmp_path):
        """Test that valid paths within CWD are accepted."""
        # Create a test file in temp directory
        test_file = tmp_path / "test.json"
        test_file.write_text("{}")

        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = validate_safe_path("test.json", must_exist=True)
            assert result.name == "test.json"
        finally:
            os.chdir(original_cwd)

    def test_path_traversal_blocked(self, tmp_path):
        """Test that path traversal attempts are blocked."""
        test_file = tmp_path / "test.json"
        test_file.write_text("{}")

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # Try to access parent directory
            with pytest.raises(SecurityError, match="Path traversal detected"):
                validate_safe_path("../../../etc/passwd", must_exist=False)
        finally:
            os.chdir(original_cwd)

    def test_absolute_path_outside_base_blocked(self, tmp_path):
        """Test that absolute paths outside base directory are blocked."""
        test_file = tmp_path / "test.json"
        test_file.write_text("{}")

        with pytest.raises(SecurityError, match="Path traversal detected"):
            validate_safe_path("/etc/passwd", base_dir=str(tmp_path), must_exist=False)

    def test_null_byte_injection_blocked(self):
        """Test that null byte injection is blocked."""
        with pytest.raises(SecurityError, match="Null bytes not allowed"):
            validate_safe_path("test\x00.json", must_exist=False)

    def test_invalid_file_extension_blocked(self, tmp_path):
        """Test that invalid file extensions are blocked."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        with pytest.raises(SecurityError, match="Invalid file extension"):
            validate_safe_path(
                str(test_file),
                base_dir=str(tmp_path),
                allowed_extensions={".json"},
            )

    def test_path_length_limit(self):
        """Test that excessively long paths are blocked."""
        long_path = "a/" * 5000  # Creates a very long path
        with pytest.raises(SecurityError, match="exceeds maximum length"):
            validate_safe_path(long_path, must_exist=False)

    def test_empty_path_rejected(self):
        """Test that empty paths are rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_safe_path("", must_exist=False)


class TestDirectoryValidation:
    """Test directory validation."""

    def test_safe_directory_validation(self, tmp_path):
        """Test that valid directories are accepted."""
        test_dir = tmp_path / "rules"
        test_dir.mkdir()

        result = validate_safe_directory(
            str(test_dir), base_dir=str(tmp_path), must_exist=True
        )
        assert result == test_dir

    def test_directory_traversal_blocked(self, tmp_path):
        """Test that directory traversal is blocked."""
        with pytest.raises(SecurityError, match="Path traversal detected"):
            validate_safe_directory(
                "../../../etc", base_dir=str(tmp_path), must_exist=False
            )

    def test_file_as_directory_rejected(self, tmp_path):
        """Test that files are rejected when directory is expected."""
        test_file = tmp_path / "test.json"
        test_file.write_text("{}")

        with pytest.raises(ValueError, match="not a directory"):
            validate_safe_directory(
                str(test_file), base_dir=str(tmp_path), must_exist=True
            )


class TestFileSizeValidation:
    """Test file size validation."""

    def test_small_file_accepted(self, tmp_path):
        """Test that small files are accepted."""
        test_file = tmp_path / "small.json"
        test_file.write_text('{"key": "value"}')

        # Should not raise
        validate_file_size(test_file)

    def test_large_file_rejected(self, tmp_path):
        """Test that files exceeding size limit are rejected."""
        test_file = tmp_path / "large.json"
        # Create a file larger than MAX_FILE_SIZE
        with open(test_file, "wb") as f:
            f.write(b"x" * (MAX_FILE_SIZE + 1))

        with pytest.raises(SecurityError, match="exceeds maximum allowed size"):
            validate_file_size(test_file)

    def test_custom_size_limit(self, tmp_path):
        """Test custom size limits."""
        test_file = tmp_path / "test.json"
        test_file.write_text("x" * 1000)

        # Should raise with 500 byte limit
        with pytest.raises(SecurityError, match="exceeds maximum allowed size"):
            validate_file_size(test_file, max_size=500)

        # Should pass with 2000 byte limit
        validate_file_size(test_file, max_size=2000)


class TestPropertyPathValidation:
    """Test property path validation."""

    def test_valid_property_paths(self):
        """Test that valid property paths are accepted."""
        valid_paths = [
            "versioning.enabled",
            "rules.0.status",
            "encryption.kms_key_id",
            "a.b.c.d.e",
        ]

        for path in valid_paths:
            validate_property_path(path)  # Should not raise

    def test_empty_property_path_rejected(self):
        """Test that empty property paths are rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_property_path("")

    def test_excessive_depth_rejected(self):
        """Test that excessively deep paths are rejected."""
        # Create a path deeper than MAX_PROPERTY_DEPTH
        deep_path = ".".join(["a"] * (MAX_PROPERTY_DEPTH + 1))
        with pytest.raises(SecurityError, match="exceeds maximum"):
            validate_property_path(deep_path)

    def test_path_with_empty_segments_rejected(self):
        """Test that paths with empty segments are rejected."""
        with pytest.raises(SecurityError, match="empty segments"):
            validate_property_path("a..b")

    def test_path_with_invalid_characters_rejected(self):
        """Test that paths with invalid characters are rejected."""
        invalid_paths = [
            "a\x00b",  # Null byte
            "a\nb",  # Newline
            "a\rb",  # Carriage return
        ]

        for path in invalid_paths:
            with pytest.raises(SecurityError, match="invalid characters"):
                validate_property_path(path)

    def test_excessively_long_path_rejected(self):
        """Test that excessively long property paths are rejected."""
        long_path = "a" * 1001
        with pytest.raises(SecurityError, match="too long"):
            validate_property_path(long_path)


class TestSanitizationFunctions:
    """Test high-level sanitization functions."""

    def test_sanitize_terraform_plan_path(self, tmp_path):
        """Test Terraform plan path sanitization."""
        # Create a valid plan file
        plan_file = tmp_path / "plan.json"
        plan_file.write_text('{"resource_changes": []}')

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = sanitize_terraform_plan_path("plan.json")
            assert result.name == "plan.json"
        finally:
            os.chdir(original_cwd)

    def test_sanitize_terraform_plan_path_wrong_extension(self, tmp_path):
        """Test that wrong extensions are rejected for plan files."""
        plan_file = tmp_path / "plan.txt"
        plan_file.write_text("content")

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(SecurityError, match="Invalid file extension"):
                sanitize_terraform_plan_path("plan.txt")
        finally:
            os.chdir(original_cwd)

    def test_sanitize_terraform_plan_path_too_large(self, tmp_path):
        """Test that oversized plan files are rejected."""
        plan_file = tmp_path / "plan.json"
        with open(plan_file, "wb") as f:
            f.write(b"x" * (MAX_FILE_SIZE + 1))

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(SecurityError, match="exceeds maximum allowed size"):
                sanitize_terraform_plan_path("plan.json")
        finally:
            os.chdir(original_cwd)

    def test_sanitize_rules_directory(self, tmp_path):
        """Test rules directory sanitization."""
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = sanitize_rules_directory("rules")
            assert result.name == "rules"
        finally:
            os.chdir(original_cwd)

    def test_sanitize_rules_directory_path_traversal(self):
        """Test that path traversal is blocked for rules directory."""
        with pytest.raises(SecurityError, match="Path traversal detected"):
            sanitize_rules_directory("../../../etc")

    def test_sanitize_output_path(self, tmp_path):
        """Test output path sanitization."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = sanitize_output_path("output.json")
            assert result.name == "output.json"
        finally:
            os.chdir(original_cwd)

    def test_sanitize_output_path_traversal_blocked(self):
        """Test that path traversal is blocked for output paths."""
        with pytest.raises(SecurityError, match="Path traversal detected"):
            sanitize_output_path("../../../etc/cron.d/malicious.json")

    def test_sanitize_output_path_wrong_extension(self, tmp_path):
        """Test that wrong extensions are rejected for output files."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(SecurityError, match="Invalid file extension"):
                sanitize_output_path("output.txt")
        finally:
            os.chdir(original_cwd)


class TestRealWorldAttacks:
    """Test real-world attack scenarios."""

    def test_symlink_attack_blocked(self, tmp_path):
        """Test that symlink attacks are blocked."""
        # Create a symlink pointing outside the base directory
        target = Path("/etc/passwd")
        if target.exists():  # Only run on systems where /etc/passwd exists
            symlink = tmp_path / "link.json"
            try:
                symlink.symlink_to(target)
                with pytest.raises(SecurityError, match="Path traversal detected"):
                    validate_safe_path(
                        str(symlink), base_dir=str(tmp_path), must_exist=True
                    )
            except OSError:
                # Skip if symlinks not supported (e.g., Windows without admin)
                pytest.skip("Symlinks not supported on this system")

    def test_windows_path_traversal(self, tmp_path):
        """Test Windows-specific path traversal attempts."""
        # Test relative path traversal (should be blocked)
        relative_traversal = "..\\..\\..\\Windows\\System32\\config\\SAM"
        with pytest.raises((SecurityError, ValueError)):
            validate_safe_path(
                relative_traversal, base_dir=str(tmp_path), must_exist=False
            )

        # Absolute paths are now allowed (users provide them)
        # but should fail on non-existent files if must_exist=True
        absolute_path = "C:\\Windows\\System32\\drivers\\etc\\hosts"
        try:
            # This may succeed or fail depending on OS and permissions
            # The key is it doesn't escape via path traversal
            validate_safe_path(absolute_path, base_dir=str(tmp_path), must_exist=False)
        except (ValueError, SecurityError):
            # Expected if file extension validation fails or other checks
            pass

    def test_unicode_normalization_attack(self, tmp_path):
        """Test Unicode normalization attacks."""
        # Try paths with Unicode characters that might normalize to '..'
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            # This should either work safely or be blocked
            # The key is it shouldn't escape the base directory
            result = validate_safe_path("test\u2024json", must_exist=False)
            # Verify the resolved path is still within tmp_path
            assert str(result.resolve()).startswith(str(tmp_path.resolve()))
        finally:
            os.chdir(original_cwd)
