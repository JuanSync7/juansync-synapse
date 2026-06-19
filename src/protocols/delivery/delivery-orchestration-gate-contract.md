---
name: delivery-orchestration-gate-contract
description: "Customer-handoff gate contract between pipeline stages — defines the gate block shape, the 4 decision tokens, the audit row format, and the non-overrideable hold rule that prevents auto-advance past customer review."
domain: delivery
subdomain: orchestration
subject: gate
kind: contract
version: 1
status: stable
tags: [gate, customer-handoff, decision-tokens, audit-row, non-overrideable]
---

# Gate Contract

This protocol defines the customer-facing review checkpoint between two pipeline stages. Without it, every orchestrator skill invents its own gate UX — token grammar drifts, audit format drifts, and the customer learns a different "how do I approve this" interaction per stage. With it, every gate everywhere uses the same block, the same tokens, and the same audit shape. The contract sits on top of `synapse-memory-external-memory-contract` — the audit row IS the program-level working memory.

A gate is **not optional**. The orchestrator may not auto-advance past a gate, even on explicit customer request ("just keep going"). The customer must emit one of four decision tokens by name — anything else is held with a clarification prompt. This is what makes the gate a load-bearing trust contract rather than a UX courtesy.

## Contract Rules

1. **Authority — orchestrator emits, customer decides.** The orchestrator skill (any skill consuming this contract) renders the gate block per Rule 2 and waits for the customer's response. The orchestrator NEVER auto-supplies a decision, NEVER infers one from silence, NEVER skips a gate. Customer is the sole decider.

2. **Block format — verbatim shape.** Every gate emits exactly this Markdown structure:

   ```markdown
   ## GATE — <stage-id> — <ISO-date>

   **Artifact produced:** `<path>` (by <writer-skill-name>)

   ### Diff summary
   - <field 1>
   - <field 2>
   - ...

   ### Risks / conflicts surfaced
   - <verbatim from writer output, or "none surfaced">

   ### Decision options
   - `approve` — advance to next stage
   - `revise <comments>` — re-invoke writer with comments
   - `pause` — suspend program; resume later
   - `abort` — close program with exit_reason=abort

   > Reply with exactly one token.
   ```

   Field rendering rules per stage live in the consuming skill's reference (e.g., `gate-presentation.md`). Block shape itself is invariant — adding sections, reordering, omitting "Risks" when empty (must show "none surfaced") all break the contract.

3. **Decision tokens — exactly four.**

   | Token | Effect | Allowed extensions |
   |---|---|---|
   | `approve` | Advance to next pipeline node | `--tag <TAG>` at [SCOPE-GATE]; `merge` / `next-tag` / `done` / `re-shape <comments>` / `resume` as [HANDOFF]-specific aliases |
   | `revise <comments>` | Re-invoke the writer with the customer's comments as args | comments required after the token |
   | `pause` | Set `customer_seat: paused` in program state; exit to suspend | none |
   | `abort` | Set `exit_reason: abort`; close program | none |

   Synonyms (`yes`, `lgtm`, `looks good`, `👍`, `cancel`, `stop`) are NOT accepted. On synonym detection, hold and emit a clarification: "Read as `approve`? Reply `approve` to confirm." This prevents silent advance on ambiguous affirmation — the leading failure mode of gate-style UX.

4. **Non-overrideable hold.** The gate may not be skipped by:
   - Customer saying "skip the review" or "just keep going"
   - A `--no-gate` flag (no such flag exists; do not invent one)
   - Orchestrator self-determination ("this looks fine, advancing")

   The only legal advance is an explicit decision token from the customer. An attempted skip is logged as a violation row in the audit table and the gate re-emits.

5. **Audit row format.** Every gate emission AND every customer decision appends one row to the consuming skill's program-state file (`PROGRAM.md` gate-history table):

   ```
   | <ISO-date> | <stage-id> | <event> | <writer-skill> | <note> |
   ```

   Where `event ∈ {emit, approve, revise, pause, abort, violation, drift-demote}`. Two rows per gate cycle minimum (one `emit`, one decision). Append-only — never edit or delete a row. The row is what makes [RESUME] possible.

6. **Idempotent re-emission.** If the orchestrator re-enters a gate node (e.g., after resume), it MUST re-emit the gate block with a fresh ISO-date and a new `emit` audit row. The customer's prior decision in the audit trail is historical context, not a binding pre-approval — re-emission gives the customer a fresh decision point on the current artifact state.

## Failure assertion

A gate is in compliance iff:

| Signature | Check |
|---|---|
| (a) | A `## GATE — ...` block was emitted to the customer before the orchestrator transitioned out of the gate node |
| (b) | An `emit` row was appended to the audit table in the same tick as the block emission |
| (c) | The decision recorded in the audit table is exactly one of `approve \| revise \| pause \| abort` (with permitted extensions per Rule 3) |
| (d) | The orchestrator did not transition out of the gate node before recording a decision row |
| (e) | The block shape matches Rule 2 verbatim (no added/removed sections) |
| (f) | Synonyms were rejected with a clarification prompt, not silently accepted |

Any failure on (a)–(f) is a contract violation. The consuming skill MUST emit the instruction:

`PROTOCOL FAILURE: delivery-orchestration-gate-contract — [signature: a | b | c | d | e | f]`

THEN halt the program and append a `violation` audit row naming the failed signature to the consuming skill's program-state file. The orchestrator MUST NOT advance `current_node` until the violation is resolved by re-emitting a compliant gate block.

## Configuration

Consuming skills MAY configure:
- The exact field set rendered under "Diff summary" (per-stage; defined in the skill's `gate-presentation.md` or equivalent reference).
- The customer-facing wording above the gate block (a one-line preamble — does not modify the block itself).
- Extension tokens at specific stages (per Rule 3 — must be documented in the consuming skill's reference).

Consuming skills MUST NOT:
- Change the four decision tokens or add a fifth.
- Drop the "Reply with exactly one token" guidance line.
- Treat any non-token reply as an implicit decision.
- Persist the gate state anywhere other than the consuming skill's program-state file (no global gate registry).

## Edge cases

- **Customer replies with both `approve` and `revise` in one message** ("approve, but revise the third FR"). Hold. Emit: "Ambiguous — read as `revise`? Reply `approve` to advance as-is or `revise <comments>` to send back."
- **Customer replies with `revise` but no comments**. Hold. Emit: "Revise requires comments — reply `revise <what to change>`."
- **Customer replies between two gate emissions** (race after re-emit). Apply the decision to the most recent `emit` row only. Older `emit` rows without a paired decision row are dangling — surface in [RESUME] as "no decision recorded".
- **`abort` at [HANDOFF]** is treated as `done` semantically (the run already happened); exit_reason becomes `abort` not `done` to preserve customer intent in the audit trail.
