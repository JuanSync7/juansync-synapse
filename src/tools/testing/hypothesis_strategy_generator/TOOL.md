---
name: hypothesis-strategy-generator
description: Emits Hypothesis @given strategies from function type hints — for property-based test generation
domain: testing
action: generator
type: internal
tags: [testing, hypothesis, property-based, ast, generate]
---

# Hypothesis Strategy Generator

Reads a function's type hints via :mod:`ast` and emits a ready-to-use Hypothesis `@given(...)` decorator string for each parameter, plus the import lines needed to make it run. Pure source inspector — no code is executed, no test files are written, and Hypothesis is **not** a runtime dependency of this tool. The output is just strings.

## When to use

- `/code-test-generator` — when scaffolding property-based tests for a *boundary function* (a pure or near-pure function whose inputs are well-typed and whose contract you want to exercise across a wide value space).
- Standalone inspection — point at any source root to see which functions are amenable to property-based testing and which need handwritten strategies.

Not the right tool when:

- You need example-based tests (use a generator that emits `pytest.parametrize`).
- The function relies on heavy mocking, live I/O, or state — Hypothesis decorators alone won't help.

## Input / output contract

### CLI

```bash
python -m src.tools.testing.hypothesis_strategy_generator <source_root> \
    [--module DOTTED] [--function NAME] [--public-only]
```

| Arg | Required | Description |
|-----|----------|-------------|
| `<source_root>` | yes | Directory to scan for `.py` files. |
| `--module DOTTED` | no | Restrict to one dotted module path (relative to `source_root`). |
| `--function NAME` | no | Restrict to functions whose name exactly matches `NAME`. |
| `--public-only` | no | Skip functions whose name starts with `_`. |

### stdout

A JSON document conforming to the `StrategyReport` schema (see `schemas.py`):

```json
{
  "source_root": "src/",
  "functions": [
    {
      "module": "myproject.math",
      "function_name": "clamp",
      "line_start": 14,
      "parameters": [
        {
          "parameter_name": "value",
          "type_hint_source": "int",
          "strategy_code": "st.integers()",
          "is_supported": true,
          "fallback_reason": null
        }
      ],
      "given_decorator": "@given(\n    value=st.integers(),\n)",
      "required_imports": ["from hypothesis import given, strategies as st"],
      "all_supported": true
    }
  ],
  "total_functions": 1,
  "fully_supported": 1,
  "partially_supported": 0,
  "timestamp": "2026-05-01T12:00:00Z"
}
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Always. The report is informational; unsupported types are surfaced inline as `is_supported: false`, not as a process failure. |

## Type-hint mapping

| Annotation | Strategy |
|------------|----------|
| `int` | `st.integers()` |
| `str` | `st.text()` |
| `bool` | `st.booleans()` |
| `float` | `st.floats(allow_nan=False, allow_infinity=False)` |
| `bytes` | `st.binary()` |
| `None` / `NoneType` | `st.none()` |
| `list[T]` | `st.lists(<T-strategy>)` |
| `tuple[T1, T2, ...]` | `st.tuples(<T1>, <T2>, ...)` |
| `tuple[T, ...]` (variadic) | `st.lists(<T-strategy>).map(tuple)` |
| `set[T]` | `st.sets(<T-strategy>)` |
| `frozenset[T]` | `st.frozensets(<T-strategy>)` |
| `dict[K, V]` | `st.dictionaries(<K>, <V>)` |
| `Optional[T]` / `T \| None` | `st.one_of(st.none(), <T-strategy>)` |
| `Union[A, B]` / `A \| B` | `st.one_of(<A>, <B>)` |
| `Literal["a", "b"]` | `st.sampled_from(["a", "b"])` |
| `datetime` | `st.datetimes()` (adds `from datetime import datetime`) |
| `date` | `st.dates()` (adds `from datetime import date`) |
| `Decimal` | `st.decimals(allow_nan=False, allow_infinity=False)` (adds `from decimal import Decimal`) |
| `UUID` | `st.uuids()` (adds `from uuid import UUID`) |
| `Enum` subclass | `st.sampled_from(list(EnumClass))` *(see note below)* |
| Pydantic `BaseModel` subclass | `st.builds(ModelClass)` *(see note below)* |
| Anything else | `st.nothing()  # TODO: unsupported` with `is_supported=false` and a `fallback_reason` |

