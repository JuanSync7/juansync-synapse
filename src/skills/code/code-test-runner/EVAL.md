# EVAL — `code-test-runner`

Evaluation specification for the `code-test-runner` skill. Three independent surfaces: blind test prompts (T), output quality criteria (O), execution criteria (E).

**Skill description:** Use when asked to run tests, execute pytest, re-run failing tests, or trigger a fix loop after test failures.

---

## Test Prompts (EVAL-Txx)

Generated blind (SKILL.md body not read by prompter). Covers 4 personas: Naive, Experienced, Adversarial, Wrong Tool.

### EVAL-T01 — Naive User: Vague run request
**Prompt:** "can you run the tests"
**Expected:** should-trigger
**Why:** Tests whether the skill asks for scope/scope_type or applies a default, then executes.

### EVAL-T02 — Naive User: Named group
**Prompt:** "run the ingest tests"
**Expected:** should-trigger
**Why:** Tests group-type scope resolution and `scripts/run-tests.sh --group ingest` command construction.

### EVAL-T03 — Naive User: Fix failing tests
**Prompt:** "the retrieval tests are failing, can you fix them"
**Expected:** should-trigger
**Why:** Exercises run → failures detected → fix loop activation path.

### EVAL-T04 — Experienced: Targeted path with marker
**Prompt:** "run `tests/ingest/test_orchestrator.py` with the marker `not slow` and timeout 45 seconds"
**Expected:** should-trigger
**Why:** Tests path-type scope with `--marker` and `--timeout` flags appended correctly.

### EVAL-T05 — Experienced: Strict mode + keyword filter
**Prompt:** "run the server group in strict mode, filtering to tests matching `test_route`"
**Expected:** should-trigger
**Why:** Tests `--strict` and `--keyword` flag combination and their appending sequence.

### EVAL-T06 — Experienced: Fix loop with max iterations context
**Prompt:** "run the guardrails group and if any tests fail, keep trying to fix them — up to 3 iterations"
**Expected:** should-trigger
**Why:** Verifies fix loop initialization with explicit iteration count, termination checks, and FR-506 final report.

### EVAL-T07 — Adversarial: No scope provided
**Prompt:** "run the tests"
**Expected:** should-clarify
**Why:** `scope` is required. Skill must ask for group name or file path rather than silently assuming `all`.

### EVAL-T08 — Adversarial: Fix loop on blocked run
**Prompt:** "run the import-check group and fix anything that fails"
**Expected:** should-trigger
**Why:** Tests that when run exits with validation block (no `report.json`), fix loop is NOT entered — `status: blocked` is reported and the agent explains the validation issue instead.

### EVAL-T09 — Wrong Tool: Write new tests
**Prompt:** "the ingest module has no tests — can you write some?"
**Expected:** should-redirect (to `/code-test-writer`)
**Why:** Test authoring, not test execution.

### EVAL-T10 — Wrong Tool: Coverage audit
**Prompt:** "can you tell me which parts of the codebase have poor test coverage?"
**Expected:** should-redirect (to `/code-test-auditor`)
**Why:** Coverage analysis and gap reporting, not test execution.

---

## Output Criteria (EVAL-Oxx)

Binary pass/fail criteria for the structured result and final status report produced by a run.

- [ ] **EVAL-O01:** All 10 output fields present on every run result
  - **Test:** Inspect result. Verify all ten fields exist: `status`, `summary`, `total`, `passed`, `failed`, `errors`, `skipped`, `failures`, `validation_issues`, `duration_seconds`. Fields with no data appear as `[]` or `0`, not `null`/absent.
  - **Fail:** A field is absent or `null` when it should be an empty default.

- [ ] **EVAL-O02:** `status` value is within the declared enum
  - **Test:** `status` ∈ {`pass`, `fail`, `blocked`, `error`}. No other values accepted.
  - **Fail:** Novel status string or missing `status` field.

- [ ] **EVAL-O03:** `summary` is a human-readable one-liner matching counts
  - **Test:** Parse `summary`. Verify it mentions `passed`, `failed`, and `errors` counts consistent with the numeric fields. Format example: "12 passed, 2 failed, 1 error".
  - **Fail:** Summary omits counts, or counts contradict numeric fields.

- [ ] **EVAL-O04:** `status: blocked` suppresses fix loop
  - **Test:** Inject a validation-blocked run (no `report.json`, `validation.json` with `status: blocked`). Verify fix loop is NOT entered; `validation_issues` is populated; numeric counts are all 0.
  - **Fail:** Fix loop entered after blocked run, or `validation_issues` left empty.

