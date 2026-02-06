# Berm - Policy Engine for CI/CD Pipelines

**Guide teams toward infrastructure best practices without blocking velocity.**

Berm is a policy-as-code engine purpose-built for teams using AI to generate infrastructure code. Like a banked turn in motocross, Berm helps teams maintain speed while staying on the optimal line.

## Why Berm?

AI assistants (Claude, GPT, Copilot) generate functionally correct infrastructure code, but often miss:
- Security best practices
- Compliance requirements
- Organizational standards

Berm provides "spell check" for AI-generated Terraform, catching missing encryption, overly permissive IAM, and compliance violations before they reach production.

## Key Features

- **Radical Simplicity** - Rules are JSON files that read like English, not complex DSLs
- **Fast Feedback** - Runs locally in < 1 second, in CI in < 10 seconds
- **Guide, Don't Block** - Separate errors from warnings, maintain velocity
- **Purpose-Built for AI** - Designed for teams using AI code generation
- **Pluggable Architecture** - Easy to extend with custom evaluators and reporters

## Quick Start

### Installation

```bash
# Install from source (PyPI distribution coming soon)
git clone https://github.com/yourusername/berm.git
cd berm
pip install -e .
```

This will install Berm with its dependencies:
- `pydantic>=2.0.0` - Rule validation and data modeling
- `click>=8.0.0` - CLI framework
- `rich>=13.0.0` - Beautiful terminal output

### Basic Usage

1. **Create a rules directory** with policy rules:

```bash
mkdir .berm
```

2. **Add a rule** (`.berm/s3-versioning.json`):

```json
{
  "id": "s3-versioning-enabled",
  "name": "S3 buckets must have versioning enabled",
  "resource_type": "aws_s3_bucket_versioning",
  "severity": "error",
  "property": "versioning_configuration.0.status",
  "equals": "Enabled",
  "message": "S3 bucket {{resource_name}} must have versioning enabled for data protection"
}
```

3. **Generate a Terraform plan**:

```bash
# Create Terraform plan
terraform plan -out=plan.tfplan

# Option A: Let Berm auto-convert (recommended - works everywhere)
# No conversion needed! Berm detects and converts binary plans automatically

# Option B: Use berm convert command (shell-agnostic)
berm convert plan.tfplan

# Option C: Manual conversion (shell-specific syntax)
# Bash/Linux/macOS: terraform show -json plan.tfplan > plan.json
# PowerShell: terraform show -json plan.tfplan | Out-File -Encoding utf8 plan.json
```

4. **Run Berm**:

```bash
# Works with binary plans (auto-converts)
berm check plan.tfplan

# Or use JSON directly
berm check plan.json
```

### Example Output

```
Errors (1):
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Resource                           │ Rule                              │ Message ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ aws_s3_bucket_versioning.bucket    │ S3 versioning enabled             │ ...     │
└─────────────────────────────────────────────────────────────────────────────────┘

Summary: 1 error(s), 0 warnings
```

## CLI Commands

### `berm check`

Check a Terraform plan against policy rules.

```bash
berm check plan.json [OPTIONS]

Options:
  --rules-dir, -r PATH    Directory containing rules (default: .berm)
  --format, -f FORMAT     Output format: terminal, github, json
  --strict                Treat warnings as errors
  --verbose, -v           Enable verbose output
```

**Examples:**

```bash
# Basic check with default rules directory
berm check plan.json

# Custom rules directory
berm check plan.json --rules-dir custom-rules/

# GitHub Actions format (for annotations)
berm check plan.json --format github

# Strict mode (fail on warnings)
berm check plan.json --strict

# JSON output for integrations
berm check plan.json --format json
```

### `berm test`

Test rules against a plan (explicit paths).

```bash
berm test --rules RULES_DIR --plan PLAN_FILE [OPTIONS]

Options:
  --rules, -r PATH        Directory containing rules (required)
  --plan, -p PATH         Terraform plan JSON file (required)
  --format, -f FORMAT     Output format: terminal, github, json
  --strict                Treat warnings as errors
```

**Example:**

```bash
berm test --rules examples/rules --plan examples/plans/plan.json
```

### `berm convert`

Convert Terraform binary plan to JSON format (shell-agnostic).

```bash
berm convert TFPLAN_FILE [OPTIONS]

Options:
  --output, -o PATH       Output JSON file path (default: plan.json)
```

**Examples:**

```bash
# Convert to plan.json
berm convert plan.tfplan

# Convert to custom output file
berm convert plan.tfplan --output my-plan.json

# Then check the converted plan
berm check plan.json
```

**Note:** This command requires `terraform` to be installed and in your PATH. It's a convenience wrapper around `terraform show -json` that ensures proper encoding across all platforms (Windows, Linux, macOS).

## Rule Format

Rules are defined in JSON files with a simple, intuitive schema:

```json
{
  "id": "unique-rule-id",
  "name": "Human-readable rule name",
  "resource_type": "terraform_resource_type",
  "severity": "error | warning",
  "property": "nested.property.path",
  "equals": "expected-value",
  "message": "Error message with {{resource_name}} template"
}
```

