---
name: write-test-coverage
description: "Use when you need a living test coverage register that maps acceptance criteria to test scenarios and tracks what is covered vs. not. Triggered by 'write test coverage', 'test coverage register', 'what is tested', 'coverage gaps', 'what needs tests'."
domain: docs.post-build
intent: write
tags: [test-coverage, coverage-register, traceability, acceptance-criteria]
user-invocable: true
argument-hint: "[spec-or-engguide-path] [test-dir]"
---

# Write Test Coverage

A test coverage register bridges the gap between *intent* (what the system should do) and *evidence* (what tests actually verify). `pytest --cov` gives line coverage — a number. This register gives scenario-level visibility: which acceptance criteria have test cases, which are partial, which are missing entirely. It serves two audiences simultaneously: humans scanning for gaps and agents deciding what to write next.

The register is initialized once by this skill and maintained incrementally by `/patch-docs` as tests are added or code changes. It should never require full regeneration on every change.

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

**Announce at start:** "I'm using the write-test-coverage skill to generate the test coverage register."

## Wrong-Tool Detection

- **User wants a test planning document** (how to structure tests in code) → redirect to `/write-test-docs`
- **User wants actual test code** (pytest, bats, etc.) → redirect to `/write-module-tests`
- **User wants to update existing docs after a code change** → redirect to `/patch-docs`
- **User wants line/branch coverage numbers** → suggest `pytest --cov` or equivalent tool directly

## Layer Context

```
Spec / Eng-Guide (intent)     ← source of "what should be tested"
Test files (evidence)          ← source of "what is tested"
                  ↓
        write-test-coverage    ← YOU ARE HERE (cross-matches intent vs evidence)
                  ↓
        test-coverage.md       ← the register (initialized here, maintained by /patch-docs)
```

## Progress Tracking

```
TaskCreate: "Phase 0: Gather inputs and validate preconditions"
TaskCreate: "Phase 1: Scan test files (subagent dispatch)"
TaskCreate: "Phase 2: Cross-match against acceptance criteria"
TaskCreate: "Phase 3: Assemble coverage register"
```

Mark each `in_progress` when starting, `completed` when done. When dispatching agents, set `model:` explicitly on every Agent dispatch.

## Phase 0: Input Gathering

Before any scanning, gather and validate:

1. **Intent document path** — from `$ARGUMENTS[0]` or ask. Accepted sources, in priority order:
   - Spec with formal acceptance criteria (best — has numbered ACs with MUST/SHOULD/MAY)
   - Engineering guide (good — documents design decisions and expected behaviors)
   - Docstrings/module headers (acceptable fallback — at least express intent)

2. **Test directory path** — from `$ARGUMENTS[1]` or auto-discover. Look for common patterns: `tests/`, `test/`, `tb/`, `__tests__/`.

3. **Output path** — defaults to `test-coverage.md` alongside the intent document, or ask.

### Precondition Check

<HARD-GATE>
If no intent document exists (no spec, no eng-guide, no docstrings with behavioral descriptions), STOP and tell the user:

"Cannot generate coverage register — no intent document found. The register maps what SHOULD be tested to what IS tested. Without a spec, eng-guide, or documented behavioral intent, there is no 'should' to map against. Consider running `/write-spec-docs` or `/write-engineering-guide` first."

Do NOT infer "what should be tested" from the source code itself — that mirrors what exists and hides gaps. The entire point of this register is to surface what's missing, which requires an independent source of truth for expected behavior.
</HARD-GATE>

### Language Detection

> **Read [`references/language-conventions.md`](references/language-conventions.md)** to identify test frameworks and file patterns for the detected languages.

Scan the test directory to identify which languages and test frameworks are in use. This determines how Phase 1 subagents locate and interpret test files.

## Phase 1: Bottom-Up Test Scan

Scan all test files and produce a behavioral summary for each test function. This phase answers: "what do the existing tests actually verify?"

### Small Repo Shortcut

If the test directory contains fewer than 10 test files, skip subagent dispatch and scan all tests in a single pass. Read each test function and produce behavioral summaries directly.

### Subagent Dispatch (10+ test files)

> **Read [`references/phase1-subagent-prompt.md`](references/phase1-subagent-prompt.md)** for the subagent prompt template.

Dispatch one subagent per test file. Each subagent:
- Reads a single test file
- Returns a list of behavioral summaries, one per test function
- Has NO knowledge of acceptance criteria — it just describes what each test verifies

Set `model: sonnet` on Phase 1 subagents — this is mechanical extraction, not judgment.

Each summary follows this schema:

```
test_file:     string   # relative path to test file
test_function: string   # function or method name
module:        string   # source module being tested (inferred from imports/fixtures)
behavior:      string   # plain-language description of what the test verifies
type:          string   # unit | integration | e2e | smoke
```

**Example:**
```
test_file:     tests/test_auth.py
test_function: test_refresh_token_expired
module:        auth
behavior:      Returns 401 when refresh token is expired
type:          unit
```

### Staleness Check

