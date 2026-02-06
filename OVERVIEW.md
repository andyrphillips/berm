# Berm - Policy Engine for CI/CD

## Project Overview
**Berm** is a policy-as-code engine for CI/CD pipelines that guides teams toward infrastructure best practices without blocking their velocity. Like a banked turn in motocross, Berm helps teams maintain speed while staying on the optimal line.

## Problem Statement
Teams using AI assistants (Claude, GPT, Copilot) to generate infrastructure code need guardrails. AI-generated code is often functionally correct but misses security best practices, compliance requirements, and organizational standards. Current solutions (OPA/Conftest) have poor developer experience - complex DSLs like Rego are difficult to write and debug in pipeline environments.

## Value Proposition
**Enable AI-powered infrastructure development safely.** Berm lets platform/DevOps teams set organizational guardrails while empowering developers to move fast with AI code generation. Think "spell check" for AI-generated Terraform - catching missing encryption, overly permissive IAM, and compliance violations before they reach production.

## Product Philosophy
- **Guide, don't block** - Paved roads and happy paths, not bureaucracy
- **Radical simplicity** - Rules that read like English, not logic programming
- **Fast feedback** - Catch issues in seconds locally, not minutes in CI
- **Community-first** - Open source core, shared rule library
- **AI-era ready** - Purpose-built for teams using AI code generation

## Target Audience

### Primary Buyer (Decision Maker)
- **Title**: Head of DevOps, VP Engineering, Staff/Principal Platform Engineer, Cloud Architect
- **Team Size**: 1-5 people at most companies
- **Pain**: Responsible for infrastructure security/compliance across multiple teams
- **Authority**: Can mandate CI/CD tooling, set deployment gates
- **AI Angle**: "How do we enable AI-assisted development safely?"

### Secondary Influencer
- **Title**: CISO, Security Engineer, Compliance Manager
- **Need**: Visibility and control over infrastructure changes
- **Influence**: Can block deployments, drive requirements

### End Users
- Software engineers writing Terraform
- Data engineers managing Airflow
- **Reality**: Using AI to generate code, want fast feedback
- **Need**: Clear error messages, not obscure policy failures

## MVP Scope
Build the simplest possible version that delivers immediate value:

### Core Functionality
- Parse Terraform plan JSON output (`terraform show -json plan.tfplan`)
- Load policy rules from JSON files in a directory (`.berm/` or `.berm-rules/`)
- Evaluate rules against resources in the plan
- Report violations with clear, actionable error messages
- Exit with appropriate codes for CI/CD integration (0 = pass, 1 = fail)
- Local testing mode for fast iteration

### Rule Capabilities (MVP)
- Check if a resource type has a required property (e.g., S3 bucket must have `versioning.enabled`)
- Validate that a property equals an expected value
- Configure severity levels (`error`, `warning`)
- Provide custom failure messages with context

### Example Rule Format
```json
{
  "id": "s3-versioning-enabled",
  "name": "S3 buckets must have versioning enabled",
  "resource_type": "aws_s3_bucket",
  "severity": "error",
  "property": "versioning.enabled",
  "equals": true,
  "message": "S3 bucket {{resource_name}} must have versioning enabled for compliance"
}
```

### CLI Interface
```bash
# Install
pip install berm

# Run against Terraform plan
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan > plan.json
berm check plan.json

# Local test mode (fast iteration)
berm test --rules .berm/ --plan plan.json

# In CI/CD
berm check plan.json --format github  # GitHub Actions annotations
```

## Technical Architecture

### Modular Design (Extensibility First)
```
berm/
├── cli.py              # Entry point, argument parsing
├── loaders/
│   ├── rules.py        # Load and validate JSON rules
│   └── terraform.py    # Parse Terraform plan JSON
├── evaluators/
│   └── simple.py       # MVP: property checks (equals, exists)
├── reporters/
│   ├── terminal.py     # Human-readable output
│   ├── github.py       # GitHub Actions annotations
│   └── sarif.py        # SARIF format (future)
└── models/
    ├── rule.py         # Rule schema/validation
    └── violation.py    # Violation data model
```

### Design Principles
- **Pluggable loaders**: Easy to add HCL parser, Kubernetes YAML, etc.
- **Pluggable evaluators**: Simple property checks now, expressions/cross-resource later
- **Pluggable reporters**: Terminal, CI annotations, SARIF, JSON
- **Clear abstractions**: Rule → Evaluator → Violation → Reporter