### Rule Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for the rule |
| `name` | string | Yes | Human-readable name |
| `resource_type` | string | Yes | Terraform resource type (e.g., `aws_s3_bucket`) |
| `severity` | string | Yes | `"error"` (blocks deployment) or `"warning"` (advisory) |
| `property` | string | Yes | Dot-notation path to property (e.g., `versioning.enabled`) |
| `message` | string | Yes | Error message (supports `{{resource_name}}` template) |

**Comparison Operators** (exactly one required):

| Operator | Type | Description |
|----------|------|-------------|
| `equals` | any | Exact value match (boolean, string, number, null) |
| `greater_than` | number | Property value must be > this number |
| `greater_than_or_equal` | number | Property value must be >= this number |
| `less_than` | number | Property value must be < this number |
| `less_than_or_equal` | number | Property value must be <= this number |

**Special Rule Types:**

| Field | Type | Description |
|-------|------|-------------|
| `resource_forbidden` | boolean | If `true`, any usage of `resource_type` is a violation. Use this to enforce module usage instead of direct resource creation. When set, `property` and comparison operators are not needed. |

### Property Path Syntax

Use dot notation to access nested properties:

```json
"property": "versioning.enabled"                    // Object property
"property": "rules.0.status"                       // Array index
"property": "encryption.kms_key_id"                // Nested object
"property": "versioning_configuration.0.status"    // Array + nested
```

## Example Rules

### S3 Bucket Versioning

```json
{
  "id": "s3-versioning-enabled",
  "name": "S3 buckets must have versioning enabled",
  "resource_type": "aws_s3_bucket_versioning",
  "severity": "error",
  "property": "versioning_configuration.0.status",
  "equals": "Enabled",
  "message": "S3 bucket {{resource_name}} must have versioning enabled for compliance"
}
```

### RDS Encryption

```json
{
  "id": "rds-storage-encrypted",
  "name": "RDS instances must have storage encryption",
  "resource_type": "aws_db_instance",
  "severity": "error",
  "property": "storage_encrypted",
  "equals": true,
  "message": "RDS instance {{resource_name}} must have storage encryption enabled"
}
```

### RDS Backup Retention (Numeric Comparison)

```json
{
  "id": "rds-backup-retention-minimum",
  "name": "RDS instances must have minimum backup retention period",
  "resource_type": "aws_db_instance",
  "severity": "warning",
  "property": "backup_retention_period",
  "greater_than_or_equal": 7,
  "message": "RDS instance {{resource_name}} should have at least 7 days backup retention for disaster recovery"
}
```

This rule uses `greater_than_or_equal` to ensure backup retention is 7 days or more, catching instances with 0-6 days retention.

### Forbidden Resource (Enforce Module Usage)

```json
{
  "id": "s3-use-module-only",
  "name": "S3 buckets must use approved module",
  "resource_type": "aws_s3_bucket",
  "severity": "error",
  "resource_forbidden": true,
  "message": "Direct use of aws_s3_bucket is not allowed. Use module.s3_bucket instead to ensure security defaults (versioning, encryption, public access blocks) are applied"
}
```

This rule prevents direct usage of `aws_s3_bucket` resources, enforcing that teams use your approved Terraform module instead. This is useful when:
- You have wrapper modules with security defaults
- You want to prevent teams from forgetting important configurations
- You need to standardize resource creation patterns across your organization

**Note:** Module resources in Terraform plans appear with addresses like `module.s3_bucket.aws_s3_bucket.this[0]`, which won't match the `aws_s3_bucket` resource_type filter. This allows module usage while blocking direct resource creation.

## CI/CD Integration

### GitHub Actions

```yaml
name: Terraform Plan Check

on: [pull_request]

jobs:
  berm-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2

      - name: Terraform Init
        run: terraform init

      - name: Terraform Plan
        run: |
          terraform plan -out=plan.tfplan
          terraform show -json plan.tfplan > plan.json

      - name: Install Berm
        run: pip install berm

      - name: Check Policies
        run: berm check plan.json --format github
```

### GitLab CI

```yaml
terraform-check:
  stage: test
  script:
    - terraform init
    - terraform plan -out=plan.tfplan
    - terraform show -json plan.tfplan > plan.json
    - pip install berm
    - berm check plan.json
```

## Exit Codes

Berm uses standard exit codes for CI/CD integration:

- `0` - No violations (or only warnings in non-strict mode)
- `1` - Policy violations found (errors, or warnings in strict mode)
- `2` - Error in execution (invalid input, missing files, etc.)

## Output Formats

### Terminal (Default)

Colorful, human-readable output with tables and summaries.

```bash
berm check plan.json
```

### GitHub Actions

Workflow annotations that appear in pull requests.

```bash
berm check plan.json --format github
```

### JSON

Machine-readable output for integrations.

```bash
berm check plan.json --format json
```

**Output structure:**

