# Contributing to Berm

Thank you for your interest in contributing to Berm! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- A GitHub account

### Setting Up Development Environment

1. **Fork and clone the repository**

```bash
git clone https://github.com/yourusername/berm.git
cd berm
```

2. **Install in development mode**

```bash
pip install -e ".[dev]"
```

This installs Berm along with its dependencies:
- **Runtime dependencies**: `pydantic>=2.0.0`, `click>=8.0.0`, `rich>=13.0.0`
- **Development dependencies**: `pytest>=7.0.0`, `pytest-cov>=4.0.0`, `black>=23.0.0`, `mypy>=1.0.0`, `ruff>=0.1.0`

3. **Verify installation**

```bash
# Run tests (configured to show coverage)
pytest

# Check formatting
black --check .

# Run linter
ruff check .

# Type check
mypy berm
```

All tests should pass and you should see coverage reports in both terminal and HTML format (`htmlcov/index.html`).

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Your Changes

- Write clear, concise code
- Follow existing code style and patterns
- Add docstrings to new functions and classes
- Keep changes focused and atomic

### 3. Write Tests

- Add unit tests for new functionality
- Ensure all tests pass: `pytest`
- Maintain test coverage above 80%: `pytest --cov=berm`

### 4. Format and Lint

```bash
# Format code
black .

# Check linting
ruff check .

# Type check
mypy berm
```

### 5. Commit Your Changes

Write clear commit messages:

```bash
git commit -m "Add feature: brief description

Longer explanation of what changed and why.
"
```

### 6. Push and Create Pull Request

```bash
git push origin your-branch-name
```

Then create a pull request on GitHub.

## Code Style Guidelines

### Python Style

Berm follows strict code quality standards:
- **PEP 8**: Enforced by Ruff linter
- **Type hints**: Required for all function signatures (enforced by mypy)
- **Line length**: 88 characters (Black default)
- **Naming**: Use descriptive names (`resource_type` not `rt`)
- **Formatting**: Automated with Black (no manual formatting needed)

### Automated Code Quality Tools

All configured in [pyproject.toml](pyproject.toml):

1. **Black** (code formatting)
   - Line length: 88
   - Target: Python 3.9+
   - Run: `black .`

2. **Ruff** (linting)
   - Checks: pycodestyle, pyflakes, isort, flake8-bugbear, comprehensions, pyupgrade
   - Run: `ruff check .`
   - Auto-fix: `ruff check --fix .`

3. **Mypy** (type checking)
   - Strict mode enabled
   - No untyped definitions allowed (except in tests)
   - Run: `mypy berm`

### Docstring Style

Use Google-style docstrings for all public functions, classes, and methods:

```python
def evaluate_rule(
    rule: Rule,
    resources: List[Dict[str, Any]]
) -> List[Violation]:
    """Evaluate a policy rule against resources.

    Args:
        rule: The policy rule to evaluate
        resources: List of Terraform resources from the plan

    Returns:
        List of violations found (empty if all resources comply)

    Raises:
        ValueError: If rule or resources are invalid

    Example:
        >>> evaluator = SimpleEvaluator()
        >>> violations = evaluator.evaluate(rule, resources)
        >>> print(f"Found {len(violations)} violations")
    """
    violations = []
    # Implementation...
    return violations
```

