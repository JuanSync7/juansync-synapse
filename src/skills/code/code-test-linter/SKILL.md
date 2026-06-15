---
name: code-test-linter
aliases: [test-lint]
description: "Use when asked to lint a Python repo, run static analysis, check test docstrings, scan for secrets, or produce a LintReport. Not for fixing lint findings (use code-test-fixer) or auditing coverage gaps (use code-test-auditor)."
domain: code
scope: test
role: linter
tags: [lint, static-analysis, ruff, mypy, bandit, descriptive-tests]
user-invocable: true
argument-hint: "[--repo-root PATH] [--output PATH]"
---

Read-only first stage of the 6-skill test coverage engine. Runs the project's full linter suite and the descriptive-test docstring validator, aggregating findings into `LintReport` — the contract consumed by `code-test-fixer`. Never modifies source, never suppresses with `# noqa`, never auto-fixes.

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

## MUST (every turn)
- Load `rules/lint-constraints.md` — read-only invariants apply at every node
- Record position: `Position: [node-id] — <context>`
- Run all 4 nodes in declared order; partial linter failures emit issues, do not abort the flow

## MUST NOT (global)
- Modify any source file, test file, lint config file, or project state file other than the LintReport target
- Suppress findings with `# noqa`, `# type: ignore`, or filter the issue list silently
- Auto-fix any issue (that is `code-test-fixer`'s responsibility)
- Exit non-zero when lint issues are found — non-zero only on linter-execution failure (config error, missing binary)

## Wrong-Tool Detection
- **User wants lint findings auto-fixed** → `/code-test-fixer` (consumes this skill's output)
- **User wants test coverage gaps audited** → `/code-test-auditor` (requires lint-clean precondition first)
- **User wants tests written** → `/code-test-generator` (downstream of audit)

## Progress Tracking

Create a task at [NEW] to track node progression:

```
TaskCreate: "code-test-linter run — <repo-root>"
  → [NEW] tool inventory verified
  → [SCAN] manifest built
  → [RUN-EACH-LINTER] linter sweep complete
  → [AGGREGATE] LintReport assembled
  → [EMIT-REPORT] report persisted
```

Update to `in_progress` at each node entry; mark `completed` at [END].

## Entry

### [NEW] Fresh session
Do:
  1. Parse arguments: `--repo-root` (default cwd), `--output` (default `project/coverage/state/LINT_REPORT.json`).
  2. Confirm tool inventory: `code-test-report-lint` (`python src/tools/testing/code-test-report-lint/lint_reporter.py`) and `code-test-scan-secrets` (`python src/tools/testing/code-test-scan-secrets/secret_scanner.py`) available — abort with clear error if missing.
  3. Verify `src/tools/testing/code-test-report-lint/schemas.py` defines `LintIssue` and `LintReport` — abort if missing (no local redeclaration).
Don't: Proceed without tool inventory verified.
Exit: → [SCAN]

## Flow

### [SCAN] Repo discovery
Load: rules/lint-constraints.md
Do: Resolve repo root; locate lint config files (`ruff.toml`, `mypy.ini`, `pyproject.toml`, `.bandit`, `.secrets.baseline`); build file manifest (Python source + test files). Record missing-config findings as `LintIssue` with `code: "MISSING_CONFIG"` for [AGGREGATE] to merge.
Don't: Skip missing-config recording — without it, downstream consumers can't distinguish "linter not configured" from "linter ran clean".
Exit: → [RUN-EACH-LINTER]

### [RUN-EACH-LINTER] Linter sweep
Load: references/ruff-config.md, references/mypy-strict.md, references/bandit-rules.md, references/vulture-thresholds.md, references/descriptive-test-rules.md
Do: Invoke linters sequentially (ordering matters for config inheritance):
  1. `code-test-report-lint` (ruff → mypy → bandit → vulture aggregator) — collect per-tool JSON.
  2. `code-test-scan-secrets` — respect `.secrets.baseline` if committed; surface baseline path in report metadata; only report new secrets not in baseline.
  3. Descriptive-test docstring validator — over test files only; check each test function for `@tests`, `@scenario`, `@asserts`, `@layer` tags. Emit one `LintIssue` per missing tag (do not collapse). Missing docstring entirely → `code: "MISSING_DOCSTRING"`.
  4. Per-linter exit-code handling: 0 = clean, 1 = findings (normal), 2 = config error → emit `LintIssue` severity `error` with `code: "CONFIG_ERROR"` containing stderr; continue remaining linters.
  5. Per-linter timeout policy: emit `LintIssue` with `code: "TIMEOUT"` rather than crashing.
Don't: Run linters in parallel — sequential ordering matters for config inheritance; parallel dispatch would mask per-tool exit codes. Do not suppress or collapse any issue.
Exit: → [AGGREGATE]

### [AGGREGATE] Merge findings
Load: templates/lint-report.md
Do: Import `LintIssue` and `LintReport` from `src/tools/testing/code-test-report-lint/schemas.py` (secret findings come from `src/tools/testing/code-test-scan-secrets/schemas.py`). Merge per-tool JSON into normalized `LintIssue` objects; populate `severity`, `files_scanned`, `duration_ms`. Partition descriptive-test docstring violations into `descriptive_test_violations` (subset of `issues`, surfaced separately). Include all findings — do not deduplicate or filter.
Don't: Declare `LintIssue` or `LintReport` locally — schema divergence from the canonical file will silently break `code-test-fixer` deserialization.
Exit: → [EMIT-REPORT]

### [EMIT-REPORT] Persist + summarize
Do:
  1. Serialize `LintReport` to JSON at `--output` path (default `project/coverage/state/LINT_REPORT.json`); create parent dirs as needed.
  2. Print human-readable summary: total issues, per-tool counts, files scanned, descriptive-test violation count, baseline path if present.
  3. Suggest: "Run `/code-test-fixer` to action the LintReport."
Exit: → [END]

### [END]
Do: Confirm report path emitted; print the suggestion to run `/code-test-fixer`.
Don't: Auto-route or invoke `/code-test-fixer` directly — handoff is the user's call.
