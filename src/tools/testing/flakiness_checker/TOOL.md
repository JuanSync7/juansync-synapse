---
name: flakiness-checker
description: Runs a pytest test ≥10 times and computes fail rate to detect flaky tests before integration
domain: testing
action: validator
type: internal
tags: [testing, flakiness, pytest, integration, stability]
---

# flakiness-checker

A CLI validator that runs a single pytest test node at least 10 times in isolation and computes a **fail rate**. Used by the `code-test-integrator` skill at the **[FLAKE-CHECK]** node to confirm a new real-integration test is stable before opening a PR.

---

## When to Use

- A new real-integration test has been written and is about to be merged.
- The `code-test-integrator` skill reaches the [FLAKE-CHECK] gate and needs a stability verdict.
- Any time you suspect a test may be environment-sensitive or timing-dependent.

Do **not** use this tool as a substitute for fixing a known-broken test. If a test is deterministically failing, fix it first.

---

## Input / Output Contract

### CLI invocation

```
python -m src.tools.testing.flakiness_checker <test_node_id> [--runs N] [--timeout SECONDS]
```

| Argument | Type | Default | Description |
|---|---|---|---|
| `test_node_id` | str (positional) | required | Pytest node id, e.g. `tests/integration/test_foo.py::test_bar` |
| `--runs` | int | `10` | How many times to run the test. Minimum is **10** — lower values are rejected. |
| `--timeout` | float | `120.0` | Per-run timeout in seconds. Must be positive. |

### JSON output (stdout)

On success or flakiness detection the tool writes a `FlakinessSummary` JSON object to **stdout** and exits. On tool error (bad args, pytest missing) it writes to **stderr** and exits 2 with no JSON output.

Example:

```json
{
  "test_id": "tests/integration/test_db.py::test_writes_record",
  "total_runs": 10,
  "failures": 0,
  "fail_rate": 0.0,
  "status": "stable",
  "outcomes": [
    {
      "run_number": 1,
      "passed": true,
      "duration_seconds": 0.342,
      "error_message": null
    }
  ],
  "run_timestamp": "2026-05-01T14:00:00+00:00"
}
```

---

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Test is **stable** — `fail_rate < 2%`. Safe to proceed with PR. |
| `1` | Test is **flaky-quarantined** — `fail_rate >= 2%`. Do not merge; investigate root cause. |
| `2` | **Tool error** — bad arguments, pytest not installed, or unexpected runtime failure. |

---

## Schema Reference: `FlakinessSummary`

| Field | Type | Description |
|---|---|---|
| `test_id` | `str` | Pytest node id passed as input |
| `total_runs` | `int` | Number of executions completed (>= 10) |
| `failures` | `int` | Count of runs that did not exit with code 0 |
| `fail_rate` | `float` | `failures / total_runs`; range `[0.0, 1.0]` |
| `status` | `"stable" \| "flaky-quarantined"` | `"stable"` when `fail_rate < 0.02`; `"flaky-quarantined"` otherwise |
| `outcomes` | `list[TestOutcome]` | Per-run detail, ordered by `run_number` |
| `run_timestamp` | `datetime` (UTC ISO-8601) | When the checker batch started |

### `TestOutcome` (per run)

| Field | Type | Description |
|---|---|---|
| `run_number` | `int` | 1-based index |
| `passed` | `bool` | `true` if pytest exited 0 |
| `duration_seconds` | `float` | Wall-clock time for this run |
| `error_message` | `str \| null` | First 2000 chars of combined stdout+stderr on failure; `null` on pass |

---

## Constraints

- **Minimum 10 runs, always.** The tool rejects `--runs` values below 10 with a hard error. This minimum is never bypassed, even if the first N runs all pass.
- **No early exit.** All `--runs` executions complete regardless of interim results. The full outcome list is required for an accurate fail rate.
- **Each run is isolated.** The tool invokes `pytest <test_node_id> -x --tb=short` as a fresh subprocess — no in-process test runner, no shared state between runs.
- **Project-agnostic.** No hardcoded paths. The tool delegates all path resolution to pytest via the node id.
- **2% threshold is fixed.** `fail_rate >= 0.02` → `"flaky-quarantined"`. This threshold is not configurable at the CLI level.
