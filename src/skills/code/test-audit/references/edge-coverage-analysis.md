# Edge Coverage Analysis

Reference for the [EDGE-COV] node. Guides `edge_coverage_analyzer` through static enumeration,
runtime cross-referencing, YAML output, and cap handling.

---

## What an Edge Is

An **edge** is a directed pair `(caller_module, callee_module)` where the two modules belong to
different packages at a defined package boundary. The boundary is crossed when the dotted prefix
of `caller_module` and `callee_module` differ at the top-level or sub-package level.

Edges are recorded from two AST constructs:

| Construct | Counted? | Notes |
|---|---|---|
| `import pkg.b` | Yes | Absolute import of a different package |
| `from pkg.b import fn` | Yes | ImportFrom with cross-package source |
| Direct function call resolved to a different package | Yes | `pkg.b.fn()` or alias-resolved |
| `from pkg.b import SomeType` (type-only) | **No** | `TYPE_CHECKING` guard or `if TYPE_CHECKING:` block |
| Same-package import (`from .sibling import x`) | **No** | Relative import within the same package |

**Concrete example:** `from synapse.tools.testing import schemas` inside
`src.skills.code.test_audit` creates edge
`(src.skills.code.test_audit, synapse.tools.testing)`.
If no integration test exercises this import path at runtime, the edge is uncovered.

---

## Why Edges Matter

Design doc §4 P5 establishes three orthogonal coverage metrics, each catching a distinct failure mode:

| Metric | Failure mode caught |
|---|---|
| Line coverage | Unexecuted code |
| Mutation kill rate | Weak assertions |
| **Edge coverage** | Untested module-to-module integration seams |

Line and mutation coverage are intra-module signals. A function can be line-covered and
mutation-clean while the wiring between modules is never exercised by any integration test.
Edge coverage is the only metric that measures these seams. A green line-coverage report
with zero or low edge coverage is a false signal — it reports internal health while
leaving integration contracts unverified.

---

## Step 1 — Static Enumeration (`E_static`)

Walk every `*.py` file under the project root. For each file, resolve its dotted module path
from the project root. Then inspect every AST node of these three types:

1. **`ast.Import`** — each `alias.name` that resolves to a different top-level or sub-package.
2. **`ast.ImportFrom`** — `node.module` when it resolves to a different package.
   Skip nodes guarded by `if TYPE_CHECKING:` — these are type-only and do not create runtime edges.
3. **`ast.Call`** — where the callable can be statically resolved (via import alias lookup)
   to a function in a different package. Record the callee's module, not the function name.

For each detected cross-package reference, emit one edge:

```
(caller_module: str, callee_module: str)
```

Deduplicate: if the same `(caller, callee)` pair appears multiple times in one file,
record it once. Edges are directed; `(a, b)` and `(b, a)` are independent entries.

The complete result is **`E_static`** — the full set of cross-package edges in the codebase.

---

## Step 2 — Runtime Instrumentation (`E_runtime`)

Do NOT execute tests inline at the [EDGE-COV] node. Consume previously-recorded trace artifacts:

```
project/coverage/state/edge_runtime.jsonl
```

Each line in this file is a JSON object written by the pytest plugin or `sys.settrace`-based
profiler during the most recent integration-marked test run:

```json
{"caller": "src.skills.code.test_audit", "callee": "synapse.tools.testing", "test_id": "tests/integration/test_audit.py::test_edge_walk"}
```

Only calls made during tests marked `@pytest.mark.integration` (or the project's equivalent
integration marker) are recorded in this file. Unit-only test runs do not contribute to
`E_runtime`.

**Tool base:** `pytest-trace` or an equivalent `sys.settrace`-based profiler configured
to emit cross-package call events to `edge_runtime.jsonl`. The profiler must be invoked
externally (by the CI integration-test run or a manual `pytest -m integration` pass)
before the [EDGE-COV] node executes.

The result is **`E_runtime`** — the set of cross-package edges observed during
integration-marked test execution.

