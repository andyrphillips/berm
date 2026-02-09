# Berm Codebase Walkthrough

## Overview
Berm is a policy-as-code engine for Terraform that validates infrastructure against security and compliance rules. Think "spell check" for AI-generated Terraform code.

## Architecture Philosophy

**Pipeline Pattern**: Rule → Evaluator → Violation → Reporter

```
[Rule Files] → [Load Rules] → [Load Terraform Plan] → [Evaluate] → [Report Violations]
     ↓              ↓                    ↓                  ↓              ↓
   .json        Pydantic           Resource Data      Comparison      Terminal/
   files        validation         extraction         logic          GitHub/JSON
```

## Project Structure

```
berm/
├── __init__.py              # Package metadata, version
├── __main__.py              # Entry point (python -m berm)
├── cli.py                   # Click-based CLI (6 commands)
├── security.py              # Input validation & sanitization (414 lines)
├── models/
│   ├── rule.py              # Rule schema (Pydantic model)
│   └── violation.py         # Violation dataclass
├── loaders/
│   ├── rules.py             # Load & validate rule files
│   └── terraform.py         # Parse Terraform plan JSON
├── evaluators/
│   └── simple.py            # Property-based rule evaluation
└── reporters/
    ├── __init__.py          # Reporter factory
    ├── terminal.py          # Rich-formatted output
    ├── github.py            # GitHub Actions annotations
    └── json_reporter.py     # Structured JSON output
```

## Core Components

### 1. CLI Layer (`cli.py`) - 258 lines

**Commands:**
- `berm check` - Main command, checks plan against rules
- `berm test` - Explicit test mode (requires --rules and --plan)
- `berm convert` - Convert binary .tfplan to JSON
- `berm init` - Create example rules directory
- `berm validate-rules` - Pre-check rule syntax
- `berm explain` - Show rule documentation

**Key Function:**
```python
def run_check(plan_file, rules_dir, format, strict, verbose) -> int:
    # 1. Validate & load inputs (with security checks)
    # 2. Evaluate rules against resources
    # 3. Report violations
    # 4. Return exit code (0=pass, 1=fail, 2=error)
```

**Security Integration:**
- All user inputs validated via `security.py`
- Errors sanitized before display
- Temporary files cleaned up on exit

---

### 2. Security Module (`security.py`) - 414 lines

**Purpose:** Defense-in-depth protection against attacks

**Constants:**
```python
MAX_FILE_SIZE = 50MB
MAX_PATH_LENGTH = 4096
MAX_PROPERTY_DEPTH = 20
MAX_ARRAY_INDEX = 100
MAX_JSON_DEPTH = 50
DANGEROUS_FILENAME_CHARS = set(';|&$`<>(){}[]"\'\\\n\r\t\x00')
```

**Functions:**

| Function | Purpose | Test Coverage |
|----------|---------|---------------|
| `validate_safe_path()` | Prevent path traversal | ✅ 7 tests |
| `validate_safe_directory()` | Validate directories | ✅ 3 tests |
| `validate_file_size()` | Limit file sizes | ✅ 3 tests |
| `validate_property_path()` | Validate dot-notation paths | ✅ 6 tests |
| `validate_json_depth()` | Prevent deeply-nested JSON DoS | ✅ 11 tests |
| `sanitize_for_output()` | Remove ANSI codes, prevent injection | ✅ 9 tests |
| `sanitize_terraform_plan_path()` | High-level plan validation | ✅ 3 tests |
| `sanitize_rules_directory()` | High-level rules dir validation | ✅ 2 tests |
| `sanitize_output_path()` | High-level output validation | ✅ 3 tests |

**Attack Vectors Protected:**
- ✅ Path traversal (../../etc/passwd)
- ✅ Symlink attacks
- ✅ Null byte injection
- ✅ Command injection (via filename chars)
- ✅ ANSI escape code injection
- ✅ GitHub Actions workflow injection (::error::)
- ✅ DoS via large files (50MB limit)
- ✅ DoS via deeply nested JSON (50 levels)

---

### 3. Models Layer

#### `models/rule.py` - 56 lines

**Purpose:** Rule schema definition and validation

**Rule Structure:**
```python
class Rule(BaseModel):
    id: str                    # Unique identifier
    name: str                  # Human-readable name
    resource_type: str         # e.g., "aws_s3_bucket"
    severity: Literal["error", "warning"]
    property: Optional[str]    # Dot-notation path
    message: str               # Template with {{resource_name}}

    # Comparison operators (exactly one required):
    equals: Optional[Any]
    greater_than: Optional[float]
    greater_than_or_equal: Optional[float]
    less_than: Optional[float]
    less_than_or_equal: Optional[float]
    contains: Optional[str | List]
    in_: Optional[List]        # Field name: "in"
    regex_match: Optional[str]

    # Special mode:
    resource_forbidden: bool = False  # Ban resource entirely
