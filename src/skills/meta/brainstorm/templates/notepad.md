# Brainstorm Notes — <topic>

<!--
  Notepad protocol:
  - Update this file BEFORE composing every response. Stale notepads lose context.
  - Threads use indexed IDs (T1, T2, ...) for unambiguous reference.
  - The memo is distilled ONCE at Done Signal from this notepad — do not draft incrementally.
  - At Done Signal, every thread must be in a terminal state. No `open`.
  - Aggressive distillation: if a concern belongs to a specific thread, put it in Zone 2 under that thread.
    Content stays in Zone 1 only when it genuinely spans 2+ threads.
-->

## Status

- **Phase:** A | B | DONE | PAUSED
- **Position:** [node-id] — <context>
- **Type:** decision | exploratory | problem | creative | planning
- **Anticipated shape:** Decision | Plan | Spec | Reframe | Decompose | Defer | Abandon
- **Turn count:** <n>
- **Hygiene flag:** <turn number when next [H] should fire, or "—">

## Lens Rotation State

- **Selected lenses:** Stakeholder, Alternative, <type-specific 1>, <type-specific 2>
- **Current thread under rotation:** <T-ID>
- **Lenses applied per thread:**

| Thread | Stakeholder | Alternative | <Lens 3> | <Lens 4> | Complete? |
|--------|-------------|-------------|----------|----------|-----------|
| T1     |             |             |          |          |           |
| T2     |             |             |          |          |           |

## Cross-cutting

<!-- Shared observations spanning 2+ threads. Only items that genuinely can't be assigned to one thread.
     If it has a home in one thread, distill it there instead. -->

## Process

<!-- Coaching observations, discarded alternatives, move reasoning.
     This is the brainstorm's "thinking" — does NOT transfer to the memo.
     Stays as the "why did we decide X" record.
     Append freely during all phases. -->

## Open / Orphaned

<!-- Unresolved session-level concerns. Must be empty before Done Signal.
     Move items here when they surface but don't yet have a home.
     Assign to a thread or resolve before [D]. -->

## Resolution Log

<!-- Timeline of thread closures. Turn number + final status + reason.
     Enables post-hoc review: "why did we decide T3 the way we did at turn 7?" -->

## Discarded Candidates

<!-- Moves, framings, options considered and rejected with reason. Prevents revisiting. -->

## Phase A Misses (if any)

<!-- Per admission protocol: if a first-order concern surfaces in Phase B,
     record what was missed, which turn, and which prior decisions need re-examination. -->

---

<!-- ═══════════════════════════════════════════════════════════════════
     ZONE 2 — Per-thread sections below this line.
     One section per thread, created as threads surface.
     Aggressive distillation: anything with a home in a thread goes here, not Zone 1.
     ═══════════════════════════════════════════════════════════════════ -->

## T1: <short title>
**Status:** open | resolved | discarded | deferred | decomposed
**Depends on:** <T-IDs, if any>

### Discussion
<!-- Concerns surfaced, options generated, pressure-test notes, resolution reasoning.
     Record which moves produced which insights. -->

### Key decisions
<!-- Resolved positions for this thread — self-contained enough for memo distillation. -->

### Verbatim blocks
<!-- VERBATIM -->
<!-- Structural content that must survive notepad→memo transfer exactly.
     Decision tables, comparison matrices, numbered lists. -->

<!-- Add T2, T3, ... as threads surface. Children of decomposed threads use dotted IDs: T5a, T5b, T5c. -->
