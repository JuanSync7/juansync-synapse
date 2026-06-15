# Decision Memo — delivery-execution-slice-contract

> Artifact type: protocol | Memo type: creation | Design doc: `.brainstorms/2026-05-22-plan-execution-vertical-slice-orchestration/design.md`

---

## What I want

A normative protocol that defines what a **slice** is, what its assignment file MUST contain, what constitutes a valid or violated slice, and when/by-whom the contract is enforced. The protocol is injected into the main agent (plan-executor skill) so it validates each slice's assignment file before dispatching a subagent on it.

A slice is the leaf dispatch unit in the vertical-slice orchestration system: one validable end-goal, one subagent dispatch, one closeout. The protocol sets the contract that the rest of the delivery system depends on — without it, main agent and subagents have no shared language for "done" or "scope."

---

## Why Claude needs it

Without this protocol the main agent has no enforcement point before dispatch. It will dispatch on underspecified slices (missing outcome, missing scope), leading to subagents that cannot determine done, produce untestable work, or overreach into undeclared files. The downstream tdd-contract and closeout-schema rely on `validable_outcome` being defined and consistent — if the slice file can be malformed, both contracts become unenforced and the delivery loop silently degrades.

---

## Injection shape

- **Policy:** judgment rules for the main agent on what to accept/reject/replan before dispatch.
- **Domain knowledge:** the canonical definition of a slice, its four required fields, size-bound heuristics, and all violation signatures.

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| Slice validation decision (pass/reject) | 1 per dispatch attempt | No | Main agent gate: proceed to dispatch-contract or route to replan-contract |

The protocol itself produces no files — it is a behavioral contract that governs the main agent's pre-dispatch gate, not a file-emitting workflow.

---

## Core definitions

### Slice definition

A **slice** is the leaf unit of dispatchable work:

- One validable end-goal (an acceptance criterion expressible as a failing test).
- Dispatchable to a single subagent in a single dispatch call.
- Closable in one closeout file.
- Equivalent to a **story / FR** in planning vocabulary.

Planning vocabulary (epic, initiative, subtask) is NOT dispatch vocabulary:

| Level | Dispatchable? | Role |
|---|---|---|
| Initiative | No | Top grouping |
| Epic | No | Sequential bucket of slices |
| **Story / FR** | **YES — this is the slice** | One validable end-goal, one subagent dispatch, one closeout |
| Subtask | No | Lives inside subagent's TDD breakdown |

### Relation to write-story

`write-story` produces one slice's spec (story.md / design.md / impl.md / test.md). `plan-executor` dispatches one slice's spec per subagent call. One write-story output ↔ one slice ↔ one subagent ↔ one closeout.

The slice-contract is NORMATIVE for the 4 required fields (D-1, SC-B1). `write-story` frontmatter is a SUPERSET of those fields. The main agent maps `acceptance_criteria` → `validable_outcome` at slice-assignment time when consuming write-story output.

---

## Required slice content (four mandatory fields)

Every slice's assignment file — whether a write-story `story.md` or a free-form `.delivery/plan/wp-N.md` — MUST contain all four:

1. **`validable_outcome`** — acceptance criteria / "done" definition expressed as something a test can encode. Source: `acceptance_criteria` from write-story output; main agent maps at assignment time.
2. **`scope` / `touches`** — files this slice reads or writes. Declares the boundary the subagent must not overreach.
3. **`depends_on`** — slice IDs of prior slices this slice requires to be closed-out green before dispatch. Empty list if no dependencies.
4. **`slice_id`** — stable identifier used for closeout cross-reference and plan/INDEX.md alignment.

These fields are sufficient for the tdd-contract to encode the outcome as a test, for the closeout-schema to cross-reference the outcome verbatim, and for the dispatch-contract to run dependency checks.

---

## Size bounds

- **Lower bound:** large enough that a TDD test meaningfully validates the outcome. Not a one-line change; not "rename a variable."
- **Upper bound:** small enough that one subagent execution completes without context exhaustion.
- **Heuristic test for "too big":** if the subagent would need to dispatch its own subagents to complete the work, the slice is too big — re-decompose at orchestrator level before dispatch.

---

## Preconditions

**SC-R2:** the slice file MUST exist at the path referenced by `plan/INDEX.md`. A path mismatch halts the main agent with an "INDEX drift" audit error. It is not silently retried — the operator must reconcile the INDEX before dispatch continues.

---

## Trigger moment

BEFORE the main agent dispatches a subagent on a slice. The main agent runs slice-contract validation as the first step of the dispatch-contract's pre-dispatch checks. If validation fails, dispatch is refused and the slice is routed to the replan-contract.