### Technology Choices
- **Language**: Python 3.9+ (aligns with user's stack)
- **Dependencies**: Minimal for MVP
  - `pydantic` for rule validation
  - `click` for CLI
  - `rich` for terminal output (optional, nice-to-have)
- **Distribution**: PyPI package, later GitHub Action

## Success Criteria (MVP)
- [ ] Developer can write a new rule in < 2 minutes
- [ ] Rule evaluation completes in < 10 seconds for typical plans (100-500 resources)
- [ ] Error messages clearly identify: which resource, which rule, why it failed, how to fix
- [ ] Works in GitHub Actions with < 5 lines of YAML config
- [ ] Local testing gives instant feedback (< 1 second)
- [ ] Catches 80%+ of common security misconfigurations in AI-generated Terraform

## Non-Goals for MVP
- ❌ Web UI or hosted service
- ❌ Cross-resource validation (e.g., "S3 bucket must have corresponding logging resource")
- ❌ Custom Python expressions in rules
- ❌ HCL static analysis (only plan JSON)
- ❌ Plugin system
- ❌ Rule marketplace
- ❌ Multiple file format support (YAML rules, etc.)
- ❌ Auto-fix suggestions
- ❌ IDE integration

## Extensibility Roadmap

### Near-term (Next 3-6 months)
1. **Cross-resource validation** - "If aws_s3_bucket exists, aws_s3_bucket_logging must reference it"
2. **Simple expressions** - `property: "tags.Environment", matches: "^(prod|staging|dev)$"`
3. **HCL static analysis** - Parse `.tf` files directly
4. **Multiple output formats** - SARIF, JSON, JUnit XML
5. **Rule composition** - Exemptions, allow-lists, rule sets

### Medium-term (6-12 months)
1. **Pattern matching** - Semgrep-style syntax for HCL
2. **Multi-language support** - Python linting, Airflow DAG validation, Kubernetes manifests
3. **Additional CI/CD providers** - GitLab CI, CircleCI, Jenkins
4. **Auto-fix suggestions** - Propose corrections for violations
5. **GitHub Action** - Native action, no pip install needed

### Long-term (12+ months) - Semgrep-Inspired
1. **Visual rule builder** - Web UI for creating rules (like Semgrep Playground)
2. **Rule registry** - Community marketplace with ratings, usage stats
3. **Cloud/SaaS offering** - Hosted policy management, dashboards, compliance reporting
4. **Compliance frameworks** - Pre-built packs (SOC2, PCI, CIS, AWS Well-Architected)
5. **IDE integration** - Real-time checking in VS Code
6. **AI features** - Generate rules from compliance docs, explain violations, suggest fixes

## Monetization Strategy (Future)

### Free Tier (Forever)
- CLI tool (unlimited)
- Community rule library
- Local testing
- GitHub Action (public repos)
- Community support

### Team Tier ($5-10K/year)
- Private repos
- Hosted rule repository
- Web UI for rule management
- Team exemptions
- Slack notifications
- Email support

### Enterprise Tier ($25-50K+/year)
- SSO/SAML
- RBAC (team-specific policies)
- Compliance dashboards
- Audit logs
- Advanced rule packs (SOC2, HIPAA, etc.)
- SLA + dedicated support
- On-premise deployment

### Additional Revenue
- Rule marketplace (20-30% take rate)
- Professional services (custom rules, migration)
- AI features (premium add-on)

## Branding & Positioning

### Name: Berm
**Metaphor**: Like a banked turn in motocross/mountain biking - it lets you go *faster* safely by taking the optimal line.

### Tagline Options
- "Take the fast line through infrastructure"
- "Infrastructure at speed"
- "Lean into best practices"
- "Bank on better infrastructure"

### Visual Identity
- Flowing lines, banked curves
- Colors: Fast but safe (blue + orange? green + gray?)
- Not intimidating - collaborative, enabling

### Marketing Angle
**"Don't let AI write insecure infrastructure"** - The essential safety net for teams using AI-assisted development. Enable velocity without sacrificing security.

## Competitive Positioning

| Tool | Strength | Weakness |
|------|----------|----------|
| **OPA/Conftest** | Powerful, flexible | Rego is hard to write/debug |
| **Checkov** | Comprehensive checks | Limited customization, slow |
| **tfsec** | Fast, good defaults | Not extensible enough |
| **Semgrep** | Great DX, visual builder | Focused on code security, not IaC policy |
| **Berm** | **Simplest rule writing, AI-era positioning** | New, unproven |

## Development Phases

### Phase 1: MVP (Weeks 1-4)
- Core engine: load rules, parse plan JSON, evaluate, report
- 5-10 example rules (S3, IAM, RDS common cases)
- Terminal reporter with clear output
- Basic test suite
- README with quick start

### Phase 2: Polish (Weeks 5-8)
- GitHub Actions integration
- Improved error messages with suggestions
- 20+ rules covering AWS basics
- Documentation site
- Community contribution guidelines

### Phase 3: Community (Weeks 9-12)
- Public launch (Product Hunt, HN, Reddit)
- Collect feedback, iterate on DX
- Build rule library with community
- First enterprise users for feedback

### Phase 4: Scale (Month 4+)
- Cross-resource validation
- Expression support
- HCL parsing
- Begin SaaS development

## Risks & Mitigation

**Risk**: OPA/Conftest are entrenched
- *Mitigation*: Target teams frustrated with Rego, emphasize 10x better DX

**Risk**: "Just another linter" perception
- *Mitigation*: AI angle differentiates, focus on enabling velocity

**Risk**: Small addressable market (1-5 buyers per company)
- *Mitigation*: High ACV ($25K+), focus on enterprise value

**Risk**: Hard to compete with HashiCorp Sentinel (for TFE users)
- *Mitigation*: Target self-hosted Terraform users (majority of market)

## First Steps (Week 1)
1. Set up Python project structure
2. Define rule schema with Pydantic
3. Build Terraform plan JSON loader
4. Implement simple property evaluator
5. Create terminal reporter
6. Write 3 example rules (S3 versioning, encryption, public access)
7. Test against real Terraform plan

---

**Ready to start building.** The path is clear: nail the MVP, make rule-writing delightful, build community, then monetize with enterprise features.