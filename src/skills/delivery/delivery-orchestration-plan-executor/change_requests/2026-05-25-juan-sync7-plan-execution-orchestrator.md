# Decision Memo — delivery-orchestration-plan-executor

> Artifact type: skill | Memo type: creation | Design doc: `.brainstorms/2026-05-22-plan-execution-vertical-slice-orchestration/design.md`

---

## What I want

A sequential, TDD-disciplined plan-execution orchestrator skill. When the user signals "start building" (or invokes `/build`), the skill takes the main agent into a manager role:

1. Ingest the plan — read existing `write-story` tickets as the authoritative WP list when present; otherwise decompose from whatever context exists (a chat, a doc, a rough plan) and materialize WPs to disk for resumability.
2. Present the decomposed WP list to the user and await one confirmation.
3. Enter an unattended sequential loop: dispatch one subagent per slice, inject the 5 delivery protocols into each subagent prompt, ingest the closeout, evaluate via replan-contract, repeat until all slices are done.
4. Terminate with a structured final summary on any stop condition.
5. Support resume: the closeout trail on the filesystem lets the skill reconstruct progress after interruption or compaction.

The skill does NOT parallelize by default. One subagent in flight at a time. An escape hatch exists for zero-overlap, zero-coupling, user-authorized parallel dispatch — but sequential is the default and recommended path.

---

## Why Claude needs it

Without this skill, Claude has no principled way to execute a multi-slice delivery plan:

- **`parallel-agents-dispatch`** (existing) is wave-based and throughput-focused. It enforces no TDD discipline, passes no lessons forward between slices, and has no closeout/resume semantics. It is being retired as the default executor in favor of this skill.
- **Ad-hoc orchestration** in chat: Claude decompose tasks informally, dispatches subagents without protocol injection, and loses progress on compaction. No lessons compound. No audit trail. Re-starts from scratch.
- **Result of baseline failure:** no enforced TDD-first discipline per slice, no lessons-forward compounding, no resume-from-closeout, and no structured escalation when a slice is blocked — leading to silent failures, repeated mistakes, and un-auditable plan drift.

This skill is the canonical, protocol-driven replacement.

---

## Injection shape

- **Workflow:** Multi-phase orchestration loop — ingest plan → decompose → confirm → sequential dispatch loop (dispatch → ingest closeout → replan → next) → terminate with summary.
- **Policy:** Judgment rules for when to escalate (N consecutive failures, M replan cycles on one slice), when to accept parallel dispatch (escape hatch three-condition check), when write-story tickets are authoritative vs. when to self-decompose.
- **Domain knowledge:** Two-surface model (docs/ spec surface vs. `.delivery/` execution surface), Model-C linkage semantics (who writes what), dispatch granularity (slice ≡ story ≡ leaf WBS unit), 5-protocol reference names and their injection points.

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| `.delivery/plan/INDEX.md` | 1 per run | Yes (main agent only) | Rolling WP list with status, deps, order |
| `.delivery/plan/wp-<id>.md` | 1 per WP (free-form mode only) | Yes (main agent only, pre-dispatch) | Per-WP assignment package (ticketed mode uses `write-story` dirs) |
| `.delivery/closeouts/wp-<id>-attempt-N.yaml` | 1 per subagent dispatch attempt | No (append-only audit trail) | Subagent-written closeout; ingested by main agent |
| `.delivery/lessons.md` | 1 per run | Append-only | Curated lessons from closeouts; injected into future subagent prompts |
| `.delivery/plan/CHANGELOG.md` | 1 per run | Append-only | Audit log of every plan mutation (via replan-contract) |
| Final summary (inline) | 1 per termination | No | Slice rollup counts, lessons tail, exit reason, plan pointer |

---

## Flow graph

```
[INGEST-PLAN]
      |
      v
[DECOMPOSE / MATERIALIZE]
      |
      v (present WP list)
[CONFIRM] <-- user reviews WP list; approves or adjusts
      |
      v
      +-----> [PRE-FLIGHT CHECKS] (RB-1)
                     |
          pass       | fail (loud halt)
                     v
             [PICK-NEXT-SLICE] <--------------------------+
                     |                                    |
                     | (all slices closed-out green)      |
                     v                                    |
             [TERMINATION] <--                            |
             (exit reason enum)                           |
                     |                                    |
                     | (next slice available)             |
                     v                                    |
             [DISPATCH-CONTRACT] (pre-dispatch checks)    |
                     |                                    |
                     v                                    |
             [SUBAGENT EXECUTION]                         |
             (slice-contract + tdd-contract               |
              + closeout-schema injected)                 |
                     |                                    |
                     v                                    |
             [INGEST-CLOSEOUT]                            |
             (parse + validate closeout-schema)           |
                     |                                    |
                     v                                    |
             [REPLAN-CONTRACT]                            |
             (eval next_moves, plan_drift,                |
              lessons append, CHANGELOG entry)            |
                     |                                    |
                     +------------------------------------+
                     (loop: pick next slice)
```

