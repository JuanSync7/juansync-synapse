---
name: coverage-analyzer
description: Computes per-function coverage gaps and cross-package call graph edges from a test suite
domain: testing
action: analyzer
type: internal
tags: [testing, coverage, edges, call-graph, audit, integrate]
---

# coverage-analyzer

Analyses a Python source tree and a test suite to produce one of two structured JSON reports,
depending on the selected mode.  The tool is project-agnostic — no paths are hardcoded.

---

## Modes

### Default mode — coverage gaps

Reads a `.coverage` data file produced by a prior `pytest --cov` run and iterates every Python
source file under `<source_root>`.  For each discovered function it computes the percentage of
statements that were executed, collects the specific missing line numbers, and flags whether the
function is a public boundary entry-point.

Output schema: **CoverageReport**

Used by: `test-audit` skill.

### `--edges` mode — cross-package call graph

Performs a static AST walk over every `.py` file under `<source_root>` to build a call graph.
A cross-package edge is recorded whenever a function in `package_a.*` calls something imported
from `package_b.*` (top-level package names differ).  Same-package calls are not edges.

If a `--baseline` snapshot is provided the tool computes the set difference and populates
`new_edges`.  Zero new edges triggers an advisory warning in downstream consumers — it **never**
causes this tool to exit non-zero.

Output schema: **EdgeCoverageReport**

Used by: `test-integrate` skill at the `[EDGE-FEEDBACK]` step to detect whether a newly merged
integration test exercises at least one new `(caller_module, callee_module)` edge.

---

## When to use each mode

| Situation | Mode |
|---|---|
| Reviewing which functions in a module lack test coverage | Default |
| Checking whether a new integration test crosses package boundaries | `--edges` |
| Generating a coverage baseline for future edge-diff comparisons | `--edges` (no `--baseline`) |
| Diffing a new test suite against a prior edge snapshot | `--edges --baseline <path>` |

---

## Input / output contract

### CLI arguments

```
python -m src.tools.testing.coverage_analyzer <source_root> [OPTIONS]

Positional arguments:
  source_root           Path to the source root directory to analyse.

Options:
  --edges               Enable edge mode (cross-package call graph).
  --test-path PATH      [--edges] Path recorded in the report as test_suite_path.
                        Defaults to source_root when omitted.
  --baseline PATH       [--edges] Path to a prior EdgeCoverageReport JSON file.
                        When provided, new_edges = current_edges - baseline_edges.
  --sha SHA             [--edges] Git commit SHA embedded in the EdgeCoverageReport.
```

### JSON output (default mode)

```json
{
  "source_root": "/abs/path/to/src",
  "gaps": [ <CoverageGap>, ... ],
  "total_functions": 142,
  "functions_with_gaps": 17,
  "report_timestamp": "2026-05-01T12:00:00+00:00"
}
```

### JSON output (`--edges` mode)

```json
{
  "commit_sha": "abc1234",
  "test_suite_path": "/abs/path/to/tests",
  "edges": [ <Edge>, ... ],
  "new_edges": [ <Edge>, ... ],
  "snapshot_timestamp": "2026-05-01T12:00:00+00:00"
}
```

---

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Always. Gaps and missing edges are informational, never errors. |

The tool **never** exits with code `1` on content grounds (no gaps found, zero new edges, etc.).
A non-zero exit is only possible for hard precondition failures (missing `source_root`, unreadable
`.coverage` file) but even then the tool prints a human-readable error to stderr before exiting.

---

## Schema reference

### CoverageGap

| Field | Type | Description |
|---|---|---|
| `module` | `str` | Dotted module path, e.g. `ragweave.ingest.queue`. |
| `function_name` | `str` | Name of the function with insufficient coverage. |
| `line_start` | `int` | First line of the function definition. |
| `line_end` | `int` | Last line of the function definition. |
| `coverage_pct` | `float` | Percentage of statements covered (0.0–100.0). |
| `missing_lines` | `list[int]` | Sorted list of uncovered line numbers within the function. |
| `is_boundary` | `bool` | True if decorated with `@app.route`, `@activity.defn`, `@click.command`, `@router.get/post/put/delete`, or its body reads `request` / `os.environ` / `sys.stdin`. |

### Edge

| Field | Type | Description |
|---|---|---|
| `caller_module` | `str` | Dotted module path of the calling module. |
| `callee_module` | `str` | Dotted module path of the called module. |
| `call_site_line` | `int \| None` | Line number in the caller where the call appears, if known. |

### EdgeCoverageReport

| Field | Type | Description |
|---|---|---|
| `commit_sha` | `str \| None` | Git commit SHA, if provided via `--sha`. |
| `test_suite_path` | `str` | Path to the test suite passed to `--test-path` (or `source_root`). |
| `edges` | `list[Edge]` | Deduplicated cross-package edges found in the source tree. |
| `new_edges` | `list[Edge]` | Edges absent from the baseline snapshot; empty list if no baseline. |
| `snapshot_timestamp` | `datetime` | UTC timestamp when the report was generated. |

### CoverageReport

| Field | Type | Description |
|---|---|---|
| `source_root` | `str` | Absolute path to the analysed source root. |
| `gaps` | `list[CoverageGap]` | All functions with at least one missing line, sorted by module then line. |
| `total_functions` | `int` | Total number of functions discovered. |
| `functions_with_gaps` | `int` | Number of functions with at least one gap. |
| `report_timestamp` | `datetime` | UTC timestamp when the report was generated. |

---

## Constraints

- **Python 3.11+, Pydantic v2.**  Default mode additionally requires the `coverage` package.
- **`--edges` mode uses `stdlib ast` only** — no third-party dependencies.
- **Edge mode is strictly advisory.**  Zero `new_edges` never blocks any pipeline step.  The
  downstream `test-integrate` consumer posts an advisory PR comment but does not fail the check.
- **No paths are hardcoded.**  The tool operates on whatever `source_root` is passed; it has no
  knowledge of the project layout.
- **Output is always written to stdout as JSON.**  Warnings and errors go to stderr.