During scanning, compare git timestamps: for each test file, check if the corresponding source file has been modified more recently. If yes, flag the test file as potentially stale. This is a generation-time check — no persistent tracking needed.

```bash
# Conceptual check — adapt to actual repo structure
git log -1 --format=%ct -- src/auth/token.py  # source last modified
git log -1 --format=%ct -- tests/test_auth.py  # test last modified
# If source > test → flag [stale?]
```

## Phase 2: Top-Down Cross-Match

Load all Phase 1 behavioral summaries and the acceptance criteria from the intent document into a single context. Cross-match them.

Set `model: opus` for Phase 2 if dispatching as a subagent — this is judgment-heavy semantic matching.

### Extracting Acceptance Criteria

From the intent document, extract every acceptance criterion. Preserve:
- **ID** — AC number or FR reference (e.g., AC-3, FR-1.2)
- **Description** — what the system must do
- **Priority** — MUST/SHOULD/MAY if present in the spec, or inferred emphasis from eng-guide
- **Module scope** — which module(s) the AC applies to

### Scenario Decomposition

For each acceptance criterion, decompose into testable scenarios. This is the core reasoning task — turning a behavioral requirement into concrete test cases.

**Good decomposition:**
```
AC-3: Token refresh flow [MUST]
  → Happy path: refresh valid token
  → Expired refresh token returns 401
  → Concurrent refresh race condition
```

**Bad decomposition (too coarse):**
```
AC-3: Token refresh flow [MUST]
  → Token refresh works
```

Each scenario should be independently testable — a single assertion or small group of related assertions.

### Matching Rules

For each scenario, search the Phase 1 summaries for a behavioral match:
- **Match found** → mark `[x]`, link to test file and function
- **No match** → mark `[ ]`, leave test reference blank
- **Ambiguous match** (summary is close but not exact) → mark `[~]`, link the candidate and note the ambiguity

For each Phase 1 summary that doesn't match any scenario → add to the **Orphaned Tests** section.

### Classification Policy

Coverage status is **derived mechanically** from the scenario checklist — never a subjective judgment:

| Scenario results | Status |
|---|---|
| All scenarios `[x]` | **Covered** |
| Mix of `[x]` and `[ ]` or `[~]` | **Partial (N/M scenarios)** |
| All scenarios `[ ]` | **Not Covered** |

Include the count: `Partial (2/5 scenarios)`. This makes the gap size visible at a glance.

### CI-Only Detection

If a behavior appears to be validated only by a CI pipeline step (e.g., "the Docker image builds" lives in a GitHub Action but has no dedicated test file), flag it:

```
  [!] Image builds successfully — CI-only validation, no dedicated test
```

CI runs tests. CI is not a test. CI-only validation is a coverage gap disguised as safety.

## Phase 3: Assemble the Register

> **Read [`templates/test-coverage-register.md`](templates/test-coverage-register.md)** for the output template.

Assemble the final `test-coverage.md` with four sections:

### Section 1: Per-Module Coverage

One sub-section per module, mirroring the repo directory structure. Each contains:
- Module header with source path and test file path
- Acceptance criteria entries with scenario checklists
- Per-AC status (derived from checklist)
- Staleness flags where detected

### Section 2: Cross-Cutting Coverage

ACs that span multiple modules. These live at the parent directory level, named by the intersecting directories:

```
## Cross-Cutting: auth + billing

AC-12: All API endpoints return structured JSON errors [MUST]
  [x] Auth 401 returns JSON error body          (test_auth.py:67)
  [x] Billing 400 returns validation errors     (test_billing.py:112)
  [ ] Users 404 returns structured error
  [ ] Rate limit 429 returns retry-after header
  Status: Partial (2/4 scenarios)
```

### Section 3: Orphaned Tests

Test functions from Phase 1 that didn't match any acceptance criterion. Each entry includes the test file, function name, and behavioral summary. These signal either:
- Incomplete spec (the test covers real behavior not captured in ACs)
- Dead test code (the test verifies behavior that no longer exists)

### Section 4: Unfound Modules

Modules in the repo that have no intent document. For each:

```
## Unfound: src/notifications/

No spec, eng-guide, or docstrings with behavioral descriptions found.
Cannot determine expected coverage — consider writing a spec or eng-guide first.
```

### Summary Table

After the four sections, include a summary table:

| Module | Total ACs | Covered | Partial | Not Covered | Staleness Flags |
|--------|----------|---------|---------|-------------|-----------------|

And a **Prioritized Gaps** section ranking uncovered ACs by priority (MUST > SHOULD > MAY), with the highest-priority gaps first. This is the "what to write next" signal for both humans and agents.

## Maintenance Contract

This register is a living document:
- **Initialized** by this skill (full generation)
- **Updated incrementally** by `/patch-docs` when tests are added, modified, or removed
- **Staleness flags refresh** on each generation — they are computed, not stored

When `/patch-docs` updates this register, it should:
- Add `[x]` marks when new tests cover previously uncovered scenarios
- Update the summary table counts
- Refresh staleness flags for affected modules
- NOT regenerate the entire register — only modify affected sections
