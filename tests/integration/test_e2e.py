"""End-to-end integration tests for Berm CLI."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from berm.cli import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def integration_plan(tmp_path):
    """Create a test plan file for integration testing."""
    plan_data = {
        "resource_changes": [
            {
                "address": "aws_s3_bucket_versioning.compliant",
                "type": "aws_s3_bucket_versioning",
                "name": "compliant",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "versioning_configuration": [{"status": "Enabled"}]
                    },
                },
            },
            {
                "address": "aws_s3_bucket_versioning.non_compliant",
                "type": "aws_s3_bucket_versioning",
                "name": "non_compliant",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "versioning_configuration": [{"status": "Disabled"}]
                    },
                },
            },
        ]
    }

    plan_file = tmp_path / "plan.json"
    with open(plan_file, "w") as f:
        json.dump(plan_data, f)

    return plan_file


@pytest.fixture
def integration_rules(tmp_path):
    """Create test rules for integration testing."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    rule_data = {
        "id": "s3-versioning-test",
        "name": "S3 Versioning Test",
        "resource_type": "aws_s3_bucket_versioning",
        "severity": "error",
        "property": "versioning_configuration.0.status",
        "equals": "Enabled",
        "message": "S3 bucket {{resource_name}} must have versioning enabled",
    }

    rule_file = rules_dir / "test-rule.json"
    with open(rule_file, "w") as f:
        json.dump(rule_data, f)

    return rules_dir


def test_cli_check_with_violations(runner, integration_plan, integration_rules):
    """Test CLI check command with violations."""
    result = runner.invoke(
        cli,
        [
            "check",
            str(integration_plan),
            "--rules-dir",
            str(integration_rules),
            "--format",
            "terminal",
        ],
    )

    # Should exit with code 1 (violations found)
    assert result.exit_code == 1


def test_cli_check_no_violations(runner, tmp_path):
    """Test CLI check command with no violations."""
    # Create plan with compliant resources only
    plan_data = {
        "resource_changes": [
            {
                "address": "aws_s3_bucket_versioning.compliant",
                "type": "aws_s3_bucket_versioning",
                "name": "compliant",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "versioning_configuration": [{"status": "Enabled"}]
                    },
                },
            }
        ]
    }

    plan_file = tmp_path / "plan.json"
    with open(plan_file, "w") as f:
        json.dump(plan_data, f)

    # Create rule
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    rule_data = {
        "id": "s3-versioning-test",
        "name": "S3 Versioning Test",
        "resource_type": "aws_s3_bucket_versioning",
        "severity": "error",
        "property": "versioning_configuration.0.status",
        "equals": "Enabled",
        "message": "Test message",
    }

    rule_file = rules_dir / "test-rule.json"
    with open(rule_file, "w") as f:
        json.dump(rule_data, f)

    result = runner.invoke(
        cli,
        ["check", str(plan_file), "--rules-dir", str(rules_dir)],
    )

    # Should exit with code 0 (no violations)
    assert result.exit_code == 0
    assert "passed" in result.output.lower()


def test_cli_check_json_format(runner, integration_plan, integration_rules):
    """Test CLI check with JSON output format."""
    result = runner.invoke(
        cli,
        [
            "check",
            str(integration_plan),
            "--rules-dir",
            str(integration_rules),
            "--format",
            "json",
        ],
    )

    # Should produce valid JSON
    try:
        output_data = json.loads(result.output)
        assert "summary" in output_data
        assert "violations" in output_data
        assert output_data["summary"]["errors"] > 0
    except json.JSONDecodeError:
        pytest.fail("Output is not valid JSON")


def test_cli_check_strict_mode(runner, tmp_path):
    """Test CLI check with strict mode (warnings become errors)."""
    # Create plan
    plan_data = {
        "resource_changes": [
            {
                "address": "aws_db_instance.db",
                "type": "aws_db_instance",
                "name": "db",
                "change": {
                    "actions": ["create"],
                    "after": {"backup_retention_period": 3},
                },
            }
        ]
    }

    plan_file = tmp_path / "plan.json"
    with open(plan_file, "w") as f:
        json.dump(plan_data, f)

    # Create warning rule
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    rule_data = {
        "id": "backup-warning",
        "name": "Backup Warning",
        "resource_type": "aws_db_instance",
        "severity": "warning",  # Warning, not error
        "property": "backup_retention_period",
        "equals": 7,
        "message": "Test warning",
    }

    rule_file = rules_dir / "test-rule.json"
    with open(rule_file, "w") as f:
        json.dump(rule_data, f)

    # Without strict mode - should pass
    result_normal = runner.invoke(
        cli,
        ["check", str(plan_file), "--rules-dir", str(rules_dir)],
    )
    assert result_normal.exit_code == 0

    # With strict mode - should fail
    result_strict = runner.invoke(
        cli,
        ["check", str(plan_file), "--rules-dir", str(rules_dir), "--strict"],
    )
    assert result_strict.exit_code == 1


def test_cli_check_invalid_plan(runner, integration_rules, tmp_path):
    """Test CLI check with invalid plan file."""
    invalid_plan = tmp_path / "invalid.json"
    invalid_plan.write_text("{ invalid json }")

    result = runner.invoke(
        cli,
        ["check", str(invalid_plan), "--rules-dir", str(integration_rules)],
    )

    # Should exit with code 2 (error)
    assert result.exit_code == 2
    assert "Error loading" in result.output


def test_cli_check_nonexistent_plan(runner, integration_rules):
    """Test CLI check with non-existent plan file."""
    result = runner.invoke(
        cli,
        ["check", "/nonexistent/plan.json", "--rules-dir", str(integration_rules)],
    )

    # Click should catch the file not existing
    assert result.exit_code != 0


def test_cli_test_command(runner, integration_plan, integration_rules):
    """Test the 'test' subcommand."""
    result = runner.invoke(
        cli,
        [
            "test",
            "--rules",
            str(integration_rules),
            "--plan",
            str(integration_plan),
        ],
    )

    # Should find violations
    assert result.exit_code == 1


def test_cli_version(runner):
    """Test version flag."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "berm" in result.output.lower()


def test_cli_help(runner):
    """Test help output."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Policy Engine" in result.output


def test_cli_check_help(runner):
    """Test check command help."""
    result = runner.invoke(cli, ["check", "--help"])
    assert result.exit_code == 0
    assert "Terraform plan" in result.output


def test_cli_verbose_mode(runner, integration_plan, integration_rules):
    """Test verbose output."""
    result = runner.invoke(
        cli,
        [
            "check",
            str(integration_plan),
            "--rules-dir",
            str(integration_rules),
            "--verbose",
        ],
    )

    # Verbose mode should show loading messages
    assert "Loading rules" in result.output or "Loading" in result.output


def test_end_to_end_with_sample_fixtures(runner, sample_plan_file):
    """Test end-to-end with the sample fixtures."""
    examples_dir = Path(__file__).parent.parent.parent / "examples" / "rules"

    if not examples_dir.exists():
        pytest.skip("Examples directory not found")

    result = runner.invoke(
        cli,
        [
            "check",
            str(sample_plan_file),
            "--rules-dir",
            str(examples_dir),
            "--format",
            "terminal",
        ],
    )

    # Should find violations in the sample plan
    assert result.exit_code in (0, 1)  # Either pass or violations found
