---
name: delivery-orchestration-replan-contract
description: "Closeout-driven plan-surface mutation rules — firing signals, allowed/forbidden mutations, mandatory CHANGELOG audit trail, M=3 escalation bound (skill-overridable). Sits on synapse-memory-external-memory-contract."
domain: delivery
subdomain: orchestration
subject: replan
kind: contract
version: 1
status: stable
tags: [replan, plan-mutation, audit-trail, changelog, escalation-bound, append-only-lessons]
---

# Replan Contract

This protocol defines exactly what the main agent does between ingesting a closeout and issuing the next dispatch. Without it, the main agent silently mutates plan files with no log, subagents may corrupt the audit trail via unauthorized writes, lessons.md is rewritten or trimmed (destroying compounding), and stuck slices produce infinite replan loops because no skill states the escalation bound. This contract sets the write-rule for the two-surface working memory: who may mutate plan/ and lessons.md, what mutations are allowed, what must be logged, and when to halt.

This protocol **sits on** `synapse-memory-external-memory-contract`. The plan surfaces (`.delivery/plan/INDEX.md`, `.delivery/lessons.md`) ARE the working memory; this protocol is the delivery-context write-rule operationalizing parent Rules 2 (skill-owned writes), 3 (read-before-reason), and 4 (write-after-turn).

## Contract Rules

1. **Authority — main agent ONLY.** Subagents propose via closeout fields (`next_moves`, `plan_drift_detected`, `lessons_learnt`). The main agent disposes — accept, transform, or discard with reason. Subagents NEVER mutate plan surfaces directly. Any subagent-originated plan write is an architectural break (violation **e**).

2. **Trigger — once per closeout ingest.** AFTER closeout validated against `delivery-orchestration-closeout-schema`, BEFORE the next dispatch is issued. The replan tick may be a no-op (no firing signals); it still runs to check.

3. **Read-before-reason.** Re-read `.delivery/plan/INDEX.md` and `.delivery/lessons.md` fresh at the start of every replan tick. Do not rely on in-context memory of their content — a user or external process may have edited them.

4. **Firing signals.** Evaluate all of these against the just-ingested closeout:

   | Signal | Source field | Default action |
   |---|---|---|
   | `plan_drift_detected: true` | `plan_drift_detected` + `plan_drift_reason` | Edit slice body / re-decompose / mark blocked per drift reason |
   | `next_moves` non-empty | `next_moves` list | Evaluate each: add new slice, merge into existing, or discard with reason |
   | `validation_result: blocked` | `validation_result` + `blocked_reason` | Re-decompose if too-big; mark blocked + escalate if real blocker |
   | `validation_result: failed` / `rejected` | `validation_result` | Increment attempt counter; when count exceeds N=2 (per dispatch-contract) → mark blocked + escalate |
   | `lessons_learnt` non-empty | `lessons_learnt` list | Append to `.delivery/lessons.md` under `### Slice <id> attempt <N>` header |

5. **Allowed mutations** (each MUST log to CHANGELOG in the same tick):
   - Add a new slice to `plan/INDEX.md` (new wp-<id>.md created in free-form mode).
   - Reorder unstarted slices in `plan/INDEX.md`.
   - Mark a slice status as `blocked`, `deferred`, or `superseded`.
   - Re-decompose an existing slice into N smaller slices (original marked `superseded` — NOT deleted).
   - Edit body or frontmatter of an **unstarted** slice (no prior dispatch).
   - Append to `.delivery/lessons.md`.
   - Update a slice's frontmatter status (e.g., `in_progress` → `pass`).

6. **Forbidden mutations** — each requires immediate halt and escalation:

   | ID | Violation |
   |---|---|
   | (a) | Deleting closed-out slice files — use `superseded`; files are permanent audit artifacts |
   | (b) | Editing or deleting any file in `.delivery/closeouts/` — append-only audit trail |
   | (c) | Editing a slice's assignment body after its first dispatch (exception: direct drift response with prior assignment+closeout preserved) |
   | (d) | Non-append edits to `.delivery/lessons.md` (rewriting, trimming, reordering existing entries) |
   | (e) | Any plan write by a subagent — architectural break, violates `synapse-memory-external-memory-contract` Rule 2 |

7. **Audit — CHANGELOG entry mandatory, same tick.** Every mutation to `.delivery/plan/` or `.delivery/lessons.md` MUST produce a `.delivery/plan/CHANGELOG.md` entry BEFORE the next dispatch is authorized. The CHANGELOG is append-only — no entry is ever edited or deleted.

   **Entry format:**

   ```markdown
   ## <ISO-8601 timestamp>
   - **Triggering closeout:** `<closeout filename>`
   - **Signal type:** <plan_drift_detected | next_moves | blocked | failed | rejected | lessons_learnt>
   - **Change:** <one-liner describing the mutation>
   - **Reason:** <why the main agent made this call>
   ```

## Out-of-Band Edit Handling (RP-R1)

If the file hash of `plan/INDEX.md` or `lessons.md` has changed between ticks but no CHANGELOG entry attributes the change, the main agent MUST:

1. Treat the change as a user intervention (the user is authoritative over their plan files).
2. Accept current file content as the new baseline.
3. Write a CHANGELOG entry attributing the change: `out-of-band edit detected — accepted as user intervention` with the current timestamp.
4. Continue the run from the new state.

