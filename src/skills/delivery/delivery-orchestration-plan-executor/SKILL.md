---
name: delivery-orchestration-plan-executor
description: "Use when the user signals start building, /build, execute the plan, ship this, or asks to deliver a multi-slice plan end-to-end. Not for single-task edits, research loops, or throughput-only parallel dispatch."
domain: delivery
subdomain: orchestration
scope: plan
role: executor
status: stable
tags: [orchestration, tdd, sequential-dispatch, subagent-loop, resumable]
user-invocable: true
argument-hint: "[plan-source or empty for ambient context]"
---

# delivery-orchestration-plan-executor

You become the manager. The main agent holds the outer loop — decompose plan into slices, dispatch one subagent per slice with TDD discipline injected, ingest the closeout, mutate the plan, repeat. Subagents do the inner Ralph loop and emit a structured closeout; they never write to plan or lessons. The filesystem holds the rolling state (`.delivery/`) so a compaction or interrupt cannot lose progress — any next session resumes by reading the closeout trail.

## MUST (every turn)
- Record position: `Position: [node-id] — <context>`. Without this, a compaction or interrupt mid-loop cannot resume cleanly — the next turn doesn't know which node it was in.
- Sequential dispatch only — one subagent in flight at a time, unless escape-hatch conditions hold (see `references/slice-decomposition-heuristics.md`). Concurrent dispatch is the leading cause of plan-divergence in this loop.
- Inject `delivery-execution-slice-contract`, `delivery-execution-tdd-contract`, and `delivery-orchestration-closeout-schema` into every subagent prompt by reference name. Without these, the subagent has no test-first discipline, no iteration obligation, and no closeout shape.
- After each closeout, route through `delivery-orchestration-replan-contract` before picking the next slice. Skipping replan means lessons and plan drift compound silently.
- Log every plan/INDEX.md or lessons.md edit in `.delivery/plan/CHANGELOG.md` in the same tick. A diff without an entry is an audit-trail break.

## MUST NOT (global)
- NEVER restate protocol bodies inline. Reference by name only. Inlining drifts from the protocol of record.
- NEVER let a subagent write to `.delivery/plan/`, `.delivery/lessons.md`, or any slice frontmatter — halt and escalate on detection. This invariant is what makes the audit trail trustworthy.
- NEVER auto-decompose `delivery-plan-writer` stories when present — they are authoritative. Re-decomposition breaks Model-C linkage to the spec surface.
- NEVER proceed past `[PRE-FLIGHT]` failures (no `.delivery/` writability, no discoverable test framework, zero decomposable slices) — `tdd-contract` is unenforceable without these.
- NEVER dispatch without all 8 prompt slots populated per `delivery-orchestration-dispatch-contract`. Missing slots produce subagents that improvise the contract.

## Wrong-Tool Detection
- **Throughput-focused, no TDD discipline needed** → redirect to `/parallel-agents-dispatch` (legacy; this skill is the canonical TDD-disciplined replacement).
- **Optimize a single target against a quality bar** → redirect to `/optimization-process-researcher` (sibling; same dispatch shape, different intent).
- **Decompose a plan but not execute it** → redirect to `/delivery-plan-writer` or `/docs-implementation-writer`.
- **Improve a single existing file with no plan** → handle directly, no skill needed.

## Progress Tracking

At `[CONFIRM]` (after WP list approved), create one task per slice:
```
TaskCreate per slice — subject="Slice <id>: <one-line>", status=pending
TaskUpdate to in_progress at [DISPATCH], completed at green closeout, blocked on N=2 or M=3 cap
```

## Entry

### [NEW] Fresh or resume
Do:
  1. Wrong-tool check — if redirect applies, stop.
  2. Probe `.delivery/closeouts/` — if non-empty, this is a resume: skip [INGEST-PLAN]/[DECOMPOSE]/[CONFIRM] and jump to [PICK-NEXT-SLICE] after reconstructing slice statuses from closeout trail.
  3. Fresh runs → [INGEST-PLAN].
Don't: silently re-decompose when a closeout trail already exists — that loses prior progress.
Exit:
  → [INGEST-PLAN] : fresh run
  → [PICK-NEXT-SLICE] : closeout trail found

## Flow

### [INGEST-PLAN]
Brief: Determine the plan source. Tickets win over context.
Do:
  1. If `delivery-plan-writer` stories exist at `.delivery/stories/TAG-NNN-*.md` with a `STORIES.md` manifest → use as authoritative WP list (path-reference only, no copy).
  2. Else → gather ambient context (chat, doc, rough plan passed as arg).
Don't: re-decompose tickets; copy ticket bodies into `.delivery/`.
Exit: → [DECOMPOSE]