---

## Node specifications

**[INGEST-PLAN]** — Load: `docs/<initiative>/.../stories/FR-NNN/` dirs if present (write-story output), else chat/doc context. Do: determine whether write-story tickets exist; if yes, treat as authoritative WP list (no re-decomposition). Do NOT copy ticket bodies — plan/INDEX.md references FR-NNN dirs by path. Exit: to [DECOMPOSE / MATERIALIZE].

**[DECOMPOSE / MATERIALIZE]** — Load: whatever context was ingested. Do: if write-story tickets present, build INDEX.md referencing them. If free-form, decompose into slice-shaped WPs (one validable end-goal each), write `plan/wp-<id>.md` per WP, build INDEX.md. Apply slice-size heuristic from `references/slice-decomposition-heuristics.md`. Do NOT dispatch yet. Exit: to [CONFIRM].

**[CONFIRM]** — Do: present full WP list (slice IDs, one-line descriptions, order) to user. Await explicit approval (Y/adjust). On adjustment: update INDEX.md and re-present. On approval: enter loop. Do NOT auto-proceed without user acknowledgment. Exit: to [PRE-FLIGHT CHECKS].

**[PRE-FLIGHT CHECKS (RB-1)]** — Do three checks in order:
1. `.delivery/` writable — create if absent; halt loud if OS denies.
2. Decomposition yields ≥1 slice — halt loud with "insufficient context" if zero.
3. Test framework discoverable (check project conventions / lockfiles) — if not discoverable, escalate: "tdd-contract unenforceable without a known test framework."
Exit: pass → [PICK-NEXT-SLICE]; fail → halt with specific diagnostic.

**[PICK-NEXT-SLICE]** — Load: `plan/INDEX.md`. Do: select next un-dispatched slice in dependency order (all `depends_on` slices must have `pass` closeouts). If no eligible slice and all are closed: exit to [TERMINATION]. If no eligible slice but some are blocked: escalate (blocked dependency). Exit: slice selected → [DISPATCH-CONTRACT]; all slices done → [TERMINATION]; blocked dependency → escalate to user.

**[DISPATCH-CONTRACT]** — Load: slice file, prior closeouts for this slice, dependency closeouts (distilled), `lessons.md`, 3 worker protocol bodies. Do: run pre-dispatch checks (slice-contract validation, dependency check, no-in-flight check, all 8 prompt slots populated). Select model explicitly (default: sonnet; opus if slice notes flag architectural complexity). Dispatch subagent. Do NOT dispatch if any check fails. Exit: subagent dispatched → [SUBAGENT EXECUTION].

**[SUBAGENT EXECUTION]** — Subagent runs with injected `slice-contract + tdd-contract + closeout-schema`. Subagent scope: read slice file (read-only), write code and tests, write one closeout YAML to `.delivery/closeouts/wp-<id>-attempt-N.yaml`, append closeout YAML to response. Subagent MUST NOT write to plan/, INDEX.md, or lessons.md. Exit: closeout received → [INGEST-CLOSEOUT].

**[INGEST-CLOSEOUT]** — Load: closeout from subagent response + closeout file. Do: parse YAML, validate closeout-schema compliance (all required fields, pass ⇒ outcome_test_path populated, files_modified ⊆ declared scope). On malformed YAML: auto-retry once with parse-error hint; second malformation → escalate. Exit: valid closeout → [REPLAN-CONTRACT].

**[REPLAN-CONTRACT]** — Load: validated closeout, `plan/INDEX.md`, `lessons.md`. Do: on `pass` — mark slice complete in INDEX.md, append lessons to lessons.md, evaluate next_moves, write CHANGELOG entry. On `blocked`/`failed`/`rejected` — increment attempt counter; if attempts > N=2 (default), mark blocked + escalate. On plan_drift — edit unstarted slices or re-decompose per drift_reason; write CHANGELOG. Every plan/INDEX.md or lessons.md diff MUST have a matching CHANGELOG entry. Check replan cycle count on this slice; if > M=3 → halt + escalate ("plan likely fundamentally misframed"). Exit: → [PICK-NEXT-SLICE].

**[TERMINATION]** — Do: emit final summary (US-1 format — see Edge cases). Emit exit reason enum. Do NOT delete any `.delivery/` files. Exit: skill complete.

---

## Edge cases considered

