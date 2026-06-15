---
name: delivery-execution-slice-contract
description: "Normative contract for what a slice is and what its assignment file must contain — enforced by the main agent before every subagent dispatch in delivery-orchestration-plan-executor"
domain: delivery
subdomain: execution
subject: slice
kind: contract
version: 1
status: stable
tags: [slice, dispatch-gate, validation, vertical-slice, leaf-wbs]
---

# Slice Contract

A slice is the **leaf** of work-breakdown. One slice ≡ one validable end-goal ≡ one subagent dispatch ≡ one closeout. Without this contract, the main agent has no enforcement point before dispatch — it ships under-specified slices, subagents cannot determine "done," and downstream protocols (`tdd-contract`, `closeout-schema`) silently degrade because they assume a `validable_outcome` that may not exist. This contract sets the shared language for scope, done, and identity across main agent and subagents.

## Contract Rules

1. **Slice ≡ story ≡ leaf-WBS.** A slice is the only dispatchable unit. Initiative, epic, and task are planning vocabulary for grouping and ordering — they are NEVER dispatched. If you find yourself dispatching an "epic," re-decompose first. If you find yourself dispatching a "task," fold it into a slice.

2. **Four required fields on every slice file.** Whether the slice file is a `write-story` `story.md` or a free-form `.delivery/plan/wp-N.md`, it MUST contain all four with non-empty values:

   | Field | Type | Purpose |
   |---|---|---|
   | `slice_id` | stable string | Cross-reference key for closeouts and INDEX.md |
   | `validable_outcome` | string | Acceptance criterion expressible as one failing test |
   | `touches` | list of paths | Files this slice may read or write — the boundary for `files_modified` validation |
   | `depends_on` | list of slice_ids (may be empty) | Slices that must be closed-out green before this slice can dispatch |

3. **`validable_outcome` is canonical to slice-contract.** When the slice is sourced from `write-story`, the main agent maps `acceptance_criteria` → `validable_outcome` at slice-assignment time. The mapping is the main agent's responsibility; if it doesn't happen, the slice is non-conformant.

4. **Slice files are read-only to subagents (Model C linkage).** Only the main agent writes to slice files. Subagents write code, tests, and their own closeout — nothing else. This invariant is what makes the parallel escape hatch safe and the audit trail trustworthy.

5. **Size bounds.**
   - **Lower:** large enough that a TDD test meaningfully validates the outcome. Not a rename, not a one-line config tweak.
   - **Upper:** small enough that one subagent execution completes within the iteration cap (default 10). If the subagent would need to dispatch its own subagents, the slice is too big — re-decompose.

6. **Trigger moment.** Validation runs as the **first** pre-dispatch check inside `delivery-orchestration-dispatch-contract`. A failure aborts dispatch and routes the slice to `delivery-orchestration-replan-contract`.

## Compliance Signature

A slice is contract-compliant when **all** of these hold:

1. The slice file contains all four required fields with non-empty values.
2. The slice file exists at the path indexed in `.delivery/plan/INDEX.md` (precondition **SC-R2**).
3. After dispatch, the subagent's closeout reports `validation_result: pass` against the stated `validable_outcome`, and no nested subagent dispatch occurred.

## Violation Signatures

The main agent MUST treat any of the following as a contract violation and either refuse dispatch (pre-) or reject the closeout (post-):

| ID | Signature | Action |
|---|---|---|
| (a) | Slice file dispatched without a `validable_outcome` | Refuse dispatch; route to replan-contract |
| (b) | Closeout reports "couldn't determine done" or no test encodes the outcome | Reject closeout; route to replan-contract |
| (c) | Subagent attempted to dispatch its own subagents | Slice too big; reject closeout; re-decompose via replan-contract |
| (d) | Closeout `files_modified` includes paths outside declared `touches` | Reject closeout; route to replan for boundary tightening |
| (e) | Any of the four required fields is absent or empty | Refuse dispatch; route to replan-contract |
| (f) **SC-R1** | Slice file is malformed / unparseable | Hard halt; escalate to operator. A malformed file cannot be repaired by replan alone — operator must restore a valid file before the loop resumes |

## Preconditions

**SC-R2:** the slice file MUST exist at the path referenced by `.delivery/plan/INDEX.md`. A path mismatch halts the main agent with an "INDEX drift" audit error. It is NOT silently retried — the operator must reconcile INDEX.md before dispatch continues.

## Linkage (Model C)

| Surface | Writer | Reader | Mutability |
|---|---|---|---|
| Slice assignment file (`story.md` or `.delivery/plan/wp-N.md`) | Main agent ONLY | Subagent (read-only) | Frontmatter mutable by main agent; body mutable only via replan |
| `.delivery/plan/INDEX.md` | Main agent ONLY | Both | Main agent edits after ingesting closeouts |
| Code + tests | Subagent | Both | Normal source code |
| Closeout files | Subagent | Main agent | Append-only — each attempt is a new file |

## Failure Reporting

Violations of this protocol use the `synapse-observability-failure-reporting-schema` format:

```
PROTOCOL FAILURE: delivery-execution-slice-contract <slice_id> [violation_id reason]
```

## Injection

The orchestrator skill (`delivery-orchestration-plan-executor`) injects this protocol's body into the main agent's pre-dispatch context, and into the subagent prompt via the `{{worker_protocols}}` slot of `delivery-orchestration-dispatch-contract`. The main agent enforces (1) pre-dispatch (field presence, SC-R2); the subagent honors (3) read-only posture; the main agent enforces (3) post-closeout (`files_modified ⊆ touches`, no nested dispatch).
