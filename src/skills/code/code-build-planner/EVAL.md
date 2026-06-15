# EVAL — `code-build-planner`

Evaluation specification for the `code-build-planner` skill. Three independent surfaces: blind test prompts (T), output quality criteria (O), execution criteria (E).

**Skill description:** Generate six-phase bias-free implementation plans (Phase 0 contracts → Phase A spec tests → Phase B implementation → Phase C engineering guide → Phase D white-box tests → Phase E full suite) with strict agent context isolation so no single agent ever holds both test logic and implementation logic.

---

## Test Prompts (EVAL-Txx)

Generated blind (SKILL.md body not read by prompter). Covers 4 personas: Naive, Experienced, Adversarial, Wrong Tool.

### EVAL-T01 — Naive User: Vague "make a plan" request
**Prompt:** "can you make a build plan for the feature"
**Expected:** should-trigger
**Why:** Tests whether the skill resolves a minimal invocation, surfaces the input requirement (implementation docs), and either requests missing input or proceeds with defaults.

### EVAL-T02 — Naive User: Has implementation docs, no design doc mentioned
**Prompt:** "I have the implementation docs for the auth subsystem — can you make an execution plan from them?"
**Expected:** should-trigger
**Why:** Canonical trigger with a real input artifact. Verifies phase structure produced, not a flat task list.

### EVAL-T03 — Naive User: Keyword trigger
**Prompt:** "create an execution plan for building the pipeline from these docs"
**Expected:** should-trigger
**Why:** Matches the "execution plan" keyword in the routing contract. Verifies skill fires on keyword, not just explicit skill name.

### EVAL-T04 — Experienced: Full invocation with both artifacts
**Prompt:** "run code-build-planner on `docs/superpowers/impl/auth-impl.md` and `docs/superpowers/specs/auth-spec.md` — produce the six-phase plan with Phase 0 contracts, Phase A spec tests, Phase B impl, Phase C guide, Phase D white-box tests, and Phase E verification. save to `docs/superpowers/plans/2026-06-13-auth-plan.md`."
**Expected:** should-trigger
**Why:** Happy-path invocation with all inputs. Verifies all six phases appear in order with correct structure.

### EVAL-T05 — Experienced: Emphasis on isolation enforcement
**Prompt:** "I need a build plan where the test agents are strictly isolated from implementation knowledge — they should derive tests from the spec alone, not from pattern code. the impl agents should work against pre-written tests they didn't author. use the implementation docs at `docs/impl/search-impl.md`."
**Expected:** should-trigger
**Why:** Expert who knows the isolation model — verifies the skill produces verbatim isolation contracts in Phase A and Phase D headers, not paraphrased versions.

### EVAL-T06 — Experienced: Subsystem with parallel-capable tasks
**Prompt:** "build plan for the event-bus subsystem — the impl docs are at `docs/impl/event-bus.md`. I know the subsystem has three independent modules (producer, consumer, dispatcher) that can be built in parallel in Phase B. make sure the plan captures that parallelism and the dependency graph is correct."
**Expected:** should-trigger
**Why:** Tests parallel Phase B modeling, dependency graph production, and Phase gate tracker generation.

### EVAL-T07 — Adversarial: Giant monorepo scope
**Prompt:** "generate one master build plan covering all 14 subsystems in the monorepo — all their impl docs are in `docs/impl/`. I want one plan that tracks everything."
**Expected:** should-redirect or should-scope-check
**Why:** Scope check rule states one plan per pipeline/subsystem. Skill should produce separate plans or ask to scope down, not a single mega-plan.

### EVAL-T08 — Adversarial: Attempt to skip Phase 0 review gate
**Prompt:** "make a build plan but skip the human review gate — we're moving fast and I trust the contracts will be fine."
**Expected:** should-redirect or should-refuse
**Why:** Review gate is a structural guarantee. Skill must decline to omit it or surface the consequence.

### EVAL-T09 — Wrong Tool: No implementation docs, only a feature request
**Prompt:** "I want to build a rate-limiter — can you give me a plan for how to implement it?"
**Expected:** should-redirect (to `/docs-implementation-writer`)
**Why:** No implementation docs present — this skill requires them. Must redirect, not fabricate inputs.

