"""Tests for Rule model."""

import pytest
from pydantic import ValidationError

from berm.models.rule import Rule


def test_rule_creation_valid():
    """Test creating a valid rule."""
    rule = Rule(
        id="test-rule",
        name="Test Rule",
        resource_type="aws_s3_bucket",
        severity="error",
        property="versioning.enabled",
        equals=True,
        message="Test message",
    )

    assert rule.id == "test-rule"
    assert rule.name == "Test Rule"
    assert rule.resource_type == "aws_s3_bucket"
    assert rule.severity == "error"
    assert rule.property == "versioning.enabled"
    assert rule.equals is True
    assert rule.message == "Test message"


def test_rule_severity_validation():
    """Test that severity must be 'error' or 'warning'."""
    # Valid severities
    rule_error = Rule(
        id="test",
        name="Test",
        resource_type="aws_s3_bucket",
        severity="error",
        property="prop",
        equals=True,
        message="msg",
    )
    assert rule_error.severity == "error"

    rule_warning = Rule(
        id="test",
        name="Test",
        resource_type="aws_s3_bucket",
        severity="warning",
        property="prop",
        equals=True,
        message="msg",
    )
    assert rule_warning.severity == "warning"

    # Invalid severity
    with pytest.raises(ValidationError):
        Rule(
            id="test",
            name="Test",
            resource_type="aws_s3_bucket",
            severity="invalid",
            property="prop",
            equals=True,
            message="msg",
        )


def test_rule_required_fields():
    """Test that all required fields must be provided."""
    with pytest.raises(ValidationError):
        Rule()


def test_rule_format_message():
    """Test message formatting with resource name."""
    rule = Rule(
        id="test",
        name="Test",
        resource_type="aws_s3_bucket",
        severity="error",
        property="prop",
        equals=True,
        message="Resource {{resource_name}} failed validation",
    )

    formatted = rule.format_message("aws_s3_bucket.example")
    assert formatted == "Resource aws_s3_bucket.example failed validation"


def test_rule_equals_types():
    """Test that equals can be various types."""
    # Boolean
    rule_bool = Rule(
        id="test",
        name="Test",
        resource_type="aws_s3_bucket",
        severity="error",
        property="prop",
        equals=True,
        message="msg",
    )
    assert rule_bool.equals is True

    # String
    rule_str = Rule(
        id="test",
        name="Test",
        resource_type="aws_s3_bucket",
        severity="error",
        property="prop",
        equals="value",
        message="msg",
    )
    assert rule_str.equals == "value"

    # Integer
    rule_int = Rule(
        id="test",
        name="Test",
        resource_type="aws_s3_bucket",
        severity="error",
        property="prop",
        equals=42,
        message="msg",
    )
    assert rule_int.equals == 42

    # Float
    rule_float = Rule(
        id="test",
        name="Test",
        resource_type="aws_s3_bucket",
        severity="error",
        property="prop",
        equals=3.14,
        message="msg",
    )
    assert rule_float.equals == 3.14


def test_rule_string_representation():
    """Test string representations of rule."""
    rule = Rule(
        id="test-rule",
        name="Test Rule",
        resource_type="aws_s3_bucket",
        severity="error",
        property="prop",
        equals=True,
        message="msg",
    )

    assert "test-rule" in str(rule)
    assert "Test Rule" in str(rule)
    assert "test-rule" in repr(rule)
