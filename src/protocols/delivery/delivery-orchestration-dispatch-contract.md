---
name: delivery-orchestration-dispatch-contract
description: "Sequential-by-default subagent dispatch contract — 8 mandatory prompt slots, 5 pre-dispatch checks, explicit model selection, parallel escape hatch with three named conditions"
domain: delivery
subdomain: orchestration
subject: dispatch
kind: contract
version: 2
status: stable
tags: [dispatch, sequential-default, prompt-assembly, pre-dispatch-checks, escape-hatch]
---

# Dispatch Contract

This is the main agent's pre-flight checklist. Nothing may be dispatched unless this contract is satisfied — every slot populated, every check passed, every model named. Without it, orchestrators dispatch a second subagent before the first closeout is ingested (losing the rolling-ball compounding effect), omit dependency closeouts (subagent re-invents contracts already pinned by prior slices), omit prior-attempt closeouts (same failing approach retried verbatim — loop death), forget worker protocols (subagent doesn't know it owes a closeout, test-first discipline, or iteration cap), and skip explicit model selection (cost surprises, non-reproducible runs). The protocol exists because each of these failures was observed when orchestration was left to ad-hoc judgment.

## Contract Rules

1. **Sequential by default.** The next dispatch cannot begin until the prior subagent's closeout is fully parsed, validated by `delivery-orchestration-closeout-schema`, and ingested. No queueing, no overlap.

2. **Parallel escape hatch — all three conditions required, every dispatch.** Parallel dispatch is permitted ONLY when all three hold simultaneously for the candidate slice pair (or set):
   1. Zero `touches` overlap between the slices.
   2. Zero mutual `depends_on` between the slices.
   3. **In-session** user authorization for this run (not a config flag, not a sticky setting — each parallel attempt is explicitly authorized).

   If any condition is uncertain, revert to sequential and warn. The cost of one extra sequential dispatch is far below the cost of a write conflict or plan-divergence incident.

3. **Model selection is explicit, every dispatch.** No inheritance from the parent agent. Default: `sonnet`. Switch to `opus` only when the slice file flags architectural complexity.

4. **The 8 prompt slots are all required, every dispatch:**

   | Slot | Content | Why non-negotiable |
   |---|---|---|
   | `{{slice_assignment}}` | Full slice file content | Subagent's entire brief — missing = no assignment |
   | `{{slice_id}}` | Stable slice identifier | Required for closeout cross-reference |
   | `{{attempt_number}}` | Prior closeouts for this slice + 1 | Subagent must know whether it's attempt 1, 2, or N |
   | `{{dependency_closeouts}}` | Distilled summaries (validation_result + tests_added paths + lessons summary) for closeouts of slices in `depends_on` — NOT full bodies | Missing → subagent re-invents pinned contracts (contract drift) |
   | `{{prior_attempt_closeouts}}` | Closeouts of prior attempts on THIS slice (if `attempt_number > 1`) | Missing → same failing approach retried verbatim (loop death) |
   | `{{lessons_md}}` | Full `.delivery/lessons.md` content (curated at write-time by replan-contract; no read-time filtering) | Missing → no compounding across slices; each subagent starts cold |
   | `{{worker_protocols}}` | Bodies of `delivery-execution-slice-contract`, `delivery-execution-tdd-contract`, `delivery-execution-coding-contract`, `delivery-orchestration-closeout-schema` | Missing → subagent doesn't know it owes a closeout, test-first discipline, an iteration cap, or the code-quality discipline (YAGNI, neighbors-first, no-dead-code, fail-loudly, green-tree-exit, security-tripwires) |
   | `{{model}}` | Explicit model identifier | Missing → cost surprises and non-reproducible runs |

5. **Pre-dispatch checks (all five, in order, every dispatch):**
   1. **Slice-contract validation** — the chosen slice file passes `delivery-execution-slice-contract`. On malformation: refuse dispatch; route to replan-contract.
   2. **Dependency check** — every slice listed in this slice's `depends_on` has a `validation_result: pass` closeout. On unmet dependency: route to replan-contract.
   3. **No-in-flight check** — sequential invariant. Confirm no subagent is currently executing. On in-flight: halt and escalate.
   4. **Slot completeness** — all 8 prompt slots are populated. On any missing slot: abort (do not launch a partial brief). In particular, `{{worker_protocols}}` MUST contain all four protocol bodies; absence of `delivery-execution-coding-contract` in the rendered injection is a halt-loud condition, not a soft warn.
   5. **Coding-discipline collision check** — exactly one coding-discipline protocol body is present in `{{worker_protocols}}`. If multiple variants are detected (e.g., a vestigial discipline body alongside `delivery-execution-coding-contract`, or two competing coding-contract drafts), halt-loud and escalate to user. Silent acceptance of a collision would let conflicting code-quality rules reach the subagent.

