# Decision Memo — delivery-orchestration-dispatch-contract

> Artifact type: protocol | Memo type: creation | Design doc: `.brainstorms/2026-05-22-plan-execution-vertical-slice-orchestration/design.md`

---

## What I want

A behavioral contract that governs every subagent dispatch made by the orchestrator skill (`delivery-orchestration-plan-executor`). It enforces sequential dispatch by default, mandates explicit model selection, requires all 8 prompt slots to be populated, and validates a set of pre-dispatch checks before any subagent is launched. The protocol is the main agent's checklist — nothing may be dispatched unless this contract is satisfied.

---

## Why Claude needs it

Without this protocol, a main agent orchestrating multiple subagents will:

- Dispatch the next subagent before the prior closeout is ingested (losing lessons that compound across slices).
- Omit model selection and inherit whatever model the parent uses (cost surprises, non-reproducible runs).
- Skip dependency closeouts in the prompt (subagent re-invents contracts already pinned in prior slices).
- On a second attempt, forget prior attempt history (same failing approach retried verbatim).
- Omit worker protocol bodies from the prompt (subagent doesn't know it owes a closeout, test-first discipline, or iteration cap).

The protocol is the load-bearing answer to "what exact state must be assembled before a dispatch is safe to issue."

---

## Injection shape

- **Policy:** sequential-by-default rule, escape hatch conditions, model-selection mandate, pre-dispatch gate logic, violation signatures.
- **Domain knowledge:** 8-slot prompt assembly spec, dependency closeout distillation approach, lessons.md injection strategy.

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| Validated subagent dispatch prompt | 1 per slice dispatch | No (assembly artifact — written once, launched once) | Bundles slice assignment + context + protocols into a self-contained subagent brief |
| Pre-dispatch gate decision (pass/halt) | 1 per dispatch attempt | No | Determines whether dispatch proceeds or routes to replan/escalate |

---

## Core rules

### Sequential default

**Hard rule:** next dispatch cannot begin until the prior subagent's closeout is fully parsed, validated, and ingested. No queuing, no overlap. Sequential is the default; parallel is opt-in.

### Escape hatch (parallel)

Parallel dispatch is allowed ONLY when **all three** of the following hold simultaneously:

1. Zero `touches` overlap between the slices being parallelized.
2. Zero mutual `depends_on` between the slices.
3. User has explicitly authorized parallel mode for this run (per-run authorization — not a sticky setting).

Default stays sequential. Opt-in, not opt-out. If any condition fails, revert to sequential and warn.

### Model selection

Model MUST be explicit on every dispatch. No inheritance from parent. Default is **sonnet**. Switch to **opus** only when the slice notes flag architectural complexity.

---

## The 8 required prompt slots

<!-- VERBATIM -->
| Slot | Content | Why non-negotiable |
|---|---|---|
| `{{slice_assignment}}` | Full slice file content | Subagent's entire work brief — missing this = no assignment |
| `{{slice_id}}` | Stable slice identifier | Required for closeout cross-reference; missing = unattributable closeout |
| `{{attempt_number}}` | Count of prior closeouts for this slice + 1 | Subagent must know it's attempt N, not attempt 1 |
| `{{dependency_closeouts}}` | Distilled summaries of closeouts for slices in this slice's `depends_on` (validation_result + tests_added + lessons summary — NOT full bodies) | Missing → subagent re-invents contracts already pinned in prior slices (contract drift) |
| `{{prior_attempt_closeouts}}` | Closeouts of prior attempts on this slice (if attempt > 1) | Missing → same failing approach retried verbatim (loop death) |
| `{{lessons_md}}` | Full `.delivery/lessons.md` (no section-filtering; curation happens at write-time not read-time) | Missing → no compounding across slices; each subagent starts cold |
| `{{worker_protocols}}` | Bodies of slice-contract + tdd-contract + closeout-schema | Missing → subagent doesn't know it owes a closeout shape, test-first discipline, or iteration cap |
| `{{model}}` | Explicit model identifier | Missing → cost surprises + non-reproducible runs |

---

## Pre-dispatch checks

The main agent MUST perform all four before issuing any dispatch:

1. **Slice-contract validation** — chosen slice file passes `delivery-execution-slice-contract`. If malformed, refuse dispatch and route to replan.
2. **Dependency check** — all slices listed in this slice's `depends_on` have a `validation_result: pass` closeout. If not, route to replan.
3. **No-in-flight check** — sequential invariant: confirm no subagent is currently executing. If one is in flight (sequential mode), halt and escalate.
4. **Slot completeness** — all 8 prompt slots are populated. If any is missing, abort dispatch (do not launch a partial brief).

---

## Violation signatures

| Violation | Response |
|---|---|
| (a) Two dispatches in flight (sequential mode) | Halt + escalate to user |
| (b) Dispatch without explicit model | Reject — unaudited cost, non-reproducible run |
| (c) Missing any prompt slot | Abort — subagent will hallucinate context |
| (d) Dispatch on slice with unresolved `depends_on` | Route to replan-contract |
| (e) Parallel dispatch without all three escape-hatch conditions | Revert to sequential + warn |

---

## Slot design rationale

### dependency_closeouts: distilled summaries, not full bodies

Passing full closeout bodies inflates prompt budget quadratically as the run grows. Distill to: `validation_result` + `tests_added` (paths) + `lessons summary` (a few lines). Enough for the subagent to know what was settled; not so much that prior slices crowd out the current assignment.

### lessons_md: passed whole, no section-filtering

Relevance scoring at read-time requires judgment the main agent shouldn't spend per dispatch. Instead, `lessons.md` curation happens at **write-time** (replan-contract curates what gets appended). By the time lessons.md is injected, it's already the curated signal; dump it whole.

---

## Cross-cutting context

### "Rolling ball" sequential-by-default rationale (locked turn 9–10)

`parallel-agents-dispatch` is retired as the canonical executor. `delivery-orchestration-plan-executor` is now canonical: sequential by default, mandatory TDD/Ralph, lessons-passed-forward "rolling ball" loop. Sequential mode was chosen because:

- File conflicts in parallel mode require worktrees and merge coordination.
- Lessons compound — each subagent's output improves the next subagent's brief.
- Lower error rate when slices have tight coupling (typical for feature work).

Escape hatch preserved for the rare case of truly independent work packages.

### Structural decision #1 (auto-research reuse)

This protocol's shape (dispatch contract with explicit slot table + sequential gate + model mandate) is intentionally extracted so the `auto-research` skill can adopt it later. auto-research differs in intent (optimize-same-target vs. build-forward) but shares the same dispatch safety requirements. The protocol is authored as a reusable contract, not a plan-executor-specific bespoke rule.

### Subdomain: orchestration

Manager-side concern: how subagents are coordinated, prompts assembled, models selected. Worker-side concerns (what the subagent does) live in `execution` subdomain protocols.

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `delivery-execution-slice-contract` | consumes (pre-dispatch gate) | Slice-contract validation is check #1 of the 4 pre-dispatch checks |
| `delivery-execution-tdd-contract` | consumes (slot body) | Injected as part of `{{worker_protocols}}` slot |
| `delivery-orchestration-closeout-schema` | consumes (slot body + in-flight gate) | Injected as part of `{{worker_protocols}}`; closeout schema defines the object the no-in-flight check inspects |
| `delivery-orchestration-replan-contract` | consumes (sequencing) | Replan completes before next dispatch; dispatch-contract's pre-dispatch checks assume replan has settled all pending mutations |
| `delivery-orchestration-plan-executor` | consumed by (consumer skill) | Plan-executor is the sole authorized caller of this protocol |

---

## Open questions

None.