This prevents false-positive halts when the user manually corrects the plan between ticks. The CHANGELOG remains the canonical audit trail — silent drift is impossible.

## Escalation Bound (RP-M1)

**M=3 replan cycles on a single slice** is the default escalation threshold. Hitting M cycles on the same slice signals the plan is fundamentally misframed for that slice — main agent halts and escalates to the user with the message: *"plan likely fundamentally misframed."*

**Skill-overridable** (parallel to TC-B1 — the TDD iteration cap is also skill-overridable). The orchestrator skill (`delivery-orchestration-plan-executor`) MAY override M at runtime via the protocol-injection prompt. NOT a hard protocol constant. Consuming skills with different needs (optimization-process-researcher, e.g., may tolerate more replan cycles) override explicitly rather than fork the protocol.

**M is distinct from N**: N (per `delivery-orchestration-dispatch-contract`) counts raw dispatch attempts on a slice (cap N=2). M counts replan-contract firings on the same slice across all attempts. A slice can hit M without hitting N if each attempt triggers a replan that re-frames rather than re-dispatches.

## Violation Signatures

| ID | Violation | Response |
|---|---|---|
| (a) | `plan/` or `lessons.md` diff detected without a CHANGELOG entry | Silent mutation — halt; backfill the CHANGELOG entry; then escalate |
| (b) | Subagent closeout or response contains plan-surface writes | Architectural break — halt and escalate before proceeding |
| (c) | In-place edit or delete detected in `closeouts/` | Halt and escalate |
| (d) | A closed-out (status: pass) slice file has been deleted | Halt; attempt restore from git history; escalate |
| (e) | Replan cycle count on a single slice exceeds M | Escalate per the escalation bound; do not continue dispatching that slice |

## Canonical Ownership (RP-B1)

This protocol owns the full **ingest-to-mutation** flow:

1. Main agent receives closeout (inline YAML + persisted file).
2. Main agent validates against `delivery-orchestration-closeout-schema`.
3. **This protocol fires** — evaluate firing signals, execute allowed mutations, write CHANGELOG entries, curate lessons.md.
4. Main agent signals readiness for next dispatch (`delivery-orchestration-dispatch-contract` runs its pre-flight after this protocol exits).

`delivery-orchestration-closeout-schema` defines **what** the closeout contains. This protocol defines **what the main agent does with it**. Closeout-schema cross-references this protocol for ingestion semantics — that flow is not duplicated there.

## Why This Protocol Is Necessary

1. **Authority split.** The boundary between "subagent proposes" and "main agent disposes" must be stated once, centrally, unambiguously. Embedding it in a skill body makes it invisible to other skills that may consume the same plan surfaces.
2. **Audit trail.** The CHANGELOG requirement creates an immutable record. Without a protocol mandating it, individual skills omit under time pressure.
3. **Escalation bound.** M is a cross-skill constant with overridability. Without a protocol naming it, each skill invents an arbitrary number or omits the bound entirely — producing unbounded replan loops.
4. **Append-only lessons.** The lessons surface compounds across slices. Non-append mutations (rewrites, trims) destroy compounding. A protocol-level prohibition is the only reliable enforcement mechanism.

## Edge Cases

| Edge case | Handling |
|---|---|
| No firing signals (all fields benign) | No-op tick; no mutations, no CHANGELOG entry required |
| `next_moves` contains a duplicate of an existing slice | Discard with reason logged in CHANGELOG |
| Slice decomposed into N slices that conflict with each other | Add sequentially with `depends_on` set; do not dispatch simultaneously |
| Subagent writes to a plan file mid-tick | Violation (b)/(e) — halt + escalate; refuse closeout until reverted |
| User edits plan mid-tick (hash drift detected on next read) | RP-R1: treat as user intervention, accept, write CHANGELOG attribution |
| M hit on slice but user wants to continue | User must explicitly override M for this run (skill-overridable); continuation requires explicit instruction |
| `lessons.md` grows very large within a run | No in-run trimming; end-of-run hook in `delivery-orchestration-plan-executor` compresses to a run summary while preserving raw at `.delivery/lessons.raw.md` |

## Failure Reporting

When a violation is detected, the main agent MUST immediately emit the following tag using the `synapse-observability-failure-reporting-schema` format, then halt or escalate per the response column in the Violation Signatures table:

```
PROTOCOL FAILURE: delivery-orchestration-replan-contract <slice_id> [violation_id reason]
```

## Injection

Loaded by `delivery-orchestration-plan-executor` at the `[REPLAN]` node, after every closeout ingestion. The protocol governs the main agent's mutation authority over plan surfaces — subagents never see this contract directly; it constrains what the orchestrator may do with their proposals.

## Linkage

- **Sits on** `synapse-memory-external-memory-contract` — plan/ and lessons.md ARE the working memory; this protocol is the write-rule.
- **Consumes output of** `delivery-orchestration-closeout-schema` — owns the full ingest-to-mutation flow (RP-B1 / CL-P1).
- **Sequences with** `delivery-orchestration-dispatch-contract` — replan completes (CHANGELOG written, mutations applied) before next dispatch is authorized.
- **Consumed by** `delivery-orchestration-plan-executor` — uses M cap (skill-overridable) and curates lessons.md for injection into subsequent dispatches.
