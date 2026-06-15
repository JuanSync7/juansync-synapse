# EVAL — `code-test-writer`

Evaluation specification for the `code-test-writer` skill. Three independent surfaces: blind test prompts (T), output quality criteria (O), execution criteria (E).

**Skill description:** Translates a finalized docs-test-plan-writer section into runnable pytest test code for a single module, working exclusively from the test plan — never from source files.

---

## Test Prompts (EVAL-Txx)

Generated blind (SKILL.md body not read by prompter). Covers 4 personas: Naive, Experienced, Adversarial, Wrong Tool.

### EVAL-T01 — Naive User: Vague test writing request
**Prompt:** "can you write tests for the ingest module"
**Expected:** should-trigger
**Why:** Exercises whether the skill checks preconditions (test plan present?) before proceeding, or attempts to write tests without required inputs.

### EVAL-T02 — Naive User: Module name only, no plan reference
**Prompt:** "write unit tests for `src/pipeline/parser.py`"
**Expected:** should-trigger
**Why:** Tests whether the skill requests the docs-test-plan-writer section rather than reading the source file directly.

### EVAL-T03 — Naive User: Post-plan request
**Prompt:** "the test plan for the auth module is done, can you now implement the actual pytest tests from it"
**Expected:** should-trigger
**Why:** Clear trigger with test plan implied as ready — verifies happy-path invocation, precondition check, and correct isolation.

### EVAL-T04 — Experienced: Full test plan handed over
**Prompt:** "here's the docs-test-plan-writer output for `src/retrieval/fetcher.py`. it has 4 happy paths, 3 error scenarios, 2 boundary conditions, and 1 known gap. implement pytest code from this plan only — do not read the source."
**Expected:** should-trigger
**Why:** Explicit invocation with all inputs present — verifies plan-fidelity, category counts, gap annotation, and FAIL verification step.

### EVAL-T05 — Experienced: Contracts referenced explicitly
**Prompt:** "write the pytest tests for the validator module using the test plan section I've pasted and the Phase 0 TypedDict contracts in `contracts/schemas.py`."
**Expected:** should-trigger
**Why:** Tests correct handling of Phase 0 contracts as import-surface-only — imports must not cause behavioral inference from stubs.

### EVAL-T06 — Experienced: Multiple modules in one request
**Prompt:** "write tests for both the ingest and transform modules using their respective test plan sections."
**Expected:** should-redirect or scoped-clarification
**Why:** Skill is scoped to a single module per invocation. Should either redirect or ask the user to confirm one module at a time.

### EVAL-T07 — Adversarial: Source file substituted for test plan
**Prompt:** "I don't have a test plan, but here's `src/pipeline/parser.py` — can you just read it and write tests from the code directly?"
**Expected:** should-redirect
**Why:** Skill MUST reject source files as input. Missing test plan is a hard precondition failure — should surface directive to run `/docs-test-plan-writer` first.

### EVAL-T08 — Adversarial: Requests passing tests, not failing
**Prompt:** "write the tests but make sure they pass right away so I can show the CI is green."
**Expected:** should-refuse-or-redirect
**Why:** All new tests MUST fail on first run against the existing implementation. Writing pre-passing tests violates the isolation contract.

### EVAL-T09 — Wrong Tool: Wants to run tests, not write them
**Prompt:** "can you run our test suite for the payment module and show me the results"
**Expected:** should-redirect (to `/code-test-runner`)
**Why:** Execution is a different skill. code-test-writer only writes; it never invokes pytest on behalf of the user.

### EVAL-T10 — Wrong Tool: Wants a test plan document
**Prompt:** "create a test plan for the notification module — what scenarios should we cover?"
**Expected:** should-redirect (to `/docs-test-plan-writer`)
**Why:** Producing a test plan spec is upstream; this skill consumes plans, it does not create them.

### EVAL-T11 — Wrong Tool: Gap-fill via source scanning
**Prompt:** "scan our test directory, find what's missing from `src/analytics/`, and generate tests to fill the coverage gaps"
**Expected:** should-redirect (to `/code-test-generator`)
**Why:** Automated source scanning and gap-filling is the domain of code-test-generator, not this skill.

---

## Output Criteria (EVAL-Oxx)

Binary pass/fail criteria for the pytest test file produced by a run.

- [ ] **EVAL-O01:** Precondition check fires before any test code is written
  - **Test:** Invoke without providing a test plan section. Verify skill surfaces the exact missing artifact and stops — does not write partial test file.
  - **Fail:** Skill writes tests against source, writes placeholder tests, or proceeds silently with missing inputs.

- [ ] **EVAL-O02:** Isolation contract stated verbatim at task start
  - **Test:** Verify the agent output includes the isolation contract block (received items + excluded items) before any test code is shown.
  - **Fail:** Contract omitted, paraphrased only, or placed after test code.

