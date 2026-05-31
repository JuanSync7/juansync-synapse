# Decision Memo — delivery-execution-tdd-contract

> Artifact type: protocol | Memo type: creation | Design doc: `.brainstorms/2026-05-22-plan-execution-vertical-slice-orchestration/design.md`

---

## What I want

A behavioral protocol that governs what a subagent does **inside** its assigned slice. It collapses three previously separate concepts into one protocol:

1. **Validable end-goal** — the slice's acceptance criterion, expressed as a failing test (the "red" in TDD red).
2. **Ralph loop** — the iterate-until-green wrapper: don't surrender after one attempt; keep iterating up to the cap.
3. **Inner TDD** — red-green-refactor discipline on each iteration of the Ralph loop.

The protocol is injected into every subagent dispatch as part of `{{worker_protocols}}`. It is enforced by the subagent (first-edit-is-test bright line) and verified by the main agent post-closeout (compliance and violation signature checks).

---

## Why Claude needs it

Without this protocol, LLM subagents exhibit two failure modes:

1. **Premature surrender.** The agent hits a wall after one or two test failures, rationalizes stopping, and reports a partial result as complete. No test encodes the outcome; no iteration budget is consumed.
2. **Code-first drift.** The agent writes production code first, then retrofits a test to match what the code does — which vacuously passes. The test no longer encodes the stated validable outcome; the pass is fabricated.

Both are silent failures. They surface only when the main agent inspects the closeout — by which point lessons have not compounded and the plan has not been updated. The protocol makes both violations detectable (violation signatures) and the expected loop shape explicit.

**Upstream backlog resolution:** this protocol resolves Backlog item B2 from `.brainstorms/2026-04-28-tracer-tdd-slicing/notes.md` — *"file `tracer-bounded-tdd` protocol + `tdd-runner` agent only if/when 3+ skills repeat TDD language."* The plan-executor skill and two sibling protocols (`delivery-execution-slice-contract`, `delivery-orchestration-closeout-schema`) all carry TDD language. We are at the threshold. One canonical protocol replaces scattered inline repetition.

---

## Injection shape

- **Policy:** judgment and compliance rules for how the subagent must behave from first file-edit through final green.
- **Workflow:** the 5-step discipline below defines the ordered execution shape inside a subagent's execution.

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| Behavioral compliance in subagent execution | 1 per dispatch | No | Ensures test-first, iterate-to-green discipline |
| `validation_result` in closeout | 1 per dispatch | No | Signals pass/blocked/failed for main agent ingestion |
| `tests_added` list in closeout | 1 per dispatch | No | Carries test path(s) encoding the validable outcome |

---

## The 5-step discipline

The subagent MUST follow these steps in order at the start of every slice execution:

1. **Read the validable outcome** from the slice assignment file.
2. **Express it as a failing test.** This test IS the done-definition. The test must fail before any production code is written.
3. **Ralph loop:** `write minimum code → run tests → observe result → adjust` until the outcome test is green. Do not surrender after the first failure.
4. **Inner TDD per iteration:** for any subordinate assertions added en route, maintain red → green → refactor discipline within that iteration.
5. **Exit when:** the outcome test is green AND no in-scope tests regressed.

---

## Key design decisions

### Iteration cap: default 10, SKILL-OVERRIDABLE

The iteration cap is **not a hard constant** baked into the protocol. The default is 10 iterations per slice. The orchestrator skill MAY override this at dispatch time via a slot in the `{{worker_protocols}}` injection prompt. Rationale: different slice sizes, different project risk tolerances. The protocol defines the cap semantics (hitting cap = `blocked`, not silent surrender); the orchestrator controls the value.

Hitting the cap MUST produce `validation_result: blocked` in the closeout. Never silent surrender.

### What Ralph adds over plain TDD

TDD says "write test, make it pass." Ralph says "don't give up after one try." LLM agents pattern-match their way into dead ends, then rationalize stopping ("this approach won't work; I'll note it in the closeout"). The iteration cap — not the first failure — is the exit door. Ralph makes persistence the default; `blocked` is the honest signal when persistence is genuinely exhausted.

### Framework agnostic

The protocol body MUST NOT name any specific test framework (no pytest, jest, go test, etc.). The test framework is determined by the slice file's `touches` field and the project's own conventions. The protocol governs discipline; the project governs tooling.

### Three facets, one protocol

TDD + Ralph + validable-end-goal are NOT three separate protocols. Structural decision #3 from the brainstorm: the validable end-goal IS the failing test (TDD red); Ralph IS the iterate-until-green wrapper; inner TDD IS red-green-refactor per iteration of that wrapper. Collapsing into one protocol avoids a multi-protocol injection burden on every dispatch and eliminates the risk that any one facet is omitted.

---

## Compliance signature

The main agent verifies compliance post-closeout. All three MUST hold for a compliant execution:

1. First file-edit by the subagent is a test file, not production code. (Bright line — no exceptions.)
2. Closeout reports `validation_result: pass` with `outcome_test_path` populated.
3. The `outcome_test_path` value appears in `tests_added` in the closeout.

---

## Violation signatures

Any of the following triggers a closeout rejection by the main agent:

| Violation | Signal | Main agent action |
|---|---|---|
| (a) Production code edited before any test | First edit is non-test file | Reject closeout; route to replan |
| (b) `validation_result: pass` without a test encoding the stated validable outcome | `outcome_test_path` absent or test doesn't cover outcome | Reject as fabricated pass |
| (c) Subagent surrendered before iteration cap | `blocked` reason absent; iterations_used < cap | Reject as premature give-up |
| (d) Subagent disabled or weakened tests to force green | Tests deleted, skipped, or assertion guards removed | Reject AND flag for human review |

Violation (d) is the cheating signature. It cannot be auto-resolved by replan — human review is mandatory.

---

## Edge cases considered

| Edge case | Handling |
|---|---|
| Slice's validable outcome cannot be expressed as a test | Protocol requires a test; if no test is possible, the slice is malformed — main agent rejects it pre-dispatch via slice-contract |
| No test framework discoverable in project | Pre-flight check in plan-executor skill (not in this protocol); halt loud before first dispatch |
| Subagent hits cap on first attempt | `blocked` closeout; main agent routes to replan-contract for re-decompose or mark-blocked decision |
| Subagent produces a passing test that doesn't encode the actual outcome | Violation (b) — fabricated pass; caught post-closeout by cross-referencing `validable_outcome` vs test content |
| Multiple subordinate tests fail during Ralph iterations | Inner TDD (step 4) governs — fix each regression before proceeding; exit only when ALL in-scope tests green |

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `delivery-execution-slice-contract` | consumes | Names the unit + validable outcome; tdd-contract names what the subagent does with that outcome. Neither stands alone. |
| `delivery-orchestration-closeout-schema` | produces for | `test_path` field in closeout is the outcome test path this protocol requires the subagent to populate |
| `delivery-orchestration-dispatch-contract` | injected via | Protocol body is carried in the `{{worker_protocols}}` slot; dispatch-contract mandates this slot |

---

## Open questions

None. All threads resolved during brainstorm lens rotation (TC-B1 locked iteration cap as skill-overridable; "Ralph adds over plain TDD" rationale confirmed turn 10; framework-agnostic confirmed at lens rotation; cheating signature confirmed as human-review flag).
