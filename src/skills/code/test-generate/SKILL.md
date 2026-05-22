---
name: test-generate
description: "consume an AuditGapReport from test-audit and generate descriptive-docstring tests gap-by-gap with branch mapping, Hypothesis where invariants exist, green-run + per-gap mutation + assertion-quality gates, then HARD-GATE on a descriptive-intent PR before any commit"
domain: code
subdomain: test
scope: module
role: generator
tags: [test, generate, pytest, hypothesis, mutation, descriptive-test, hard-gate]
user-invocable: true
argument-hint: "[--audit-report PATH] [--max-gaps N] [--mutation-threshold all|N] [--no-pr]"
---

Third stage of the 6-skill test coverage engine. Consumes `AuditGapReport` from `test-audit`; iterates each gap in priority order through a 9-step loop (branch-map → input-craft → hypothesis-decision → generate → green-run → mutation → assertion-quality → **hard-gate intent review** → commit + state). Engine STOPS at the hard gate and waits for reviewer approval of a plain-English descriptive-intent list before any test is committed.

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

## MUST (every turn)
- Load `rules/generation-constraints.md` and `references/assertion-policy.md` — invariants apply at every generation node
- Record position: `Position: [node-id] — <context>`
- Process gaps in `AuditGapReport` priority order (critical → standard → cold)
- Run all gates (green-run, mutation, assertion-quality) before the hard gate; never bypass

## MUST NOT (global)
- Write per-line tests, `assert True`, `assert 1`, or any vacuous-assertion padding
- Generate a test without a 5-tag descriptive docstring (`@tests`, `@scenario`, `@asserts`, `@layer`, `@generation_id`)
- Commit any test before the hard gate (STEP 8) returns approved
- Call `_private` functions directly — cover them through public callers only
- Create a second test file for a module that already has one — append instead
- Auto-approve, timeout-approve, or simulate human approval at the hard gate
- Run full-project mutation testing inside the loop — STEP 6 is per-gap scoped (~5–20 lines)

## Wrong-Tool Detection
- **User has no AuditGapReport on disk** → `/test-audit` first, then return here
- **User wants to run/execute existing tests** → `/test-runner`
- **User wants to evaluate test quality of existing suite** → `/test-evaluate`
- **User wants to fix lint findings** → `/test-fix`

## Entry

### [NEW] Fresh session
Do:
  1. Parse arguments: `--audit-report` (default `project/coverage/state/AUDIT_GAP_REPORT.json`), `--max-gaps` (default unlimited), `--mutation-threshold` (default `all` = all-mutants-killed), `--no-pr` (skip [GATE]; write intent list to disk and stop).
  2. Load `AuditGapReport` from disk; verify it parses against `src/skills/code/test-evaluate/schemas.py` `AuditGapReport` model.
  3. If `gaps` is empty → print "no gaps to close — coverage already meets thresholds" and exit (no PR, no state mutation).
  4. Confirm engine tools available in `src/tools/testing/`: `branch_mapper`, `hypothesis_strategy_generator`, `mutation_runner`, `assertion_quality`, `coverage_analyzer`, `log_contract_validator` (invoke as `python -m src.tools.testing.<tool>`). Abort if missing.
  5. Initialize `closed_gaps`, `unresolvable_gaps`, `human_rejected_gaps` accumulators; generate batch `generation_id` (UUID).
Don't: Proceed if report cannot be parsed; touch source code; pre-commit anything.
Exit: → [BRANCH-MAP] (first gap)

## Flow

### [BRANCH-MAP] Map public-function branches
Load: rules/generation-constraints.md, references/assertion-policy.md, references/layer-unit.md
Do: For the current gap, run `branch_mapper` on the target public function. Build a tree: public entry → reachable `_private` calls → leaf branches (if/else, early return, raise, with-block exits). If a `_private` function is unreachable from any public caller, mark gap as `implementation-coupled` in the state buffer and skip to the next gap.
Don't: Inspect `_private` internals directly; descend into stdlib or third-party code.
Exit: → [INPUT-CRAFT] (branch map ready) | → [BRANCH-MAP] (next gap, if current marked implementation-coupled)

### [INPUT-CRAFT] Craft minimal inputs per branch
Load: rules/generation-constraints.md, references/assertion-policy.md, references/layer-unit.md, references/layer-contract.md
Do: For each leaf branch in the map, craft a minimal concrete input that exercises that branch through the public API. Use type hints, existing fixtures, and pydantic schemas as guides. Note any branch that only fires on side-effect state (env var, filesystem, time) — these need fixtures or freezegun, not raw inputs.
Don't: Skip the public API to construct inputs that hit `_private` directly; reuse oversized fixtures that obscure what's exercised.
Exit: → [HYPOTHESIS]

### [HYPOTHESIS] Decide example-test vs property-test
Load: rules/generation-constraints.md, references/assertion-policy.md, references/hypothesis-strategies.md
Do: For each candidate test, apply Hypothesis when (pure function + structured input + statable invariant). Use `hypothesis_strategy_generator` with `from_type` to derive strategies from type hints. Target ≥30% of unit tests in this gap as property-based; track with a counter on the gap.
Don't: Apply Hypothesis to single-mapping cases, side-effect-heavy code without a clean invariant, or where assertions would just restate the implementation.
Exit: → [GENERATE]