> **Note on Enum / BaseModel subclasses:** the AST cannot tell the difference between a bare class name that is an Enum, a BaseModel, a dataclass, or a plain class. The tool flags such bare names as `is_supported=false` with a `fallback_reason` that suggests the right wrapping (`st.sampled_from(list(...))` or `st.builds(...)`). The mapping table above documents the *intended* hand-edit, not an automatic rewrite.

The base import `from hypothesis import given, strategies as st` is always included in `required_imports`. Stdlib type imports (`datetime`, `Decimal`, `UUID`, etc.) are appended only when their type appears in the resolved strategy.

## Schema reference

See `schemas.py` — pydantic v2 models:

- `ParameterStrategy` — one parameter's strategy mapping (with `is_supported` / `fallback_reason`).
- `FunctionStrategy` — full `@given(...)` bundle for one function, plus `required_imports` and `all_supported`.
- `StrategyReport` — top-level CLI payload with `total_functions`, `fully_supported`, `partially_supported` rollups.

## How it works

1. Walk every `.py` file under `<source_root>` (sorted, recursive).
2. Parse each file with `ast.parse`. If the file fails to parse (syntax error, encoding error, unreadable), the file is **skipped silently** — never raises.
3. For every `FunctionDef` / `AsyncFunctionDef`:
   - Apply `--module` / `--function` / `--public-only` filters.
   - Drop `self` / `cls` (first positional only) and any unannotated parameters.
   - If no annotated parameters remain, the function is skipped (no decorator to emit).
4. For each remaining parameter, walk its annotation AST and map it to a strategy expression per the table above. Annotation source is captured via `ast.unparse`.
5. Compose the multi-line `@given(...)` decorator and the deduplicated `required_imports` list.
6. Stamp `timestamp` (UTC), serialize the `StrategyReport` to stdout, exit `0`.

## Constraints

- **Never raises on parse failure.** Files that won't parse are skipped; the report still emits.
- **Unknown types map to `st.nothing()` with a TODO.** The decorator string is still well-formed; callers can grep for `# TODO: unsupported` to find handwritten work.
- **Project-agnostic.** No hardcoded paths, no project-specific imports, no assumed package layout beyond the supplied `source_root`.
- **Hypothesis is not a runtime dep of this tool.** It only emits strategy code as strings; the consumer's test environment must install Hypothesis to run the generated decorator.
- **AST-only.** No imports are executed, no type resolution beyond what the source text reveals. Aliased imports (e.g. `from typing import List as _List`) are not tracked — the bare alias name is what gets matched.
- **Python 3.11+, pydantic v2, stdlib `ast` only.**

## Out of scope

- Writing test files. This tool emits decorator strings; the consuming skill is responsible for assembling the `def test_...` body and writing it to disk.
- Strategy *quality* tuning (boundary values, custom shrinkers, `assume(...)` predicates). Output is the minimum viable strategy for the declared type.
- Resolving forward references, `TYPE_CHECKING`-only imports, or runtime type aliases. Annotations are read as written.
- Non-Python languages.

## Failure handling

Per-file parse / read failures are swallowed silently — the file is omitted from the report and the next file is attempted. There is no per-file error channel in `StrategyReport`; the contract is "best-effort emission". Top-level argument errors (missing `source_root`, malformed flags) are surfaced by `argparse` with its own non-zero exit. A missing `source_root` directory yields an empty, well-formed report and exit `0`.