```

**Validation:**
- Exactly one comparison operator required (unless resource_forbidden)
- Property required (unless resource_forbidden)
- Numeric operators require float/int values
- Regex patterns validated on load

**Key Method:**
```python
def format_message(resource_name: str, output_context: str = "terminal") -> str:
    # Replaces {{resource_name}} with actual name
    # Sanitizes output based on context (terminal/github/json)
```

#### `models/violation.py` - 25 lines

**Purpose:** Violation result container

```python
@dataclass
class Violation:
    rule_id: str
    rule_name: str
    resource_name: str
    resource_type: str
    severity: str              # "error" or "warning"
    message: str
    location: Optional[str] = None
```

**Methods:**
- `is_error()` - Check if severity is error
- `is_warning()` - Check if severity is warning
- `format_compact()` - Single-line format
- `format_detailed()` - Multi-line format

---

### 4. Loaders Layer

#### `loaders/rules.py` - 59 lines

**Purpose:** Load and validate rule files

**Key Functions:**

```python
def load_rules(rules_dir: str) -> List[Rule]:
    # 1. Validate directory path (security check)
    # 2. Find all *.json files recursively
    # 3. Parse and validate each rule
    # 4. Return sorted by rule ID
```

```python
def load_single_rule(rule_file: str) -> Rule:
    # 1. Validate file path (security check)
    # 2. Check file size (50MB limit)
    # 3. Parse JSON
    # 4. Validate JSON depth (50 levels max)
    # 5. Create Pydantic Rule object
```

**Security:** Uses `validate_safe_directory()` and `validate_json_depth()`

#### `loaders/terraform.py` - 77 lines

**Purpose:** Parse Terraform plan JSON files

**Key Functions:**

```python
def load_terraform_plan(plan_file: str) -> List[Dict]:
    # 1. Validate file path (security check)
    # 2. Check file size
    # 3. Parse JSON
    # 4. Validate JSON depth (prevents DoS)
    # 5. Extract resource_changes array
    # 6. Filter out deleted/no-op resources
    # 7. Return list of resources with "after" state
```

```python
def get_nested_property(obj: Dict, path: str) -> Any:
    # Traverse nested properties using dot notation
    # Examples:
    #   "versioning.enabled" → obj["versioning"]["enabled"]
    #   "rules.0.status" → obj["rules"][0]["status"]
```

**Resource Filtering:**
- Only includes resources with `"create"` or `"update"` actions
- Excludes `"delete"` and `"no-op"` actions
- Extracts `change.after` state (planned state)

---

### 5. Evaluators Layer

#### `evaluators/simple.py` - 135 lines

**Purpose:** Property-based rule evaluation engine

**Class Structure:**

```python
class SimpleEvaluator:
    def __init__(self, rules: List[Rule]):
        self.rules = rules

    def evaluate_all(self, resources: List[Dict]) -> List[Violation]:
        # Evaluate all rules against all resources
        # Returns list of violations
```

**Evaluation Logic:**

```python
def evaluate(self, rule: Rule, resources: List[Dict]) -> List[Violation]:
    # 1. Filter resources by resource_type
    # 2. For each matching resource:
    #    a. Check if resource_forbidden (instant violation)
    #    b. Extract property value
    #    c. Apply comparison operator
    #    d. Create Violation if check fails
```

**Comparison Operators:**

| Operator | Logic |
|----------|-------|
| `equals` | Exact match (with type coercion) |
| `greater_than` | Numeric > comparison |
| `greater_than_or_equal` | Numeric >= comparison |
| `less_than` | Numeric < comparison |
| `less_than_or_equal` | Numeric <= comparison |
| `contains` | String/list containment |
| `in_` | Value in whitelist |
| `regex_match` | Regex pattern matching |

**Type Coercion:**
```python
# "true" (string) → True (bool)
# "123" (string) → 123 (int)
# Handles Terraform's JSON representation quirks
```

**Property Extraction:**
- Uses `get_nested_property()` from terraform.py
- Handles missing properties gracefully
- Supports array indexing: `rules.0.status`

---

### 6. Reporters Layer

**Purpose:** Format violations for different output contexts

#### `reporters/__init__.py` - 9 lines

**Factory Pattern:**
```python
def get_reporter(format: str) -> Reporter:
    if format == "terminal":
        return TerminalReporter()
    elif format == "github":
        return GithubReporter()
    elif format == "json":
        return JsonReporter()