```json
{
  "summary": {
    "total_violations": 2,
    "errors": 1,
    "warnings": 1,
    "passed": false
  },
  "violations": [
    {
      "rule_id": "s3-versioning-enabled",
      "rule_name": "S3 versioning enabled",
      "resource_name": "aws_s3_bucket.example",
      "resource_type": "aws_s3_bucket",
      "severity": "error",
      "message": "S3 bucket must have versioning enabled",
      "location": null
    }
  ]
}
```

## Development

### Prerequisites

- Python 3.9+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/berm.git
cd berm

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=berm

# Format code
black .

# Lint
ruff check .

# Type check
mypy berm
```

### Project Structure

```
berm/
├── __init__.py              # Package metadata and version
├── cli.py                   # CLI entry point with click commands
├── models/
│   ├── __init__.py
│   ├── rule.py              # Pydantic Rule model with validation
│   └── violation.py         # Violation dataclass
├── loaders/
│   ├── __init__.py
│   ├── rules.py             # JSON rule file loader with validation
│   └── terraform.py         # Terraform plan JSON parser
├── evaluators/
│   ├── __init__.py
│   └── simple.py            # Property equality evaluator
└── reporters/
    ├── __init__.py          # Reporter factory function
    ├── terminal.py          # Rich-formatted terminal output
    ├── github.py            # GitHub Actions annotations
    └── json_reporter.py     # Structured JSON output

tests/
├── conftest.py              # Shared pytest fixtures
├── models/
│   ├── test_rule.py
│   └── test_violation.py
├── loaders/
│   ├── test_rules.py
│   └── test_terraform.py
├── evaluators/
│   └── test_simple.py
├── integration/
│   └── test_e2e.py          # End-to-end integration tests
└── fixtures/
    └── sample-plan.json     # Sample Terraform plan for testing

examples/
├── README.md                # Example usage guide
├── rules/                   # Example policy rules
│   ├── s3-versioning-enabled.json
│   ├── s3-encryption-enabled.json
│   ├── s3-block-public-access.json
│   ├── rds-encryption-enabled.json
│   └── rds-backup-retention.json
└── terraform/
    └── main.tf              # Example Terraform configuration
```

## Implementation Status

### ✅ Completed (MVP)
- Core CLI with `check` and `test` commands
- JSON rule loading and Pydantic validation
- Terraform plan JSON parsing
- Property-based equality evaluator with dot notation support
- Three output formats: terminal (Rich), GitHub Actions, JSON
- Comprehensive test suite with pytest
- Error handling and exit codes for CI/CD
- Example rules and Terraform configurations
- Full type hints with mypy compliance

### 🚧 Roadmap

#### Near-term
- Cross-resource validation (e.g., S3 bucket must have corresponding logging resource)
- Regex pattern matching in rules
- HCL static analysis (parse `.tf` files directly)
- SARIF output format
- Rule exemptions and allow-lists
- PyPI package distribution

#### Medium-term
- Pattern matching (Semgrep-style syntax)
- Multi-language support (Python linting, Airflow DAG validation, Kubernetes manifests)
- Auto-fix suggestions
- Native GitHub Action
- Additional comparison operators (greater than, less than, contains, etc.)

#### Long-term
- Visual rule builder
- Community rule marketplace
- Compliance framework packs (SOC2, PCI, CIS, AWS Well-Architected)
- Cloud/SaaS offering with dashboards
- IDE integration (VS Code extension)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Architecture & Design

### Modular Design
Berm is built with extensibility in mind:
- **Pluggable Loaders**: Currently supports Terraform plan JSON, designed to add HCL, Kubernetes YAML, etc.
- **Pluggable Evaluators**: Simple equality checks now, expression-based evaluation later
- **Pluggable Reporters**: Three formats implemented (terminal, GitHub, JSON), easy to add more (SARIF, JUnit XML)
- **Clear Abstractions**: Rule → Evaluator → Violation → Reporter pipeline

### Key Implementation Details
- **Type Safety**: Full type hints throughout, validated with mypy
- **Data Validation**: Pydantic models ensure rule correctness
- **Property Access**: Dot notation supports nested objects and array indexing (e.g., `versioning_configuration.0.status`)
- **Error Handling**: Custom exception types for clear error messages
- **Testing**: Comprehensive test suite with fixtures, unit tests, and integration tests
- **Code Quality**: Black for formatting, Ruff for linting, pytest for testing

## Support

- GitHub Issues: [github.com/yourusername/berm/issues](https://github.com/yourusername/berm/issues)
- Documentation: [github.com/yourusername/berm#readme](https://github.com/yourusername/berm#readme)
- Examples: See [examples/](examples/) directory for working demonstrations

## Philosophy

**Guide, don't block.** Berm is designed to help teams move fast while maintaining best practices. We believe in:

- Paved roads over bureaucracy
- Fast feedback over slow pipelines
- Clear errors over cryptic messages
- Community-driven rules over vendor lock-in
- AI-era development over legacy tooling

---

**Take the fast line through infrastructure.**
