# Decision Memo — test-generate

> Artifact type: skill | Memo type: creation | Design doc: `.brainstorms/2026-04-28-test-strategy-improvements/design.md`

---

## What I want

A semi-autonomous test-generation skill that is the **core value** and most complex component of the autonomous test coverage engine. It receives an `AuditGapReport` from `test-audit`, then works through each coverage gap in priority order: mapping branches, crafting test inputs that reach every leaf, applying Hypothesis property tests where invariants exist, generating test files with fully descriptive docstrings, running each test to verify it passes green, running per-gap mutation testing to verify assertions are strong, scoring assertion quality, and then stopping at a **hard gate** to present the reviewer with a plain-English descriptive-intent list (not test code) for approval before committing anything. On approval it commits the tests and updates `COVERAGE_STATE.yaml`. On rejection it marks the gap as human-rejected and iterates.

The skill must enforce: no per-line tests, no `assert True` padding, ≥2 assertions per test, mock-by-default, descriptive docstring required on every generated test, and failing tests are never committed.

---

## Why Claude needs it

Without this skill Claude defaults to problematic generation patterns that silently undermine test quality:

- **Per-line tests:** Claude writes one test per source line, inflating coverage numbers while covering no branching logic.
- **`assert True` / `assert 1` padding:** Claude pads test count to satisfy coverage thresholds with vacuous assertions that assert nothing about behavior.
- **No mutation validation:** Claude has no mechanism to verify whether its assertions would catch a mutated version of the code — weak assertions pass through undetected.
- **No descriptive intent:** Claude omits or truncates docstrings, leaving reviewers unable to evaluate what the test is supposed to prove without reading implementation details.
- **No hard gate:** Without a stopping point, Claude commits untrusted tests directly, making it impossible for a human to approve or reject the testing strategy at the intent level before implementation is locked in.
- **No Hypothesis adoption:** Claude defaults to example-only tests, missing the property-based coverage for pure functions with structured inputs where invariants exist.

---

## Injection shape

- **Workflow:** 9-step generation loop per coverage gap, with a hard gate at step 8 that stops the engine and waits for human approval of a descriptive-intent list before committing anything.
- **Policy:** Judgment rules loaded always — generation constraints (no per-line, no `assert True`, ≥2 assertions, descriptive docstring required, mock-by-default); assertion policy (equality, raises, mock.assert_*, parametrize, approx); Hypothesis policy (apply when invariant exists, ≥30% of unit tests, `from_type` for type-hint-derived strategies).

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| Test file(s) with descriptive docstrings | 1 per gap (appended to existing file if one exists) | Yes | Closes the coverage gap identified in `AuditGapReport` |
| Updated `COVERAGE_STATE.yaml` | 1 (cumulative) | Yes | Tracks which gaps have been closed, which are human-rejected, validation status per test |
| Generation PR (hard-gate) | 1 per batch | Temporary | Presents descriptive-intent list to reviewer; engine stops until approved or rejected |

---

## Flow graph

```
generate produces tests
  ↓
extract descriptive-intent list from docstrings
  ↓
open PR with intent list as PR body
  ↓
notify reviewer (Slack/email — blocking)
  ↓
WAIT
  ↓ (approve)         ↓ (reject)
commit + update     mark gaps as
COVERAGE_STATE      "human-rejected", iterate
```

---

## Node specifications

**[STEP 1 — BRANCH MAP]** Load: `references/layer-unit.md`, source file under gap. Do: Run `branch_mapper` tool on the target function — build a map of public-function entry point → all reachable `_private` calls → all leaf branches (if/else, early return, raise). Don't: inspect `_private` function internals directly — cover through public callers only; if a `_private` function cannot be reached via any public caller, mark as implementation-coupled in `COVERAGE_STATE.yaml`. Exit: branch map ready → STEP 2.

**[STEP 2 — INPUT CRAFTING]** Load: `references/layer-unit.md`, `references/layer-contract.md` (if applicable). Do: For each leaf branch in the map, craft a minimal concrete input that exercises that branch through the public function. Use type hints and existing test fixtures as guides. Don't: generate inputs that skip the public API to call `_private` functions directly. Exit: input set per branch → STEP 3.