## Violation Signatures

| ID | Violation | Response |
|---|---|---|
| (a) | Two dispatches in flight (sequential mode) | Halt + escalate to user |
| (b) | Dispatch without explicit `{{model}}` | Reject — unaudited cost, non-reproducible run |
| (c) | Missing any prompt slot | Abort — never launch with a partial brief |
| (d) | Dispatch on a slice with unresolved `depends_on` | Route to replan-contract |
| (e) | Parallel dispatch without all three escape-hatch conditions | Revert to sequential + warn the user |
| (f) | `{{worker_protocols}}` rendered without `delivery-execution-coding-contract` body | Halt-loud — never dispatch without code-quality discipline |
| (g) | Multiple coding-discipline variants present in `{{worker_protocols}}` | Halt-loud + escalate to user |

## Slot Design Rationale

### `{{dependency_closeouts}}` — distilled, not full
Passing full closeout bodies inflates prompt budget quadratically as the run grows. Distill to: `validation_result`, `tests_added` (paths only), and a short lessons summary. Enough for the subagent to know what was settled by prior slices; not so much that prior slices crowd out the current brief.

### `{{lessons_md}}` — passed whole, no section-filtering
Relevance scoring at read-time is judgment the main agent should not spend per dispatch. Curation happens at **write-time** in `delivery-orchestration-replan-contract` — by the time `lessons.md` is injected, it is already the curated signal. Dump it whole.

### `{{worker_protocols}}` — four bodies, not by reference
The subagent runs in a fresh context with no access to the main agent's loaded protocols. Bodies MUST be inlined into the prompt: `delivery-execution-slice-contract`, `delivery-execution-tdd-contract`, `delivery-execution-coding-contract`, `delivery-orchestration-closeout-schema`. Reference-only would force the subagent to load files it cannot reach.

## "Rolling-ball" Sequential Rationale

`parallel-agents-dispatch` is retired as the canonical executor. This contract makes sequential the default for `delivery-orchestration-plan-executor` because:

- File conflicts in parallel mode require worktrees and merge coordination — overhead that erases the throughput gain on coupled work.
- Lessons compound — each subagent's `lessons_learnt` improves the next subagent's brief. Parallel breaks compounding.
- Coupled feature work has a much lower error rate sequentially. Most slices in practice ARE coupled.

The escape hatch exists for the rare case of truly independent slices — keeping the option open without making it the path of least resistance.

## Reusability — `optimization-process-researcher` Adoption

This contract's shape (8-slot table + sequential gate + model mandate) is intentionally extracted as a reusable shape, not bespoke to `delivery-orchestration-plan-executor`. `optimization-process-researcher` differs in intent (optimize-same-target vs. build-forward) but shares the same dispatch-safety requirements and can adopt this contract unchanged when ready.

## Edge Cases

| Edge case | Handling |
|---|---|
| Slice's `depends_on` references a slice with no closeout yet | Pre-dispatch check #2 fails → route to replan (cannot dispatch out of dependency order) |
| Subagent crashes before emitting closeout | No-in-flight check #3 surfaces stale dispatch; main agent treats as `failed`, increments attempt counter |
| User says "go parallel" but two candidate slices share one file in `touches` | Escape-hatch condition 1 violated → revert to sequential + warn (DO NOT honor the user's request when conditions fail) |
| Lessons.md is empty (early in run) | Inject as empty content — slot is still required to be present (an empty body counts as populated) |
| Slice flags architectural complexity but no model preference | Default escalation: select `opus` and log the rationale alongside the dispatch |

## Failure Reporting

When a violation of this protocol is detected, the main agent MUST immediately emit the following tag using the `synapse-observability-failure-reporting-schema` format, then halt or escalate per the response column in the Violation Signatures table:

```
PROTOCOL FAILURE: delivery-orchestration-dispatch-contract <slice_id> [violation_id reason]
```

Where `violation_id` is the letter from the Violation Signatures table (a–g) and `reason` is a one-line description of the unmet condition.

## Injection

This protocol is loaded by `delivery-orchestration-plan-executor` at the `[DISPATCH]` node. The protocol governs the main agent's behavior at dispatch assembly time — the subagent never sees this contract directly (only its outputs: the bundled prompt and the worker protocols carried within).
