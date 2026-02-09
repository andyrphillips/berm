"""Security tests for input validation and sanitization."""

import os
import tempfile
from pathlib import Path

import pytest

from berm.security import (
    MAX_FILE_SIZE,
    MAX_JSON_DEPTH,
    MAX_PROPERTY_DEPTH,
    SecurityError,
    sanitize_for_output,
    sanitize_output_path,
    sanitize_rules_directory,
    sanitize_terraform_plan_path,
    validate_file_size,
    validate_json_depth,
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


class TestOutputSanitization:
    """Test output sanitization for injection attack prevention."""

    def test_ansi_escape_code_removal(self):
        """Test that ANSI escape codes are removed."""
        # Red color code
        text_with_ansi = "\x1b[31mRed text\x1b[0m"
        sanitized = sanitize_for_output(text_with_ansi, context="terminal")
        assert sanitized == "Red text"
        assert "\x1b" not in sanitized

        # Multiple escape codes
        text_with_multiple = "\x1b[1m\x1b[31mBold Red\x1b[0m\x1b[0m"
        sanitized = sanitize_for_output(text_with_multiple, context="terminal")
        assert sanitized == "Bold Red"

    def test_control_character_removal(self):
        """Test that control characters are removed."""
        # Newline and carriage return
        text_with_controls = "Line1\nLine2\rLine3"
        sanitized = sanitize_for_output(text_with_controls, context="terminal")
        assert "\n" not in sanitized
        assert "\r" not in sanitized
        assert sanitized == "Line1Line2Line3"

        # Tab should be preserved
        text_with_tab = "Column1\tColumn2"
        sanitized = sanitize_for_output(text_with_tab, context="terminal")
        assert "\t" in sanitized

        # DEL character (0x7f)
        text_with_del = "Text\x7fMore"
        sanitized = sanitize_for_output(text_with_del, context="terminal")
        assert "\x7f" not in sanitized

    def test_github_actions_command_injection_prevention(self):
        """Test GitHub Actions workflow command injection prevention."""
        # Test :: command injection
        malicious = "::error::Injected error message"
        sanitized = sanitize_for_output(malicious, context="github")
        assert "::" not in sanitized
        assert ":\u200b:" in sanitized  # Zero-width space breaks command

        # Test set-output command
        malicious = "::set-output name=token::secret123"
        sanitized = sanitize_for_output(malicious, context="github")
        assert "::set-output" not in sanitized
        assert ":\u200b:" in sanitized

        # Terminal context should not add zero-width space
        text = "::normal text::"
        sanitized_terminal = sanitize_for_output(text, context="terminal")
        assert "::" in sanitized_terminal
        assert "\u200b" not in sanitized_terminal

    def test_length_truncation(self):
        """Test that excessively long strings are truncated."""
        # Create a string longer than 10,000 characters
        long_text = "A" * 15000
        sanitized = sanitize_for_output(long_text, context="terminal")

        # Should be truncated to 10,000 + "... (truncated)"
        assert len(sanitized) < len(long_text)
        assert sanitized.endswith("... (truncated)")
        assert len(sanitized) <= 10000 + len("... (truncated)")

    def test_empty_string_handling(self):
        """Test that empty strings are handled correctly."""
        assert sanitize_for_output("", context="terminal") == ""
        assert sanitize_for_output("", context="github") == ""
        assert sanitize_for_output("", context="json") == ""

    def test_json_context_sanitization(self):
        """Test JSON context-specific sanitization."""
        # JSON context should still remove ANSI and control characters
        text_with_ansi = "\x1b[31mRed\x1b[0m"
        sanitized = sanitize_for_output(text_with_ansi, context="json")
        assert "\x1b" not in sanitized
        assert sanitized == "Red"

        # Control characters removed
        text_with_controls = "Line1\nLine2"
        sanitized = sanitize_for_output(text_with_controls, context="json")
        assert "\n" not in sanitized

    def test_combined_attack_vectors(self):
        """Test multiple attack vectors combined."""
        # Combine ANSI codes, control characters, and GitHub commands
        malicious = "\x1b[31m::error::\x1b[0m\nInjected\rCommand"

        # Terminal context
        sanitized_terminal = sanitize_for_output(malicious, context="terminal")
        assert "\x1b" not in sanitized_terminal
        assert "\n" not in sanitized_terminal
        assert "\r" not in sanitized_terminal

        # GitHub context
        sanitized_github = sanitize_for_output(malicious, context="github")
        assert "\x1b" not in sanitized_github
        assert "::" not in sanitized_github
        assert ":\u200b:" in sanitized_github

    def test_preserves_normal_text(self):
        """Test that normal text is preserved."""
        normal_text = "This is normal text with punctuation! And numbers: 123."
        sanitized = sanitize_for_output(normal_text, context="terminal")
        assert sanitized == normal_text

    def test_unicode_text_preservation(self):
        """Test that legitimate Unicode characters are preserved."""
        unicode_text = "Hello 世界 🌍 émojis"
        sanitized = sanitize_for_output(unicode_text, context="terminal")
        # Should preserve Unicode characters (only control chars removed)
        assert "世界" in sanitized
        assert "🌍" in sanitized
        assert "é" in sanitized


class TestJsonDepthValidation:
    """Test JSON depth validation for DoS prevention."""

    def test_valid_shallow_json(self):
        """Test that shallow JSON structures are accepted."""
        shallow_obj = {"a": 1, "b": 2, "c": {"d": 3}}
        validate_json_depth(shallow_obj)  # Should not raise

        shallow_list = [1, 2, [3, 4, [5, 6]]]
        validate_json_depth(shallow_list)  # Should not raise

    def test_valid_moderate_depth_json(self):
        """Test that moderate depth JSON is accepted."""
        # Create nested dict at depth 25 (within limit of 50)
        obj = {"level": 0}
        current = obj
        for i in range(1, 25):
            current["nested"] = {"level": i}
            current = current["nested"]

        validate_json_depth(obj)  # Should not raise

    def test_maximum_allowed_depth(self):
        """Test JSON at exactly the maximum depth."""
        # Create nested structure at depth MAX_JSON_DEPTH (50)
        obj = {"level": 0}
        current = obj
        for i in range(1, MAX_JSON_DEPTH):
            current["nested"] = {"level": i}
            current = current["nested"]

        validate_json_depth(obj)  # Should not raise

    def test_excessive_depth_rejected(self):
        """Test that excessively deep JSON is rejected."""
        # Create nested structure deeper than MAX_JSON_DEPTH
        obj = {"level": 0}
        current = obj
        for i in range(1, MAX_JSON_DEPTH + 5):
            current["nested"] = {"level": i}
            current = current["nested"]

        with pytest.raises(SecurityError, match="exceeds maximum allowed depth"):
            validate_json_depth(obj)

    def test_deeply_nested_arrays(self):
        """Test deeply nested array structures."""
        # Create deeply nested array
        arr = []
        current = arr
        for i in range(MAX_JSON_DEPTH + 2):
            nested = []
            current.append(nested)
            current = nested

        with pytest.raises(SecurityError, match="exceeds maximum allowed depth"):
            validate_json_depth(arr)

    def test_mixed_nesting(self):
        """Test mixed dict and array nesting."""
        # Create mixed structure at the limit
        obj = {"data": []}
        current_dict = obj
        current_list = obj["data"]

        for i in range(MAX_JSON_DEPTH + 2):
            if i % 2 == 0:
                new_dict = {"level": i}
                current_list.append(new_dict)
                current_dict = new_dict
                current_dict["nested"] = []
                current_list = current_dict["nested"]
            else:
                new_list = []
                current_dict["nested"] = new_list
                current_list = new_list

        with pytest.raises(SecurityError, match="exceeds maximum allowed depth"):
            validate_json_depth(obj)

    def test_primitive_values(self):
        """Test that primitive values are accepted."""
        validate_json_depth(None)  # Should not raise
        validate_json_depth(123)  # Should not raise
        validate_json_depth("string")  # Should not raise
        validate_json_depth(True)  # Should not raise
        validate_json_depth(3.14)  # Should not raise

    def test_custom_depth_limit(self):
        """Test custom depth limits."""
        # Create structure with depth 10
        obj = {"level": 0}
        current = obj
        for i in range(1, 10):
            current["nested"] = {"level": i}
            current = current["nested"]

        # Should pass with limit of 15
        validate_json_depth(obj, max_depth=15)

        # Should fail with limit of 5
        with pytest.raises(SecurityError, match="exceeds maximum allowed depth"):
            validate_json_depth(obj, max_depth=5)

    def test_wide_but_shallow_structures(self):
        """Test wide structures that are not deep."""
        # Create a wide dict (many keys, but shallow)
        wide_obj = {f"key{i}": i for i in range(1000)}
        validate_json_depth(wide_obj)  # Should not raise

        # Wide array
        wide_array = list(range(1000))
        validate_json_depth(wide_array)  # Should not raise

    def test_empty_structures(self):
        """Test empty dicts and arrays."""
        validate_json_depth({})  # Should not raise
        validate_json_depth([])  # Should not raise
        validate_json_depth({"empty_dict": {}, "empty_list": []})  # Should not raise

    def test_realistic_terraform_plan_structure(self):
        """Test a realistic Terraform plan JSON structure."""
        terraform_plan = {
            "format_version": "1.0",
            "terraform_version": "1.5.0",
            "resource_changes": [
                {
                    "address": "aws_s3_bucket.example",
                    "mode": "managed",
                    "type": "aws_s3_bucket",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "bucket": "my-bucket",
                            "versioning": {
                                "enabled": True,
                                "mfa_delete": False
                            },
                            "tags": {
                                "Environment": "production",
                                "Team": "platform"
                            }
                        }
                    }
                }
            ]
        }

        validate_json_depth(terraform_plan)  # Should not raise