### EVAL-T10 — Wrong Tool: Vertical-slice story breakdown for delivery
**Prompt:** "slice our auth feature into vertical stories that parallel delivery agents can pick up — I need them organized by delivery slice, not by TDD phase."
**Expected:** should-redirect (to `/delivery-plan-writer`)
**Why:** Delivery-slice decomposition is the adjacent `delivery-plan-writer` case, not six-phase TDD isolation.

---

## Output Criteria (EVAL-Oxx)

Binary pass/fail criteria for the plan document produced by a run.

- [ ] **EVAL-O01:** Plan document contains all six phases in order
  - **Test:** Verify headings Phase 0, Phase A, Phase B, Phase C, Phase D, Phase E present and in that sequence.
  - **Fail:** Phase absent, mislabeled, or phases appear out of sequence.

- [ ] **EVAL-O02:** Review gate announced between Phase 0 and Phase A
  - **Test:** Plan contains an explicit `[REVIEW GATE]` annotation or equivalent human-approval checkpoint between Phase 0 and Phase A sections.
  - **Fail:** No gate; Phase A immediately follows Phase 0 without approval checkpoint.

- [ ] **EVAL-O03:** Each Phase A task contains verbatim isolation contract
  - **Test:** Every Phase A task block includes "Agent input (ONLY these):" and "Must NOT receive:" clauses. Isolation contract wording matches SKILL.md verbatim or near-verbatim.
  - **Fail:** Missing clause, or clause present but "Must NOT receive" list is empty or absent.

- [ ] **EVAL-O04:** Every Phase A test case is tagged with an FR number
  - **Test:** Each bullet under "Test cases" in a Phase A task references at least one FR number (e.g., `FR-3`, `FR-12`).
  - **Fail:** Test case bullet without an FR tag.

- [ ] **EVAL-O05:** Phase B tasks reference their Phase A test file explicitly
  - **Test:** Each Phase B task's "Agent input:" includes the exact Phase A test file path for that task.
  - **Fail:** Phase B task that does not name its corresponding Phase A test file.

- [ ] **EVAL-O06:** Phase B tasks include completion report format
  - **Test:** Each Phase B task specifies a completion report with at minimum: Task ID, files modified, pytest command + PASS confirmation, commit hash.
  - **Fail:** Completion report absent or missing required fields.

- [ ] **EVAL-O07:** Phase C isolation contracts present in both C-parallel and C-cross tasks
  - **Test:** C-parallel tasks include "Must NOT receive: other modules' source, any test files, the design doc." C-cross task specifies it receives ONLY module docs + spec, not source files.
  - **Fail:** Either sub-phase missing its isolation clause.

- [ ] **EVAL-O08:** Phase D tasks contain verbatim isolation contract and expected FAIL outcome
  - **Test:** Each Phase D task includes the verbatim isolation contract from SKILL.md and specifies "Pytest command with expected FAIL outcome."
  - **Fail:** Missing isolation contract, or Phase D expected outcome is PASS (tests are new — implementation already exists, tests should fail before being run against it).

- [ ] **EVAL-O09:** Phase E contains full-suite pytest command
  - **Test:** Phase E section includes `pytest tests/ -v` or equivalent full-suite invocation, a PASS assertion for both Phase A and Phase D tests, and a git commit step.
  - **Fail:** Phase E is missing any of these three elements.

- [ ] **EVAL-O10:** Plan saved to `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md` or user-specified path
  - **Test:** Plan document path matches the SKILL.md default convention or the user-specified override, not an ad hoc location.
  - **Fail:** No save path declared, or path deviates from convention without user instruction.

- [ ] **EVAL-O11:** Dependency graph present and reflects design document
  - **Test:** Plan includes an ASCII dependency graph showing Phase 0 → review gate → Phase A (parallel) → Phase B (dependency order). Graph matches the implementation docs' dependency graph.
  - **Fail:** No graph, or graph contradicts the implementation docs' stated dependencies.

