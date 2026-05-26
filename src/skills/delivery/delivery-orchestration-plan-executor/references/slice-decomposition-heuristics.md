# slice-decomposition-heuristics

Loaded at `[DECOMPOSE]` and consulted when the sequential-default invariant is under pressure (escape-hatch). Decomposition mistakes are the root of most failed runs — under-sized slices waste dispatches; over-sized slices fail TDD discipline and produce unscoped diffs.

## What a slice is

A slice is the **leaf** of work-breakdown — equivalent to a story / FR-NNN ticket. One slice ≡ one validable end-goal ≡ one subagent dispatch ≡ one closeout. Epics and tasks are **planning vocabulary** for grouping and ordering; they are never dispatched.

| Term | Used for | Dispatchable? |
|---|---|---|
| Initiative / epic | Grouping multiple slices toward a higher-level outcome | No |
| Slice / story / FR-NNN | One validable end-goal, one subagent | **Yes — the only dispatch unit** |
| Task / subtask | Internal step inside one slice's TDD execution | No |

If you find yourself wanting to dispatch an "epic" — re-decompose it into slices first. If you find yourself wanting to dispatch a "task" — it belongs inside an existing slice.

## Slice-size bounds

| Bound | Test | Failure mode if violated |
|---|---|---|
| Lower | Can the validable outcome be expressed as one failing test that meaningfully exercises the change? | One-line edits don't justify the dispatch overhead and produce noisy closeout trails. |
| Upper | Can one subagent execution complete the slice with the iteration cap (default 10)? Does the diff touch ≥1 schema/config + code + test as a coherent unit? | Subagent hits the cap and emits `blocked`; main agent burns replan cycles trying to re-frame an oversized slice. |

**"Too big" tripwires:**
- The slice description contains the word "and" connecting two distinct outcomes → split.
- The slice spans more than one bounded context (auth + billing, frontend + backend pipeline) → split.
- The slice's `touches` list grows past ~5 files in distinct modules → reconsider.

**"Too small" tripwires:**
- The outcome is "rename X to Y" or a single config-key tweak → fold into the nearest substantive slice.
- The failing test would be a pure restatement of the existing test → there is no new behavior to validate.

## When to re-decompose mid-run (vs. escalate)

Re-decompose via `replan-contract` when:
- A closeout's `plan_drift_detected: true` with a concrete `drift_reason` that names which slice boundaries are wrong.
- A slice hits attempt cap N=2 because the validable outcome itself was mis-framed (not because the implementation is hard).

Escalate to user when:
- M=3 replan cycles on a single slice — plan is fundamentally misframed, no local edit will fix it.
- A dependency is blocked and the blocker is outside the plan's scope (external service down, missing decision).
- Re-decomposition would require touching the spec surface (`docs/.../FR-NNN/`) — that is `write-story`'s authority, not this skill's.

## Escape-hatch — when parallel dispatch is permitted

Sequential dispatch is the invariant. Parallel is permitted only when **all three** conditions hold for the candidate slices:

1. **Zero `touches` overlap** — declared `touches` sets of the candidate slices are disjoint. Any single file in two `touches` lists disqualifies parallel.
2. **Zero `depends_on` coupling** — neither slice depends on the other, directly or transitively.
3. **Explicit user authorization for this run** — the user must opt in by name to parallel dispatch for the run. Not a config flag, not a heuristic — an in-session affirmation.

If any condition is uncertain, default to sequential. The cost of one extra sequential dispatch is far below the cost of a write-conflict or plan-divergence incident.

## Slice-shape checklist (apply at materialization)

Before writing a slice file at `[DECOMPOSE]`, verify:
- [ ] One validable outcome stated in plain language, expressible as a single failing test.
- [ ] `touches` list is explicit and minimal — no wildcards, no whole-directory entries.
- [ ] `depends_on` is acyclic and references only sibling slice IDs.
- [ ] The slice is independent enough that its subagent prompt does not need to embed prior slices' code.
