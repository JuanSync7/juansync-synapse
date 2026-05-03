# write-test-coverage — Evaluation Criteria

## Structural Criteria

Delegated to improve-skill baseline checklist (frontmatter validation, wrong-tool detection, companion file references, etc.).

## Execution Criteria

- [ ] **EVAL-E01:** Phase 1 subagents dispatch per test file, not as a single-pass scan
  - **Test:** For repos with ≥10 test files, observe that the skill spawns one Agent call per test file (or per small batch). Each Agent call targets a specific test file path.
  - **Fail signal:** A single Agent call or inline Read loop processes all test files in one context — no per-file dispatch observed.

- [ ] **EVAL-E02:** Phase 1 subagents use `model: sonnet` (mechanical extraction tier)
  - **Test:** Inspect each Phase 1 Agent dispatch. The `model` parameter is explicitly set to `sonnet`.
  - **Fail signal:** Phase 1 subagents dispatch without an explicit `model` parameter (inheriting opus) or explicitly set to `opus`.

- [ ] **EVAL-E03:** Phase 2 cross-matching runs on `model: opus` (judgment tier)
  - **Test:** If Phase 2 is dispatched as a subagent, verify `model` is set to `opus`. If Phase 2 runs in the main context, verify the main context is opus-tier.
  - **Fail signal:** Phase 2 cross-matching dispatches with `model: sonnet` or another non-frontier model.

- [ ] **EVAL-E04:** Small repo shortcut skips subagent dispatch for <10 test files
  - **Test:** For repos with fewer than 10 test files, observe that the skill performs a single-pass scan without spawning per-file subagents.
  - **Fail signal:** Per-file subagents are dispatched for a repo with only 3-5 test files — unnecessary orchestration overhead.

- [ ] **EVAL-E05:** Phase 1 subagents receive no acceptance criteria
  - **Test:** Inspect the prompt sent to each Phase 1 subagent. It contains the test file path and language conventions but no AC list, spec content, or eng-guide content.
  - **Fail signal:** A Phase 1 subagent prompt includes acceptance criteria, spec excerpts, or eng-guide content — violating the two-phase context isolation invariant.

## Output Criteria

- [ ] **EVAL-O01:** All four register sections are present
  - **Test:** The output document contains: (1) per-module coverage sections, (2) a cross-cutting coverage section (or explicit statement that no cross-cutting ACs exist), (3) an orphaned tests section (or explicit statement that none were found), (4) an unfound modules section (or explicit statement that all modules have intent docs).
  - **Fail signal:** One or more of the four sections is missing entirely — no header, no content, no "none found" statement.

- [ ] **EVAL-O02:** Every acceptance criterion from the intent document appears in the register
  - **Test:** Extract all AC/FR identifiers from the intent document. For each one, verify it appears in the register body (in a module section or cross-cutting section) with a scenario checklist.
  - **Fail signal:** An AC from the intent document has no corresponding entry in the register — it was silently dropped.

- [ ] **EVAL-O03:** Coverage status is mechanically derived from scenario checklist counts
  - **Test:** For every AC entry, count the `[x]`, `[~]`, `[ ]`, and `[!]` marks. Verify the stated status matches: all `[x]` = "Covered", all `[ ]` = "Not Covered", mix = "Partial (N/M scenarios)" where N and M match the actual counts.
  - **Fail signal:** Status label contradicts the checklist (e.g., "Covered" but one scenario is `[ ]`), or the N/M count is wrong.

- [ ] **EVAL-O04:** Every checked scenario `[x]` links to a specific test file and function
  - **Test:** For every `[x]` mark, verify there is a parenthetical reference containing a test file path and line number or function name (e.g., `(test_auth.py:45)` or `(test_auth.py::test_login_success)`).
  - **Fail signal:** A `[x]` mark has no test reference, or the reference is vague (e.g., "somewhere in test_auth.py" without a line or function).

