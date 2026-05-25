# Decision Memo — delivery-orchestration-closeout-schema

> Artifact type: protocol | Memo type: creation | Design doc: `.brainstorms/2026-05-22-plan-execution-vertical-slice-orchestration/design.md`

---

## What I want

A data-shape protocol that defines the YAML structure a subagent MUST produce at the end of every slice dispatch. It governs two things simultaneously: the inline YAML appended to the subagent's response (for immediate ingestion) and the file written to `.delivery/closeouts/<slice-id>-attempt-<N>.yaml` (for audit trail and resumability). It does NOT govern what the main agent does with that data — ingestion semantics are owned by `delivery-orchestration-replan-contract`.

This protocol extends `synapse-observability-execution-trace` — it adds delivery-specific fields on top of the parent's execution-trace envelope without forking or duplicating the parent's field definitions.

---

## Why Claude needs it

Without a shared, normative closeout schema, each subagent invents its own output format. The main agent has no stable surface to parse, validate, or diff. Resume after compaction fails because there is no predictable file shape to reconstruct from. Lessons cannot be reliably extracted. The audit trail is ungrepable.

Additionally, without the dual-target atomicity rule (file-write before inline emit), a context compaction event between the subagent's file write and its inline YAML emission silently drops the closeout, breaking resumability with no error signal.

---

## Injection shape

- **Policy:** Governs the subagent's write behavior at dispatch end — dual-target order, atomicity rule, required fields, field constraints. Also governs the main agent's validation behavior (what constitutes a rejection-worthy closeout vs. one that passes intake).
- **Domain knowledge:** The field table and constraint rules constitute structured domain knowledge about what a well-formed delivery closeout looks like. Loaded once per subagent prompt via `{{worker_protocols}}` slot (see `delivery-orchestration-dispatch-contract`).

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| `.delivery/closeouts/<slice-id>-attempt-<N>.yaml` | 1 per dispatch attempt | No (append-only audit) | Persistent closeout for resume + audit trail |
| Inline YAML block appended to subagent response | 1 per dispatch attempt | No | Immediate ingestion surface for main agent |

---

## Schema: required field table

This table is normative. Every field is required unless marked conditional.

| Field | Type | Constraints |
|---|---|---|
| `slice_id` | string | Must match the `id` field from the dispatched slice assignment |
| `attempt_number` | integer ≥ 1 | Matches `{{attempt_number}}` slot from dispatch prompt |
| `validable_outcome` | string | Verbatim copy of the validable outcome from the slice assignment — no paraphrase |
| `validation_result` | enum | One of: `pass` \| `blocked` \| `failed` \| `rejected` |
| `outcome_test_path` | string | Path to the test that encodes the validable outcome — **required if `validation_result: pass`**; omit otherwise |
| `iterations_used` | integer ≥ 1 | Count of Ralph-loop iterations consumed before exit |
| `files_created` | list[string] | All files created during this dispatch; empty list `[]` if none |
| `files_modified` | list[string] | All files modified during this dispatch; must be ⊆ slice's declared `touches` scope |
| `tests_added` | list[string] | All test file paths added or materially modified; must include `outcome_test_path` when `pass` |
| `lessons_learnt` | list[string] | Observations the subagent wants to pass forward; empty list `[]` if none |
| `next_moves` | list[{summary, rationale, suggested_slice_id?}] | Proposed follow-on actions for main agent evaluation via replan-contract; empty list `[]` if none |
| `plan_drift_detected` | bool | `true` if subagent observed that the slice assignment no longer reflects reality as encountered |
| `plan_drift_reason` | string | **Required if `plan_drift_detected: true`**; describes what drifted and why |
| `blocked_reason` | string | **Required if `validation_result: blocked`**; describes the specific blocker |

---

## Extends synapse-observability-execution-trace

`delivery-orchestration-closeout-schema` is a superset of `synapse-observability-execution-trace` (at `/home/kok-shew-juan/juansync-synapse/synapse/protocols/observability/synapse-observability-execution-trace.md`). The parent protocol's fields are inherited — do not duplicate their definitions in this protocol's body. Cross-reference the parent for the base envelope (agent identity, timestamp, context token counts, etc.). This protocol's field table above defines delivery-specific additions only.

Structural decision from brainstorm: extend, do not fork. Rationale: forking would diverge the observability surface across delivery and synapse contexts; extending preserves tooling that consumes the base trace format.

