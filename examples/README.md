# Berm Examples

This directory contains example Terraform configurations and policy rules to demonstrate Berm's capabilities.

## Quick Start

### 1. Review the Terraform Configuration

The `terraform/main.tf` file contains:
- ✅ Compliant resources (S3 bucket with versioning, encryption, public access blocks)
- ❌ Non-compliant resources (S3 bucket without security features)
- ⚠️ Resources with warnings (RDS with low backup retention)

### 2. Review the Policy Rules

The `rules/` directory contains example policy rules:
- `s3-versioning-enabled.json` - S3 buckets must have versioning enabled
- `s3-encryption-enabled.json` - S3 buckets must have encryption
- `s3-block-public-access.json` - S3 buckets must block public access
- `rds-encryption-enabled.json` - RDS instances must be encrypted
- `rds-backup-retention.json` - RDS instances should have 7+ day backup retention

### 3. Generate a Terraform Plan

```bash
cd terraform/
terraform init
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan > ../plans/plan.json
cd ..
```

### 4. Run Berm

```bash
# From the examples directory
berm test --rules rules/ --plan plans/plan.json

# Or from the project root
berm test --rules examples/rules --plan examples/plans/plan.json
```

### 5. View the Results

Berm will:
- ✅ Report 3-4 errors for non-compliant resources
- ⚠️ Report 1-2 warnings for resources with recommendations
- 📊 Show a summary of findings

## Expected Output

```
Errors (3):
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Resource                 │ Rule                              │ Message   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ aws_s3_bucket_versio...  │ S3 buckets must have versioning  │ ...       │
│ aws_s3_bucket_public...  │ S3 buckets must block public...  │ ...       │
│ aws_db_instance.non_...  │ RDS instances must have encry... │ ...       │
└────────────────────────────────────────────────────────────────────────┘

Warnings (1):
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Resource                 │ Rule                              │ Message   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ aws_db_instance.non_...  │ RDS instances must have minimu... │ ...       │
└────────────────────────────────────────────────────────────────────────┘

Summary: 3 error(s), 1 warning(s)
```

## Trying Different Output Formats

### JSON Output
```bash
berm test --rules rules/ --plan plans/plan.json --format json
```

### GitHub Actions Format
```bash
berm test --rules rules/ --plan plans/plan.json --format github
```

### Strict Mode (Treat Warnings as Errors)
```bash
berm test --rules rules/ --plan plans/plan.json --strict
```

## Creating Your Own Rules

1. Create a new JSON file in the `rules/` directory
2. Follow the rule schema:

```json
{
  "id": "unique-id",
  "name": "Human-readable name",
  "resource_type": "terraform_resource_type",
  "severity": "error",
  "property": "nested.property.path",
  "equals": "expected-value",
  "message": "Error message with {{resource_name}} template"
}
```

3. Test it:
```bash
berm test --rules rules/ --plan plans/plan.json
```

## Using with CI/CD

### GitHub Actions Example

```yaml
- name: Check Terraform Policies
  run: |
    terraform plan -out=plan.tfplan
    terraform show -json plan.tfplan > plan.json
    pip install berm
    berm check plan.json --rules-dir .berm --format github
```

### Exit Codes

- `0` = All checks passed (or only warnings in non-strict mode)
- `1` = Policy violations found
- `2` = Error in execution (invalid files, etc.)

## Next Steps

- Review the [main README](../README.md) for full documentation
- Explore the [rule files](rules/) to understand the schema
- Customize rules for your organization's policies
- Integrate Berm into your CI/CD pipeline
