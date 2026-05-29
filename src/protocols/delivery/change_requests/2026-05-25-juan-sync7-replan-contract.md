# Decision Memo — delivery-orchestration-replan-contract

> Artifact type: protocol | Memo type: creation | Design doc: `.brainstorms/2026-05-22-plan-execution-vertical-slice-orchestration/design.md`

---

## What I want

A protocol that governs exactly what the main agent does after ingesting a subagent closeout and before issuing the next dispatch. It defines:

- Which signals from the closeout trigger a replan cycle.
- Which mutations to the plan surfaces (`.delivery/plan/INDEX.md`, `.delivery/lessons.md`) are permitted, and which are forbidden.
- The mandatory audit trail for every mutation (`.delivery/plan/CHANGELOG.md`).
- How out-of-band user edits to plan surfaces are detected and handled.
- The escalation bound that caps runaway replan loops per slice.

This protocol is the write-rule for the two-surface working memory. It is the canonical owner of the full ingest-to-mutation flow — `delivery-orchestration-closeout-schema` cross-references here rather than duplicating that logic.

---

## Why Claude needs it

Without an explicit replan protocol, the main agent has no stable definition of:

1. When it is authorized to mutate the plan vs. when it must pass through.
2. Which mutations are safe (add/reorder/mark-blocked) vs. destructive (delete closed slices, edit completed closeouts).
3. How to detect and handle plan writes that originated from a subagent (architectural break) rather than from user input.
4. When to escalate vs. continue cycling — leaving the loop unbounded produces infinite replan death spirals on pathological plans.

Concretely: without this protocol, a main agent will silently edit plan files mid-run with no log, subagents may attempt plan writes that corrupt the audit trail, and the orchestrator has no defined exit condition for stuck slices beyond the per-attempt N cap.

---

## Injection shape

- **Policy:** Authority split (main agent only writes plan surfaces), mutation allow/forbid lists, firing-signal decision table, escalation bound, out-of-band edit handling. Judgment rules the main agent applies after every closeout parse.
- **Workflow:** Single-phase trigger (AFTER closeout ingestion, BEFORE next dispatch). Not multi-phase — one decision point per tick.

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| `.delivery/plan/INDEX.md` (mutations) | 0–N per tick | Yes (guarded) | Updated WP status, added slices, reordered queue |
| `.delivery/plan/wp-<id>.md` (new or edited) | 0–N per tick | Yes (guarded) | New slices added, or unstarted slice bodies edited |
| `.delivery/lessons.md` (appended) | 0–1 per tick | Append-only | Curated lessons from closeout's `lessons_learnt` |
| `.delivery/plan/CHANGELOG.md` (appended) | 1 per mutation | Append-only | Mandatory audit entry for every plan surface change |

---

## Sits on parent protocol

This protocol sits on top of `synapse-memory-external-memory-contract` (at `synapse/protocols/memory/synapse-memory-external-memory-contract.md`). The plan surfaces — `.delivery/plan/INDEX.md` and `.delivery/lessons.md` — ARE the working memory for the delivery orchestration run. This protocol is the write-rule for that memory; it operationalizes Rules 2 ("Skill-owned writes"), 3 ("Read-before-reason"), and 4 ("Write-after-turn") from the parent in the delivery context.

The parent protocol's Rule 2 is what makes forbidden mutation (e) — any plan write by a subagent — an architectural break, not merely a policy violation.

---

## Trigger

AFTER closeout ingestion (closeout file parsed + validated by main agent), BEFORE next dispatch is issued. One replan tick per closeout ingest. The replan tick may be a no-op (no signals fire); the protocol still runs to check.

---

## Authority

**Main agent ONLY.** Subagents surface proposals via closeout fields (`next_moves`, `plan_drift_detected`, `lessons_learnt`). The main agent disposes of each proposal — accept, discard with reason, or transform. Subagents never execute plan mutations directly.

---

## Firing signals

Any one of the following triggers the replan evaluation:

<!-- VERBATIM -->
| Signal | Source closeout field | Default action |
|---|---|---|
| `plan_drift_detected: true` | `plan_drift_detected` + `plan_drift_reason` | Edit slice body / re-decompose / mark blocked per drift reason |
| `next_moves` non-empty | `next_moves` list | Evaluate each: add new slice / merge into existing / discard with reason |
| `validation_result: blocked` | `validation_result` | Re-decompose if too-big; mark blocked + escalate if real blocker |
| `validation_result: failed` or `rejected` | `validation_result` | Increment attempt counter; >N=2 ⇒ mark blocked + escalate |
| `lessons_learnt` non-empty | `lessons_learnt` list | Append to `.delivery/lessons.md` with `### Slice <id> attempt <N>` header |