- [ ] **EVAL-O05:** Scenario decomposition is fine-grained (each scenario independently testable)
  - **Test:** For each AC entry, verify that scenarios describe single assertions or tightly coupled assertion groups — not entire features. Check that no scenario is just the AC description restated (e.g., AC: "Token refresh flow" → scenario: "Token refresh works" is a restatement, not a decomposition).
  - **Fail signal:** A scenario is a restatement of the AC without decomposition, or a scenario bundles multiple unrelated assertions that could be tested independently.

- [ ] **EVAL-O06:** Summary table counts match section details
  - **Test:** For each module row in the summary table, count the ACs in the corresponding module section and verify Total/Covered/Partial/Not Covered counts match. Verify the Total row sums all module rows correctly.
  - **Fail signal:** Any count in the summary table differs from what's in the section body.

- [ ] **EVAL-O07:** Prioritized gaps are ordered by AC priority (MUST > SHOULD > MAY)
  - **Test:** Check that the Prioritized Gaps section exists and entries are ordered with MUST-priority gaps before SHOULD-priority gaps before MAY-priority gaps. Verify every "Not Covered" AC with MUST or SHOULD priority appears in this section.
  - **Fail signal:** Gaps are unordered, or a MUST-priority uncovered AC is missing from the Prioritized Gaps section.

- [ ] **EVAL-O08:** Cross-cutting ACs reference test files across multiple modules
  - **Test:** For each entry in the Cross-Cutting section, verify that `[x]` references point to test files in at least two different modules. If an AC is in the Cross-Cutting section but all test references are from a single module, it should be in the per-module section instead.
  - **Fail signal:** A cross-cutting AC entry has test references from only one module, or an AC that spans multiple modules is buried in a single module's section.

- [ ] **EVAL-O09:** Orphaned tests include behavioral summaries and possible explanations
  - **Test:** For each entry in the Orphaned Tests section, verify it includes: test file path, function name, a behavioral summary (what the test does), and a possible explanation (incomplete spec, dead code, utility test).
  - **Fail signal:** Orphaned tests are listed as bare file/function names without behavioral context or explanation.

- [ ] **EVAL-O10:** Missing intent docs produce explicit "cannot assess" entries, not silent omissions
  - **Test:** If there are modules in the repo with no spec/eng-guide/docstrings, verify they appear in the Unfound Modules section with a clear statement that coverage cannot be assessed and a recommendation to create an intent document.
  - **Fail signal:** A module with no intent document is silently omitted from the register rather than flagged in the Unfound Modules section.

- [ ] **EVAL-O11:** Intent document is the source of truth for "what should be tested" — not source code
  - **Test:** Verify that ACs and scenarios in the register trace back to the intent document (spec, eng-guide, or docstrings). Check that no AC was invented from reading source code implementation details.
  - **Fail signal:** The register contains ACs or scenarios that exist in the source code but not in any intent document — the skill inferred coverage targets from implementation rather than requirements.

- [ ] **EVAL-O12:** Staleness flags appear where source code is newer than test code
  - **Test:** If the skill had access to git timestamps, verify that modules where source files were modified more recently than test files have a staleness warning. If no staleness was detected, verify the register does not contain false staleness flags.
  - **Fail signal:** A module with clearly newer source code has no staleness warning, or a staleness warning appears for a module where tests are newer than source.

- [ ] **EVAL-O13:** Ambiguous `[~]` marks include an explanation of the uncertainty
  - **Test:** For every `[~]` mark in the register, verify there is a parenthetical test reference AND a trailing note explaining why the match is ambiguous (e.g., "checks message text but not response timing").
  - **Fail signal:** A `[~]` mark has no ambiguity explanation, or the explanation is generic (e.g., "partially covered") without stating what specifically is uncertain.

- [ ] **EVAL-O14:** Intent document hierarchy is respected when multiple sources exist
  - **Test:** If a module has both a spec and an eng-guide, verify the register uses the spec as the primary source for ACs (spec > eng-guide > docstrings). The "Intent source" field in the module section should reference the highest-priority document available.
  - **Fail signal:** A module with a formal spec lists an eng-guide or docstrings as the intent source, or ACs are drawn from a lower-priority source when a higher-priority one exists.

