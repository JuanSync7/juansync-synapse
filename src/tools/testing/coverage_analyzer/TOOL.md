---
name: coverage-analyzer
description: Computes per-function coverage gaps and cross-package call graph edges from a test suite
domain: testing
action: analyzer
type: internal
tags: [testing, coverage, edges, call-graph, audit, integrate]
---

# coverage-analyzer

Two-mode analyzer for the test coverage engine. Default mode reports which functions are under-covered; `--edges` mode walks the source AST to compute cross-package call graph edges and diffs against a prior snapshot.

## When to use

| Mode | Used by | When |
|------|---------|------|
| Default | `code-test-auditor` | After running pytest with `--cov`; identifies coverage gaps to feed into `code-test-generator` |
| `--edges` | `code-test-integrator` at [EDGE-FEEDBACK] | After a real integration test is merged; detects whether it exercises new cross-package edges |

## Input

```bash
# Default mode — per-function coverage gaps
python -m src.tools.testing.coverage_analyzer <source_root>

# Edge mode — cross-package call graph edges
python -m src.tools.testing.coverage_analyzer <source_root> \
  --edges \
  [--test-path PATH] \
  [--baseline PATH] \
  [--sha SHA]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `source_root` | yes | Path to the Python source root to analyze |
| `--edges` | no | Switch to edge-coverage mode |
| `--test-path` | no | Test suite path (metadata only; default: `tests/`) |
| `--baseline` | no | Path to a prior `EdgeCoverageReport` JSON for new-edge diffing |
| `--sha` | no | Git commit SHA to embed in the report |

**Default mode prerequisite:** a `.coverage` data file must exist in the current directory (produced by `pytest --cov <source_root>`).

## Output

Both modes output a single JSON object to stdout.

**Default mode** — `CoverageReport`:
```json
{
  "source_root": "/path/to/src",
  "gaps": [
    {
      "module": "ragweave.ingest.queue",
      "function_name": "dispatch",
      "line_start": 42,
      "line_end": 67,
      "coverage_pct": 61.5,
      "missing_lines": [51, 52, 58, 59, 60],
      "is_boundary": true
    }
  ],
  "total_functions": 84,
  "functions_with_gaps": 12,
  "report_timestamp": "2026-05-02T10:00:00+00:00"
}
```

**`--edges` mode** — `EdgeCoverageReport`:
```json
{
  "commit_sha": "abc1234",
  "test_suite_path": "tests/integration/",
  "edges": [
    {"caller_module": "ragweave.api.handlers", "callee_module": "ragweave.ingest.queue", "call_site_line": 88}
  ],
  "new_edges": [
    {"caller_module": "ragweave.api.handlers", "callee_module": "ragweave.ingest.queue", "call_site_line": 88}
  ],
  "snapshot_timestamp": "2026-05-02T10:00:00+00:00"
}
```

`new_edges` is empty when no `--baseline` is provided. When a baseline is provided, `new_edges` contains only edges whose `(caller_module, callee_module)` pair was absent from the baseline.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Analysis complete (gaps and zero-new-edges are informational, never errors) |
| 2 | Tool error (missing `.coverage` file, bad source root, import failure) |

## Schema reference

### `CoverageGap`

| Field | Type | Description |
|-------|------|-------------|
| `module` | `str` | Dotted module path |
| `function_name` | `str` | Function or method name |
| `line_start` | `int` | First line of the function |
| `line_end` | `int` | Last line of the function |
| `coverage_pct` | `float` | Percentage of lines covered (0–100) |
| `missing_lines` | `list[int]` | Uncovered line numbers |
| `is_boundary` | `bool` | True if exposed via route/activity/command decorator or reads env/stdin |

### `Edge`

| Field | Type | Description |
|-------|------|-------------|
| `caller_module` | `str` | Dotted module path of the calling module |
| `callee_module` | `str` | Dotted module path of the called module |
| `call_site_line` | `int \| None` | Line number of the call site |

### `EdgeCoverageReport`

| Field | Type | Description |
|-------|------|-------------|
| `commit_sha` | `str \| None` | Git SHA of the measured commit |
| `test_suite_path` | `str` | Path to the test suite |
| `edges` | `list[Edge]` | All cross-package edges found, deduplicated by `(caller, callee)` |
| `new_edges` | `list[Edge]` | Edges absent from baseline; empty if no baseline provided |
| `snapshot_timestamp` | `datetime` | UTC timestamp of the report |

### `CoverageReport`

| Field | Type | Description |
|-------|------|-------------|
| `source_root` | `str` | Absolute path to the analyzed source root |
| `gaps` | `list[CoverageGap]` | Functions with ≥1 missing line |
| `total_functions` | `int` | Total functions analyzed |
| `functions_with_gaps` | `int` | Count of functions with gaps |
| `report_timestamp` | `datetime` | UTC timestamp of the report |

## Constraints

- **Edge mode is advisory.** Zero `new_edges` never causes a non-zero exit or blocks any workflow. The `code-test-integrator` skill posts an advisory PR comment when `new_edges` is empty; it does not revert or block.
- **Default mode requires `.coverage`.** The tool does not run pytest itself; it reads an existing `.coverage` data file.
- **Edge detection is static AST only.** Dynamic dispatch and runtime-constructed calls are not detected. The edge set is a conservative undercount — false negatives are possible, false positives are not.
- **Cross-package definition.** An edge exists when `caller_module.split('.')[0] != callee_module.split('.')[0]`. Same top-level package calls are not edges.
- **No hardcoded paths.** Tool is project-agnostic.
