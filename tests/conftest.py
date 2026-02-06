"""Shared pytest fixtures for Berm tests."""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from berm.models.rule import Rule
from berm.models.violation import Violation


@pytest.fixture
def sample_rule() -> Rule:
    """Create a sample rule for testing."""
    return Rule(
        id="test-rule",
        name="Test Rule",
        resource_type="aws_s3_bucket",
        severity="error",
        property="versioning.enabled",
        equals=True,
        message="S3 bucket {{resource_name}} must have versioning enabled",
    )


@pytest.fixture
def sample_warning_rule() -> Rule:
    """Create a sample warning rule for testing."""
    return Rule(
        id="test-warning",
        name="Test Warning",
        resource_type="aws_db_instance",
        severity="warning",
        property="backup_retention_period",
        equals=7,
        message="RDS instance {{resource_name}} should have 7 days backup retention",
    )


@pytest.fixture
def sample_violation() -> Violation:
    """Create a sample violation for testing."""
    return Violation(
        rule_id="test-rule",
        rule_name="Test Rule",
        resource_name="aws_s3_bucket.example",
        resource_type="aws_s3_bucket",
        severity="error",
        message="S3 bucket must have versioning enabled",
    )


@pytest.fixture
def sample_resources() -> List[Dict[str, Any]]:
    """Create sample Terraform resources for testing."""
    return [
        {
            "address": "aws_s3_bucket.compliant",
            "type": "aws_s3_bucket",
            "name": "compliant",
            "values": {
                "bucket": "my-bucket",
                "versioning": {"enabled": True},
            },
        },
        {
            "address": "aws_s3_bucket.non_compliant",
            "type": "aws_s3_bucket",
            "name": "non_compliant",
            "values": {
                "bucket": "my-other-bucket",
                "versioning": {"enabled": False},
            },
        },
        {
            "address": "aws_db_instance.database",
            "type": "aws_db_instance",
            "name": "database",
            "values": {
                "identifier": "my-db",
                "backup_retention_period": 3,
            },
        },
    ]


@pytest.fixture
def fixtures_dir() -> Path:
    """Get the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_plan_file(fixtures_dir: Path) -> Path:
    """Get path to sample plan JSON file."""
    return fixtures_dir / "sample-plan.json"


@pytest.fixture
def temp_rule_file(tmp_path: Path) -> Path:
    """Create a temporary rule file for testing."""
    rule_data = {
        "id": "temp-test-rule",
        "name": "Temporary Test Rule",
        "resource_type": "aws_s3_bucket",
        "severity": "error",
        "property": "encryption.enabled",
        "equals": True,
        "message": "Test message for {{resource_name}}",
    }

    rule_file = tmp_path / "test-rule.json"
    with open(rule_file, "w") as f:
        json.dump(rule_data, f)

    return rule_file


@pytest.fixture
def temp_rules_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with multiple rule files."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    # Create multiple rule files
    rules = [
        {
            "id": "rule-1",
            "name": "Rule One",
            "resource_type": "aws_s3_bucket",
            "severity": "error",
            "property": "versioning.enabled",
            "equals": True,
            "message": "Message one",
        },
        {
            "id": "rule-2",
            "name": "Rule Two",
            "resource_type": "aws_db_instance",
            "severity": "warning",
            "property": "backup_retention_period",
            "equals": 7,
            "message": "Message two",
        },
    ]

    for i, rule_data in enumerate(rules):
        rule_file = rules_dir / f"rule-{i + 1}.json"
        with open(rule_file, "w") as f:
            json.dump(rule_data, f)

    return rules_dir
