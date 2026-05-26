---
name: delivery-orchestration-closeout-schema
description: "YAML data shape every subagent emits at dispatch end — required fields, dual-target atomic write (file before inline), extends synapse-observability-execution-trace"
domain: delivery
subdomain: orchestration
subject: closeout
kind: schema
version: 1
status: draft
tags: [closeout, dual-target, audit-trail, resumable, extends-execution-trace]
---

# Closeout Schema

Without a normative closeout shape, each subagent invents its own output format — the main agent has no stable surface to parse, validate, or diff; resume after compaction fails because the file shape is unpredictable; lessons cannot be reliably extracted; the audit trail is ungrepable. Without the dual-target atomicity rule (file before inline), a compaction event between the subagent's file write and its inline emit silently drops the closeout, breaking resumability with no error signal. This schema fixes both problems with one contract: a required field table, and a write ordering invariant.

This schema **extends** `synapse-observability-execution-trace` — delivery-specific fields are layered on top of the parent's envelope. The body below documents the delta only; readers must consult the parent for the base trace fields.

## Contract Rules

1. **Dual-target atomic write (CL-R1).** Every dispatch produces **two** artifacts containing the same YAML body:
   - **File:** `.delivery/closeouts/<slice_id>-attempt-<attempt_number>.yaml`
   - **Inline:** YAML block appended to the subagent's response

   **Order is non-negotiable: file MUST be written first, then the inline block emitted.** A compaction or interrupt between the two writes leaves the file intact (recoverable); writing inline first risks losing the closeout entirely if the file write later fails.

2. **File-write failure halts the dispatch.** If the file write fails (path not writable, disk full, permission error), the subagent MUST halt immediately, surface the write failure, and NOT emit the inline YAML. The main agent treats any dispatch with no closeout file as `failed` — never as silent success.

3. **Required fields.** All fields are required unless marked conditional:

   | Field | Type | Constraints |
   |---|---|---|
   | `slice_id` | string | Matches the `slice_id` from the dispatched slice assignment |
   | `attempt_number` | integer ≥ 1 | Matches `{{attempt_number}}` slot from dispatch prompt |
   | `validable_outcome` | string | **Verbatim** copy from the slice assignment — no paraphrase |
   | `validation_result` | enum | `pass` \| `blocked` \| `failed` \| `rejected` |
   | `outcome_test_path` | string | **Required when `validation_result: pass`**; omit otherwise |
   | `iterations_used` | integer ≥ 1 | Ralph-loop iterations consumed before exit |
   | `files_created` | list[string] | All files created; empty `[]` if none |
   | `files_modified` | list[string] | Must be ⊆ slice's declared `touches` scope (from slice-contract) |
   | `tests_added` | list[string] | All test paths added or materially modified; MUST include `outcome_test_path` when `pass` |
   | `lessons_learnt` | list[string] | Forward-passable observations; empty `[]` if none |
   | `next_moves` | list[{summary, rationale, suggested_slice_id?}] | Proposed follow-ons for main-agent evaluation; empty `[]` if none |
   | `plan_drift_detected` | bool | `true` if subagent observed assignment-vs-reality drift |
   | `plan_drift_reason` | string | **Required when `plan_drift_detected: true`** |
   | `blocked_reason` | string | **Required when `validation_result: blocked`** |

4. **`validable_outcome` is verbatim.** The subagent MUST copy the outcome string from the slice assignment without paraphrase. Paraphrase is a contract violation (signature **d**) that signals the subagent did not faithfully read the brief.

## Compliance Signature

A closeout passes intake validation when **all** hold:

1. Well-formed YAML, all required fields present.
2. `pass` ⇒ `outcome_test_path` populated AND appears in `tests_added`.
3. `blocked` ⇒ `blocked_reason` populated.
4. `plan_drift_detected: true` ⇒ `plan_drift_reason` populated.
5. `files_modified` ⊆ slice's declared `touches` (cross-referenced with slice-contract).
6. `validable_outcome` is verbatim from the assignment.
7. Closeout file exists at `.delivery/closeouts/<slice_id>-attempt-<attempt_number>.yaml` with identical content to the inline block.

## Violation Signatures

Main agent rejects the closeout (routes to `delivery-orchestration-replan-contract`) on any of:

| ID | Condition | Signal |
|---|---|---|
| (a) | Missing `slice_id`, `validable_outcome`, or `validation_result` | Structural failure — request re-emit with parse-error hint |
| (b) | `pass` without `outcome_test_path` | Fabricated pass — also caught by `delivery-execution-tdd-contract`; escalate for human review |
| (c) | `files_modified` includes paths outside declared `touches` | Subagent overreach — route to replan |
| (d) | `validable_outcome` paraphrased rather than verbatim | Brief not faithfully read — treat as `rejected`; re-dispatch with stronger brief injection |
| (e) | Malformed YAML | Auto-retry **once** with parse-error hint in re-prompt; second malformation escalates to user (no unbounded retry loop) |

## Ingestion Semantics — Scoped Out

This protocol defines the **data shape** of a closeout and the **write contract** that produces it. It does NOT define what the main agent does after intake (mark slice complete, append lessons, evaluate `next_moves`, mutate plan, log to CHANGELOG). That logic is owned by `delivery-orchestration-replan-contract` (per **CL-P1** from brainstorm). Readers seeking the ingest-to-mutation flow must cross-reference that protocol.

## Extends `synapse-observability-execution-trace`

The parent at `synapse/protocols/observability/synapse-observability-execution-trace.md` defines the base trace envelope (agent identity, phases executed, agents dispatched, workflow decisions, precondition checks, context isolation). The fields above are **delivery-specific additions** layered on top. Do NOT duplicate parent definitions. A consumer of a closeout reads both protocols.

**Why extend, not fork:** forking would diverge the observability surface across delivery and synapse contexts and create two formats that tooling must understand. Extending preserves base-trace tooling and keeps the delivery surface purely additive.

## Edge Cases

| Edge case | Handling |
|---|---|
| File write fails before inline emit | Subagent halts; surfaces write failure; no inline YAML emitted; main agent treats as `failed` |
| Malformed YAML on first emit | Auto-retry once with parse-error hint; second malformation escalates to user |
| Subagent writes correct file with wrong `attempt_number` | Filename collision detected by main agent counting existing closeouts for the slice |
| `next_moves` references a nonexistent slice_id | replan-contract resolves; closeout-schema does not validate — treat as a loose proposal |
| `files_modified` includes untracked files outside `touches` | Violation (c) — overreach; route to replan |

## Failure Reporting

Violations of this protocol use the `synapse-observability-failure-reporting-schema` format:

```
PROTOCOL FAILURE: delivery-orchestration-closeout-schema <slice_id> [violation_id reason]
```

## Injection

The orchestrator skill (`delivery-orchestration-plan-executor`) injects this protocol's body into every subagent prompt via the `{{worker_protocols}}` slot of `delivery-orchestration-dispatch-contract`. The subagent writes (rules 1–4 producer side); the main agent validates (compliance + violation signatures) on intake before routing to replan.
