# Decision Memo — test-evaluate

> Artifact type: skill | Memo type: creation | Design doc: `.brainstorms/2026-04-28-test-strategy-improvements/design.md`

---

## What I want

A read-only classification skill that sits between `generate` and `integrate` in the test coverage pipeline. After `generate` has produced a suite of mocked-integration tests, `evaluate` inspects each module in the covered set, detects whether its external dependencies cross logical or runtime boundaries, scores the replacement value of each mock, and emits a per-module `IntegrationStrategy` document that tells `integrate` exactly which mocks to convert, with which lifecycle pattern, and why.

The skill is analysis-only. It never writes test code, never modifies source, and never spins up real services. Its only output is documentation — one `IntegrationStrategy` per module — surfaced as a soft-gated PR so a reviewer can comment asynchronously while the engine continues.

This skill stays separate from `generate` (which writes tests under mock-by-default) and `integrate` (which converts mocks to real services). Boundary analysis is its own distinct concern.

---

## Why Claude needs it

Without this skill, Claude has no systematic method for deciding which mocks should be replaced with real integration tests. The two failure modes observed in practice:

1. **Over-mocking:** Claude mocks every external dependency by default (correctly, per `generate`'s mock-by-default policy), then never revisits the classification. The final test suite has near-zero real integration coverage, serialization quirks and real DB constraints go untested, and edge coverage of cross-module call-graph edges stays low.

2. **Over-real-integrating:** When asked to add real integration tests without a classification step, Claude attempts to spin up real services for every external call — including low-value internal helpers — producing expensive, slow, and flaky test suites with no prioritization.

The root cause is the same in both cases: Claude has no boundary detection heuristic, no replacement-value scoring formula, and no lifecycle pattern assignment logic. Without `evaluate`, the transition from "mocked suite" to "real integration suite" is driven by ad-hoc human judgment on each individual test, which is inconsistent and unscalable.

`evaluate` closes this gap by providing Claude with a deterministic classification workflow, a two-tier boundary detection rule, a scoring formula, and a lifecycle pattern table — all sourced from design doc decisions that were pressure-tested during the brainstorm.

---

## Injection shape

- **Workflow:** Per-module classification loop — five steps per module, iterated over the top-N critical modules.
- **Policy:** Analysis only, no code or test modification. Never produce test code. Never modify source. Never spin up services.
- **Domain knowledge:** Two-tier boundary detection via `__init__.py` `__all__` inspection (logical tier) and decorator/IO-pattern grep (runtime tier). Lifecycle pattern table loaded from design doc. Boundary-category reference files loaded on-demand per module category.

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| `IntegrationStrategy` document (per module) | N (one per classified module) | No | Tells `integrate` which mocks to replace, with which lifecycle pattern, and why |
| Soft-gated PR (classification doc bundle) | 1 | No | Queues reviewer async feedback on mock-vs-real classification decisions |

---

## Flow graph

```
CoverageState (post-generate)
  ↓
[LOAD] boundary detection rules + lifecycle pattern table
  ↓
for each module in top-N (by criticality):
  ↓
  [DETECT] boundary tier (logical / runtime / internal)
  ↓
  [IDENTIFY] mocked dependencies in tests
  ↓
  [SCORE] replacement value: boundary_tier × external_dependency_risk × current_mock_coverage_gap
  ↓
  [ASSIGN] lifecycle pattern from category table
  ↓
  [EMIT] IntegrationStrategy for module
  ↓
[GATE] open PR with IntegrationStrategy bundle — soft gate (queued review)
  ↓
IntegrationStrategy → integrate
```

---

## Node specifications

**[LOAD]** — Load: `rules/evaluate-constraints.md` (always), `references/real-integration-checklist.md`, lifecycle pattern table from design doc cross-cutting section. Do: establish read-only constraint; load boundary detection rules; load lifecycle pattern table. Don't: load test files or source for modification. Exit: proceed to per-module loop.

**[DETECT]** — Load: `references/boundary-<category>.md` for the relevant category (db, api, queue, file, cli). Do: grep `__init__.py` for `__all__` exports (logical tier); grep source for `@app.route`, `@activity.defn`, `@click.command`, and reads of `request`/`os.environ`/`sys.stdin` (runtime tier). Do: classify each function as boundary (logical), boundary (runtime), or internal. Don't: re-classify internal functions as boundary unless a grep-detectable signal is present. Exit: classification record per function in module.

**[IDENTIFY]** — Load: `CoverageState` (mocked test references for this module). Do: enumerate all mocked external dependencies in tests covering this module; record which mock corresponds to which boundary function. Don't: evaluate mock correctness or test quality — that is `audit`'s concern. Exit: mock inventory per module.

**[SCORE]** — Load: none (formula is inline). Do: compute `replacement_value = boundary_tier × external_dependency_risk × current_mock_coverage_gap` for each mocked dependency. `boundary_tier`: runtime > logical > internal (numeric weights: 3, 2, 0 — internal always excluded). `external_dependency_risk`: DB > external API > queue > file > CLI (weights: 5, 4, 3, 2, 1). `current_mock_coverage_gap`: fraction of boundary branches currently covered only by mocked tests (0.0–1.0). Don't: invent risk weights not in the formula; don't score internal functions. Exit: ranked list of mock-replacement candidates per module.

**[ASSIGN]** — Load: `references/lifecycle-patterns.md`. Do: for each candidate, pick exactly one lifecycle pattern from the category table (transaction rollback / schema-per-test / vcrpy / ephemeral container). Match category: DB → transaction rollback (or schema-per-test if DDL/auto-commit); external APIs → vcrpy; whole-system / queue → ephemeral container. Don't: assign multiple patterns to the same dependency; don't invent patterns not in the table. Exit: `IntegrationStrategy` document draft for this module.

**[EMIT + GATE]** — Load: `templates/integration-strategy.md`. Do: write `IntegrationStrategy` document for the module (which mocks to replace, with which pattern, why, replacement_value score). After all modules in top-N are classified: bundle all `IntegrationStrategy` docs into a PR, open it, notify reviewer. Don't: wait for reviewer — soft gate, work is complete. Don't: write any test code or modify source. Exit: handoff to `integrate`.

---

## Entry gates

| Transition | Gate |
|---|---|
| Start → LOAD | `CoverageState` exists and contains at least one module with mocked-integration tests (post-generate) |
| DETECT → IDENTIFY | Module has at least one function classified as boundary (logical or runtime); internal-only modules are skipped |
| IDENTIFY → SCORE | Mock inventory is non-empty (at least one mocked external dependency found) |
| SCORE → ASSIGN | At least one candidate has `replacement_value > 0` (boundary tier > 0 and external_dependency_risk > 0) |
| ASSIGN → EMIT | Lifecycle pattern assigned for each candidate |
| EMIT → [soft gate PR] | All top-N modules processed; `IntegrationStrategy` documents written |
| PR open → done | Soft gate: reviewer feedback queued asynchronously; engine does not wait |

---

## Edge cases considered

| Edge case | Handling |
|---|---|
| Top-N cutoff: what is N? | Creator decides based on project size. The skill does not hardcode N — it must be a configurable parameter (default: all critical-tier modules from `AuditGapReport.priority_ranking`). |
| Revisiting prior IntegrationStrategy docs on re-run | Unresolved — creator decides whether to re-classify all modules or only newly-changed ones. Recommendation: re-classify modules whose source changed since last `evaluate` run; preserve prior strategy for unchanged modules. |
| Module has only internal functions (no boundary) | Skip — do not emit `IntegrationStrategy` for this module. Log as "no boundary functions detected — no real integration needed." |
| Mocked dependency resolves to an internal function (not external) | Score as 0 (boundary_tier = 0 for internal). Exclude from `IntegrationStrategy`. Surface as a warning: "mock targets internal function — likely over-mocking in `generate`." |
| Multiple lifecycle patterns plausible for one dependency (e.g., DB with auto-commit) | Apply decision rule from lifecycle pattern table: prefer transaction rollback; use schema-per-test only when transactions don't isolate. One pattern per dependency — no exceptions. |
| Boundary function re-classification on re-run | Grep-detectable: if a function was added to `__all__` or received a decorator since last run, re-classify as boundary. Quarterly audit re-greps all boundary callers. |
| Module has no mocked tests (tests already use real services) | Skip IDENTIFY → SCORE → ASSIGN. Emit a note: "module already uses real integration tests — no replacement needed." |

---

## Companion files anticipated

**Always-loaded (every run):**
- `rules/evaluate-constraints.md` — loaded at LOAD node. Enforces: analysis only, no code/test modification, no real service spin-up.

**References (loaded per module category during DETECT/ASSIGN):**
- `references/boundary-db.md` — DB boundary detection patterns and lifecycle assignment.
- `references/boundary-api.md` — HTTP/REST boundary detection patterns and vcrpy assignment.
- `references/boundary-queue.md` — Queue/worker boundary detection and container assignment.
- `references/boundary-file.md` — File I/O boundary detection patterns.
- `references/boundary-cli.md` — CLI boundary detection and lifecycle assignment.
- `references/external-lib-policy.md` — Policy for third-party library mocks vs. real calls.
- `references/real-integration-checklist.md` — Pre-conditions for recommending real integration.
- `references/lifecycle-patterns.md` — Lifecycle pattern table (verbatim from design doc cross-cutting).

**Templates:**
- `templates/integration-strategy.md` — Output document schema for per-module `IntegrationStrategy`.

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `test-generate` | consumes from | `CoverageState` (post-generate, with mocked-integration tests in place); pydantic schema from `ai-synapse/tools/testing/schemas.py` |
| `test-integrate` | produces for | `IntegrationStrategy` document per module — specifies which mocks to replace, which lifecycle pattern to use, and why |
| `ai-synapse/tools/testing/schemas.py` | consumes from | Shared pydantic models for `CoverageState` and `IntegrationStrategy` handoff contracts |

---

## Open questions

1. **Top-N cutoff:** What default value of N should the skill use when not explicitly configured? Options: all critical-tier modules, top 20 by `replacement_value`, or a time-budget-based cutoff. Creator decides — note that `audit`'s `PriorityRanking` provides the tier data.

2. **Re-run behavior:** On a second `evaluate` run after some modules have already been classified, should the skill re-classify all modules from scratch, or preserve prior `IntegrationStrategy` for unchanged modules and only classify newly-changed or newly-added ones? The notepad leaves this to the creator — the recommendation above (re-classify on source change, preserve otherwise) is advisory.
