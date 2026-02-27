# Berm Implementation Plan for c-c-t Organization

## Overview

This plan guides you through implementing berm as your centralized Terraform policy validation system using the GitHub Actions reusable workflow pattern.

---

## Phase 1: Repository Setup

### 1.1 Fork Berm Repository ✅ COMPLETED
- [x] Forked to: `c-c-t/berm`

### 1.2 Set Up Berm Policies Repository

**Repository:** `c-c-t/terraform-policies`

This repository will store your centralized berm policy rules.

#### Directory Structure to Create

```bash
cd terraform-policies/

# Create directory structure
mkdir -p aws/compute
mkdir -p aws/storage
mkdir -p aws/database
mkdir -p aws/security
mkdir -p tagging
mkdir -p examples
mkdir -p .github/workflows
```

#### Copy Example Rules from Berm Fork

From your `c-c-t/berm` repository, copy the example rules:

```bash
# Navigate to berm repo
cd /path/to/berm

# Copy rules to terraform-policies repo
cp .berm/s3-*.json ../terraform-policies/aws/storage/
cp .berm/rds-*.json ../terraform-policies/aws/database/
cp .berm/lambda-*.json ../terraform-policies/aws/compute/
cp .berm/publicly-accessible-warning.json ../terraform-policies/aws/security/
cp .berm/multi-resource-tags-*.json ../terraform-policies/tagging/
```

#### Rules Inventory (14 rules included)

**AWS Storage (4 rules)**
- `s3-versioning-enabled.json` - Error: S3 versioning required
- `s3-encryption-enabled.json` - Error: S3 encryption required
- `s3-block-public-access.json` - Error: S3 public access must be blocked
- `s3-use-module-only.json` - Error: Enforce module usage instead of direct resources

**AWS Database (5 rules)**
- `rds-encryption-enabled.json` - Error: RDS encryption required
- `rds-backup-retention.json` - Warning: 7+ day retention recommended
- `rds-engine-version.json` - Version compliance checks
- `rds-postgres-version-error.json` - Error: PostgreSQL version too old
- `rds-postgres-version-warning.json` - Warning: PostgreSQL version approaching EOL

**AWS Compute (2 rules)**
- `lambda-python-38-error.json` - Error: Python 3.8 is EOL
- `lambda-python-39-warning.json` - Warning: Python 3.9 approaching EOL

**AWS Security (1 rule)**
- `publicly-accessible-warning.json` - Warning: Resources should not be publicly accessible

**Tagging (2 rules)**
- `multi-resource-tags-required.json` - Error: Required tags (Environment, Owner, CostCenter)
- `multi-resource-tags-not-empty.json` - Error: Tags must not be empty

---

## Phase 2: Centralized Workflow Setup

### 2.1 Create/Update Centralized Workflow Repository

**Repository:** `c-c-t/centralized-workflows` (or your workflows repo)

**File:** `.github/workflows/terraform-compliance.yml`

Use the completed `example-workflow.yml` from the berm repository as your template. This workflow is already configured with:

✅ Berm integration
✅ Repository variable support for S3 buckets
✅ Repository variable support for AWS Account IDs
✅ Environment detection (dev/test/prod)
✅ GitHub format output with artifacts

### 2.2 Copy Workflow File

```bash
# From berm repo
cp example-workflow.yml /path/to/centralized-workflows/.github/workflows/terraform-compliance.yml
```

**Key Configuration Points:**

The workflow already defaults to:
- `berm_repo: c-c-t/berm`
- `berm_policies_repo: c-c-t/terraform-policies`
- `berm_output_format: github`
- `berm_strict_mode: false` (warnings advisory only)

---

## Phase 3: Configure Calling Repositories

For each repository that deploys Terraform infrastructure:

### 3.1 Set Required Repository Variables

**Navigate to:** Repository → Settings → Secrets and variables → Actions → Variables

**Create these variables:**

| Variable Name | Example Value | Description |
|---------------|---------------|-------------|
| `TF_STATE_BUCKET_DEV` | `myapp-terraform-state-dev` | S3 bucket for dev state |
| `TF_STATE_BUCKET_TEST` | `myapp-terraform-state-test` | S3 bucket for test state |
| `TF_STATE_BUCKET_PROD` | `myapp-terraform-state-prod` | S3 bucket for prod state |
| `AWS_ACCOUNT_ID_DEV` | `123456789012` | AWS account ID for dev |
| `AWS_ACCOUNT_ID_TEST` | `234567890123` | AWS account ID for test |
| `AWS_ACCOUNT_ID_PROD` | `345678901234` | AWS account ID for prod |

**Note:** All 6 variables are **required**. The workflow will fail with a clear error if any are missing.

### 3.2 Create Workflow File in Calling Repository

