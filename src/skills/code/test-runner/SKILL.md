---
name: test-runner
description: Run pytest test suites safely through a validated execution pipeline with structured output and optional fix loop
domain: code.test
intent: execute
tags: [pytest, test execution, fix loop]
tools: Bash, Read, Grep, Glob, Edit, Agent
allowed-tools: Bash, Read, Grep, Glob, Edit, Agent
---

# Test Runner Skill

Executes pytest test suites through a validated pipeline — discovers tests, runs them safely, captures structured output, and optionally enters a fix loop when failures occur. The goal is reliable, reproducible test execution with clear pass/fail reporting.

## Wrong-Tool Detection

- **User wants to write test code** → redirect to `/write-module-tests`
- **User wants a test planning document** → redirect to `/write-test-docs`
- **User wants to run non-pytest tests** → this skill is pytest-specific; proceed without it

## Purpose

Run pytest tests through the safe execution workflow. Validates test files for dangerous
patterns (subprocess, os.system, network access, file writes, etc.) via AST analysis
before execution. Produces structured JSON output for programmatic consumption. Optionally
runs an automated fix loop for failing tests.

## Input

The user or calling agent provides:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scope` | string | Yes | Group name (e.g., "ingest"), file path, or directory path |
| `scope_type` | string | Yes | `"group"` or `"path"` |
| `marker` | string | No | Pytest marker expression for filtering (`-m` flag) |
| `keyword` | string | No | Pytest keyword expression for filtering (`-k` flag) |
| `strict` | bool | No | Treat WARN violations as BLOCK (default: false) |
| `timeout` | int | No | Per-test timeout override in seconds |

## Execution

### Step 1: Build the shell command

Based on `scope_type`, construct the base command:

- **group**: `scripts/run-tests.sh --group <scope>`
- **path**: `scripts/run-tests.sh --path <scope>`

### Step 2: Append optional flags

Append each optional flag when its corresponding input parameter is provided:

- `marker` provided: append `--marker "<value>"`
- `keyword` provided: append `--keyword "<value>"`
- `strict` is true: append `--strict`
- `timeout` provided: append `--timeout <value>`

### Step 3: Run via Bash tool

Invoke the constructed command using the Bash tool. Capture the exit code.

### Step 4: Read output files

After the command completes, read the result files from `.tmp-test-results/`:

- **Exit code 0** (all tests pass): Read `.tmp-test-results/report.json` for test results.
- **Exit code 1** (test failures OR validation block):
  - First check if `.tmp-test-results/report.json` exists. If yes, tests ran but some failed -- read it.
  - If `report.json` does not exist, tests were blocked by validation -- read `.tmp-test-results/validation.json`.
- **Exit code 2** (error): Read `.tmp-test-results/validation.json` if it exists.
- **Exit code 124** (total run timeout exceeded): Read `.tmp-test-results/run.log` for partial output.
- **Always**: Read `.tmp-test-results/meta.json` for run metadata.

If neither `report.json` nor `validation.json` exists, report status `"error"` with a message
indicating the output files were not found.

### Step 5: Handle validation failures

When the runner exits due to validation failure (no `report.json`, `validation.json` has `status: "blocked"`):

1. Set `status` to `"blocked"`.
2. Parse `validation.json` for violation details.
3. Populate `validation_issues` with `{file, line, category, message}` for each violation.
4. Set `total`, `passed`, `failed`, `errors`, `skipped` to 0.
5. Set `summary` to a human-readable message listing the blocked files and reasons.

## Output Format

Report the following structured result to the caller:

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"pass"` \| `"fail"` \| `"blocked"` \| `"error"` |
| `summary` | string | Human-readable one-liner (e.g., "12 passed, 2 failed, 1 error") |
| `total` | int | Total number of tests collected |
| `passed` | int | Number of tests passed |
| `failed` | int | Number of tests failed |
| `errors` | int | Number of tests with errors |
| `skipped` | int | Number of tests skipped |
| `failures` | list | List of `{test_name, file, line, message, longrepr}` for each failure |
| `validation_issues` | list | List of `{file, line, category, message}` if status is `"blocked"` |
| `duration_seconds` | float | Total test run duration |

## Fix Loop Protocol (FR-500)

When tests fail and the caller requests fixes, execute this loop.

### Iteration Tracking (FR-501)

Initialize:
- `iteration_count = 0`
- `max_iterations = 3`
- `previous_failures = {}` (empty set of `(test_name, message)` tuples)
- `previous_failure_count = 0`
- `files_modified = []`
- `stall_budget = 0` (extra iteration allowance for same-count-different-set case)

### Per-Iteration Steps