---

## Compliance signature

All three of the following must hold for a slice to be considered contract-compliant:

1. Slice file contains all four required fields with non-empty values.
2. Slice file exists at the path indexed in `plan/INDEX.md` (SC-R2).
3. After dispatch: the subagent's closeout reports `validation_result: pass` against the stated `validable_outcome`, and no nested subagent dispatch occurred.

---

## Violation signatures

The main agent MUST treat any of the following as a contract violation and refuse dispatch (or reject the closeout):

| ID | Signature | Action |
|---|---|---|
| (a) | Slice file dispatched without a `validable_outcome` stated | Main agent MUST refuse dispatch; route to replan-contract |
| (b) | Closeout reports "couldn't determine done" / no test encodes the outcome | Slice was malformed; route to replan-contract |
| (c) | Subagent attempted to dispatch its own subagents | Slice was too big; re-decompose into smaller slices via replan-contract |
| (d) | Closeout reports modifications outside declared `scope` / `touches` boundary | Slice under-specified or subagent overreached; both signal replan |
| (e) | Any of the four required fields is absent or empty | Main agent refuses dispatch; route to replan-contract |
| (f) — SC-R1 | Slice file is malformed / unparseable | Main agent halts and escalates; cannot attempt dispatch on an unreadable assignment |

Violation (f) (SC-R1) is the hard-stop case: a malformed file cannot be repaired by replan alone — operator must intervene to restore a valid file before the loop resumes.

---

## Linkage: ticket files are read-only inputs (Model C)

The slice-contract enforces a strict read-only posture for the subagent on ticket/assignment files:

| Surface | Writer | Reader |
|---|---|---|
| Slice assignment files (`story.md` or `.delivery/plan/wp-N.md`) | Main agent ONLY | Subagent (read-only) |
| `plan/INDEX.md` | Main agent ONLY | Both |
| Code + tests | Subagent | Both |
| Closeout files (`.delivery/closeouts/wp-<id>-attempt-N.yaml`) | Subagent | Main agent |

**Why:** subagent write-access to ticket files risks spec divergence; in the parallel escape hatch, write conflicts are guaranteed. The slice spec is sacred — only the main agent reconciles spec drift, and only via replan-contract.

---

## Edge cases considered

| Edge case | Handling |
|---|---|
| Slice file path in INDEX.md does not match filesystem (SC-R2) | Halt with "INDEX drift" audit error; operator must reconcile INDEX before dispatch |
| Slice file exists but is unparseable (SC-R1) | Hard halt + escalate; do not attempt dispatch |
| Slice has no dependencies but `depends_on` field is missing | Treat as field-absent violation (e); route to replan |
| Slice too big — subagent dispatches nested subagents | Post-closeout rejection (c); re-decompose via replan before next attempt |
| Subagent scope overreach (files outside `touches`) | Post-closeout rejection (d); route to replan for boundary tightening |
| Write-story `acceptance_criteria` present but main agent didn't map it to `validable_outcome` | Violation (a) at pre-dispatch; mapping is the main agent's responsibility at assignment time |

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `write-story` | upstream (consumes) | Frontmatter superset source; slice-contract is normative for the 4 required fields; write-story `acceptance_criteria` is mapped to `validable_outcome` by the main agent at slice-assignment time |
| `delivery-orchestration-dispatch-contract` | downstream (called by) | Calls slice-contract validation as its first pre-dispatch check (pre-flight step 1); slice-contract violation aborts the dispatch sequence |
| `delivery-orchestration-plan-executor` | downstream (consumer skill) | The orchestrator skill that runs the main agent loop; enforces slice-contract at every dispatch point |
| `delivery-execution-tdd-contract` | sibling (pairs with) | Slice-contract names the unit + outcome (enforced pre-dispatch by main agent); tdd-contract names what the subagent does with that outcome (enforced during execution, verified post-closeout by main agent). Neither stands alone. |
| `delivery-orchestration-replan-contract` | sibling (routes to on violation) | Any slice-contract violation routes the slice to replan-contract for decomposition, re-specification, or escalation |
| `delivery-orchestration-closeout-schema` | sibling (validates against) | Closeout must report `validable_outcome` verbatim from the slice assignment; slice-contract violations detected in closeout (b, c, d) are confirmed by closeout-schema cross-check |

---

## Open questions

None. All threads were resolved during the brainstorm. The exact YAML frontmatter schema for the slice assignment file (field names and types) is flagged as **Resolved (not fleshed)** — the creator should confirm alignment with write-story's story.md frontmatter at companion-file design time, but the four required logical fields are locked.