### [DECOMPOSE]
Load: `references/slice-decomposition-heuristics.md`
Brief: Materialize into slice-shaped WPs. A slice is leaf-WBS (≡ story); not epic, not task.
Do:
  1. Ticketed mode: build `.delivery/plan/INDEX.md` referencing FR-NNN dirs.
  2. Free-form mode: decompose into slices, write one `.delivery/plan/wp-<id>.md` per slice, then INDEX.md.
  3. Apply slice-size bounds from heuristics — refuse to dispatch a slice that can't be validated by one test.
Don't: dispatch yet. Materialize first; dispatching from in-memory plan loses resumability.
Exit: → [CONFIRM]

### [CONFIRM]
Brief: One gate — user approves the WP list before unattended loop begins.
Do: present INDEX.md; await Y/adjust. On adjust → update INDEX.md, re-present.
Don't: auto-proceed; the loop is unattended after this gate, so confirmation is the only steering moment.
Exit: → [PRE-FLIGHT]

### [PRE-FLIGHT]
Brief: Three hard checks; halt loud on any failure.
Do:
  1. `.delivery/` writable (create if absent).
  2. Decomposition yields ≥1 slice.
  3. Test framework discoverable (lockfile, config) — without this, `tdd-contract` is unenforceable.
Don't: paper over a failed check with a fallback; the loop's correctness depends on all three.
Exit: → [PICK-NEXT-SLICE]

### [PICK-NEXT-SLICE]
Brief: Walk INDEX.md in dependency order; pick first eligible.
Do: select first un-dispatched slice whose `depends_on` are all green. If none eligible but some blocked → escalate (blocked-dep). If none and all closed → [TERMINATION].
Don't: pick a slice whose dependency is still in-flight or failed — that violates the sequential invariant.
Exit:
  → [DISPATCH] : eligible slice picked
  → [TERMINATION] : all closed
  → escalate : blocked dependency, user input required

### [DISPATCH]
Brief: Apply `delivery-orchestration-dispatch-contract`. Pre-dispatch checks gate everything.
Do:
  1. Validate slice file against `delivery-execution-slice-contract` — refuse on malformation.
  2. Bundle all 8 prompt slots (slice_assignment, slice_id, attempt_number, dependency_closeouts distilled, prior_attempt_closeouts, lessons_md, worker_protocols, model).
  3. Select model explicitly — sonnet default; opus only when slice flags architectural complexity.
  4. Dispatch ONE subagent. The subagent runs `tdd-contract` (Ralph loop, iteration cap default 10) and emits per `closeout-schema` (dual-target: file then inline).
Don't: dispatch with any slot missing; dispatch without explicit model; dispatch a second subagent before the first closeout is ingested.
Exit: → [INGEST-CLOSEOUT]

### [INGEST-CLOSEOUT]
Brief: Parse + validate the closeout against `closeout-schema`.
Do: parse YAML, verify required fields, check `files_modified ⊆ slice.touches`, check `pass ⇒ outcome_test_path populated and in tests_added`. On malformed YAML → retry once with parse-error hint; second malformation → escalate.
Don't: ingest a closeout that writes outside declared scope — that's a `slice-contract` violation, not a warning.
Exit: → [REPLAN]

### [REPLAN]
Brief: Apply `delivery-orchestration-replan-contract`. Main agent is the sole writer to plan/ and lessons.md.
Do:
  - On `pass`: mark slice complete in INDEX.md, append distilled lessons, evaluate `next_moves`.
  - On `blocked`/`failed`/`rejected`: increment attempt counter; at N=2 → mark blocked + escalate.
  - On `plan_drift_detected`: edit unstarted slices or re-decompose per drift reason.
  - Write a `CHANGELOG.md` entry for every plan/lessons mutation, same tick.
  - At M=3 replan cycles on one slice → halt + escalate ("plan likely fundamentally misframed").
Don't: delete closed-out slice files (mark superseded); edit closeout files; apply non-append edits to lessons.md.
Exit:
  → [PICK-NEXT-SLICE] : loop continues
  → escalate : N=2 or M=3 cap reached

### [TERMINATION]
Load: `references/final-summary-format.md`
Brief: Emit structured final summary; preserve all `.delivery/` files for resume/audit.
Do: produce the US-1 final summary (slice rollup counts, lessons tail, INDEX.md pointer, exit reason enum).
Don't: delete `.delivery/`; suppress lessons; emit free-form prose summary.
Exit: → [END]

### [END]
Do:
  1. Print final summary verbatim.
  2. Surface exit reason: `all_slices_green` | `escalated_blocked` | `escalated_replan_cap` | `user_interrupt`.
Don't: auto-launch follow-up work; the user owns the next move after a terminated run.