1. Read `.tmp-test-results/report.json` failures list.
2. Build `current_failures` as a set of `(test_name, message)` tuples from the failures.
3. For each failure:
   a. Read the test file at `failures[i].file` around line `failures[i].line` using the Read tool.
   b. Infer the source file under test from imports in the test file (use Grep to find the source module).
   c. Determine whether this is a test bug or a source bug based on the `longrepr` traceback.
   d. Fix the appropriate file using the Edit tool:
      - The file MUST be git-tracked. Verify with: `git ls-files --error-unmatch <path>`
      - MUST NOT create new files.
      - MUST NOT delete files.
      - Only edit operations are permitted.
   e. Track the file in `files_modified`.
4. Re-invoke: `scripts/run-tests.sh` with the same scope and flags as the original invocation.
5. Increment `iteration_count`.

### Fixer Context Per Failure (FR-504)

When fixing each failure, gather and use this context:

| Context | Source |
|---------|--------|
| Test file path | `failures[i].file` |
| Test function name | `failures[i].test_name` |
| Full failure output | `failures[i].longrepr` from report.json |
| Inferred source file | Derived from imports in the test file |
| Whether this is a retry | `iteration_count > 0` |
| Previous fix description | What was tried in the last iteration (if retry) |

Fix ONE failure at a time. Do not batch all failures into a single edit.

### Fixer File Scope (FR-505)

- MAY edit test files and source files.
- File MUST be tracked by git (`git ls-files --error-unmatch <path>` must succeed).
- MUST NOT create new files.
- MUST NOT delete files.
- Only edit operations are permitted.

### Termination Checks (after each iteration)

Evaluate in this exact order of precedence:

1. **All tests pass**: `current_failures` is empty. Report success.
   - `termination_reason: all_passed`

2. **FR-502 -- Same-failure detection**: `current_failures == previous_failures` (exact set equality
   on `(test_name, message)` tuples). Stop immediately.
   - `termination_reason: same_failure`
   - Report: "Unable to fix: same failures persist after fix attempt."

3. **FR-503 -- Monotonic progress check** (only evaluated when failure set has changed):
   - If failure set changed AND count **decreased**: continue (progress is being made).
   - If failure set changed AND count is **the same**: allow ONE more iteration (`stall_budget = 1`),
     then stop if count still has not decreased.
     - `termination_reason: stalled`
   - If failure set changed AND count **increased**: stop immediately.
     - `termination_reason: stalled`

4. **Max iterations**: `iteration_count >= max_iterations`. Stop.
   - `termination_reason: max_iterations`

After evaluating termination checks, update `previous_failures = current_failures` and
`previous_failure_count = len(current_failures)` before the next iteration.

### Final Status Report (FR-506)

After the fix loop completes (success, max iterations reached, or early termination), report:

| Field | Description |
|-------|-------------|
| `final_status` | `pass` \| `fail` \| `blocked` |
| `iterations_used` | N of max_iterations |
| `termination_reason` | `all_passed` \| `max_iterations` \| `same_failure` \| `stalled` |
| `remaining_failures` | List of test names still failing (if any) |
| `files_modified` | List of files edited during the fix loop |

## Available Groups

| Group | Domain | Timeout | Description |
|-------|--------|---------|-------------|
| `ingest` | tests/ingest/ | 30s/300s | Ingestion pipeline tests |
| `retrieval` | tests/retrieval/ | 15s/120s | Retrieval pipeline tests |
| `guardrails` | tests/guardrails/ | 30s/180s | NeMo guardrails tests |
| `observability` | tests/observability/ | 15s/120s | Langfuse observability tests |
| `server` | tests/server/ | 15s/120s | Server schema/route tests |
| `import-check` | tests/import_check/ | 15s/120s | Import checker tests (subprocess override) |
| `root` | tests/test_*.py | 30s/300s | Root-level mixed tests |
| `all` | tests/ | 30s/600s | Full test suite (subprocess override) |

## Examples

Run all ingest tests:
```
scripts/run-tests.sh --group ingest
```

Run a specific test file:
```
scripts/run-tests.sh --path tests/ingest/test_orchestrator.py
```

Dry-run validation only (no pytest execution):
```
scripts/run-tests.sh --group all --dry-run
```

Run with marker filter:
```
scripts/run-tests.sh --group ingest --marker "not slow"
```

Run with keyword filter:
```
scripts/run-tests.sh --group retrieval --keyword "test_query"
```

Run in strict mode (warnings become errors):
```
scripts/run-tests.sh --group server --strict
```

Run with custom per-test timeout:
```
scripts/run-tests.sh --group guardrails --timeout 60
```
