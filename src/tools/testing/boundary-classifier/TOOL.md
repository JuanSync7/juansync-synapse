---
name: boundary-classifier
description: Classifies every function as boundary (runtime-exposed) or internal — directs where to apply boundary-style tests
domain: testing
action: classifier
type: internal
tags: [testing, ast, boundaries, audit, generate]
---

# boundary-classifier

## Description

`boundary-classifier` walks a Python source tree and labels every
`FunctionDef` / `AsyncFunctionDef` as either a **boundary** (a function
exposed at runtime to an external caller) or an **internal** helper.

The classifier is a stdlib-`ast`-only static analyzer — it does not import or
execute project code. Output is a single `BoundaryClassification` JSON document
written to stdout.

## When to use

This tool is consumed by other testing tools in the engine; it is rarely run
directly by humans.

- **`test-audit`** — uses the boundary list to flag boundary functions whose
  defensive branches and error paths are not exercised by the existing test
  suite.
- **`test-generate`** — directs expensive techniques (Hypothesis property
  tests, exhaustive defensive-branch coverage) at boundary functions only,
  keeping internal helpers on cheaper example-based tests.

Use directly when you want a one-shot snapshot of the runtime surface of a
package, or when validating that a refactor did not accidentally promote an
internal helper to a boundary (or vice versa).

## Input / output contract

### Input

```
python -m src.tools.testing.boundary_classifier <source_root> [--include-internals]
```

- `<source_root>` — path to the directory to walk. Every `.py` file beneath
  it is parsed.
- `--include-internals` — if set, populate the `internals` list in the
  output. Without it, internal functions are still **counted** in
  `internal_count` but the array is left empty (keeps JSON small for the
  common audit-only path).

### Output

A single `BoundaryClassification` JSON document on stdout. Exit code is
**always 0** — the tool is informational. Downstream consumers decide how to
react to empty/skewed counts.

## Boundary type catalogue

| Boundary type        | Detection rule                                                                  | Example                               |
| -------------------- | ------------------------------------------------------------------------------- | ------------------------------------- |
| `http_route`         | Decorator attribute is `route`, `get`, `post`, `put`, `patch`, `delete`, `head`, `options` | `@app.route("/foo")`, `@router.get("/x")` |
| `temporal_activity`  | Decorator is `<name>.defn` where the LHS is `activity`                          | `@activity.defn`                      |
| `temporal_workflow`  | Decorator is `<name>.defn` where the LHS is `workflow`                          | `@workflow.defn`                      |
| `cli_command`        | Decorator attribute is `command` or `group`                                     | `@click.command()`                    |
| `celery_task`        | Decorator attribute is `task`, or bare-name `@shared_task`                      | `@app.task`, `@shared_task`           |
| `env_reader`         | Body reads `os.environ[...]`, `os.environ.get(...)`, or `os.getenv(...)`        | reads `os.getenv("API_KEY")`          |
| `stdin_reader`       | Body reads `sys.stdin.{read,readline,readlines}` or accesses `sys.argv`         | parses `sys.argv`                     |
| `exported_public`    | Function name is in module `__all__` and is not a `_private` name               | `def search(...)` listed in `__all__` |

Decorator matching is **right-hand-side keyed** — `@app.route`, `@bp.route`,
and `@router.route` all detect, regardless of the binding name.

## Priority order

Detection runs in strict priority order. **First match wins**:

1. **Decorator-based detection** — record the decorator's full source via
   `ast.unparse` in `decorator_source`.
2. **Body-scan detection** — `os.environ` / `os.getenv` for `env_reader`,
   `sys.stdin` / `sys.argv` for `stdin_reader`. Only consulted when no
   decorator matched.
3. **Export-based detection** — `exported_public` only fires when the module
   has a static `__all__`, the function name appears in it, and the name is
   not `_private`.

If none of the above match, the function is recorded as `InternalFunction`.

## Schema reference

See `schemas.py` for the authoritative pydantic v2 models:

- `BoundaryFunction` — module, function_name, qualified_name, line,
  `boundary_type`, `detection_reason`, `decorator_source`.
- `InternalFunction` — module, function_name, qualified_name, line,
  `is_private`, `in_all`.
- `BoundaryClassification` — top-level envelope with `source_root`,
  `boundaries`, `internals`, `total_functions`, `boundary_count`,
  `internal_count`, `timestamp`.

## Constraints

- **Strict priority order** — decorator > body-scan > export. The tool never
  promotes a function across categories once a higher-priority rule fires.
- **`__all__` parsing tolerates dynamic construction** — only static
  list/tuple/set of string literals is recognised. Dynamically-constructed
  `__all__` (e.g. `__all__ = sorted(_NAMES)`) is treated as if `__all__` were
  absent for export-based detection purposes.
- **Project-agnostic** — no hardcoded package names, framework imports, or
  filesystem layout assumptions. Decorator matching keys off the right-hand
  attribute name so any binding works.
- **Static only** — runs purely on `ast`; never imports project code. Files
  that fail to parse are silently skipped (tool is informational).
- **Python 3.11+** required (uses `ast.unparse`, modern type syntax,
  pydantic v2).