**[STEP 3 — HYPOTHESIS DECISION]** Load: `references/hypothesis-strategies.md`. Do: Evaluate each test candidate against the Hypothesis policy — apply Hypothesis when: pure function with structured inputs; statable invariant; user-shaped data. Use `hypothesis_strategy_generator` tool with `from_type` to derive strategies from type hints. Target ≥30% of the unit tests for this gap as property-based. Don't: apply Hypothesis when: single obvious mapping; nothing universal to assert; side-effect-heavy function without an invariant. Exit: each test candidate flagged as example-test or property-test → STEP 4.

**[STEP 4 — TEST FILE GENERATION]** Load: `rules/generation-constraints.md` (always-loaded), `references/assertion-policy.md` (always-loaded), `references/descriptive-test-schema.md`, `templates/test-file.md`. Do: Generate test file (or append to existing file if one already covers this module). Each test must have a descriptive docstring with all five tags: `@tests`, `@scenario`, `@asserts`, `@layer`, `@generation_id`. Include ≥2 assertions per test (structural + value). Mock all external dependencies. Don't: write per-line tests; write `assert True` or `assert 1`; create a new file if an existing test file covers this module; suppress docstring tags. Exit: test file draft ready → STEP 5.

**[STEP 5 — GREEN RUN]** Load: none additional. Do: Execute the generated tests with pytest. All generated tests must pass. Don't: commit anything if any test fails. Exit: all tests green → STEP 6. Any test red → return to STEP 4 (diagnose and fix, or discard the failing test and log it as unresolvable in `COVERAGE_STATE.yaml`).

**[STEP 6 — MUTATION VALIDATION]** Load: none additional (mutation_runner is a tool call). Do: Run `mutation_runner` tool scoped to only the lines just covered (~5–20 lines per gap). All mutants must be killed. This is per-gap scope (seconds of wall-clock cost, not hours). Don't: run full-project mutation at this step — that is the nightly job. Exit: all mutants killed → STEP 7. Surviving mutants → return to STEP 4 to strengthen assertions.

**[STEP 7 — ASSERTION QUALITY SCORE]** Load: `references/assertion-policy.md` (always-loaded). Do: Run `assertion_quality` tool on the generated tests. Score must meet project threshold. Check: ≥2 assertions per test; no `assert True` / `assert 1`; no mocking the thing being tested; no copy-paste tests (AST hash dedup). Don't: pass a test to the hard gate that scores below threshold. Exit: quality threshold met → STEP 8.

**[STEP 8 — HARD GATE: INTENT REVIEW]** Load: `templates/generation-pr.md`. Do: Extract a plain-English descriptive-intent list from the test docstrings — one line per test in the format `<function> — <scenario> → <asserts>`. Open PR with this list as the PR body. Notify reviewer via blocking notification (Slack/email). Stop the engine and wait. Don't: commit test files before approval; continue to next gap before this gate resolves. Exit: approved → STEP 9. Rejected → mark affected gaps as `human-rejected` in `COVERAGE_STATE.yaml`, iterate back to STEP 1 for remaining gaps.

**[STEP 9 — COMMIT AND STATE UPDATE]** Load: none additional. Do: Commit the approved test files. Update `COVERAGE_STATE.yaml` with: gap closed, auto-generated test IDs, validation status (green + mutants killed + approved), `generation_id`. Run `coverage_analyzer` to verify the gap is actually closed in the coverage map. Run `log_contract_validator` to verify generated tests exercise log paths correctly if the function under test emits logs. Don't: close a gap in state before verifying coverage actually improved. Exit: state updated → move to next gap in priority order.

---

## Entry gates

| Transition | Gate |
|---|---|
| STEP 5 red → STEP 4 | Hard: test failure — diagnose before retrying; discard if unresolvable |
| STEP 6 surviving mutants → STEP 4 | Hard: mutation survival — must strengthen assertions before proceeding |
| STEP 7 below threshold → STEP 4 | Hard: assertion quality score below project threshold |
| STEP 8 WAIT → STEP 9 | **Hard gate (HITL):** engine stops; reviewer must explicitly approve the descriptive-intent list; no timeout auto-approval |
| STEP 8 rejected → STEP 1 | Hard: mark gap `human-rejected`; do not re-attempt without new `AuditGapReport` or explicit re-trigger |

---

## Edge cases considered

