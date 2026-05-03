# LintReport Template

Template for [AGGREGATE] node assembly of `LintReport`. Schema is canonical — do NOT redeclare locally.

---

## Schema Source

```python
from ai_synapse.tools.testing.schemas import LintIssue, LintReport
```

Both are `pydantic.BaseModel`. Verify presence at [NEW] before proceeding.

---

## Schema Reference

<!-- VERBATIM -->
```python
class LintIssue(BaseModel):
    tool: Literal["ruff", "mypy", "bandit", "vulture", "detect-secrets"]
    file: str
    line: int
    code: str
    message: str
    severity: Literal["error", "warning", "info"]

class LintReport(BaseModel):
    issues: list[LintIssue]
    files_scanned: int
    duration_ms: int
    descriptive_test_violations: list[LintIssue]  # subset, surfaced separately
```

> **Schema extension required:** The canonical `Literal` currently lists 5 tools. `descriptive-test` and `lint-skill` are additional valid values used by this skill. Propose updating `ai_synapse/tools/testing/schemas.py` to include them. Until then, instantiate `LintIssue` with those tool values — pydantic validation will fail without the schema patch.

---

## Field Assembly Recipe

| Field | Source | Rule |
|---|---|---|
| `issues` | Union of all per-tool findings | No dedup, no filter — include every finding emitted by every linter |
| `files_scanned` | [SCAN] file manifest | Count of unique Python files in manifest (not files with findings) |
| `duration_ms` | Wall-clock timer | Start at [SCAN] entry; stop at [EMIT-REPORT] entry; convert to int ms |
| `descriptive_test_violations` | Subset of `issues` | Filter: `tool == "descriptive-test"`; same objects, surfaced separately for downstream consumers |

---

## Tool Field Values

Exhaustive list of valid `tool` strings:

| `tool` value | Source | Notes |
|---|---|---|
| `ruff` | `lint_reporter` ruff findings | — |
| `mypy` | `lint_reporter` mypy findings | — |
| `bandit` | `lint_reporter` bandit findings | — |
| `vulture` | `lint_reporter` vulture findings | — |
| `detect-secrets` | `secret_scanner` findings | String is `detect-secrets` (matches underlying scanner); wrapper is named `secret_scanner` |
| `descriptive-test` | Docstring validator findings | Populates `descriptive_test_violations`; requires schema extension |
| `lint-skill` | Skill meta-issues | CONFIG_ERROR, MISSING_CONFIG, TIMEOUT, NOSEC_PRESENT; requires schema extension |

---

## Severity Assignment Recipe

| Tool | Condition | `severity` |
|---|---|---|
| `ruff` | See `references/ruff-config.md` | per ruff-config.md rules |
| `mypy` | error | `"error"` |
| `mypy` | note | `"info"` |
| `mypy` | warning | `"warning"` |
| `bandit` | HIGH confidence | `"error"` |
| `bandit` | MEDIUM confidence | `"warning"` |
| `bandit` | LOW confidence | `"info"` |
| `vulture` | 100% confidence | `"warning"` |
| `vulture` | 80–99% confidence | `"info"` |
| `detect-secrets` | New secret not in baseline | `"error"` |
| `descriptive-test` | Any violation | `"warning"` |
| `lint-skill` | CONFIG_ERROR | `"error"` |
| `lint-skill` | MISSING_CONFIG | `"warning"` |
| `lint-skill` | TIMEOUT | `"error"` |
| `lint-skill` | NOSEC_PRESENT | `"info"` |

---

## JSON Serialization

```python
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(report.model_dump_json(indent=2))
```

Default output path: `project/coverage/state/LINT_REPORT.json`

Overridden by `--output` argument parsed at [NEW].

---

## detect-secrets Baseline Metadata

If a `.secrets.baseline` file is detected during [SCAN], include its **absolute path** in the `message` field of every `detect-secrets` `LintIssue`:

```python
message=f"Secret detected (not in baseline). Baseline: {baseline_path.resolve()}"
```

This allows `test-fix` to locate the baseline file without re-scanning.
