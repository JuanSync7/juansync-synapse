---
name: test-lint
description: "run ruff/mypy/bandit/vulture/detect-secrets plus descriptive-test docstring validator over a Python repo; emit LintReport for downstream test-fix; never auto-fix or suppress"
domain: code.test
intent: analyze
tags: [lint, static-analysis, ruff, mypy, bandit, descriptive-tests]
user-invocable: true
argument-hint: "[--repo-root PATH] [--output PATH]"
---

Read-only first stage of the 6-skill test coverage engine. Runs the project's full linter suite and the descriptive-test docstring validator, aggregating findings into `LintReport` — the contract consumed by `test-fix`. Never modifies source, never suppresses with `# noqa`, never auto-fixes.

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

## MUST (every turn)
- Load `rules/lint-constraints.md` — read-only invariants apply at every node
- Record position: `Position: [node-id] — <context>`
- Run all 4 nodes in declared order; partial linter failures emit issues, do not abort the flow

## MUST NOT (global)
- Modify any source file, test file, lint config file, or project state file other than the LintReport target
- Suppress findings with `# noqa`, `# type: ignore`, or filter the issue list silently
- Auto-fix any issue (that is `test-fix`'s responsibility)
- Exit non-zero when lint issues are found — non-zero only on linter-execution failure (config error, missing binary)

## Wrong-Tool Detection
- **User wants lint findings auto-fixed** → `/test-fix` (consumes this skill's output)
- **User wants test coverage gaps audited** → `/test-audit` (requires lint-clean precondition first)
- **User wants tests written** → `/test-generate` (downstream of audit)

## Entry

### [NEW] Fresh session
Do:
  1. Parse arguments: `--repo-root` (default cwd), `--output` (default `project/coverage/state/LINT_REPORT.json`).
  2. Confirm tool inventory: `lint_reporter` and `secret_scanner` available in `ai-synapse/tools/testing/` — abort with clear error if missing.
  3. Verify `ai-synapse/tools/testing/schemas.py` defines `LintIssue` and `LintReport` — abort if missing (no local redeclaration).
Don't: Proceed without tool inventory verified.
Exit: → [SCAN]

## Flow

### [SCAN] Repo discovery
Load: rules/lint-constraints.md
Do: Resolve repo root; locate lint config files (`ruff.toml`, `mypy.ini`, `pyproject.toml`, `.bandit`, `.secrets.baseline`); build file manifest (Python source + test files). Record missing-config findings as `LintIssue` with `code: "MISSING_CONFIG"` for [AGGREGATE] to merge.
Exit: → [RUN-EACH-LINTER]

### [RUN-EACH-LINTER] Linter sweep
Load: references/ruff-config.md, references/mypy-strict.md, references/bandit-rules.md, references/vulture-thresholds.md, references/descriptive-test-rules.md
Do: Invoke linters sequentially (ordering matters for config inheritance):
  1. `lint_reporter` (ruff → mypy → bandit → vulture aggregator) — collect per-tool JSON.
  2. `secret_scanner` — respect `.secrets.baseline` if committed; surface baseline path in report metadata; only report new secrets not in baseline.
  3. Descriptive-test docstring validator — over test files only; check each test function for `@tests`, `@scenario`, `@asserts`, `@layer` tags. Emit one `LintIssue` per missing tag (do not collapse). Missing docstring entirely → `code: "MISSING_DOCSTRING"`.
  4. Per-linter exit-code handling: 0 = clean, 1 = findings (normal), 2 = config error → emit `LintIssue` severity `error` with `code: "CONFIG_ERROR"` containing stderr; continue remaining linters.
  5. Per-linter timeout policy: emit `LintIssue` with `code: "TIMEOUT"` rather than crashing.
Exit: → [AGGREGATE]

### [AGGREGATE] Merge findings
Load: templates/lint-report.md
Do: Import `LintIssue` and `LintReport` from `ai-synapse/tools/testing/schemas.py`. Merge per-tool JSON into normalized `LintIssue` objects; populate `severity`, `files_scanned`, `duration_ms`. Partition descriptive-test docstring violations into `descriptive_test_violations` (subset of `issues`, surfaced separately). Include all findings — do not deduplicate or filter.
Exit: → [EMIT-REPORT]

### [EMIT-REPORT] Persist + summarize
Do:
  1. Serialize `LintReport` to JSON at `--output` path (default `project/coverage/state/LINT_REPORT.json`); create parent dirs as needed.
  2. Print human-readable summary: total issues, per-tool counts, files scanned, descriptive-test violation count, baseline path if present.
  3. Suggest: "Run `/test-fix` to action the LintReport."
Exit: → [END]

### [END]
Do: Confirm report path emitted; print the suggestion to run `/test-fix`.
Don't: Auto-route or invoke `/test-fix` directly — handoff is the user's call.