**File:** `.github/workflows/terraform.yml`

```yaml
name: Terraform Plan & Compliance

on:
  pull_request:
    branches:
      - main
      - develop
      - test
    paths:
      - '**/*.tf'
      - '**/*.tfvars'

permissions:
  id-token: write
  contents: read
  pull-requests: write

jobs:
  terraform-compliance:
    name: Terraform Compliance Check
    uses: c-c-t/centralized-workflows/.github/workflows/terraform-compliance.yml@main
    secrets:
      TERRAFORM_POLICIES_SECRET: ${{ secrets.TERRAFORM_POLICIES_SECRET }}
```

That's it! The workflow automatically:
- Reads repository variables for S3 buckets and AWS accounts
- Detects environment from target branch (main→prod, test→test, develop→dev)
- Runs Terraform plan
- Validates with berm policies
- Posts violations as PR annotations

---

## Phase 4: Testing Strategy

### 4.1 Local Testing (Before Workflow Integration)

**Prerequisites:**
```bash
pip install git+https://github.com/c-c-t/berm.git@main
```

**Test in a Terraform repository:**

```bash
# Generate plan
terraform init
terraform plan -out=tfplan.binary
terraform show -json tfplan.binary > tfplan.json

# Clone policies
git clone https://github.com/c-c-t/terraform-policies.git .berm-policies

# Run berm locally
berm check tfplan.json --rules-dir .berm-policies --format terminal
```