---

## Allowed mutations

The following mutations are permitted within one replan tick (each MUST be logged to CHANGELOG.md):

1. Add a new slice to `plan/INDEX.md` (new WP file created if free-form mode).
2. Reorder unstarted slices in `plan/INDEX.md`.
3. Mark a slice status as `blocked`, `deferred`, or `superseded` in `plan/INDEX.md` / slice frontmatter.
4. Re-decompose an existing slice into N smaller slices (original marked `superseded` — NOT deleted).
5. Edit the body or frontmatter of an **unstarted** slice (no prior dispatch attempt on it).
6. Append an entry to `.delivery/lessons.md`.
7. Update a slice's frontmatter status field (e.g., `in_progress` → `pass`, `blocked`).

---

## Forbidden mutations

The following are prohibited. Violation requires immediate halt and escalation:

- **(a)** Deleting closed-out slice files — use `superseded` status; files are permanent audit artifacts.
- **(b)** Editing or deleting closeout files in `.delivery/closeouts/` — append-only audit trail; any modification is a data integrity violation.
- **(c)** Editing a slice's assignment body after its first dispatch (unless the edit is a direct drift response and the prior assignment+closeout pair is preserved in the audit trail).
- **(d)** Non-append edits to `.delivery/lessons.md` (rewriting, trimming, or re-ordering existing entries).
- **(e)** Any plan write by a subagent — this is an architectural break (violates `synapse-memory-external-memory-contract` Rule 2). Main agent MUST halt, surface the violation, and refuse the closeout until the write is reverted.

---

## Audit requirement

Every mutation to `.delivery/plan/` or `.delivery/lessons.md` MUST be logged to `.delivery/plan/CHANGELOG.md` within the same replan tick — before the next dispatch is issued.

**CHANGELOG.md format:** Markdown with H2 entries. Each entry contains:

```markdown
## <ISO-8601 timestamp>
- **Triggering closeout:** `<closeout filename>`
- **Signal type:** <plan_drift_detected | next_moves | blocked | failed | rejected | lessons_learnt>
- **Change:** <one-liner describing the mutation>
- **Reason:** <why the main agent made this call>
```

The CHANGELOG is append-only. No entry is ever edited or deleted. It is the definitive record of every plan surface change during the run.

---

## Out-of-band user edit handling (RP-R1)

The main agent reads `plan/INDEX.md` and `lessons.md` fresh at the start of every replan tick ("read-before-reason" from the parent protocol). If the file hash has changed since the last tick but no CHANGELOG entry attributes the change:

- Treat as a user intervention (user is authoritative over their own plan files).
- Accept the current state as the new baseline.
- Write a CHANGELOG entry: `"out-of-band edit detected — accepted as user intervention"` with timestamp.
- Continue the run from the new state.

This prevents false-positive halts when the user corrects the plan manually between ticks.

---

## Escalation bound (RP-M1)

**M=3 replan cycles on a single slice** is the default escalation threshold. Hitting M cycles on the same slice signals that the plan is fundamentally misframed for that slice — the main agent halts and escalates to the user.

**This is a skill-overridable default** (consistent with TC-B1 — the TDD iteration cap is also skill-overridable). The orchestrator skill (`delivery-orchestration-plan-executor`) MAY override M at runtime via the protocol-injection prompt slot. It is NOT a hard protocol constant. Consuming skills that need a different threshold (e.g., auto-research, which may tolerate more replan cycles) override it explicitly rather than forking the protocol.

M is distinct from the per-attempt attempt cap N=2 (which is governed by `delivery-orchestration-dispatch-contract` pre-flight). M counts how many times the replan-contract has fired on the same slice across all its attempts; N counts raw dispatch attempts.

---

## Violation signatures

Any of the following constitutes a protocol violation and requires the stated response:

- **(a)** `plan/` or `lessons.md` diff detected without a corresponding CHANGELOG entry → silent mutation. Main agent halts, backfills the CHANGELOG entry, then escalates.
- **(b)** Subagent Task() return or closeout contains plan surface writes → architectural break. Main agent halts and escalates before proceeding.
- **(c)** In-place edit or delete detected in `closeouts/` → halt and escalate.
- **(d)** A closed-out (status: pass) slice file has been deleted → halt and attempt restore from git history.
- **(e)** Replan cycle count on a single slice exceeds M → escalate per the escalation bound; do not continue dispatching on that slice.

---

## Why this protocol is necessary

Four structural requirements justify a dedicated replan protocol rather than embedding this logic in the orchestrator skill body:

1. **Authority split.** The boundary between "subagent proposes" and "main agent disposes" must be stated once, centrally, and unambiguously. Embedding it in a skill body makes it invisible to other skills that may later consume the same plan surfaces.

2. **Audit trail.** The CHANGELOG requirement creates an immutable record of every plan mutation. Without a protocol that mandates this, individual skill implementations omit it under time pressure.

3. **Escalation bound.** The M=3 cycle cap is a cross-skill constant (with overridability). Without a protocol that names it, each skill re-invents an arbitrary number or omits the bound entirely, producing unbounded replan loops.

4. **Append-only lessons.** The lessons surface is a compounding asset — its value grows across slices. Non-append mutations (rewrites, trims) destroy compounding. A protocol-level prohibition is the only reliable enforcement mechanism.

---

## Canonical ownership (RP-B1)

This protocol is the canonical owner of the full ingest-to-mutation flow. The sequence is:

1. Main agent receives closeout (inline YAML + persisted file).
2. Main agent validates closeout against `delivery-orchestration-closeout-schema`.
3. **This protocol fires.** Main agent evaluates firing signals, executes allowed mutations, writes CHANGELOG entries, and curates lessons.md.
4. Main agent signals readiness for next dispatch to `delivery-orchestration-dispatch-contract`.

`delivery-orchestration-closeout-schema` defines WHAT the closeout contains. This protocol defines WHAT THE MAIN AGENT DOES with it. The closeout-schema cross-references this protocol for ingestion semantics and does not duplicate the flow.

---

## Edge cases considered

| Edge case | Handling |
|---|---|
| No firing signals (all fields benign) | Replan tick is a no-op; no mutations, no CHANGELOG entry required |
| `next_moves` contains a duplicate of an existing slice | Main agent discards with reason logged in CHANGELOG |
| Slice decomposed into N slices but some N-slices conflict with each other | Main agent adds them sequentially with deps set; does not dispatch simultaneously |
| Subagent writes to a plan file and the write is detected mid-tick | Forbidden mutation (e): halt + escalate; refuse closeout until reverted |
| User edits plan while main agent is mid-tick (hash drift detected on next read) | RP-R1: treat as user intervention, accept, write CHANGELOG "out-of-band edit detected" |
| M=3 cap hit on slice but user wants to continue | User may override M for this run (skill-overridable); main agent must receive explicit instruction before continuing |
| lessons.md grows very large within a run | No in-run trimming; end-of-run hook (in plan-executor skill) compresses to run summary while preserving `.delivery/lessons.raw.md` |

---

## Companion files anticipated

- `references/replan-firing-decision-tree.md` — loaded when the main agent evaluates `next_moves` items; decision heuristics for add-slice vs. merge vs. discard.
- `references/changelog-format.md` — CHANGELOG.md entry format reference; loaded when writing audit entries (keeps protocol body lean).

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `synapse-memory-external-memory-contract` | sits on (parent) | plan/ and lessons.md ARE the working memory; this protocol is the write-rule. Rules 2, 3, 4 of the parent apply here. |
| `delivery-orchestration-closeout-schema` | consumes output | Owns the full ingest-to-mutation flow (RP-B1 / CL-P1). Closeout-schema cross-refs here; ingestion semantics live here, not there. |
| `delivery-orchestration-dispatch-contract` | sequencing | Replan completes (CHANGELOG written, mutations applied) before next dispatch is authorized. The dispatch-contract pre-flight runs after this protocol exits. |
| `delivery-orchestration-plan-executor` | consumer skill | Uses M cap (skill-overridable) and curates lessons.md for injection into subsequent subagent dispatches. |

---

## Open questions

None. All items in the notepad's Open section for this artifact were resolved during lens rotation (RP-B1, RP-M1, RP-R1 lock-ins confirmed at [B]).
