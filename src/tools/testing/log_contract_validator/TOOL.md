---
name: log-contract-validator
description: Validates logging calls against a log archetype contract; computes log path coverage
domain: testing
action: validator
type: internal
tags: [testing, logging, observability, audit, generate]
---

# log-contract-validator

## Description

`log-contract-validator` is an internal testing tool that audits a Python
source tree for **log archetype conformance** — the project-defined contract
that says *what* should be logged, *at which level*, and *with which
structured fields* on every meaningful code path.

It walks every `.py` file under a given source root, AST-extracts all
logging calls, detects violations against an optional `LOG_POLICY.yaml`,
and computes a **log path coverage** metric: the fraction of branch nodes
(`if` / `except` / `for` / `while`) that contain at least one log call.

The tool is heuristic — it favors visibility over precision. Reviewers
should treat the report as advisory.

## When to use

- **`test-audit`** invokes this tool to verify that every error/exception
  path in a module is logged at the right level with the right structured
  fields before signing off on a coverage audit.
- **`test-generate`** uses the discovered `LogCall` set and the
  `log_path_coverage` metric to plan tests for log-emitting branches —
  e.g. asserting that a specific `extra={...}` payload is emitted on
  failure paths.

## Input / output contract

### Input

```
python -m src.tools.testing.log_contract_validator <source_root> \
    [--policy LOG_POLICY.yaml] \
    [--ignore-patterns tests/,migrations/]
```

| Argument            | Required | Description                                  |
| ------------------- | -------- | -------------------------------------------- |
| `source_root`       | yes      | Directory to scan recursively for `.py` files |
| `--policy`          | no       | Path to a `LOG_POLICY.yaml` archetype contract |
| `--ignore-patterns` | no       | Comma-separated substrings/globs to skip      |

### Output

A `LogContractReport` JSON document is written to **stdout**. The schema
is defined in [`schemas.py`](./schemas.py).

```json
{
  "source_root": "/path/to/src",
  "policy_path": "/path/to/LOG_POLICY.yaml",
  "log_calls": [ { "module": "...", "line": 42, "level": "error", ... } ],
  "violations": [ { "violation_type": "missing_log_in_except", ... } ],
  "total_branches": 120,
  "branches_with_log": 78,
  "log_path_coverage": 0.65,
  "timestamp": "2026-05-01T12:34:56+00:00"
}
```

## `LOG_POLICY.yaml` format

The policy file declares the archetype contract. Today the validator only
reads `required_fields_per_level`; additional keys are reserved for future
rules and will be ignored.

```yaml
# LOG_POLICY.yaml
required_fields_per_level:
  error:
    - request_id
    - error_code
  exception:
    - request_id
    - error_code
  warning:
    - request_id
  info: []
  debug: []
```

If `--policy` is omitted (or PyYAML is not installed), the
`missing_required_field` rule is silently disabled. All other rules still
run.

## Violation type catalogue

| Violation type              | What it flags                                                                 |
| --------------------------- | ----------------------------------------------------------------------------- |
| `missing_log_in_except`     | `except` block with no log call, no `raise`, and no `pass`                     |
| `wrong_level_for_archetype` | Log call inside `except` at `debug`/`info`, or weak-level log after a `raise` |
| `missing_required_field`    | Log call lacks a field declared in `required_fields_per_level` for its level   |
| `f_string_template`         | First positional arg is an f-string (loses structured-template semantics)      |
| `bare_logger_no_module`     | Uses `logging.<level>(...)` instead of a module-bound `logger`                 |
| `log_in_hot_loop`           | Log call inside `for`/`while` with no enclosing `if` guard (heuristic)         |

## Exit codes

| Code | Meaning                                       |
| ---- | --------------------------------------------- |
| `0`  | No violations found                           |
| `1`  | At least one violation reported               |
| `2`  | Tool error (bad arguments, unreadable source) |

## Schema reference

Pydantic v2 models live in [`schemas.py`](./schemas.py):

- `LogCall` — a single discovered log call.
- `LogContractViolation` — a single rule infraction.
- `LogContractReport` — the aggregated report (also carries the
  `log_path_coverage` metric).

## Constraints

- **Heuristic-based.** False positives are possible — particularly for
  `log_in_hot_loop`, which uses an enclosing-`if` heuristic and cannot
  detect runtime throttling (rate limiters, sampling, debouncers).
- **`--policy` is optional.** Without it, only the structural rules run.
  PyYAML is imported lazily; if the package is unavailable, policy
  enforcement degrades to a no-op.
- **Python only.** Other languages are out of scope.
- **No code execution.** The validator never imports the target source —
  it operates purely on the AST.
- **Project-agnostic.** No paths or module names are hardcoded; everything
  is supplied by the caller.