### [GENERATE] Write test file (or append)
Load: rules/generation-constraints.md, references/assertion-policy.md, references/descriptive-test-schema.md, references/layer-unit.md, references/layer-mock-integration.md, templates/test-file.md
Do: If a test file already covers this module, append; otherwise create one from `templates/test-file.md`. Each test gets a 5-tag docstring (`@tests`, `@scenario`, `@asserts`, `@layer`, `@generation_id={batch}`), ≥2 assertions (structural + value), and mocks all external dependencies by default.
Don't: Write per-line tests; use `assert True`/`assert 1`; mock the unit under test; create a second file for a module already covered; suppress or shorten any of the 5 docstring tags.
Exit: → [GREEN-RUN]

### [GREEN-RUN] Verify all generated tests pass
Do: Run pytest scoped to the generated test file. Every generated test must pass green. If a test fails: diagnose once and rewrite at [GENERATE]; if still red, discard the failing test and log it under the gap as `unresolvable` in the state buffer with a one-line reason.
Don't: Commit; advance with red tests in the file; loop more than once on the same failing test.
Exit: → [MUTATE] (all green) | → [GENERATE] (one diagnosis cycle, then discard if still red)

### [MUTATE] Per-gap mutation testing
Load: rules/generation-constraints.md, references/assertion-policy.md
Do: Run `mutation_runner` scoped to ONLY the lines covered by the new tests (~5–20 lines per gap). Threshold from `--mutation-threshold` (default: all mutants killed). Surviving mutants → return to [GENERATE] to strengthen assertions. Single restrengthen cycle per gap; if mutants still survive after one cycle, log gap as `mutation-survived` in state and continue to the next gap (do not commit).
Don't: Run full-project mutation; lower threshold mid-run; advance with surviving mutants.
Exit: → [SCORE] (all killed) | → [GENERATE] (one cycle) | → [BRANCH-MAP] (next gap if still surviving after one restrengthen)

### [SCORE] Assertion-quality score
Load: rules/generation-constraints.md, references/assertion-policy.md
Do: Run `assertion_quality` on the generated tests. Verify: ≥2 assertions per test, no `assert True`/`assert 1`, no self-mocking of unit under test, no AST-hash duplicates of existing tests. Score must meet project threshold.
Don't: Pass to the hard gate below threshold; suppress findings; rerun until it passes (fix the tests).
Exit: → [GATE] (threshold met) | → [GENERATE] (single cycle to fix) | → [BRANCH-MAP] (log gap as `score-deficit` if still below after one cycle)

### [GATE] Hard gate — descriptive-intent review
Load: templates/generation-pr.md
Do:
  1. After all gaps in this batch have completed [SCORE] (or been logged as unresolvable / mutation-survived / score-deficit), extract a plain-English intent list from the docstrings: one line per generated test in the form `<function> — <scenario> → <asserts>`.
  2. If `--no-pr`: write the intent list to `project/coverage/state/GENERATION_INTENT.md` and exit cleanly without committing or opening a PR.
  3. Otherwise: detect any open PR for this batch (by `generation_id` label); update its body if found, else open a new PR using `templates/generation-pr.md`. Apply blocking GitHub label `awaiting-intent-approval` plus reviewer notification.
  4. STOP. Wait for reviewer to approve or reject explicitly via PR comment / label flip. No timeout, no auto-approval, no proceed-on-quiet.
Don't: Commit test files; advance to [COMMIT] without explicit human approval; partially commit on partial approval (whole batch is approved or rejected together).
Exit: → [COMMIT] (approved) | → [REJECT] (rejected) | → [END] (`--no-pr` path)

### [REJECT] Mark batch as human-rejected
Do: Mark every gap in this batch as `human-rejected` in `COVERAGE_STATE.yaml` with the reviewer's reason (from PR comment if present, else "rejected without comment"). Do not retry these gaps without a fresh `AuditGapReport` or explicit re-trigger.
Don't: Partially commit any tests from a rejected batch; auto-iterate; treat rejection as a transient failure.
Exit: → [END]

### [COMMIT] Commit tests + update state
Do:
  1. Commit the approved test files as `test(generate): close gaps <gap-ids> [generation_id=<id>]`.
  2. Update `project/coverage/state/COVERAGE_STATE.yaml` for each gap: status (`closed` / `unresolvable` / `mutation-survived` / `score-deficit` / `implementation-coupled` / `human-rejected`), auto-generated test IDs, validation status (green + mutation-killed + score-met + approved), `generation_id`.
  3. Run `coverage_analyzer` to confirm coverage actually improved at each closed gap; if not, downgrade the gap status to `coverage-unchanged` with a note.
  4. Run `log_contract_validator` if the function under test emits logs; record any failure as a non-blocking warning in state.
  5. If `benchmark_selector` flagged candidates during [INPUT-CRAFT] / [GENERATE], record them under `benchmark_candidates` in state — surface for human authoring; do not auto-write benchmark tests.
Don't: Mark a gap closed if `coverage_analyzer` shows no improvement; block the commit on `log_contract_validator` warnings; auto-author benchmark suites.
Exit: → [END]

### [END]
Do: Print PR URL (or intent-list path with `--no-pr`), per-gap result table (closed / unresolvable / mutation-survived / score-deficit / implementation-coupled / human-rejected), Hypothesis ratio achieved, and benchmark candidate count. Suggest `/test-evaluate` once the PR is reviewed and merged.
Don't: Auto-route or invoke `/test-evaluate` directly — handoff is the user's call.
