# Coverage Analysis — [SNAPSHOT] Reference

Loaded at [SNAPSHOT]. Covers what `coverage_analyzer` returns and how to decide whether each
function's output constitutes a gap. This is a decision guide, not a coverage.py manual.

---

## What `coverage_analyzer` Returns

`coverage_analyzer` emits a `CoverageGap[]` — one entry per function. Each entry carries:

| Field | Type | Meaning |
|---|---|---|
| `function_id` | `str` | `module.ClassName.method_name` or `module.function_name` |
| `line_coverage_pct` | `float` | Fraction of executable lines executed by any test (0.0–100.0) |
| `uncovered_branches` | `list[Branch]` | Branch objects with `(line, condition, direction)` for every branch not taken |
| `layer` | `str` | Pyramid layer assignment (see classification section below) |
| `tier` | `str \| None` | Populated by [SCORE], not [SNAPSHOT] — leave `None` at this node |

The tool reads from the existing `.coverage` file (or equivalent coverage artifact) in the repo
root. It does not run tests.

**If `.coverage` is missing:** do not attempt to run the test suite inline. Stop and direct the
caller:

> "No `.coverage` file found. Run the test suite first (`pytest --cov`), then re-invoke the audit."

Emit an empty `coverage_gaps: []` with `snapshot_status: "missing_coverage_file"` in the report
and continue to [SCORE] — do not abort the full pipeline.

---

## Three Orthogonal Coverage Metrics (P5 — Design §4)

The engine tracks three metrics that measure different failure modes:

| Metric | Catches | Computed by |
|---|---|---|
| **Line coverage** | Unexecuted code paths | `coverage_analyzer` at [SNAPSHOT] |
| **Mutation kill rate** | Weak or missing assertions | `mutation_runner` in `code-test-generator` (per-gap) |
| **Edge coverage** | Untested module-to-module integration paths | `edge_coverage_analyzer` at [EDGE-COV] |

[SNAPSHOT] produces **line coverage only**. Mutation kill rate is computed per-gap inside
`code-test-generator`, not here. Edge coverage is computed later at [EDGE-COV] via static AST walk and
runtime instrumentation.

A passing line-coverage score does not imply the other two metrics are acceptable. All three are
required for a valid audit (see §4 of the design doc). Do not draw conclusions about mutation or
edge coverage from data collected at this node.

---

## Layer Classification Heuristic

Each `CoverageGap` must be assigned a pyramid layer. The layer tells downstream nodes
(`code-test-generator`) what style of test is needed. Full layer definitions live in
`references/coverage-pyramid.md` — this section teaches the classification heuristic only.

Classify by asking, in order:

1. **Is the function decorated `@app.route`, `@activity.defn`, or `@click.command`, or does it
   read `request` / `os.environ` / `sys.stdin`?** → `mock-integration` (runtime boundary).
2. **Is it listed in `__init__.py` `__all__` or imported by tests or other packages?** →
   `contract` (logical boundary).
3. **Does it persist state (DB write, file write, queue publish) and the call is idempotent?** →
   `idempotency`.
4. **Does it validate or parse config (pydantic model, cross-field constraint)?** → `config`.
5. **Is it an internal helper called only within the same module?** → `unit`.
6. **Anything else** → `unit` (safe default; reviewer may reclassify).

For real-infrastructure tests (testcontainers, vcrpy), classification happens in `code-test-evaluator`,
not here. Mark those as `mock-integration` at [SNAPSHOT] and let [EDGE-COV] and `code-test-evaluator`
refine.

---

## Decision Criteria: What Counts as a Gap

A function's `CoverageGap` entry is a **reportable gap** when either condition holds:

**Condition A — line coverage below tier target:**

| Tier | Target | Source |
|---|---|---|
| `critical` | 95% | Design §10 |
| `standard` | 85% | Design §10 |
| `cold` | 70% | Design §10 |

> Note: tier is assigned by [SCORE], not [SNAPSHOT]. At this node, record the raw
> `line_coverage_pct` and leave `tier: None`. The gap classification (`is_gap: true/false`) is
> finalized after [SCORE] runs.

**Condition B — any uncovered branch in a `critical`-tier function:**

Even at 94% line coverage, if a function is tagged `critical` and has one or more entries in
`uncovered_branches`, it is a gap. Branch misses in `standard` or `cold` functions are reported
but do not independently trigger gap status unless Condition A also holds.

---

## Good vs Bad Example

**Gap — critical function at 80% line coverage:**

```
function_id:       "ingestion.chunker.split_text"
line_coverage_pct: 80.0
uncovered_branches: [(line=42, condition="len(text)==0", direction="true")]
layer:             "unit"
tier:              null   # assigned by [SCORE]
```

After [SCORE] assigns `tier: "critical"`, target = 95%. 80% < 95% → **gap**.

**Not a gap — cold function at 80% line coverage:**

```
function_id:       "utils.legacy_formatter.format_date"
line_coverage_pct: 80.0
uncovered_branches: []
layer:             "unit"
tier:              null   # assigned by [SCORE]
```

After [SCORE] assigns `tier: "cold"`, target = 70%. 80% ≥ 70% → **not a gap**.

Same raw percentage; different outcome because tier sets the bar.

---

## What This Node Must NOT Do

- Do not run tests or modify `.coverage` files.
- Do not assign tiers — that belongs to [SCORE].
- Do not run mutation testing — that belongs to `code-test-generator`.
- Do not compute edge coverage — that belongs to [EDGE-COV].
- Do not make priority decisions — collect and report; `generate` acts on the ranking.
