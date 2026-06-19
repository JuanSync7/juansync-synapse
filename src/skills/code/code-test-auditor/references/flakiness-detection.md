# Flakiness Detection Reference

Loaded at [FLAKINESS] — consulted by `flakiness_checker` before computing scores.

---

## Metric Definition

```
fail_rate = distinct_outcomes / total_runs
```

Computed per `(test_id, sha)` pair — the same test on the same commit hash.

**`distinct_outcomes`** — count of distinct result categories observed across all runs
of `(test_id, sha)`. The four valid outcome values are: `pass`, `fail`, `error`, `skip`.

**Interpretation:**
- `fail_rate = 0.0` — impossible by definition (at least one outcome exists).
- `fail_rate` close to `1/N` — effectively deterministic; all N runs returned the same outcome.
- `fail_rate = 1.0` — every single run on the same sha produced a different outcome; maximally flaky.
- `fail_rate = 0.04` (e.g., 2 distinct outcomes across 50 runs) — real flakiness signal.

The metric is bounded to `(0, 1]`. Lower is more deterministic; higher is more flaky.

---

## Threshold

Flag any `(test_id, sha)` pair where `fail_rate > 0.02` as a **quarantine candidate**.

This is a **recommendation signal only.** Audit emits the signal; `code-test-integrator` owns the
actual quarantine decision. Do NOT quarantine, delete, or modify any test from this node.

---

## FLAKE_HISTORY.csv Schema

| Column | Type | Description |
|---|---|---|
| `test_id` | string | Fully qualified test identifier (e.g., `tests/unit/test_foo.py::test_bar`) |
| `sha` | string | Full git commit SHA at time of run |
| `run_timestamp` | ISO 8601 datetime | When the test execution completed |
| `outcome` | enum | One of: `pass`, `fail`, `error`, `skip` |
| `duration_ms` | integer | Wall-clock duration of the test run in milliseconds |

**Append-only.** One row per test execution. Never truncate, sort, or rewrite this file — audit is
read-only with respect to `FLAKE_HISTORY.csv`.

---

## Missing-File Handling

If `FLAKE_HISTORY.csv` does not exist:

1. Emit `flakiness_scores: {}` (empty dict) — do NOT raise or abort.
2. Note absence in `AuditGapReport` under `audit_gaps` with message:
   `"FLAKE_HISTORY.csv not found — flakiness scores unavailable for this run."`
3. Do NOT trigger an inline reruns campaign. Deciding whether and how to collect flakiness
   history is `code-test-integrator`'s responsibility (open question tracked in the decision memo).

---

## Low-Confidence Filter

Ignore any `(test_id, sha)` pair with `total_runs < 3`.

**Rationale:** A single run cannot distinguish a flaky test from a broken environment.
With fewer than 3 data points, `fail_rate` is numerically unreliable and should not influence
quarantine recommendations.

---

## Edge Cases

### Test that always fails (broken, not flaky)

If a test runs N times on the same sha and every run returns `fail`:
- `distinct_outcomes = 1` (only one outcome observed: `fail`)
- `fail_rate = 1 / N`

For N ≥ 3 this yields `fail_rate ≤ 0.33`, which may or may not exceed the 2% threshold
depending on N. A consistently-failing test with N = 50 runs gives `fail_rate = 0.02` —
exactly at the boundary, not flagged. This is correct: a consistently broken test is a
coverage gap, not a flakiness problem. Do not conflate the two signals.

### New test with a single row

- `total_runs = 1`, `distinct_outcomes = 1`, `fail_rate = 1.0`
- This would falsely flag the test as maximally flaky.
- **Mitigation:** the `total_runs < 3` low-confidence filter suppresses it. No action taken.

---

## Decision Examples

| Scenario | Calculation | Flagged? |
|---|---|---|
| 50 runs on sha A: 47 pass, 3 fail | distinct\_outcomes=2, fail\_rate=2/50=0.04 | YES — 0.04 > 0.02 |
| 1 run on sha B: outcome fail | total\_runs=1 → low-confidence | NO — suppressed |
| 10 runs on sha C: all fail | distinct\_outcomes=1, fail\_rate=1/10=0.10 | YES — but this is a broken test, not flaky |
| 5 runs on sha D: all pass | distinct\_outcomes=1, fail\_rate=1/5=0.20 | NO — 0.20 is low, well below threshold |
| 2 runs on sha E: 1 pass, 1 fail | total\_runs=2 → low-confidence | NO — suppressed |

> Note on the "10 runs all fail" row: the test is correctly flagged by fail_rate math, but
> the AuditGapReport context (outcome distribution) should make it clear to reviewers that
> this is a reliability failure, not environmental non-determinism. The `flakiness_checker`
> emits the raw scores; human or `code-test-integrator` interprets the pattern.

---

## Output Contract

`flakiness_checker` returns `dict[str, float]` mapping `test_id` to `fail_rate`.

Only pairs that pass the `total_runs ≥ 3` filter and exceed 0% fail_rate are included.
Pairs at exactly `fail_rate = 0` (impossible by definition) are never emitted.
Pairs suppressed by the low-confidence filter are omitted entirely — not zeroed.

This dict is merged into `AuditGapReport.flakiness_scores` at [CONSOLIDATE].

---

## Audit Is Read-Only

MUST NOT write to, truncate, or reorder `FLAKE_HISTORY.csv`.
MUST NOT quarantine, disable, or delete any test.
MUST NOT trigger test reruns to populate history.

Emit the signal. Downstream skills decide what to do with it.
