---
name: mutation-runner
description: Generates AST mutants of a target function and runs the test suite per mutant to detect weak assertions
domain: testing
action: validator
type: internal
tags: [testing, mutation, ast, assertions, generate]
---

# Mutation Runner

AST-driven mutation-testing harness for a single Python source file. Generates small, targeted mutants of a target function (operator swaps, constant changes, boundary flips, return-value blanking, condition negation) and runs the project's test suite against each one. A mutant that the test suite *fails* to detect is a "survivor" — a signal that assertions are too weak.

The runner is **project-agnostic**. Inputs and outputs flow on the command line; nothing about the host project is hardcoded.

## When to use

- **Per coverage gap, from `test-generate`** — invoked with a tight line budget (≤20 mutated lines) on the function being newly tested. Surviving mutants tell the generator which assertions need strengthening.
- **Nightly job** — run across all hot files in the repo to track mutation-kill rate as a quality signal. A drop in kill rate signals new tests are weaker than what they replaced.
- **Ad-hoc debugging** — when a code path "feels" untested but coverage looks green, mutate it and watch tests pass.

## Input / output contract

```bash
python -m src.tools.testing.mutation_runner <module_path> \
    [--function NAME] [--test-cmd "pytest tests/"] \
    [--max-lines 20] [--timeout 30]
```

| Arg | Required | Description |
|-----|----------|-------------|
| `<module_path>` | yes | Filesystem path to a single `.py` file containing the target function. |
| `--function NAME` | no | Name of the target function. If omitted, all functions in the file are mutated. |
| `--test-cmd CMD` | no | Test command to run per mutant. Default `pytest`. |
| `--max-lines N` | no | Maximum count of *distinct* mutated lines this run. Default `20`. |
| `--timeout SEC` | no | Per-mutant subprocess timeout. Default `30`. Timeouts count as kills. |

Output: a `MutationReport` JSON document on stdout (see `schemas.py`).

## Mutation type catalogue

| Mutation type | AST node | Transformation |
|---------------|----------|---------------|
| `arithmetic_op` | `BinOp` | `+` ↔ `-`, `*` ↔ `/` |
| `comparison_op` | `Compare.ops[i]` | `<` ↔ `>`, `==` ↔ `!=`, `<=` ↔ `>=` |
| `boolean_op` | `BoolOp` | `And` ↔ `Or` |
| `constant_swap` | `Constant` | int `0` ↔ `1`, bool `True` ↔ `False` |
| `boundary_flip` | `Compare.ops[i]` | `<` → `<=`, `>` → `>=` |
| `return_value` | `Return.value` | replace with `Constant(value=None)` |
| `negate_condition` | `If.test` | wrap in `UnaryOp(Not(), ...)` |

Each generated mutant carries a stable `mutant_id` of the form `<module>.<func>:<line>:<mutation_type>:<ordinal>` so reports diff cleanly across runs.

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Every mutant was killed (`kill_rate == 1.0`), or no mutants were generated. |
| `1` | At least one mutant survived. |
| `2` | Tool error: missing/unreadable file, parse failure, refused input (test file), or fatal subprocess error. |

## Schema reference

See `schemas.py` for the pydantic v2 contracts: `Mutant`, `MutationResult`, `MutationReport`, and the `MutationType` literal union. The `MutationReport` payload printed to stdout is the canonical output surface.

## Safety

- **File restoration is non-negotiable.** The original source is captured in memory before the first mutation. After every mutant — pass or fail — the original is written back via atomic replace inside a `try/finally`. A second `try/finally` wraps the whole loop as belt-and-braces.
- **Signal handling.** A `_RestoreOnSignal` context manager installs `SIGINT` and `SIGTERM` handlers that restore the backup before re-raising as `KeyboardInterrupt`, so the file is never left mutated even if the user hits Ctrl-C between subprocess runs.
- **Atomic writes.** Mutated source is written to a tempfile in the same directory, then `os.replace`d into place. No partial writes.
- **Never mutates test files.** If `<module_path>` is named `test_*.py`, ends in `_test.py`, or sits anywhere under a `tests/` (or `test/`) directory, the tool exits `2` with a refusal error before touching anything.

## Constraints

- **Single-file scope.** The tool mutates exactly one `.py` file per invocation. Cross-file mutations are out of scope.
- **Line-budget enforcement.** `--max-lines` caps the number of *distinct* mutated lines. Once the budget is hit, further new lines are skipped (existing mutated lines still accumulate ordinals). This keeps `test-generate` invocations bounded.
- **Project-agnostic.** No hardcoded paths, test commands, or framework assumptions. The caller supplies the test command.
- **Stdlib + pydantic only.** `ast`, `subprocess`, `tempfile`, `shutil`, `signal`, `os` plus pydantic v2. Python 3.11+.
- **Timeout semantics.** A subprocess timeout counts as a kill (the test environment is degraded — that *is* a detected fault). The timeout count is reported separately so callers can distinguish.

## Out of scope

- **Equivalent-mutant detection.** The runner does not attempt to prove that surviving mutants are semantically equivalent to the original. That judgement is left to the human or to a downstream skill.
- **Coverage measurement.** Use `coverage.py` for that. The mutation-runner assumes the line is already executed by some test.
- **Cross-file or cross-module mutations.** One file in, one report out.
- **Test discovery.** The caller is responsible for `--test-cmd`. The runner does not introspect the project's test layout.
