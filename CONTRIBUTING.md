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

This installs Berm along with development dependencies (pytest, black, mypy, ruff).

3. **Verify installation**

```bash
# Run tests
pytest

# Check formatting
black --check .

# Run linter
ruff check .

# Type check
mypy berm
```

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

- Follow PEP 8
- Use type hints for function signatures
- Maximum line length: 88 characters (Black default)
- Use descriptive variable names

### Example

```python
def evaluate_rule(
    rule: Rule,
    resources: List[Dict[str, Any]]
) -> List[Violation]:
    """Evaluate a policy rule against resources.

    Args:
        rule: The policy rule to evaluate
        resources: List of Terraform resources

    Returns:
        List of violations found
    """
    violations = []
    # Implementation...
    return violations
```

### Documentation

- Add docstrings to all public functions, classes, and methods
- Use Google-style docstrings
- Include examples in docstrings when helpful

## Testing Guidelines

### Unit Tests

- Place unit tests in `tests/` directory
- Mirror the source structure: `berm/models/rule.py` → `tests/models/test_rule.py`
- Test both success and error cases
- Use descriptive test names: `test_rule_validation_rejects_invalid_severity`

### Integration Tests

- Place integration tests in `tests/integration/`
- Test complete workflows end-to-end
- Use fixtures for test data

### Test Coverage

- Aim for >80% code coverage
- Focus on critical paths and edge cases
- Use `pytest --cov=berm --cov-report=html` to view coverage report

## Contributing New Features

### Adding a New Rule Type

1. Extend the `Rule` model in `berm/models/rule.py`
2. Update the evaluator in `berm/evaluators/`
3. Add tests in `tests/evaluators/`
4. Document in README.md

### Adding a New Reporter

1. Create new reporter class in `berm/reporters/`
2. Implement the `report()` method
3. Add to reporter factory in `berm/reporters/__init__.py`
4. Add CLI option in `berm/cli.py`
5. Add tests
6. Document in README.md

### Adding New Loaders

1. Create loader in `berm/loaders/`
2. Follow the pattern of existing loaders
3. Add comprehensive tests
4. Update CLI if needed

## Contributing Rules

We welcome contributions of policy rules!

1. Create rule JSON file in `examples/rules/`
2. Test against real Terraform plans
3. Document the rule's purpose and use case
4. Submit via pull request

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

1. **Automated checks**: Tests, linting, type checking must pass
2. **Manual review**: A maintainer reviews the code
3. **Feedback**: Address any requested changes
4. **Approval**: Once approved, maintainer merges

## Community Guidelines

- Be respectful and inclusive
- Help others learn
- Provide constructive feedback
- Focus on the problem, not the person
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md) (TODO)

## Questions?

- Open a GitHub Discussion for questions
- Check existing documentation in README.md
- Look at existing code for examples

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Berm! 🚀
