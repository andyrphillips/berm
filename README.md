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
# Install from PyPI (coming soon)
pip install berm

# Or install from source
git clone https://github.com/yourusername/berm.git
cd berm
pip install -e .
```

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
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan > plan.json
```

4. **Run Berm**:

```bash
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

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier for the rule |
| `name` | string | Human-readable name |
| `resource_type` | string | Terraform resource type (e.g., `aws_s3_bucket`) |
| `severity` | string | `"error"` (blocks deployment) or `"warning"` (advisory) |
| `property` | string | Dot-notation path to property (e.g., `versioning.enabled`) |
| `equals` | any | Expected value (boolean, string, number) |
| `message` | string | Error message (supports `{{resource_name}}` template) |

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

### RDS Backup Retention (Warning)

```json
{
  "id": "rds-backup-retention-minimum",
  "name": "RDS instances should have minimum backup retention",
  "resource_type": "aws_db_instance",
  "severity": "warning",
  "property": "backup_retention_period",
  "equals": 7,
  "message": "RDS instance {{resource_name}} should have at least 7 days backup retention"
}
```

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
├── __init__.py           # Package metadata
├── cli.py                # CLI entry point
├── models/
│   ├── rule.py           # Rule data model
│   └── violation.py      # Violation data model
├── loaders/
│   ├── rules.py          # Rule file loader
│   └── terraform.py      # Terraform plan parser
├── evaluators/
│   └── simple.py         # Property evaluation engine
└── reporters/
    ├── terminal.py       # Terminal output
    ├── github.py         # GitHub Actions format
    └── json_reporter.py  # JSON output
```

## Roadmap

### Near-term
- Cross-resource validation
- Simple regex expressions in rules
- HCL static analysis (parse `.tf` files directly)
- SARIF output format
- Rule exemptions and allow-lists

### Medium-term
- Pattern matching (Semgrep-style)
- Multi-language support (Python, Airflow, Kubernetes)
- Auto-fix suggestions
- Native GitHub Action

### Long-term
- Visual rule builder
- Community rule marketplace
- Compliance framework packs (SOC2, PCI, CIS)
- Cloud/SaaS offering

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- GitHub Issues: [github.com/yourusername/berm/issues](https://github.com/yourusername/berm/issues)
- Documentation: [github.com/yourusername/berm#readme](https://github.com/yourusername/berm#readme)

## Philosophy

**Guide, don't block.** Berm is designed to help teams move fast while maintaining best practices. We believe in:

- Paved roads over bureaucracy
- Fast feedback over slow pipelines
- Clear errors over cryptic messages
- Community-driven rules over vendor lock-in
- AI-era development over legacy tooling

---

**Take the fast line through infrastructure.**