**Expected Output:**
- Green checkmarks for compliant resources
- Red errors for violations (will block PR)
- Yellow warnings for advisory issues (won't block PR)

### 4.2 Workflow Testing (After Integration)

**Test Repository Selection:**
Choose a non-production repository with:
- Active Terraform code
- Some intentional policy violations (for testing)

**Test Cases:**

1. **Missing Variables Test**
   - Don't set repository variables
   - Create a PR
   - Verify: Workflow fails with clear error about missing `TF_STATE_BUCKET_DEV` or `AWS_ACCOUNT_ID_DEV`

2. **Policy Violation Test - Errors**
   - Set all required variables
   - Create Terraform with violations (e.g., S3 without versioning)
   - Create a PR
   - Verify: PR shows error annotations, workflow fails

3. **Policy Violation Test - Warnings**
   - Create Terraform with warnings (e.g., publicly accessible RDS)
   - Create a PR
   - Verify: PR shows warning annotations, workflow succeeds

4. **Compliant Code Test**
   - Create compliant Terraform
   - Create a PR
   - Verify: Workflow succeeds, no annotations

5. **Branch-Specific Test**
   - Create PR into `main` branch
   - Verify: Uses `PROD` variables
   - Create PR into `develop` branch
   - Verify: Uses `DEV` variables

---

## Phase 5: Rollout Plan

### 5.1 Pilot Phase (Week 1-2)

**Repositories:** 1-2 non-critical repos

**Actions:**
1. Set repository variables
2. Add workflow file
3. Create test PRs
4. Monitor for false positives
5. Adjust policies if needed

**Success Criteria:**
- Workflow runs successfully
- Violations are caught
- No false positives
- Team understands error messages

### 5.2 Staged Rollout (Week 3-4)

**Repositories:** 5-10 active dev repos

**Actions:**
1. Set repository variables in batches
2. Add workflow files
3. Communicate changes to teams
4. Provide support for first few PRs

**Communication Template:**

> **New: Terraform Policy Validation with Berm**
>
> We've added automated Terraform policy validation to this repository.
>
> **What this means:**
> - All PRs will be checked against our infrastructure policies
> - **Errors** (red) will block PR merges - must be fixed
> - **Warnings** (yellow) are advisory - won't block merges
>
> **Common Issues:**
> - S3 buckets must have versioning enabled
> - S3 buckets must be encrypted
> - Resources must have required tags: Environment, Owner, CostCenter
> - Lambda functions must use Python 3.10+
>
> **Need help?** Contact #platform-engineering

### 5.3 Full Rollout (Week 5+)

**Repositories:** All Terraform repos

**Actions:**
1. Enable on remaining repositories
2. Establish policy update process
3. Document exemption process (if needed)

---

## Phase 6: Policy Management

### 6.1 Adding New Policies

**Process:**
1. Create rule JSON file in `terraform-policies` repo
2. Test locally with sample plan
3. Validate rule syntax: `berm validate-rules --rules-dir .`
4. Submit PR to `terraform-policies` repo
5. Merge to `main`
6. All repos automatically use new policy on next PR

**Example - Add EC2 IMDSv2 Requirement:**

**File:** `terraform-policies/aws/compute/ec2-imdsv2-required.json`

```json
{
  "id": "ec2-imdsv2-required",
  "name": "EC2 instances must use IMDSv2",
  "resource_type": "aws_instance",
  "severity": "error",
  "property": "metadata_options.0.http_tokens",
  "equals": "required",
  "message": "EC2 instance {{resource_name}} must enforce IMDSv2 (set metadata_options.http_tokens = 'required')"
}
```

### 6.2 Updating Existing Policies

**Severity Changes:**
- **Warning → Error**: Review with teams first, may break existing PRs
- **Error → Warning**: Safe to deploy immediately

**Policy Updates:**
1. Edit rule file in `terraform-policies`
2. Test locally
3. Submit PR with explanation
4. Merge to `main`

### 6.3 Policy Exemptions (If Needed)

**Approach 1: Environment-Specific Rules**
Create separate rules for dev/test/prod environments using separate directories.

**Approach 2: Per-Repo Overrides**
Allow repos to reference their own rules:
```yaml
jobs:
  terraform-compliance:
    uses: c-c-t/centralized-workflows/.github/workflows/terraform-compliance.yml@main
    with:
      berm_policies_repo: "c-c-t/myapp-custom-policies"  # Override
```

---

## Phase 7: Monitoring & Maintenance

### 7.1 Metrics to Track

**Via GitHub Insights:**
- Workflow success/failure rate
- Average time to fix violations
- Most common violations
- Repositories without compliance workflow

**Via Artifacts:**
Download `berm-reports-*` artifacts from workflow runs for analysis.

### 7.2 Common Issues & Solutions

**Issue:** "Missing required repository variable: TF_STATE_BUCKET_DEV"
**Solution:** Set the variable in repo settings

**Issue:** Workflow fails on `terraform init`
**Solution:** Check AWS credentials, verify S3 bucket exists

**Issue:** False positive - compliant code flagged
**Solution:** Review rule logic, may need to adjust property path

**Issue:** Too many warnings cluttering PR
**Solution:** Promote important warnings to errors, remove noise warnings

### 7.3 Berm Version Updates

**Process:**
1. Monitor `c-c-t/berm` for upstream updates
2. Test new version locally
3. Update `berm_version` input (or keep as `main` for auto-updates)
4. Announce to teams if breaking changes

---

## Phase 8: Documentation

### 8.1 Create Runbook

**Location:** `terraform-policies/README.md`

**Contents:**
- How to interpret berm errors
- Common violations and fixes
- How to add new policies
- How to request exemptions
- Contact information

### 8.2 Team Training

**Topics:**
- What is berm and why we're using it
- How to read PR annotations
- How to fix common violations
- How to test locally before pushing

---

## Quick Reference

### Required Repository Variables (Per Calling Repo)

```
TF_STATE_BUCKET_DEV
TF_STATE_BUCKET_TEST
TF_STATE_BUCKET_PROD
AWS_ACCOUNT_ID_DEV
AWS_ACCOUNT_ID_TEST
AWS_ACCOUNT_ID_PROD
```

### Environment Mapping

| PR Target Branch | Environment | Uses Variables |
|-----------------|-------------|----------------|
| `main`/`master` | `prod` | `*_PROD` |
| `test` | `test` | `*_TEST` |
| `develop`/`dev` | `dev` | `*_DEV` |

### Severity Levels

| Severity | Blocks PR? | Use For |
|----------|-----------|---------|
| `error` | ✅ Yes | Critical security/compliance requirements |
| `warning` | ❌ No | Best practices, recommendations |

### Local Testing Commands

```bash
# Install berm
pip install git+https://github.com/c-c-t/berm.git@main

# Generate plan
terraform plan -out=tfplan.binary
terraform show -json tfplan.binary > tfplan.json

# Run checks
berm check tfplan.json --rules-dir /path/to/terraform-policies --format terminal
```

---

## Success Criteria

### Week 2
- [ ] Pilot repos have workflow enabled
- [ ] First violations caught and fixed
- [ ] No blocking issues

### Week 4
- [ ] 50% of Terraform repos have workflow
- [ ] Team adoption is positive
- [ ] Policy violations trending down

### Week 8
- [ ] 100% of Terraform repos have workflow
- [ ] < 5% false positive rate
- [ ] Policy update process established
- [ ] Documentation complete

---

## Support & Resources

### Repositories
- **Berm:** https://github.com/c-c-t/berm
- **Policies:** https://github.com/c-c-t/terraform-policies
- **Workflows:** https://github.com/c-c-t/centralized-workflows

### Contacts
- Platform Engineering: #platform-engineering
- Policy Questions: [Team lead]
- Workflow Issues: [DevOps team]

### Documentation
- Berm README: `c-c-t/berm/README.md`
- Policy Catalog: `c-c-t/terraform-policies/README.md`
- Workflow Guide: `c-c-t/centralized-workflows/README.md`