```

#### `reporters/terminal.py` - 56 lines

**Purpose:** Rich-formatted terminal output

**Features:**
- Color-coded severity (red=error, yellow=warning)
- Table layout for violations
- Summary section
- Uses `rich` library for formatting

**Output Example:**
```
Errors (1):
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Resource        ┃ Rule            ┃ Message     ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ aws_s3_bucket.x │ S3 versioning   │ Must enable │
└─────────────────┴─────────────────┴─────────────┘

Summary: 1 error(s), 0 warnings
```

**Security:** Sanitizes all output via `sanitize_for_output()`

#### `reporters/github.py` - 28 lines

**Purpose:** GitHub Actions workflow annotations

**Output Format:**
```
::error file=terraform/main.tf,line=10,title=S3 versioning enabled::Message text
```

**Features:**
- Creates inline PR comments
- Severity mapped to `::error` or `::warning`
- File/line number extraction (when available)

**Security:**
- Sanitizes output to prevent `::` command injection
- Uses zero-width space to break `::` sequences

#### `reporters/json_reporter.py` - 13 lines

**Purpose:** Machine-readable structured output

**Output Structure:**
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
      "message": "Message text",
      "location": null
    }
  ]
}
```

**Security:** Sanitizes all fields via `sanitize_for_output()`

---

## Data Flow Example

**Scenario:** Check S3 bucket versioning

**1. User Command:**
```bash
berm check plan.json
```

**2. CLI (`cli.py`):**
```python
run_check("plan.json", ".berm", "terminal", False, False)
  → sanitize_terraform_plan_path("plan.json")  # Security check
  → load_rules(".berm")
  → load_terraform_plan("plan.json")
```

**3. Loaders:**
```python
# rules.py
load_rules(".berm")
  → Find: .berm/s3-versioning-enabled.json
  → Parse: {"id": "s3-versioning-enabled", ...}
  → Validate: Pydantic Rule model
  → Return: [Rule(id="s3-versioning-enabled", ...)]

# terraform.py
load_terraform_plan("plan.json")
  → Parse JSON
  → Extract: resource_changes[*]
  → Filter: actions=["create"]
  → Return: [{"type": "aws_s3_bucket_versioning", ...}]
```

**4. Evaluator (`evaluators/simple.py`):**
```python
evaluator = SimpleEvaluator(rules)
violations = evaluator.evaluate_all(resources)
  → For each rule:
      → Filter resources by type
      → Extract property: versioning_configuration.0.status
      → Compare: actual != "Enabled"
      → Create violation if failed
```

**5. Reporter (`reporters/terminal.py`):**
```python
reporter = get_reporter("terminal")
reporter.report(violations)
  → Format violations in Rich table
  → Color-code by severity
  → Print summary
```

**6. Exit Code:**
```python
exit(1 if violations else 0)
```

---

## Testing Strategy

**Test Structure:**
- **Unit tests:** Individual components (models, loaders, evaluators)
- **Integration tests:** End-to-end CLI tests
- **Security tests:** Attack scenarios and edge cases

**Test Coverage (117 tests):**
- `models/` - 64% (rule edge cases, message formatting)
- `loaders/` - 81-82% (file loading, error handling)
- `evaluators/` - 66% (all operators, type coercion)
- `security.py` - 90% (path traversal, injection attacks)
- `reporters/` - 25-100% (output formatting)
- `cli.py` - 41% (command execution, error handling)

**Security Tests (50 total):**
- Path validation (7 tests)
- Directory validation (3 tests)
- File size limits (3 tests)
- Property paths (6 tests)
- Output sanitization (9 tests)
- JSON depth validation (11 tests)
- Real-world attacks (3 tests)
- Sanitization functions (8 tests)

---

## Key Design Decisions

### 1. **Pydantic for Validation**
- Self-documenting schemas
- Runtime validation
- Type safety
- Easy JSON serialization

### 2. **Dot Notation for Property Paths**
```python
"versioning_configuration.0.status"
#   object field    array  field
```
- Intuitive syntax
- Supports nested objects
- Array indexing built-in

### 3. **Separation of Concerns**
- Loaders: Parse & validate input
- Evaluators: Business logic
- Reporters: Format output
- Security: Cross-cutting concern

### 4. **Multiple Output Formats**
- Terminal: Human-readable
- GitHub: CI/CD integration
- JSON: Machine-readable, scriptable

### 5. **Defense-in-Depth Security**
- Validate at boundaries (file loading)
- Sanitize at outputs (reporters)
- Limit resource usage (file size, JSON depth)
- Prevent injection (ANSI codes, GitHub commands)

---

## Extension Points

### Adding a New Comparison Operator

**1. Add field to Rule model (`models/rule.py`):**
```python
class Rule(BaseModel):
    # ... existing fields ...
    starts_with: Optional[str] = None
```