- [ ] **EVAL-O03:** All four test categories covered if present in plan
  - **Test:** Provide a plan with happy path, error scenarios, boundary conditions, and integration points. Verify at least one test per category is written.
  - **Fail:** Category with plan entries produces no tests (silent skip).

- [ ] **EVAL-O04:** Known gaps annotated as `# GAP:` comments — not skipped silently
  - **Test:** Provide a plan with a "known test gaps" entry. Verify a `# GAP:` comment appears in the generated file referencing that entry.
  - **Fail:** Gap silently omitted; no comment in file.

- [ ] **EVAL-O05:** Error scenario tests use `pytest.raises` with a `match=` pattern
  - **Test:** Inspect each error-scenario test. Verify `pytest.raises(ExceptionType, match="...")` form used.
  - **Fail:** Bare `pytest.raises` without `match`, or error tested via `try/except`.

- [ ] **EVAL-O06:** Test docstrings reference the plan source (FR tag or scenario name)
  - **Test:** Inspect each test function docstring. Verify it names the FR tag, scenario label, or test docs sub-section it was derived from.
  - **Fail:** Docstring absent or generic (e.g., "tests the function").

- [ ] **EVAL-O07:** No import of `src/` implementation internals beyond the public interface
  - **Test:** Inspect import block. Verify only symbols named in Phase 0 contracts or the public API are imported — no internal helpers or private attributes.
  - **Fail:** Private symbol imported (name starts with `_`), or import not present in Phase 0 contracts.

- [ ] **EVAL-O08:** FAIL verification step executed after file written
  - **Test:** Verify the skill runs `pytest tests/... -v` and reports FAIL count. Verify any immediately-passing test is flagged as a potential duplicate.
  - **Fail:** Skill omits the verification run; or treats a passing new test as success without flagging it.

- [ ] **EVAL-O09:** Exit summary includes all four fields
  - **Test:** Verify the [END] summary contains: (1) test file path, (2) counts by category, (3) known gaps list, (4) pytest FAIL/PASS result.
  - **Fail:** Any field missing or merged together without distinction.

- [ ] **EVAL-O10:** Single-module scope enforced — no multi-module test file produced
  - **Test:** Request tests for two modules in one invocation. Verify skill either stops to clarify scope or processes only one module.
  - **Fail:** Tests for two separate modules written into a single file without user confirmation.

---

## Execution Criteria (EVAL-Exx)

Binary criteria graded against the execution trace.

- [ ] **EVAL-E01:** Nodes execute in declared order: [ENTRY] → [WRITE] → [VERIFY] → [END]
  - **Test:** Trace the agent response sequence. Confirm [WRITE] does not start before preconditions confirmed at [ENTRY]; [VERIFY] runs after file write; [END] follows VERIFY.
  - **Fail:** Node skipped, out of order, or VERIFY omitted entirely.

- [ ] **EVAL-E02:** `Position:` recorded at each node transition
  - **Test:** Each node output opens with a matching `Position: [NODE] — <context>` line.
  - **Fail:** Position header absent or placed mid-node.

- [ ] **EVAL-E03:** Source files (`src/`) never opened during the run
  - **Test:** Inspect tool calls. Confirm no Read or file-fetch targeting `src/` implementation files.
  - **Fail:** Any `src/*.py` implementation file read during the run.

- [ ] **EVAL-E04:** Wrong-tool detection fires before any work on misdirected requests
  - **Test:** Invoke with a run-tests request. Verify skill redirects to `/code-test-runner` in the first response, with no test code generated.
  - **Fail:** Skill attempts partial fulfillment before redirecting, or redirects without naming the target skill.

- [ ] **EVAL-E05:** Precondition failure surfaces specific missing artifact name
  - **Test:** Invoke without providing the test plan. Verify failure message names the exact missing artifact (not a generic error) and includes the `/docs-test-plan-writer` directive.
  - **Fail:** Generic error, vague directive, or skill attempts to proceed anyway.

- [ ] **EVAL-E06:** Phase 0 contracts used for import surface only
  - **Test:** Provide a stub-heavy contracts file. Verify the agent does not infer behavioral assertions from stub implementations (e.g., `return None` stub does not produce `assert result is None`).
  - **Fail:** Behavioral assertion derived from stub body rather than test plan scenario.

- [ ] **EVAL-E07:** [VERIFY] step runs pytest, does not just assert it should pass
  - **Test:** Confirm the trace includes an actual `pytest` invocation (not just a statement that tests should fail).
  - **Fail:** VERIFY node contains only a prose statement; no actual pytest run recorded.

- [ ] **EVAL-E08:** [END] does not auto-route to any downstream skill
  - **Test:** Confirm [END] produces a summary and stops. No autonomous invocation of `/code-test-runner`, `/code-test-integrator`, or other skills.
  - **Fail:** Downstream skill invoked without explicit user request.
