"""Tests for rule loader."""

import json
from pathlib import Path

import pytest

from berm.loaders.rules import RuleLoadError, load_rules, load_single_rule
from berm.models.rule import Rule


def test_load_rules_from_directory(temp_rules_dir):
    """Test loading rules from a directory."""
    rules = load_rules(str(temp_rules_dir))

    assert len(rules) == 2
    assert all(isinstance(r, Rule) for r in rules)
    assert rules[0].id == "rule-1"
    assert rules[1].id == "rule-2"


def test_load_rules_sorted_by_id(temp_rules_dir):
    """Test that rules are sorted by ID."""
    rules = load_rules(str(temp_rules_dir))

    # Should be sorted alphabetically by ID
    rule_ids = [r.id for r in rules]
    assert rule_ids == sorted(rule_ids)


def test_load_rules_nonexistent_directory():
    """Test loading from non-existent directory."""
    with pytest.raises(RuleLoadError, match="does not exist"):
        load_rules("/nonexistent/path")


def test_load_rules_not_a_directory(temp_rule_file):
    """Test loading when path is a file, not a directory."""
    with pytest.raises(RuleLoadError, match="not a directory"):
        load_rules(str(temp_rule_file))


def test_load_rules_no_json_files(tmp_path):
    """Test loading from directory with no JSON files."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.raises(RuleLoadError, match="No rule files"):
        load_rules(str(empty_dir))


def test_load_rules_invalid_json(tmp_path):
    """Test loading directory with invalid JSON."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    # Create invalid JSON file
    invalid_file = rules_dir / "invalid.json"
    invalid_file.write_text("{ invalid json }")

    with pytest.raises(RuleLoadError, match="Invalid JSON"):
        load_rules(str(rules_dir))


def test_load_rules_invalid_schema(tmp_path):
    """Test loading rule with invalid schema."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    # Create file with invalid rule schema
    invalid_rule = rules_dir / "invalid.json"
    with open(invalid_rule, "w") as f:
        json.dump({"id": "test", "missing": "required fields"}, f)

    with pytest.raises(RuleLoadError, match="Validation failed"):
        load_rules(str(rules_dir))


def test_load_single_rule(temp_rule_file):
    """Test loading a single rule file."""
    rule = load_single_rule(str(temp_rule_file))

    assert isinstance(rule, Rule)
    assert rule.id == "temp-test-rule"
    assert rule.name == "Temporary Test Rule"


def test_load_single_rule_nonexistent():
    """Test loading non-existent file."""
    with pytest.raises(RuleLoadError, match="does not exist"):
        load_single_rule("/nonexistent/file.json")


def test_load_single_rule_not_a_file(tmp_path):
    """Test loading when path is a directory."""
    with pytest.raises(RuleLoadError, match="not a file"):
        load_single_rule(str(tmp_path))


def test_load_rules_recursive(tmp_path):
    """Test loading rules recursively from subdirectories."""
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    # Create nested directory structure
    subdir = rules_dir / "aws"
    subdir.mkdir()

    # Create rule in subdirectory
    rule_data = {
        "id": "nested-rule",
        "name": "Nested Rule",
        "resource_type": "aws_s3_bucket",
        "severity": "error",
        "property": "prop",
        "equals": True,
        "message": "msg",
    }

    rule_file = subdir / "nested.json"
    with open(rule_file, "w") as f:
        json.dump(rule_data, f)

    # Should find nested rule
    rules = load_rules(str(rules_dir))
    assert len(rules) == 1
    assert rules[0].id == "nested-rule"


def test_load_rules_from_examples():
    """Test loading rules from examples directory."""
    examples_dir = Path(__file__).parent.parent.parent / "examples" / "rules"

    if examples_dir.exists():
        rules = load_rules(str(examples_dir))
        assert len(rules) > 0
        assert all(isinstance(r, Rule) for r in rules)
