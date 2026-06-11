---
name: branch-mapper
description: Enumerates executable branches per public function — including transitive private helpers — for test generation
domain: testing
action: analyzer
type: internal
tags: [testing, ast, branches, coverage, generate]
---

# Branch Mapper

Static analyzer that walks the Python AST of a source tree and, for each
public function, enumerates every executable branch reachable from that
function — including branches inside same-module private helpers it
transitively calls. Output is a typed `BranchMap` JSON document. Pure
analyzer: never modifies source, never executes user code.

## When to use

- `/code-test-generator` — primary consumer. Uses the per-function branch
  contract to drive generation of tests that cover every path (true/false
  legs of every `if`, every `except` handler, every loop entry, both arms
  of every ternary, every short-circuit point of every `and`/`or`).
- Coverage forensics — point at any source root to get a structured
  inventory of branches per function without running the code.

## Input / output contract

### CLI

```bash
python -m src.tools.testing.branch_mapper <source_root> \
    [--module DOTTED] [--function NAME] [--include-private]
```

| Arg | Required | Description |
|-----|----------|-------------|
| `<source_root>` | yes | Path to the source tree to analyze. |
| `--module` | no | Restrict analysis to a single dotted module path (relative to `source_root`). |
| `--function` | no | Restrict analysis to functions with this exact name. |
| `--include-private` | no | Include private (underscore-prefixed) functions as top-level entries (in addition to descending into them as helpers). |

### stdout

A JSON document conforming to the `BranchMap` schema (see `schemas.py`):

```json
{
  "source_root": "src/",
  "functions": [
    {
      "module": "pkg.mod",
      "function_name": "process",
      "line_start": 10,
      "line_end": 42,
      "is_public": true,
      "branches": [
        {
          "branch_type": "if",
          "line": 12,
          "end_line": 18,
          "condition": "value > 0",
          "in_function": "pkg.mod.process"
        },
        {
          "branch_type": "except",
          "line": 25,
          "end_line": 27,
          "condition": "ValueError",
          "in_function": "pkg.mod.process._normalize"
        }
      ],
      "transitive_helpers": ["pkg.mod.process._normalize"],
      "total_branch_count": 2
    }
  ],
  "timestamp": "2026-05-01T12:00:00Z"
}
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Always (informational tool). Bad CLI arguments are surfaced by `argparse` with its own non-zero exit. |

## Branch detection rules

Each AST construct maps to one or more `Branch` entries:

| AST node | Emitted branches |
|----------|-------------------|
| `If` | one `if` + one `elif` per chained `elif` + one `else` if an else clause exists |
| `Try` | one `try` + one `except` per handler + one `else` if `orelse` exists + one `finally` if `finalbody` exists |
| `For`, `AsyncFor` | one `for` |
| `While` | one `while` |
| `IfExp` | one `ternary` |
| `BoolOp` (`And`) | one `and` per operand after the first |
| `BoolOp` (`Or`) | one `or` per operand after the first |

`condition` is the source text of the test (via `ast.unparse`) for
constructs that have one; it is `None` for `else` and `finally` branches.
For an `except` handler, `condition` is the source of the exception type
(or `None` for a bare `except:`).

## `is_public` detection logic

A function is **public** when **both** hold:

1. Its name does **not** start with `_`.
2. Either the module defines no `__all__`, or the name appears in
   `__all__` (string literal entries only — dynamic `__all__` assignments
   are not resolved).

By default only public functions become top-level `FunctionBranchMap`
entries; private functions are still descended into transitively when
called by name from a public function. `--include-private` promotes
private functions to top-level entries as well.

## Transitive helper descent

Within a single function entry, branches from same-module private helpers
are inlined into the entry's `branches` list, with each branch's
`in_function` field set to the qualified path
(`module.public.helper.deeper`). A BFS walks helper calls breadth-first;
the qualified names of all helpers reached are listed in
`transitive_helpers` in discovery order.

Helper resolution rules:

- Only **bare-name calls** (`helper()`) are followed; attribute calls
  (`self.foo()`, `mod.bar()`) are not, because resolving instance
  methods and cross-module references is out of scope.
- Only **same-module** functions are followed.
- Only **private** helpers (names starting with `_`) are descended into.
- A **visited set** guards against recursive call cycles — each helper
  is inlined at most once per top-level entry.

## Schema reference

See `schemas.py` — pydantic v2 models:

- `Branch` — a single executable branch with type, line range, condition,
  and qualified `in_function` attribution.
- `FunctionBranchMap` — branches plus helper lineage for one function.
- `BranchMap` — top-level CLI payload.

## Constraints

- **Static analysis only.** The tool parses with `ast.parse` and never
  imports or executes the target code.
- **Same-module helper descent only.** Cross-module call graphs and
  instance-method dispatch are intentionally not resolved.
- **Cycle-safe.** Recursive private-helper call cycles are bounded by a
  visited set per top-level entry.
- **Project-agnostic.** No hardcoded paths; all input comes from the CLI.
- **Python 3.11+, pydantic v2, stdlib `ast` only.**

## Out of scope

- Cross-module call graph resolution.
- Method dispatch on `self`/`cls` and resolving instance methods.
- Reachability pruning (e.g., dropping an `else` whose `if` is a
  compile-time constant) — branch enumeration is syntactic, not
  semantic.
- Coverage measurement against an existing test suite — that is a
  runtime concern handled by `coverage.py`, not by this analyzer.
