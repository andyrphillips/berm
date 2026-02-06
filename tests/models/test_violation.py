"""Tests for Violation model."""

from berm.models.violation import Violation


def test_violation_creation():
    """Test creating a violation."""
    violation = Violation(
        rule_id="test-rule",
        rule_name="Test Rule",
        resource_name="aws_s3_bucket.example",
        resource_type="aws_s3_bucket",
        severity="error",
        message="Test message",
    )

    assert violation.rule_id == "test-rule"
    assert violation.rule_name == "Test Rule"
    assert violation.resource_name == "aws_s3_bucket.example"
    assert violation.resource_type == "aws_s3_bucket"
    assert violation.severity == "error"
    assert violation.message == "Test message"
    assert violation.location is None


def test_violation_with_location():
    """Test creating a violation with location."""
    violation = Violation(
        rule_id="test-rule",
        rule_name="Test Rule",
        resource_name="aws_s3_bucket.example",
        resource_type="aws_s3_bucket",
        severity="error",
        message="Test message",
        location="main.tf:10",
    )

    assert violation.location == "main.tf:10"


def test_violation_is_error():
    """Test is_error method."""
    error = Violation(
        rule_id="test",
        rule_name="Test",
        resource_name="resource",
        resource_type="type",
        severity="error",
        message="msg",
    )
    assert error.is_error() is True
    assert error.is_warning() is False


def test_violation_is_warning():
    """Test is_warning method."""
    warning = Violation(
        rule_id="test",
        rule_name="Test",
        resource_name="resource",
        resource_type="type",
        severity="warning",
        message="msg",
    )
    assert warning.is_error() is False
    assert warning.is_warning() is True


def test_violation_format_compact():
    """Test compact formatting."""
    violation = Violation(
        rule_id="test-rule",
        rule_name="Test Rule",
        resource_name="aws_s3_bucket.example",
        resource_type="aws_s3_bucket",
        severity="error",
        message="Versioning not enabled",
    )

    compact = violation.format_compact()
    assert "[ERROR]" in compact
    assert "aws_s3_bucket.example" in compact
    assert "aws_s3_bucket" in compact
    assert "Versioning not enabled" in compact


def test_violation_format_compact_warning():
    """Test compact formatting for warnings."""
    violation = Violation(
        rule_id="test-rule",
        rule_name="Test Rule",
        resource_name="aws_db_instance.db",
        resource_type="aws_db_instance",
        severity="warning",
        message="Low backup retention",
    )

    compact = violation.format_compact()
    assert "[WARN]" in compact


def test_violation_format_detailed():
    """Test detailed formatting."""
    violation = Violation(
        rule_id="test-rule",
        rule_name="Test Rule",
        resource_name="aws_s3_bucket.example",
        resource_type="aws_s3_bucket",
        severity="error",
        message="Versioning not enabled",
        location="main.tf:15",
    )

    detailed = violation.format_detailed()
    assert "Severity: ERROR" in detailed
    assert "Rule: Test Rule (test-rule)" in detailed
    assert "Resource: aws_s3_bucket.example (aws_s3_bucket)" in detailed
    assert "Message: Versioning not enabled" in detailed
    assert "Location: main.tf:15" in detailed


def test_violation_string_representation():
    """Test string representations."""
    violation = Violation(
        rule_id="test-rule",
        rule_name="Test Rule",
        resource_name="aws_s3_bucket.example",
        resource_type="aws_s3_bucket",
        severity="error",
        message="Test message",
    )

    # __str__ should use compact format
    str_repr = str(violation)
    assert "[ERROR]" in str_repr
    assert "aws_s3_bucket.example" in str_repr

    # __repr__ should include key fields
    repr_str = repr(violation)
    assert "test-rule" in repr_str
    assert "aws_s3_bucket.example" in repr_str