## Test Prompts

### Naive User: Bare minimum request

**Prompt:** "what's tested in my project?"

**Why this tests the skill:** Tests whether the skill asks for the required inputs (spec/eng-guide path, test directory) or attempts to auto-discover and proceeds with reasonable defaults.

### Naive User: Vague coverage concern

**Prompt:** "I feel like we have gaps in our test coverage. can you check?"

**Why this tests the skill:** Tests whether the skill distinguishes itself from line-coverage tools (pytest --cov) and guides the user toward providing acceptance criteria as the source of truth.

### Naive User: Single module, no spec mentioned

**Prompt:** "generate a test coverage register for the auth module, tests are in tests/test_auth.py"

**Why this tests the skill:** Tests behavior when the user provides a test file but no intent document — does the skill ask for a spec/eng-guide or silently infer coverage targets from code?

### Experienced User: Multi-language repo with specific inputs

**Prompt:** "Write a test coverage register for our payment gateway. Spec is at docs/payments/SPEC.md with formal ACs, test directory is tests/payments/. We also have bats tests for the deploy scripts in tests/deploy/. Map everything against the spec's MUST/SHOULD/MAY priorities and flag anything that's only validated in CI."

**Why this tests the skill:** Tests handling of multi-language scanning (Python + bats), priority-aware classification, and CI-only detection — a demanding request with explicit expectations.

### Experienced User: Large repo, cross-cutting concerns

**Prompt:** "I need a coverage register for the entire backend — 14 modules across src/, with specs under docs/specs/ and an eng-guide at docs/ENGINEERING_GUIDE.md. I care especially about cross-cutting requirements like error handling and auth middleware that span multiple modules. Tests are in tests/ mirroring the src/ structure. There are also SystemVerilog UVM testbenches under tb/ for the FPGA controller."

**Why this tests the skill:** Tests scalability (14 modules), cross-cutting detection, mixed language support (Python + SystemVerilog), and whether the skill uses subagent dispatch vs single-pass for a large repo.

### Experienced User: Coverage update, not initialization

**Prompt:** "We already have a test-coverage.md but it's 3 months stale. Can you regenerate it? The spec hasn't changed but we've added ~40 new tests since the last run. Same paths as before — docs/api/SPEC.md and tests/."

**Why this tests the skill:** Tests whether the skill handles regeneration vs initialization, and whether it detects and flags staleness from git timestamps.

### Adversarial: No spec, no eng-guide, just code

**Prompt:** "generate a coverage register for src/. there's no spec or eng-guide, just well-commented source code. tests are in tests/. figure out what should be tested from reading the code."

**Why this tests the skill:** Tests the hard precondition — the skill should refuse to infer coverage targets from source code and direct the user to write a spec or eng-guide first.

### Adversarial: Contradictory scope

**Prompt:** "write test coverage for the whole monorepo — 200+ modules, 3000 test files. also write the missing tests while you're at it. spec is a confluence page at https://wiki.internal/specs."

**Why this tests the skill:** Tests three failure modes: unrealistic scope (200+ modules), scope creep into test writing (wrong skill), and external URL as input (inaccessible).

### Wrong Tool: Wants test planning, not coverage assessment

**Prompt:** "I need a document that tells my team how to structure their pytest tests — fixtures, parametrize patterns, what to mock vs integration test."

**Why this tests the skill:** This needs `/write-test-docs` (test planning), not coverage assessment. Tests wrong-tool detection for the closest sibling skill.

### Wrong Tool: Wants actual test code

**Prompt:** "look at my spec's acceptance criteria and write the pytest test functions for each one"

**Why this tests the skill:** This needs `/write-module-tests` (test code implementation). Tests wrong-tool detection — the trigger keywords ("acceptance criteria", "test") overlap heavily with this skill's domain.