| Edge case | Handling |
|---|---|
| Failing generated test | Never committed. Return to STEP 4. If test cannot be made green after diagnosis, discard and log as `unresolvable` in `COVERAGE_STATE.yaml`. |
| `_private` function coverage | Cover through public callers only. If no public caller reaches it, mark as `implementation-coupled` in `COVERAGE_STATE.yaml` — do not write a test that calls it directly. |
| Existing test file for module | Append tests to existing file. Never create a second test file for the same module — it fractures test discovery and fixture reuse. |
| Mutation kill threshold | Starts at "all mutants killed for new gaps" (strictest). Project-wide threshold tuned post-hoc based on volume. Gap cannot be closed in state if mutants survive. |
| Hypothesis target not met (< 30% property-based) | Log gap in `COVERAGE_STATE.yaml` as `hypothesis_deficit`; surface in next audit cycle. Do not block the current generation — 30% is a target, not a per-gap hard requirement. |
| Reviewer rejects entire intent list | Mark all gaps in the batch as `human-rejected`. Do not partially commit. Iterate from STEP 1 on remaining unresolved gaps. |
| PR already open for this batch | Detect existing open PR before opening a new one; update PR body with revised intent list rather than duplicating. |
| `log_contract_validator` failure in STEP 9 | Surface as a warning in `COVERAGE_STATE.yaml`; do not block the commit — log-path coverage is a separate metric, not a blocking gate at this stage. |

---

## Companion files anticipated

**Always-loaded (present at every node):**
- `rules/generation-constraints.md` — never per-line tests; never `assert True`; ≥2 assertions per test; must include descriptive docstring; mock-by-default. Loaded at STEP 4 and enforced throughout.
- `references/assertion-policy.md` — pattern-matching guide: equality, raises, `mock.assert_*`, parametrize, `approx`, etc. Loaded at STEP 4 and STEP 7.

**References (loaded on-demand at relevant steps):**
- `references/hypothesis-strategies.md` — Hypothesis policy, `from_type` usage, CI tier targets (`max_examples=100` on PR, `max_examples=1000` nightly). Loaded at STEP 3.
- `references/descriptive-test-schema.md` — full tag specification for `@tests`, `@scenario`, `@asserts`, `@layer`, `@generation_id`. Loaded at STEP 4.
- `references/layer-unit.md` — unit test conventions and patterns. Loaded at STEP 1, STEP 2.
- `references/layer-config.md` — pydantic + cross-field constraint test patterns. Loaded on demand.
- `references/layer-contract.md` — DB, API, schema, file format, queue, CLI contract test patterns. Loaded on demand.
- `references/layer-idempotency.md` — process-twice invariant patterns. Loaded on demand.
- `references/layer-mock-integration.md` — end-to-end with mocks patterns; mock-by-default rationale. Loaded at STEP 4.

**Templates:**
- `templates/test-file.md` — canonical test file structure with descriptive docstring block. Loaded at STEP 4.
- `templates/generation-pr.md` — descriptive-intent list format for the hard gate PR body. Loaded at STEP 8.

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `test-audit` | Consumes from | `AuditGapReport` pydantic model from `ai-synapse/tools/testing/schemas.py` — gaps list, priority ranking (critical/standard/cold tiers), gaming alerts, project SHA |
| `test-evaluate` | Produces for | `CoverageState` pydantic model — closed gaps, auto-generated test IDs, validation status, `generation_id`s; also produces the mocked-integration test files that `evaluate` will classify for real-integration promotion |
| `ai-synapse/tools/testing/` | Consumes from | `branch_mapper`, `mutation_runner`, `hypothesis_strategy_generator`, `assertion_quality`, `coverage_analyzer`, `log_contract_validator`, `benchmark_selector` tools |
| `project/coverage/state/COVERAGE_STATE.yaml` | Produces to | Updated per-gap after STEP 9; `human-rejected` entries written on hard-gate rejection |

---

## Open questions

1. **Mutation kill-rate threshold calibration:** The current stance is "all mutants killed for newly generated gaps" (strictest). Once the first real project is run through this engine, the project-wide threshold needs to be tuned. Creator should decide whether the threshold is surfaced as a config key in the skill or locked as a hard constraint.
2. **Token budget per generation cycle:** Not measured yet. The 9-step loop may be expensive on large gap lists. Creator should measure during first build and add a configurable `max_gaps_per_run` parameter if needed.
3. **Benchmark candidate integration:** `benchmark_selector` is listed as a used tool. The exact integration point (does `generate` write benchmark tests, or only flag candidates for human authoring?) is unresolved. Creator decides.
