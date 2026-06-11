# lint-constraints.md

Hard constraints for `code-test-linter`. Loaded at every node. No exceptions.

---

## Read-Only Invariant

- MUST NOT modify any source file, test file, lint config file (`ruff.toml`, `mypy.ini`, `pyproject.toml`, `.bandit`), or any other project state file.
- MUST write only one artifact per run: the `LintReport` JSON at the configured output path.
- MUST create parent directories for the output path if they do not exist; that is the only filesystem side-effect permitted.

---

## No Suppression

- MUST NOT insert `# noqa`, `# type: ignore`, `# nosec`, `# pylint: disable`, or any other suppression directive into any file.
- MUST NOT silently drop, omit, or hide any finding from the `LintReport`. Every finding a linter emits becomes a `LintIssue`.

---

## No Auto-Fix

- MUST NOT auto-fix any issue, including trivially-fixable ones (whitespace, trailing commas, unused imports).
- MUST surface all fixable findings as `LintIssue` entries — fixing is `code-test-fixer`'s responsibility, not this skill's.

---

## Exit-Code Contract

- MUST exit non-zero ONLY when a linter binary cannot run (missing binary or config error that prevents invocation).
- MUST NOT exit non-zero when lint findings are present. Findings are normal output, not skill failures.

---

## Complete Reporting

- MUST include every finding in the report. Do not deduplicate, collapse, merge, or filter issues.
- MUST emit one `LintIssue` per missing descriptive-test docstring tag. Do not merge multiple missing tags from the same function into one issue.

---

## Linter Exit-Code 2 Handling

- If a linter exits with code 2 (config error): emit a `LintIssue` with `severity: "error"`, `code: "CONFIG_ERROR"`, `message: <stderr content>`.
- MUST continue running remaining linters after a code-2 exit. Do not abort the run.
- Code-2 from one linter is not a skill-level failure; it is a reported finding.

---

## Linter Timeout Handling

- If a linter times out: emit a `LintIssue` with `code: "TIMEOUT"` rather than propagating an exception or crashing.
- MUST continue running remaining linters after a timeout.

---

## Descriptive-Test Docstring Contract

- Required tags: `@tests`, `@scenario`, `@asserts`, `@layer`.
- Optional tag: `@generation_id` (LLM-generated tests only; absence is not a violation).
- Each missing required tag MUST emit its own `LintIssue` with a specific code (e.g., `MISSING_LAYER_TAG`, `MISSING_TESTS_TAG`).
- A test function with no docstring at all MUST emit `code: "MISSING_DOCSTRING"` (not one issue per tag).
- Full tag rules and valid values live in `references/descriptive-test-rules.md`; defer to that file for edge cases.

---

## Schema Source of Truth

- MUST import `LintIssue` and `LintReport` from `src/tools/testing/lint_reporter/schemas.py` (and secret-finding schemas from `src/tools/testing/secret_scanner/schemas.py`).
- MUST NOT redeclare these types locally, even partially. If the import fails, abort with a clear error rather than falling back to a local definition.

---

## Out of Scope

- Pre-commit hook installation and configuration are not this skill's responsibility. MUST NOT install, update, or configure pre-commit hooks under any circumstances.
