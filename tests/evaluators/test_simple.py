"""Tests for simple evaluator."""

import pytest

from berm.evaluators.simple import SimpleEvaluator
from berm.models.rule import Rule
from berm.models.violation import Violation


def test_evaluator_no_violations(sample_rule):
    """Test evaluation when all resources comply."""
    evaluator = SimpleEvaluator()

    resources = [
        {
            "address": "aws_s3_bucket.compliant",
            "type": "aws_s3_bucket",
            "name": "compliant",
            "values": {
                "bucket": "my-bucket",
                "versioning": {"enabled": True},
            },
        }
    ]

    violations = evaluator.evaluate(sample_rule, resources)
    assert len(violations) == 0


def test_evaluator_finds_violation(sample_rule):
    """Test evaluation finds violations."""
    evaluator = SimpleEvaluator()

    resources = [
        {
            "address": "aws_s3_bucket.non_compliant",
            "type": "aws_s3_bucket",
            "name": "non_compliant",
            "values": {
                "bucket": "my-bucket",
                "versioning": {"enabled": False},
            },
        }
    ]

    violations = evaluator.evaluate(sample_rule, resources)
    assert len(violations) == 1
    assert isinstance(violations[0], Violation)
    assert violations[0].resource_name == "aws_s3_bucket.non_compliant"
    assert violations[0].severity == "error"


def test_evaluator_missing_property(sample_rule):
    """Test evaluation when property doesn't exist."""
    evaluator = SimpleEvaluator()

    resources = [
        {
            "address": "aws_s3_bucket.missing",
            "type": "aws_s3_bucket",
            "name": "missing",
            "values": {
                "bucket": "my-bucket",
                # versioning property is missing
            },
        }
    ]

    violations = evaluator.evaluate(sample_rule, resources)
    assert len(violations) == 1
    assert "not found" in violations[0].message


def test_evaluator_filters_by_resource_type(sample_rule):
    """Test that evaluator only checks matching resource types."""
    evaluator = SimpleEvaluator()

    resources = [
        {
            "address": "aws_s3_bucket.bucket",
            "type": "aws_s3_bucket",
            "name": "bucket",
            "values": {
                "versioning": {"enabled": False},  # Violates rule
            },
        },
        {
            "address": "aws_db_instance.database",
            "type": "aws_db_instance",
            "name": "database",
            "values": {
                "versioning": {"enabled": False},  # Should be ignored (wrong type)
            },
        },
    ]

    violations = evaluator.evaluate(sample_rule, resources)
    # Only S3 bucket should be checked
    assert len(violations) == 1
    assert violations[0].resource_type == "aws_s3_bucket"


def test_evaluator_multiple_resources(sample_rule):
    """Test evaluation with multiple resources of same type."""
    evaluator = SimpleEvaluator()

    resources = [
        {
            "address": "aws_s3_bucket.compliant",
            "type": "aws_s3_bucket",
            "name": "compliant",
            "values": {"versioning": {"enabled": True}},
        },
        {
            "address": "aws_s3_bucket.non_compliant_1",
            "type": "aws_s3_bucket",
            "name": "non_compliant_1",
            "values": {"versioning": {"enabled": False}},
        },
        {
            "address": "aws_s3_bucket.non_compliant_2",
            "type": "aws_s3_bucket",
            "name": "non_compliant_2",
            "values": {"versioning": {"enabled": False}},
        },
    ]

    violations = evaluator.evaluate(sample_rule, resources)
    assert len(violations) == 2
    addresses = [v.resource_name for v in violations]
    assert "aws_s3_bucket.non_compliant_1" in addresses
    assert "aws_s3_bucket.non_compliant_2" in addresses


def test_evaluator_warning_severity(sample_warning_rule):
    """Test evaluation with warning severity."""
    evaluator = SimpleEvaluator()

    resources = [
        {
            "address": "aws_db_instance.db",
            "type": "aws_db_instance",
            "name": "db",
            "values": {
                "backup_retention_period": 3,  # Should be 7
            },
        }
    ]

    violations = evaluator.evaluate(sample_warning_rule, resources)
    assert len(violations) == 1
    assert violations[0].severity == "warning"


def test_evaluator_evaluate_all(sample_rule, sample_warning_rule):
    """Test evaluating multiple rules."""
    evaluator = SimpleEvaluator()

    resources = [
        {
            "address": "aws_s3_bucket.bucket",
            "type": "aws_s3_bucket",
            "name": "bucket",
            "values": {"versioning": {"enabled": False}},
        },
        {
            "address": "aws_db_instance.db",
            "type": "aws_db_instance",
            "name": "db",
            "values": {"backup_retention_period": 3},
        },
    ]

    rules = [sample_rule, sample_warning_rule]
    violations = evaluator.evaluate_all(rules, resources)

    assert len(violations) == 2
    # One error from S3 rule, one warning from DB rule
    errors = [v for v in violations if v.severity == "error"]
    warnings = [v for v in violations if v.severity == "warning"]
    assert len(errors) == 1
    assert len(warnings) == 1


def test_evaluator_value_types():
    """Test evaluation with different value types."""
    evaluator = SimpleEvaluator()

    # String comparison
    rule_string = Rule(
        id="test-string",
        name="String Test",
        resource_type="aws_resource",
        severity="error",
        property="status",
        equals="Enabled",
        message="Test",
    )

    resources_string = [
        {
            "address": "aws_resource.good",
            "type": "aws_resource",
            "name": "good",
            "values": {"status": "Enabled"},
        }
    ]

    violations = evaluator.evaluate(rule_string, resources_string)
    assert len(violations) == 0

    # Integer comparison
    rule_int = Rule(
        id="test-int",
        name="Int Test",
        resource_type="aws_resource",
        severity="error",
        property="count",
        equals=5,
        message="Test",
    )

    resources_int = [
        {
            "address": "aws_resource.good",
            "type": "aws_resource",
            "name": "good",
            "values": {"count": 5},
        }
    ]

    violations = evaluator.evaluate(rule_int, resources_int)
    assert len(violations) == 0


def test_evaluator_value_coercion():
    """Test that evaluator handles type coercion."""
    evaluator = SimpleEvaluator()

    rule = Rule(
        id="test",
        name="Test",
        resource_type="aws_resource",
        severity="error",
        property="enabled",
        equals=True,
        message="Test",
    )

    # String "true" should match boolean True
    resources = [
        {
            "address": "aws_resource.test",
            "type": "aws_resource",
            "name": "test",
            "values": {"enabled": "true"},
        }
    ]

    violations = evaluator.evaluate(rule, resources)
    assert len(violations) == 0