Key points:
- First line: Brief one-line summary
- Args/Returns/Raises: Document all parameters and return values
- Examples: Include when helpful for understanding usage
- Type hints: Always use type hints in signatures (don't just document types)

## Testing Guidelines

### Test Structure

The test suite is organized to mirror the source code:
```
tests/
├── conftest.py              # Shared pytest fixtures
├── models/
│   ├── test_rule.py         # Tests for Rule model
│   └── test_violation.py    # Tests for Violation model
├── loaders/
│   ├── test_rules.py        # Tests for rule loading
│   └── test_terraform.py    # Tests for Terraform plan parsing
├── evaluators/
│   └── test_simple.py       # Tests for property evaluator
├── integration/
│   └── test_e2e.py          # End-to-end integration tests
└── fixtures/
    └── sample-plan.json     # Sample Terraform plan for testing
```

### Unit Tests

- Place tests in corresponding directory: `berm/models/rule.py` → `tests/models/test_rule.py`
- Test both success and error cases
- Use descriptive test names: `test_rule_validation_rejects_invalid_severity()`
- Leverage shared fixtures from [conftest.py](tests/conftest.py):
  - `sample_rule()` - Basic error rule
  - `sample_warning_rule()` - Warning rule
  - `sample_violation()` - Sample violation
  - `sample_resources()` - Sample Terraform resources
  - `temp_rules_dir(tmp_path)` - Temporary rules directory

Example:
```python
def test_evaluator_finds_violations(sample_rule, sample_resources):
    evaluator = SimpleEvaluator()
    violations = evaluator.evaluate(sample_rule, sample_resources)
    assert len(violations) > 0
```

### Integration Tests

- Place in `tests/integration/`
- Test complete workflows end-to-end
- Test CLI commands, not just internal APIs
- Use temporary directories for file operations

### Test Coverage

- Target: >80% code coverage (currently configured in pyproject.toml)
- Coverage reports generated automatically on test runs
- View HTML report: `open htmlcov/index.html`
- Focus on critical paths and edge cases
- Don't test external libraries (pydantic, click, etc.)

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/models/test_rule.py

# Run specific test function
pytest tests/models/test_rule.py::test_rule_validation

# Run with verbose output
pytest -v

# Run without coverage
pytest --no-cov

# Generate HTML coverage report
pytest --cov=berm --cov-report=html
```

## Project Structure Overview

```
berm/
├── __init__.py              # Package version and metadata
├── cli.py                   # Click-based CLI with check/test commands
├── models/
│   ├── rule.py              # Pydantic Rule model
│   └── violation.py         # Violation dataclass
├── loaders/
│   ├── rules.py             # Rule file loader (recursively finds .json)
│   └── terraform.py         # Terraform plan parser + property accessor
├── evaluators/
│   └── simple.py            # Property equality evaluator
└── reporters/
    ├── __init__.py          # get_reporter() factory
    ├── terminal.py          # Rich-based terminal output
    ├── github.py            # GitHub Actions annotations
    └── json_reporter.py     # Structured JSON output
```

## Contributing New Features

### Adding a New Comparison Operator

Currently, rules only support `equals` checks. To add new operators (e.g., `greater_than`, `contains`, `matches`):

1. **Update the Rule model** in [berm/models/rule.py](berm/models/rule.py)
   - Add new optional field (e.g., `greater_than: Optional[int] = None`)
   - Add validation to ensure only one comparison operator is set

2. **Update the evaluator** in [berm/evaluators/simple.py](berm/evaluators/simple.py)
   - Add logic to `_check_resource()` to handle new operator
   - Ensure clear error messages

3. **Add tests** in [tests/evaluators/test_simple.py](tests/evaluators/test_simple.py)
   - Test success case
   - Test failure case
   - Test edge cases

4. **Update documentation** in [README.md](README.md)
   - Add to rule format section
   - Provide example

### Adding a New Reporter

1. **Create reporter class** in `berm/reporters/new_reporter.py`
   ```python
   from typing import List
   from berm.models.violation import Violation

   class NewReporter:
       def report(self, violations: List[Violation]) -> None:
           # Implement your output format
           pass
   ```

2. **Add to reporter factory** in [berm/reporters/__init__.py](berm/reporters/__init__.py)
   ```python
   from berm.reporters.new_reporter import NewReporter

   def get_reporter(format: str):
       reporters = {
           # ... existing reporters
           "new_format": NewReporter,
       }
   ```

3. **Update CLI** in [berm/cli.py](berm/cli.py)
   - Add format to the `click.Choice` list in `--format` option

4. **Add tests** in `tests/reporters/test_new_reporter.py`

5. **Document** in [README.md](README.md) under "Output Formats"

### Adding New Loaders

To support additional file formats (e.g., HCL, Kubernetes YAML):

1. **Create loader** in `berm/loaders/new_loader.py`
   - Follow pattern from [terraform.py](berm/loaders/terraform.py)
   - Return normalized resource structure:
     ```python
     {
         "address": "resource.name",
         "type": "resource_type",
         "name": "name",
         "values": {...}  # Resource configuration
     }
     ```

2. **Add custom exception** for error handling
   ```python
   class NewLoaderError(Exception):
       pass
   ```

3. **Add comprehensive tests** in `tests/loaders/test_new_loader.py`
   - Test valid input
   - Test invalid input
   - Test edge cases

4. **Update CLI** in [berm/cli.py](berm/cli.py) if needed

5. **Document** in [README.md](README.md)

### Extending the Rule Model

Current rule fields:
- `id`: Unique identifier
- `name`: Human-readable name
- `resource_type`: Terraform resource type
- `severity`: "error" or "warning"
- `property`: Dot-notation path
- `equals`: Expected value
- `message`: Error message (supports `{{resource_name}}` template)

To add new fields:
1. Update [Rule model](berm/models/rule.py)
2. Add Pydantic validators if needed
3. Update evaluator to use new fields
4. Update tests
5. Update documentation and examples

## Contributing Rules

We welcome contributions of policy rules! Community-driven rules are a key part of Berm's value.

### Creating a New Rule

1. **Create rule JSON file** in [examples/rules/](examples/rules/)
   - Use kebab-case naming: `service-feature-requirement.json`
   - Follow the existing pattern (see [s3-versioning-enabled.json](examples/rules/s3-versioning-enabled.json))

2. **Test against real Terraform plans**
   ```bash
   # Create a test Terraform config
   # Generate plan
   terraform plan -out=plan.tfplan
   terraform show -json plan.tfplan > plan.json

   # Test your rule
   berm test --rules examples/rules --plan plan.json
   ```

3. **Document the rule**
   - Add clear, descriptive `name` and `message` fields
   - Explain what the rule checks and why it matters
   - If the rule is specific to a compliance framework (SOC2, PCI, etc.), mention it in the message

4. **Submit via pull request**
   - Include example Terraform code that violates the rule
   - Include example Terraform code that passes the rule
   - Explain the use case in the PR description

### Rule Writing Best Practices

- **Be specific**: Target exact resource types (e.g., `aws_s3_bucket_encryption` not just `aws_s3_bucket`)
- **Use "error" sparingly**: Reserve for security/compliance violations, use "warning" for recommendations
- **Provide context**: Include why the rule exists in the message
- **Test thoroughly**: Verify the rule works on real Terraform plans
- **Use clear IDs**: Format as `service-resource-requirement` (e.g., `s3-bucket-versioning-enabled`)

Example rule:
```json
{
  "id": "s3-versioning-enabled",
  "name": "S3 buckets must have versioning enabled",
  "resource_type": "aws_s3_bucket_versioning",
  "severity": "error",
  "property": "versioning_configuration.0.status",
  "equals": "Enabled",
  "message": "S3 bucket {{resource_name}} must have versioning enabled for data protection and compliance"
}
```

## Reporting Bugs

### Before Submitting

- Check existing issues to avoid duplicates
- Verify bug exists in the latest version
- Collect relevant information (OS, Python version, error messages)

### Creating a Bug Report

Include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Minimal steps to reproduce
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, Python version, Berm version
6. **Logs/Output**: Error messages, stack traces

## Feature Requests

We welcome feature suggestions! When requesting a feature:

1. Check if it already exists or has been requested
2. Clearly describe the use case
3. Explain why it would be valuable
4. Provide examples if possible

## Code Review Process

All contributions go through code review:

1. **Automated checks**: Must pass before review
   - All tests pass (`pytest`)
   - Code formatted with Black (`black --check .`)
   - No linting errors (`ruff check .`)
   - Type checking passes (`mypy berm`)
   - Coverage maintained (>80%)

2. **Manual review**: A maintainer reviews the code for:
   - Code correctness and clarity
   - Test coverage and quality
   - Documentation completeness
   - Adherence to design patterns
   - Performance considerations

3. **Feedback**: Address any requested changes
   - Make updates in new commits (don't force push)
   - Respond to review comments
   - Update tests if implementation changes

4. **Approval**: Once approved, maintainer merges
   - Squash merge for feature branches
   - Direct merge for hotfixes

### Pre-submission Checklist

Before submitting a PR, ensure:
- [ ] All tests pass: `pytest`
- [ ] Code is formatted: `black .`
- [ ] No linting errors: `ruff check .`
- [ ] Type checking passes: `mypy berm`
- [ ] Documentation updated (README, docstrings, etc.)
- [ ] New features have tests
- [ ] Commit messages are clear and descriptive

## Community Guidelines

- **Be respectful and inclusive**: Welcome contributors of all skill levels
- **Help others learn**: Share knowledge and explain decisions
- **Provide constructive feedback**: Focus on improving the code, not criticizing the author
- **Focus on the problem**: Address technical issues, not personal attributes
- **Assume good intent**: Contributors are here to help make Berm better
- **Be patient**: Everyone is learning, including maintainers

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **Pull Requests**: Code contributions and discussions
- **GitHub Discussions**: Questions, ideas, general discussion (coming soon)

## Questions?

- Open a GitHub Discussion for questions
- Check existing documentation in README.md
- Look at existing code for examples

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Berm! 🚀