- [ ] **EVAL-O05:** `failures` list carries all four required sub-fields
  - **Test:** When `failures` is non-empty, every entry has `test_name`, `file`, `line`, `message`, and `longrepr`.
  - **Fail:** Any sub-field absent on a failure entry.

- [ ] **EVAL-O06:** Fix loop final report includes all FR-506 fields
  - **Test:** After fix loop exits (any termination reason), final report contains: `final_status`, `iterations_used`, `termination_reason`, `remaining_failures`, `files_modified`.
  - **Fail:** Any FR-506 field absent from final report.

- [ ] **EVAL-O07:** `termination_reason` is within the declared enum
  - **Test:** `termination_reason` ∈ {`all_passed`, `max_iterations`, `same_failure`, `stalled`}.
  - **Fail:** Novel termination string or missing field when fix loop was entered.

- [ ] **EVAL-O08:** Fix loop MUST NOT create or delete files
  - **Test:** Record file system state (git status) before fix loop. After loop completes, verify no new files created and no files deleted. Only edits to tracked files are permitted.
  - **Fail:** Any untracked file created, or any tracked file deleted.

- [ ] **EVAL-O09:** Fix loop edits only git-tracked files
  - **Test:** After each edit in the fix loop, verify the target file passes `git ls-files --error-unmatch <path>`. No edits to untracked or ignored files.
  - **Fail:** Edit applied to a file that fails `git ls-files --error-unmatch`.

- [ ] **EVAL-O10:** Same-failure detection (FR-502) stops loop immediately
  - **Test:** Simulate a fix attempt that produces identical `(test_name, message)` pairs across two iterations. Verify loop stops with `termination_reason: same_failure` and does NOT consume another iteration.
  - **Fail:** Loop continues past a same-failure match, or uses a third iteration before stopping.

---

## Execution Criteria (EVAL-Exx)

Binary criteria graded against the execution trace.

- [ ] **EVAL-E01:** Correct command constructed for scope_type
  - **Test:** For `scope_type: group`, trace shows `scripts/run-tests.sh --group <scope>`. For `scope_type: path`, trace shows `scripts/run-tests.sh --path <scope>`. No other base command forms accepted.
  - **Fail:** Wrong flag, missing flag, or `python -m pytest` used directly instead of the script.

- [ ] **EVAL-E02:** Optional flags appended only when their parameter is provided
  - **Test:** Run without `marker`, `keyword`, `strict`, `timeout`. Confirm command contains none of `--marker`, `--keyword`, `--strict`, `--timeout`. Then run with each; confirm each appears exactly once.
  - **Fail:** Flag appears in command without corresponding input, or is absent when input is provided.

- [ ] **EVAL-E03:** Output files read after run completes, matched to exit code
  - **Test:** Verify read sequence per exit code: 0 → `report.json` + `meta.json`; 1 → `report.json` (if exists) or `validation.json` + `meta.json`; 2 → `validation.json` (if exists) + `meta.json`; 124 → `run.log` + `meta.json`.
  - **Fail:** Wrong file read for the observed exit code, or `meta.json` skipped.

- [ ] **EVAL-E04:** Fix loop reads `report.json` failures before each edit, not once upfront
  - **Test:** Trace shows a `report.json` read at the start of each iteration (not only iteration 0).
  - **Fail:** Failures list read once and reused across iterations without re-reading from disk.

- [ ] **EVAL-E05:** Fix loop processes one failure at a time (FR-504)
  - **Test:** When multiple failures exist, trace shows individual edits per failure, not a single bulk edit touching all failures simultaneously.
  - **Fail:** All failures processed in a single Edit call or parallel edits.

- [ ] **EVAL-E06:** Monotonic progress check (FR-503) enforced correctly
  - **Test:** Simulate failure count increasing between iterations. Verify loop stops with `termination_reason: stalled` after count increases, not after max_iterations.
  - **Fail:** Loop continues past an increasing failure count, or stall_budget consumed when count increased (not just same-count-different-set).

- [ ] **EVAL-E07:** Fix loop re-invokes the same scope and flags as the original run
  - **Test:** Note the original `scripts/run-tests.sh` invocation. After each fix attempt, confirm the re-invocation uses identical scope, scope_type, marker, keyword, strict, and timeout values.
  - **Fail:** Re-invocation omits a flag that was present in the original, or adds a flag that was not.
