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


def test_rule_with_resource_types_array():
    """Test creating a rule with multiple resource types."""
    rule = Rule(
        id="multi-type-rule",
        name="Multi Type Rule",
        resource_types=["aws_s3_bucket", "aws_db_instance", "aws_lambda_function"],
        severity="error",
        property="tags",
        has_keys=["Environment", "Owner"],
        message="Resource {{resource_name}} must have required tags",
    )

    assert rule.resource_types == ["aws_s3_bucket", "aws_db_instance", "aws_lambda_function"]
    assert rule.resource_type is None
    assert rule.has_keys == ["Environment", "Owner"]


def test_rule_resource_type_mutual_exclusivity():
    """Test that resource_type and resource_types cannot both be specified."""
    with pytest.raises(ValidationError, match="cannot specify both"):
        Rule(
            id="invalid",
            name="Invalid",
            resource_type="aws_s3_bucket",
            resource_types=["aws_db_instance"],
            severity="error",
            property="prop",
            equals=True,
            message="msg",
        )


def test_rule_resource_type_required():
    """Test that either resource_type or resource_types must be specified."""
    with pytest.raises(ValidationError, match="must specify either"):
        Rule(
            id="invalid",
            name="Invalid",
            severity="error",
            property="prop",
            equals=True,
            message="msg",
        )


def test_rule_resource_types_empty_list():
    """Test that resource_types cannot be empty."""
    with pytest.raises(ValidationError, match="at least 1 item"):
        Rule(
            id="invalid",
            name="Invalid",
            resource_types=[],
            severity="error",
            property="prop",
            equals=True,
            message="msg",
        )


def test_rule_resource_types_duplicates():
    """Test that resource_types cannot contain duplicates."""
    with pytest.raises(ValidationError, match="duplicate"):
        Rule(
            id="invalid",
            name="Invalid",
            resource_types=["aws_s3_bucket", "aws_s3_bucket"],
            severity="error",
            property="prop",
            equals=True,
            message="msg",
        )


def test_rule_has_keys_operator():
    """Test rule with has_keys operator."""
    rule = Rule(
        id="test-has-keys",
        name="Has Keys Test",
        resource_type="aws_s3_bucket",
        severity="error",
        property="tags",
        has_keys=["Environment", "Owner", "CostCenter"],
        message="Resource must have required tag keys",
    )

    assert rule.has_keys == ["Environment", "Owner", "CostCenter"]
    assert rule.equals is None


def test_rule_is_not_empty_operator():
    """Test rule with is_not_empty operator."""
    rule = Rule(
        id="test-not-empty",
        name="Not Empty Test",
        resource_type="aws_s3_bucket",
        severity="warning",
        property="tags",
        is_not_empty=True,
        message="Resource should have tags",
    )

    assert rule.is_not_empty is True
    assert rule.equals is None


def test_rule_multiple_operators_with_new_ones():
    """Test that only one operator can be specified including new ones."""
    with pytest.raises(ValidationError, match="only one comparison operator"):
        Rule(
            id="invalid",
            name="Invalid",
            resource_type="aws_s3_bucket",
            severity="error",
            property="prop",
            equals=True,
            has_keys=["key1"],
            message="msg",
        )


def test_rule_matches_resource_type_single():
    """Test matches_resource_type helper with single resource_type."""
    rule = Rule(
        id="test",
        name="Test",
        resource_type="aws_s3_bucket",
        severity="error",
        property="prop",
        equals=True,
        message="msg",
    )

    assert rule.matches_resource_type("aws_s3_bucket") is True
    assert rule.matches_resource_type("aws_db_instance") is False


def test_rule_matches_resource_type_multiple():
    """Test matches_resource_type helper with multiple resource_types."""
    rule = Rule(
        id="test",
        name="Test",
        resource_types=["aws_s3_bucket", "aws_db_instance", "aws_lambda_function"],
        severity="error",
        property="prop",
        equals=True,
        message="msg",
    )

    assert rule.matches_resource_type("aws_s3_bucket") is True
    assert rule.matches_resource_type("aws_db_instance") is True
    assert rule.matches_resource_type("aws_lambda_function") is True
    assert rule.matches_resource_type("aws_instance") is False
