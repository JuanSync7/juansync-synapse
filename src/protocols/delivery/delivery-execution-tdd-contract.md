---
name: delivery-execution-tdd-contract
description: "Subagent execution discipline — test-first, Ralph-loop-to-green, cap-aware blocked. Collapses TDD, Ralph, and validable-end-goal into one contract injected into every dispatch."
domain: delivery
subdomain: execution
subject: tdd
kind: contract
version: 1
status: stable
tags: [tdd, ralph-loop, validable-outcome, subagent-discipline, iteration-cap]
---

# TDD Contract

LLM subagents have two failure modes inside a slice. Without persistence, they surrender after one or two test failures, rationalize stopping, and report a partial result as complete. Without a test-first bright line, they write production code, then retrofit a vacuously-passing test. Both are silent — they surface only when the main agent inspects the closeout, by which point lessons have not compounded and the plan has not been updated. This contract collapses three facets that are easier to enforce together than apart: the **validable end-goal** is the failing test (TDD red); **Ralph** is the iterate-until-green wrapper; **inner TDD** is red-green-refactor inside each iteration. Three names, one discipline, one protocol.

## Contract Rules

1. **Test-first bright line.** The subagent's FIRST file-edit MUST be a test file. No exceptions. The test encodes the slice's `validable_outcome` and MUST fail on first run.

2. **The 5-step discipline (in order, every dispatch):**
   1. Read the `validable_outcome` from the slice assignment.
   2. Express it as a failing test. This test IS the done-definition.
   3. **Ralph loop:** `write minimum code → run tests → observe → adjust` until the outcome test is green. Persist until the iteration cap, not the first failure.
   4. **Inner TDD per iteration:** for subordinate assertions added en route, maintain red → green → refactor inside that iteration.
   5. Exit when the outcome test is green AND no in-scope tests have regressed.

3. **Iteration cap = `blocked`, never silent surrender.** The default cap is **N=10** iterations per slice. The cap is **skill-overridable** at dispatch time (per **TC-B1**) via the `{{worker_protocols}}` injection — different slice sizes and project risks warrant different values. Hitting the cap MUST produce `validation_result: blocked` in the closeout with `blocked_reason` populated. Rational surrender is `blocked`; silent give-up is a violation.

4. **Framework-agnostic.** This protocol body MUST NOT name a specific test framework (pytest, jest, go test, etc.). The framework is determined by the slice's `touches` field and the project's own conventions. The protocol governs discipline; the project governs tooling.

5. **No nested subagent dispatch.** A subagent under this contract MUST NOT dispatch its own subagents. If the slice cannot be completed in one execution, the slice was too big — emit `blocked` and let the main agent re-decompose via `delivery-orchestration-replan-contract`.

## Compliance Signature

All three must hold for a compliant execution:

1. The subagent's first file-edit is a test file (bright line, no exceptions).
2. The closeout reports `validation_result: pass` with `outcome_test_path` populated.
3. The value of `outcome_test_path` appears in the closeout's `tests_added` list.

## Violation Signatures

Any of these triggers a closeout rejection by the main agent:

| ID | Violation | Signal | Main agent action |
|---|---|---|---|
| (a) | Production code edited before any test | First edit is non-test file | Reject closeout; route to replan-contract |
| (b) | Fabricated pass — `validation_result: pass` without a test that actually encodes the stated `validable_outcome` | `outcome_test_path` absent, or test content does not encode the outcome | Reject as fabricated pass |
| (c) | Premature surrender | `blocked` reported but `iterations_used` < cap and no `blocked_reason` justifies stopping early | Reject as premature give-up |
| (d) | Test cheating | Tests deleted, skipped, assertion guards removed, or `pytest.skip`/`xfail` introduced to force green | Reject AND flag for human review — cannot be auto-resolved by replan |

Violation (d) is the cheating signature. The main agent MUST surface it to the operator; it is the one violation that does not auto-route to replan.

## Edge Cases

| Edge case | Handling |
|---|---|
| Slice's `validable_outcome` cannot be expressed as a test | Slice is malformed — main agent rejects pre-dispatch via `delivery-execution-slice-contract` violation (a); does not reach this protocol |
| No test framework discoverable in project | Pre-flight check in `delivery-orchestration-plan-executor`; halt loud before first dispatch — this contract is unenforceable without a framework |
| Subagent hits cap on first attempt | `blocked` closeout with `blocked_reason` populated; main agent routes to `delivery-orchestration-replan-contract` |
| Multiple subordinate tests fail during Ralph iterations | Inner TDD (rule 2 step 4) governs — fix each regression before proceeding; exit only when ALL in-scope tests are green |
| Outcome test passes but unrelated in-scope test regresses | Not exit-eligible (rule 2 step 5) — keep iterating until the regression is fixed |

## Configuration

| Knob | Default | Overrideable by | Notes |
|---|---|---|---|
| Iteration cap (Ralph budget) | 10 | Orchestrator skill, per dispatch (TC-B1) | Cap hit ⇒ `blocked`. Reducing the cap on small slices is reasonable; raising it on architectural slices is reasonable. The protocol semantics do not change. |

## Failure Reporting

Violations of this protocol use the `synapse-observability-failure-reporting-schema` format:

```
PROTOCOL FAILURE: delivery-execution-tdd-contract <slice_id> [violation_id reason]
```

## Injection

This protocol's body is injected into every subagent dispatch via the `{{worker_protocols}}` slot of `delivery-orchestration-dispatch-contract`. The subagent enforces rules 1, 2, 4, 5 during execution; the main agent verifies compliance and detects violations post-closeout. The iteration cap value is passed alongside the protocol body so the subagent knows its budget for this dispatch.

## Linkage

- `delivery-execution-slice-contract` names the unit and the `validable_outcome`; this protocol governs what the subagent does with that outcome. Neither stands alone.
- `delivery-orchestration-closeout-schema` is the reporting surface; this contract dictates which fields (`validation_result`, `outcome_test_path`, `tests_added`, `iterations_used`, `blocked_reason`) are non-negotiable.
- Resolves backlog item B2 from `.brainstorms/2026-04-28-tracer-tdd-slicing/notes.md` — one canonical TDD protocol replaces scattered inline repetition once 3+ artifacts reference it.