---

## Coverage Formula

```
edge_coverage = |E_runtime ∩ E_static| / |E_static|
```

An edge is **covered** if it appears in both `E_static` and `E_runtime`. An edge present
in `E_static` but absent from `E_runtime` is **uncovered** — an integration seam that no
integration-marked test exercises.

**Per-package decomposition** is recommended in addition to the project-wide ratio.
Compute coverage separately for each top-level caller package so that gaps can be
attributed to the team or module that owns the caller.

---

## `EDGE_COVERAGE.yaml` Schema

```yaml
version: 1
computed_at: <ISO8601>           # e.g. 2026-04-30T14:22:05Z
project_sha: <sha>               # git HEAD SHA at time of computation
total_edges: <int>               # |E_static|
covered_edges: <int>             # |E_runtime ∩ E_static|
coverage_ratio: <float 0-1>      # covered_edges / total_edges
uncovered:
  - {from: pkg.a, to: pkg.b}
  - {from: pkg.c, to: pkg.d}
unanalyzed:
  - {from: pkg.e, to: pkg.f, reason: max-edges-cap}
```

`uncovered` lists every edge in `E_static \ E_runtime`.
`unanalyzed` lists every edge excluded by the `--max-edges` cap (see below).
An edge MUST appear in exactly one of `uncovered`, `unanalyzed`, or be implicit in
`covered_edges` — never silently dropped.

---

## `--max-edges` Cap

When `|E_static|` exceeds the configured cap (default set by the project; no universal default):

1. Compute an **edge weight** for each edge:
   `weight = LOC(caller_module) + LOC(callee_module)`
2. Sort edges by weight **descending** — heavier edges involve larger modules and are
   higher-priority integration seams.
3. Analyze the top N edges (where N = cap). These are candidates for `E_runtime` intersection.
4. Place all remaining edges in `unanalyzed` with `reason: max-edges-cap`.

NEVER silently truncate. Every edge excluded by the cap must appear in `unanalyzed` with
an explicit reason. The `AuditGapReport.edge_coverage_gaps` field surfaces the count of
unanalyzed edges so downstream skills and human reviewers know coverage is incomplete.

---

## Edge Cases

**First run — no `EDGE_COVERAGE.yaml` exists:**
Write baseline from scratch. Set `covered_edges` and `coverage_ratio` from current data.
Mark `coverage_ratio` as informational in the report — there is no prior baseline to
compare against. Do not fail the audit node; proceed to [LOG-CONTRACT].

**No integration-marked tests in the project:**
`E_runtime` is empty. Set `covered_edges = 0`, `coverage_ratio = 0.0`. This is not an
audit failure; it signals an integration test gap. Surface it as a finding in
`AuditGapReport.edge_coverage_gaps` with a note: "No integration-marked tests found;
all static edges are uncovered."

**Cyclic edges (`a → b` and `b → a`):**
Both are counted independently. The edge `(a, b)` and the edge `(b, a)` are separate
entries in `E_static`. Coverage of one does not imply coverage of the other.

**`edge_runtime.jsonl` missing:**
No prior integration test run has produced trace artifacts. Treat as equivalent to
"no integration-marked tests": `E_runtime = ∅`, `covered_edges = 0`,
`coverage_ratio = 0.0`. Note the missing artifact in the report.

---

## Output Contract

`edge_coverage_analyzer` returns an `EdgeCoverageGaps` model (defined in
`src/tools/testing/coverage_analyzer/schemas.py`) containing:

- `total_edges`, `covered_edges`, `coverage_ratio`
- `uncovered: list[EdgePair]`
- `unanalyzed: list[EdgePairWithReason]`
- `computed_at`, `project_sha`

This model is written to `EDGE_COVERAGE.yaml` and embedded in `AuditGapReport.edge_coverage_gaps`.
The [EDGE-COV] node MUST NOT exit without writing `EDGE_COVERAGE.yaml`, even on first run.