- [ ] **EVAL-O12:** Task-to-requirement mapping table present
  - **Test:** Plan includes a table with columns: Task, Phase 0 contracts, Phase A test file, Phase B source file, Phase C module doc, Phase D test file, FR numbers.
  - **Fail:** Table absent or missing a required column.

- [ ] **EVAL-O13:** Phase 0 stubs use `raise NotImplementedError("Task B-X.Y")` — no implementation hints
  - **Test:** All function stubs in Phase 0 tasks have body `raise NotImplementedError(...)` only; no logic, no comments about how to implement, no pattern hints.
  - **Fail:** Stub body contains implementation logic or hints beyond the NotImplementedError.

- [ ] **EVAL-O14:** Pure utility functions in Phase 0 are fully implemented (not stubbed)
  - **Test:** Functions identified as pure utilities in the implementation docs appear fully implemented in Phase 0, not as stubs.
  - **Fail:** Pure utility left as stub, or non-utility fully implemented when it should be a stub.

---

## Execution Criteria (EVAL-Exx)

Binary criteria graded against the execution trace.

- [ ] **EVAL-E01:** Skill announces itself at start
  - **Test:** First output contains "I'm using the code-build-planner skill to create a bias-free implementation plan."
  - **Fail:** No announcement; user has no signal which skill is driving.

- [ ] **EVAL-E02:** TaskCreate calls issued for all seven tasks before any phase work begins
  - **Test:** Trace shows seven `TaskCreate` calls (Phase 0, Review gate, Phase A, Phase B, Phase C, Phase D, Phase E) at session start, before any plan content is produced.
  - **Fail:** Tasks created mid-execution, or fewer than seven tasks created.

- [ ] **EVAL-E03:** Input precondition checked — implementation docs required
  - **Test:** If no implementation docs path provided, skill surfaces a clear request before proceeding. If path provided but file absent, skill fails loudly and stops.
  - **Fail:** Skill proceeds without implementation docs, or proceeds silently with a missing file.

- [ ] **EVAL-E04:** `model:` set explicitly on every Agent dispatch
  - **Test:** Every Agent dispatch call in the produced plan includes a `model:` field. No dispatch relies on session default.
  - **Fail:** Any Agent dispatch missing `model:` field.

- [ ] **EVAL-E05:** Phase 0 derived from implementation docs contract entries, not design doc
  - **Test:** Plan production trace or plan content shows contracts copied from implementation docs. If design doc is referenced for Phase 0, it must only be for gap-filling, not as primary source.
  - **Fail:** Phase 0 re-derived from design doc when implementation docs contract entries are available.

- [ ] **EVAL-E06:** One plan per subsystem — scope check enforced
  - **Test:** When input covers multiple independent subsystems, skill either produces separate plans or asks user to scope down before producing one mega-plan.
  - **Fail:** Single plan produced for multiple independent subsystems without user consent.

- [ ] **EVAL-E07:** Review gate announced explicitly before transitioning from Phase 0 planning to Phase A planning
  - **Test:** Execution trace contains an explicit gate announcement: "Phase 0 must be human-reviewed before Phase A begins" or equivalent. Not just present in the plan document — also announced in session.
  - **Fail:** Gate present in document but not surfaced in session; or gate absent from both.

- [ ] **EVAL-E08:** Reviewer dispatched after plan is written (Review Loop)
  - **Test:** After plan document is complete, trace shows a reviewer dispatch referencing `references/reviewer-prompt.md`. Reviewer checks: spec coverage, isolation clauses, dependency graph alignment.
  - **Fail:** Reviewer not dispatched; or plan delivered to user without review loop.

- [ ] **EVAL-E09:** Max 3 review iterations before human escalation
  - **Test:** If reviewer returns issues, plan is revised and re-reviewed. After 3 failed iterations, skill surfaces to human with open issues listed.
  - **Fail:** Fourth automated revision attempted without human escalation.

- [ ] **EVAL-E10:** Execution handoff summary delivered at end
  - **Test:** Final output contains the six-phase handoff summary from SKILL.md ("Plan complete. Six execution phases: ...") and closes with "Ready to start with Phase 0?"
  - **Fail:** Handoff summary absent, truncated, or phases described in wrong order.
