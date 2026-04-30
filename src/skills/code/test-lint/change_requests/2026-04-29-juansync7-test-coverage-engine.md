# Decision Memo — test-lint

> Artifact type: skill | Memo type: creation | Design doc: `.brainstorms/2026-04-28-test-strategy-improvements/design.md`

---

## What I want

A fully autonomous, read-only skill that runs the project's full linter suite (ruff, mypy, bandit, vulture, detect-secrets) against a Python repository and emits a structured `LintReport`. The skill never modifies source, never suppresses findings with `# noqa`, and never auto-fixes anything. Its sole job is to scan, aggregate, and hand off a clean machine-readable report to the `fix` skill.

In addition to tool-level lint issues, the skill validates that all test files conform to the descriptive-test docstring contract — flagging missing `@tests`, `@scenario`, `@asserts`, and `@layer` tags as first-class lint errors. This catches malformed tests before they can reach `generate`'s hard gate.

---

## Why Claude needs it

Without this skill, Claude has no standardized entry point for code-quality work. Left to its own devices it will:

- Run linters ad-hoc, inconsistently, or not at all.
- Mix linting with fixing in the same pass, making re-verification impossible.
- Silently ignore mypy or bandit findings that require configuration flags.
- Produce unstructured prose summaries instead of machine-readable output, breaking any downstream handoff to `fix`.
- Never check test docstrings, allowing malformed generated tests to silently fail the hard gate in `generate` with no upstream signal about why.

The skill enforces a clean separation: lint produces a report; fix consumes it. No conflation.

---

## Injection shape

- **Workflow:** Linear four-phase flow: scan repo → run each linter → aggregate JSON → emit `LintReport`. Phase descriptions define exactly what happens at each node, what files are loaded, and how the node exits.
- **Policy:** Judgment rules loaded as always-on constraints — never auto-fix, never suppress with `# noqa` without flagging, never exit early on a single linter failure. Applies to every node.
- **Domain knowledge:** Per-linter reference files loaded at the run-each-linter node — ruff ruleset, mypy strict flags, bandit security ruleset, vulture confidence thresholds, descriptive-test docstring tag requirements.

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| `LintReport` (pydantic, serialized to JSON) | 1 per run | No | Structured issues per tool; consumed by `fix` |
| `descriptive_test_violations` subset (within `LintReport`) | 1 per run | No | Surfaced separately so `generate` can act on docstring gaps independently |

---

## Flow graph

```
[SCAN]
  ↓
[RUN-EACH-LINTER]   ← ruff → mypy → bandit → vulture → detect-secrets → docstring-validator
  ↓
[AGGREGATE]
  ↓
[EMIT-REPORT]       → LintReport (JSON)
                          ↓
                        fix skill
```

---

## Node specifications

**[SCAN]** — Load: `rules/lint-constraints.md` (always-loaded). Do: resolve repo root path; locate lint config files (`ruff.toml`, `mypy.ini`, `pyproject.toml`); build file manifest (Python source files + test files). Don't: read or modify source content. Exit: manifest ready → RUN-EACH-LINTER.

**[RUN-EACH-LINTER]** — Load: `references/ruff-config.md`, `references/mypy-strict.md`, `references/bandit-rules.md`, `references/vulture-thresholds.md`, `references/descriptive-test-rules.md`. Do: invoke `lint_reporter` tool (ruff + mypy + bandit + vulture JSON aggregator); invoke `secret_scanner` tool; invoke docstring validator against test files (check for `@tests`, `@scenario`, `@asserts`, `@layer` tags per descriptive-test contract). Don't: apply any fix; suppress any finding; invoke tools in parallel if ordering matters for config inheritance. Exit: all linters have run to completion (exit-code 0 or 1 — see Edge Cases); raw JSON collected per tool → AGGREGATE.

**[AGGREGATE]** — Load: `templates/lint-report.md`. Do: merge per-tool raw JSON into `LintIssue` objects; normalize `severity` field; populate `files_scanned` and `duration_ms`; partition `descriptive_test_violations` as a separate named list within `LintReport`. Don't: filter or deduplicate issues silently — all findings must appear in the output. Exit: `LintReport` constructed → EMIT-REPORT.

**[EMIT-REPORT]** — Do: serialize `LintReport` to JSON; write to a well-known output path (creator decides convention — e.g., `project/coverage/state/LINT_REPORT.json`); print a human-readable summary (issue count per tool, total files scanned, descriptive-test violation count). Don't: exit non-zero if issues are found — the presence of lint issues is not a skill failure; exit non-zero only if a linter itself could not run (config error). Exit: report written → skill complete; hand-off signal to `fix`.

---

## Entry gates