---

## Dual-target atomic invariant (CL-R1)

The subagent MUST write the closeout file BEFORE emitting the inline YAML in its response. This ordering is non-negotiable.

**Rule:** write `.delivery/closeouts/<slice-id>-attempt-<N>.yaml` → THEN append the same YAML inline in the response.

**Why:** a context compaction event or session interruption between the two writes would leave the file intact (recoverable) but drop the inline emit silently. By writing the file first, the worst case is that the main agent re-reads from disk rather than parsing the response — resumability is preserved either way.

**Failure behavior:** if the file write fails (path not writable, disk full, permission error), the subagent MUST halt immediately and report the write failure. It must NOT emit the inline YAML and proceed as if the closeout succeeded. The main agent treats any dispatch with no closeout file as `failed` — never as silent success.

---

## Compliance signatures

A closeout passes intake validation when ALL of the following hold:

1. Well-formed YAML, all required fields present.
2. `validation_result: pass` ⇒ `outcome_test_path` is populated AND appears in `tests_added`.
3. `validation_result: blocked` ⇒ `blocked_reason` is populated.
4. `plan_drift_detected: true` ⇒ `plan_drift_reason` is populated.
5. `files_modified` ⊆ slice's declared `touches` scope (from slice-contract).
6. `validable_outcome` is verbatim from the assignment (not paraphrased).
7. Closeout file exists at `.delivery/closeouts/<slice_id>-attempt-<attempt_number>.yaml` with identical content.

---

## Violation signatures

Main agent rejects the closeout (routes to replan-contract) on any of the following:

| # | Condition | Signal |
|---|---|---|
| (a) | Missing `slice_id`, `validable_outcome`, or `validation_result` | Structural failure — request re-emit with parse error hint |
| (b) | `pass` without `outcome_test_path` | Fabricated pass — also caught by tdd-contract; escalate for human review |
| (c) | `files_modified` includes paths outside declared slice `touches` scope | Subagent overreach — route to replan |
| (d) | `validable_outcome` doesn't match assignment verbatim | Subagent didn't read brief — treat as `rejected`, re-dispatch with stronger brief injection |
| (e) | Malformed YAML | Auto-retry ONCE with the parse error included as a hint in the re-prompt; if second attempt also malformed, escalate to user (do not enter an unbounded retry loop) |

---

## Ingestion semantics: scoped out

This protocol describes the DATA SHAPE of a closeout. It does not describe what the main agent does after validation passes or fails (mark slice complete, append lessons, evaluate next_moves, trigger replan). That logic is owned by `delivery-orchestration-replan-contract` (see CL-P1 from brainstorm [B] lens rotation). Cross-reference that protocol for the full ingest-to-mutation flow.

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `synapse-observability-execution-trace` | consumes (parent — extends) | Provides the base execution-trace envelope; this protocol adds delivery-specific fields on top |
| `delivery-execution-tdd-contract` | consumes | Defines what `pass` means (outcome test is green) and what `outcome_test_path` must reference |
| `delivery-orchestration-replan-contract` | produces for | Consumes validated closeouts; owns the full ingestion-to-plan-mutation flow (per CL-P1) |
| `delivery-execution-slice-contract` | consumes | Defines `touches` scope — used to validate `files_modified ⊆ touches` compliance signature |

---

## Edge cases considered

| Edge case | Handling |
|---|---|
| File write fails before inline emit | Subagent halts; reports write failure; no inline YAML emitted; main agent treats as `failed` |
| Malformed YAML on first emit | Auto-retry once with parse error hint; second malformation → escalate to user |
| `validable_outcome` paraphrased rather than verbatim | Violation (d) — treat as `rejected`; re-dispatch with stronger injection |
| `files_modified` includes untracked files not in `touches` | Violation (c) — overreach signal; route to replan |
| `pass` without outcome test path | Violation (b) — fabricated pass; escalate for human review |
| Subagent writes correct file but wrong `attempt_number` | Collision on next attempt's filename; main agent detects by counting existing closeout files for this slice and comparing |
| `next_moves` entries with `suggested_slice_id` referencing nonexistent slice | replan-contract resolves — closeout-schema does not validate; treat as a loose proposal |

---

## Open questions

None. All threads resolved during brainstorm phases [A], [N], and [B].