**2. Update validation:**
```python
@model_validator(mode="after")
def validate_operators(self):
    operators = [self.equals, ..., self.starts_with]
    # Check exactly one is set
```

**3. Add evaluation logic (`evaluators/simple.py`):**
```python
def _check_operator(self, rule: Rule, value: Any) -> bool:
    # ... existing checks ...
    if rule.starts_with is not None:
        return str(value).startswith(rule.starts_with)
```

**4. Add tests:**
```python
def test_evaluator_starts_with():
    # Test the new operator
```

### Adding a New Reporter

**1. Create reporter file (`reporters/sarif.py`):**
```python
class SarifReporter:
    def report(self, violations: List[Violation]) -> None:
        # Format as SARIF JSON
```

**2. Register in factory (`reporters/__init__.py`):**
```python
def get_reporter(format: str):
    if format == "sarif":
        return SarifReporter()
```

**3. Add CLI option (`cli.py`):**
```python
@click.option("--format", type=click.Choice([..., "sarif"]))
```

---

## Common Patterns

### Error Handling
```python
try:
    # Operation
except SpecificError as e:
    safe_error = sanitize_for_output(str(e), context="terminal")
    console.print(f"[red]Error:[/red] {safe_error}")
    sys.exit(2)  # Error exit code
```

### Resource Type Filtering
```python
def get_resources_by_type(resources: List[Dict], resource_type: str) -> List[Dict]:
    return [r for r in resources if r.get("type") == resource_type]
```

### Property Extraction
```python
def get_nested_property(obj: Dict, path: str) -> Any:
    parts = path.split(".")
    current = obj
    for part in parts:
        if part.isdigit():  # Array index
            current = current[int(part)]
        else:  # Object key
            current = current[part]
    return current
```

---

## Development Workflow

**1. Run Tests:**
```bash
pytest tests/ -v
pytest tests/ --cov=berm --cov-report=html
```

**2. Format Code:**
```bash
black berm/ tests/
```

**3. Lint:**
```bash
ruff check berm/ tests/
```

**4. Type Check:**
```bash
mypy berm/
```

**5. Run CLI:**
```bash
python -m berm check plan.json
# or after install:
berm check plan.json
```

---

## Performance Considerations

**Current Performance:**
- < 1 second for local runs
- < 10 seconds in CI/CD

**Optimization Strategies:**
1. **Early filtering:** Filter by resource_type before property extraction
2. **Lazy loading:** Don't load all rules if only checking specific types
3. **Caching:** Cache compiled regex patterns
4. **Parallel evaluation:** Could evaluate rules in parallel (not implemented)

**Limits:**
- Max file size: 50MB
- Max JSON depth: 50 levels
- Max property depth: 20 levels
- These prevent DoS attacks

---

## Security Threat Model

**Threats Protected Against:**

1. **Path Traversal**
   - Attack: `../../etc/passwd`
   - Defense: `validate_safe_path()` with `resolve()` and `relative_to()` checks

2. **Command Injection**
   - Attack: `file.json; rm -rf /`
   - Defense: Dangerous character blocking in filenames

3. **DoS via Large Files**
   - Attack: Upload 1GB JSON file
   - Defense: 50MB file size limit

4. **DoS via Deeply Nested JSON**
   - Attack: JSON with 10,000 nesting levels
   - Defense: 50-level depth limit

5. **Terminal Escape Code Injection**
   - Attack: `\x1b[31m` to manipulate terminal
   - Defense: `sanitize_for_output()` removes ANSI codes

6. **GitHub Actions Command Injection**
   - Attack: `::set-output name=token::secret`
   - Defense: Replace `::` with `:\u200b:` (zero-width space)

**Threats NOT Protected Against:**
- ReDoS (Regular Expression DoS) - regex patterns not validated
- Windows device names (CON, PRN, etc.)
- Time-of-check-time-of-use (TOCTOU) race conditions

---

## Questions for Discussion

1. **Cross-Resource Validation:** Should we support rules like "S3 bucket must have corresponding CloudTrail"?

2. **Rule Inheritance:** Should rules support inheritance/composition?

3. **Exemptions:** Should we support rule exemptions with justification tracking?

4. **Performance:** At what scale should we add caching/parallelization?

5. **Additional Operators:** Do we need `not_equals`, `starts_with`, `ends_with`?

6. **IDE Integration:** Should we build a VS Code extension for real-time validation?

---

## Resources

- **README.md** - User documentation and examples
- **CONTRIBUTING.md** - Development guidelines
- **OVERVIEW.md** - Strategic vision and roadmap
- **SESSION_NOTES.md** - Development session history

---

*Last updated: 2026-02-09*
*Test suite: 117 tests passing, 69% coverage*
*Security: 50 tests, 90% security module coverage*