| Edge case | Handling |
|---|---|
| All slices closed-out green | [TERMINATION] with exit reason `all_slices_green` |
| User interrupts mid-run | Skill exits; closeout trail on filesystem preserves state; resume reads trail to find next un-closed slice |
| N=2 consecutive subagent failures on same slice | Mark slice `blocked`; escalate to user with closeout trail for context |
| M=3 replan cycles on same slice | Halt + escalate with "plan likely fundamentally misframed" — distinct from per-slice attempt cap |
| Test framework not discoverable at pre-flight | Halt loud before any dispatch; tdd-contract is unenforceable without known framework |
| Zero slices after decomposition | Halt loud: "insufficient context to decompose into at least one slice" |
| `.delivery/` not writable | Halt loud with OS error detail; no silent fallback |
| Escape hatch parallel dispatch | Allowed ONLY when: (a) zero `touches` overlap, (b) zero `depends_on` overlap, (c) user explicitly authorizes for this run. Default stays sequential — opt-in, not opt-out |
| write-story tickets present | Authoritative — consumed as-is as WP list; main agent does NOT re-decompose |
| Free-form context, no tickets | Main agent decomposes into slice-shaped WPs, materializes to `.delivery/plan/wp-N.md`, builds INDEX.md |
| Subagent writes to plan/ or lessons.md | Halt + escalate: architectural invariant violated (only main agent writes plan surfaces) |
| Closeout `files_modified` outside declared scope | Closeout-schema violation → reject; route to replan |
| Resume after compaction | Read closeout trail from `.delivery/closeouts/`; reconstruct which slices are pass/blocked/undispatched; re-enter [PICK-NEXT-SLICE] |
| Setup vs auto-decompose | Auto-decompose always; present WP list at [CONFIRM]; user reviews before loop begins |
| Progress notification mid-run | TaskCreate per WP at dispatch (status `in_progress`); mark `completed` at green closeout |

---

## Companion files anticipated

**Always-loaded (in SKILL.md body):**
- Protocol names only, referenced by name — never restated inline (PR-1 enforcement: creator MUST NOT copy protocol bodies into SKILL.md; reference by name and load point only)

**References (loaded at specific decision points):**
- `references/slice-decomposition-heuristics.md` — loaded at [DECOMPOSE / MATERIALIZE]; one-page heuristic for epic-vs-story-vs-task judgment, slice-size bounds, "too big" test
- `references/final-summary-format.md` — loaded at [TERMINATION]; US-1 format spec: slice rollup table (total/green/blocked/superseded counts), lessons.md tail (last 5–10 lines), pointer to plan/INDEX.md, exit reason enum

**Templates:**
- No fixed templates — subagent prompts are assembled dynamically per dispatch-contract's 8 mandatory slots

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `delivery-orchestration-dispatch-contract` | consumes | Pre-dispatch checks, 8 mandatory prompt slots, escape-hatch conditions, model selection rule |
| `delivery-orchestration-replan-contract` | consumes | Plan mutation authority, CHANGELOG requirement, M=3 escalation bound, lessons.md write rule |
| `delivery-orchestration-closeout-schema` | consumes | Closeout YAML validation, dual-target write requirement, ingestion flow ownership |
| `delivery-execution-slice-contract` | consumes (injects into subagent) | Slice assignment file structure, 4 required fields, violation signatures for pre-dispatch rejection |
| `delivery-execution-tdd-contract` | consumes (injects into subagent) | TDD discipline, iteration cap (default 10, skill-overridable), Ralph loop semantics, violation signatures for closeout rejection |
| `synapse-memory-external-memory-contract` | consumes (via replan-contract) | `.delivery/plan/` and `lessons.md` as working memory surfaces |
| `synapse-observability-execution-trace` | consumes (via closeout-schema) | Base schema that closeout-schema extends — do not fork |
| `write-story` | consumes upstream output | Produces FR-NNN ticket directories; plan-executor reads them as authoritative WP list when present |
| `parallel-agents-dispatch` | retirement relationship | This skill is the canonical sequential replacement; parallel-agents-dispatch retained only for explicit throughput-over-discipline use cases |
| `code-build-planner`, `docs-implementation-writer` | upstream producers | May produce plan-shaped artifacts consumed at [INGEST-PLAN] |

---

## Open questions

Two items from the meta-process-brainstormer Open section were not resolved to decisions (held as "Bet:" — unconfirmed):

1. **Progress notification granularity:** Does the skill emit `TaskCreate` per WP (status `in_progress` at dispatch, `completed` at green closeout), or stay silent until terminal summary? Bet: TaskCreate per WP. Creator should implement the bet and note it as an empirically-revisable default.

2. **Setup mode vs. auto-decompose:** Does the skill offer an interactive WP decomposition mode (user reviews each WP interactively before confirmation), or always auto-decompose and present at [CONFIRM]? Bet: auto-decompose → present full list → single confirmation gate → unattended loop. Creator should implement this bet.

Both bets are directionally unambiguous — implement as stated, flag for post-dogfooding review.
