---
name: code-test-score-assertions
description: Scores pytest test functions by assertion strength — flags trivial, tautological, and missing assertions
domain: code
subdomain: test
action: score
target: assertions
kind: internal
tags: [testing, ast, assertions, quality, audit]
---

# Assertion Quality

AST-based analyzer for pytest suites. Scores every `test_*` function by assertion strength and flags weak patterns that game coverage tools without verifying behavior.

## When to use

Called by the `code-test-auditor` skill when reviewing a test suite for behavior coverage (as opposed to line coverage). Surfaces tests that pass through the test runner but assert nothing meaningful.

## Input / output contract

```bash
python src/tools/testing/code-test-score-assertions/assertion_quality.py <test_root> [--threshold 0.5] [--min-assertions 2]
```

| Arg | Required | Default | Description |
|-----|----------|---------|-------------|
| `test_root` | yes | — | Directory containing pytest test files. Walked recursively. |
| `--threshold` | no | `0.5` | Minimum acceptable `quality_score` per test. |
| `--min-assertions` | no | `2` | Assertion count required to earn the clean-test bonus. |

Files scanned: `test_*.py` and `*_test.py` anywhere under `<test_root>`.

Functions scored: every top-level or nested function whose name starts with `test_`.

Output: a JSON-serialized `AssertionQualityReport` (see `schemas.py`) printed to stdout.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Every scored test meets the threshold. |
| 1 | At least one test scored below the threshold. |
| 2 | Tool error (bad path, invalid threshold, etc.). |

## Issue catalogue

| `issue_type` | What it catches | Example |
|--------------|-----------------|---------|
| `no_assertion` | Test body contains zero asserts, `pytest.raises`, or `mock.assert_*` calls. | `def test_foo(): build_thing()` |
| `trivial_assertion` | `assert` on a literal constant — always passes (or always fails) regardless of code under test. | `assert True`, `assert 1`, `assert "x"` |
| `tautological_assertion` | `assert` compares an expression to itself. | `assert x == x`, `assert obj is obj` |
| `mock_called_no_args` | Verifies invocation but not arguments. | `assert mock.called`, `mock.assert_called()`, `mock.assert_called_once()` |
| `weak_isinstance` | Test only checks return type, never the value. | `assert isinstance(result, dict)` (and nothing else) |
| `exception_swallowed` | `try/except` block neither re-raises nor asserts. | `try: do(); except Exception: pass` |

## Scoring formula

Start at `1.0` and apply per-issue penalties:

| Issue | Penalty |
|-------|---------|
| `no_assertion` | `-0.4` |
| `trivial_assertion` | `-0.2` |
| `tautological_assertion` | `-0.2` |
| `mock_called_no_args` | `-0.2` |
| `weak_isinstance` | `-0.1` |
| `exception_swallowed` | `-0.1` |

Then:

- Clamp to `[0.0, 1.0]`.
- Add `+0.1` bonus iff the test has **zero issues** AND `assertion_count >= --min-assertions`.

`has_meaningful_assertion` is `True` iff `assertion_count >= 1` AND no `no_assertion` / `trivial_assertion` issue is present on the test.

## Schema reference

See [`schemas.py`](./schemas.py):

- `AssertionIssue` — single weak-assertion finding (`line`, `issue_type`, `message`, `snippet`).
- `TestQualityScore` — per-function score (`assertion_count`, `quality_score`, `issues`, `has_meaningful_assertion`).
- `AssertionQualityReport` — top-level report (`scores`, `total_tests`, `tests_below_threshold`, `tests_with_no_assertion`, `average_score`, `threshold`, `timestamp`).

## Constraints

- **Per-test scoring** — every `test_*` function gets its own score; no cross-test aggregation beyond the summary counters.
- **Read-only** — never modifies source files; pure AST analysis.
- **Threshold configurable** — pass/fail bar is set by `--threshold`, not hard-coded.
- **Stdlib only for parsing** — uses Python's built-in `ast` module; no third-party AST or linting dependencies.
- **Project-agnostic** — accepts any `test_root`; no hardcoded paths.
- **Python 3.11+** required (uses modern `from __future__ import annotations` + `Literal` typing).