| Transition | Gate |
|---|---|
| Start → SCAN | None — fully autonomous; no precondition check required |

---

## Edge cases considered

| Edge case | Handling |
|---|---|
| Linter exits with code 2 (configuration error, not lint failure) | Creator decides exact behavior — recommended: abort the run for that linter, emit a `LintIssue` of severity `error` with `code: "CONFIG_ERROR"` and `message` containing the stderr output, continue remaining linters. Do not treat as a lint finding. |
| Missing lint config file (`ruff.toml`, `mypy.ini`, etc.) | Surface as a `LintIssue` with `code: "MISSING_CONFIG"` before invoking the linter; still attempt to run with defaults so the report is not empty. Creator decides whether to abort or continue. |
| Very large repos (10k+ Python files) | `lint_reporter` should be invoked with standard parallelism flags (ruff supports `--jobs`; mypy supports daemon mode). Creator specifies timeout policy — recommended: per-linter timeout with a `TIMEOUT` sentinel issue in the report rather than a hard crash. |
| Test file has no docstring at all | Treated as a `descriptive_test_violation` with `code: "MISSING_DOCSTRING"` — equivalent to all four tags missing. Not a separate code path; same `LintIssue` struct. |
| Test function has partial tags (e.g., has `@tests` but missing `@layer`) | Each missing tag emits its own `LintIssue` with a specific `code` (e.g., `MISSING_LAYER_TAG`). The validator does not collapse multiple missing tags into one issue. |
| `detect-secrets` finds a baseline file (`.secrets.baseline`) already committed | Respect baseline: only report new secrets not already in the baseline. Surface baseline path in the report metadata so `fix` can use it. |

---

## Companion files anticipated

<!-- VERBATIM -->
**Companion files:**
- `rules/lint-constraints.md` (always-loaded): never auto-fix; report only; never suppress with `# noqa` without flagging; descriptive-test docstring rules.
- `references/ruff-config.md`: standard ruff ruleset for Python projects.
- `references/mypy-strict.md`: mypy strict-mode flags.
- `references/bandit-rules.md`: security ruleset.
- `references/vulture-thresholds.md`: dead-code confidence thresholds.
- `references/descriptive-test-rules.md`: docstring tag requirements.
- `templates/lint-report.md`: LintReport schema.

---

## Output schema

<!-- VERBATIM -->
**Output schema (`LintReport`):**
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

Canonical schema lives in `ai-synapse/tools/testing/schemas.py`. Both `lint` and `fix` import from there — do not redeclare locally.

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `ai-synapse/tools/testing/lint_reporter` | consumes | Runs ruff + mypy + bandit + vulture; returns per-tool JSON |
| `ai-synapse/tools/testing/secret_scanner` | consumes | Returns `SecretScanResult[]`; normalized into `LintIssue` list by the skill |
| `ai-synapse/tools/testing/schemas.py` | consumes | Canonical pydantic types for `LintIssue`, `LintReport` |
| `test-fix` | produces for | `LintReport` is the only required input to `fix`; shared contract via `schemas.py` |

---

## Descriptive-test contract (cross-cutting reference)

This is a system-wide contract validated by `lint` and enforced as a hard gate in `generate`. The canonical form is:

```python
def test_chunker_handles_unicode_grapheme_clusters():
    """
    @tests: chunker.split_text
    @scenario: input contains emoji and combining characters
    @asserts: chunk boundaries don't split graphemes
    @layer: unit
    @generation_id: 2026-04-28-abc123
    """
```

Required tags: `@tests`, `@scenario`, `@asserts`, `@layer`. The `@generation_id` tag is required only for LLM-generated tests (used to trace lineage). Tests with malformed or missing tags are rejected before review reaches a human. The `lint` skill surfaces these as `descriptive_test_violations` so they can be actioned by `fix` or fed back to `generate` without waiting for the hard gate.

Full tag rules live in `references/descriptive-test-rules.md`.

---

## Open questions

These items were marked "Resolved (not fleshed)" in the brainstorm — the creator must make the concrete decision:

1. **Linter exit-code 2 behavior** — The brainstorm resolved that exit-code 2 (configuration error) is distinct from exit-code 1 (lint findings), but did not specify whether to abort the entire run or continue remaining linters. Recommend: continue remaining linters and emit a `CONFIG_ERROR` issue, but the creator should codify this in `rules/lint-constraints.md`.

2. **Pre-commit hook integration** — The brainstorm explicitly deferred the decision of whether the `lint` skill should bundle pre-commit hook setup or leave that to project-level configuration. If bundled, the skill needs a node for hook installation; if not, document that pre-commit is out of scope and must be configured separately. This affects the companion file list (a `references/pre-commit-setup.md` may be needed).
