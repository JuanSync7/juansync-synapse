---
name: code-test-writer
aliases: [write-module-tests]
description: "Use when the user has a test plan in hand and needs pytest test code written for a specific module. Triggered by 'write module tests', 'implement the tests', 'create pytest code for this module', 'turn the test plan into code'."
domain: code
scope: test
role: writer
tags: [pytest, module-tests, test-code]
user-invocable: false
---

# Write Module Tests

This skill translates a finalized test plan into runnable pytest code for a single module. The core discipline is **plan fidelity over source inspection**: tests must prove the specification was honored, not that the implementation happens to behave a certain way. Reading source files undermines this — a test written against source can pass even when the specification was violated.

**Preconditions — MUST stop and surface an error if any are missing:** (1) Test plan section for this module from `/docs-test-plan-writer`, (2) Phase 0 contracts for the module's interfaces. If either is missing, tell the user: "Cannot write tests for [module] — missing [artifact]. Run `/docs-test-plan-writer` first."

## Wrong-Tool Detection

Redirect immediately — do NOT proceed — when the intent does not match:

| If the user wants… | Redirect to |
|---|---|
| Run existing tests and see results | `/code-test-runner` — this skill only WRITES tests, never executes them |
| A written test-plan document (not code) | `/docs-test-plan-writer` — outputs a markdown spec, not pytest files |
| Auto-fill gaps by scanning the codebase | `/code-test-generator` — scans source to find and fill coverage gaps |

Tell the user which skill to use and why in one sentence. Do NOT attempt to partially fulfill the misdirected intent.

## Layer Context

```
Phase 0: Contracts               (docs-implementation-writer)
Phase B: Implementation          (implement-code)
Phase C: Engineering Guide       (docs-engineering-guide-writer)
Phase D: Test Docs               (docs-test-plan-writer)
Phase E: Test Implementation     ← YOU ARE HERE (code-test-writer)
```

## MUST

- MUST derive every test from the docs-test-plan-writer section — never from reading `src/` files.
- MUST check preconditions before writing any test; fail loudly with a specific message if artifacts are missing.
- MUST note every known gap from the test plan as a `# GAP:` comment — never skip silently.
- MUST verify all tests FAIL after creation (new tests against existing implementation); flag any that pass immediately as potential coverage duplicates.
- Record position at each phase: `Position: [ENTRY | WRITE | VERIFY | END] — <context>`

## MUST NOT

- MUST NOT read source implementation files (`src/`) — inference from stubs or source violates the isolation contract.
- MUST NOT infer behavior from Phase 0 contract stubs beyond the import surface (type signatures only).
- MUST NOT auto-run tests on behalf of the user without explicit instruction.
- MUST NOT include more than one module's tests in a single task invocation.

## Isolation Contract

**State verbatim at the start of every task invocation:**

> **Agent isolation contract:** This agent receives ONLY:
> 1. The module section from docs-test-plan-writer (happy path, error scenarios, boundary conditions, integration points, known gaps)
> 2. Phase 0 contract files (TypedDicts, signatures, exceptions — for import surface only)
>
> **Excluded from context:** Source implementation files (`src/`), the engineering guide, other modules' test specs.

## Entry

### [ENTRY] Start

**Do:**
1. Announce: "Using `code-test-writer` to implement test code."
2. Confirm the two required inputs are present (test plan section + Phase 0 contracts).
3. If either is missing: surface the specific missing artifact and stop. Do NOT improvise.
4. State the isolation contract verbatim (see above).

**Don't:**
- Don't proceed if preconditions fail — even partially.
- Don't fetch source files to supplement a thin test plan; note the gap instead.

**Exit:** → [WRITE] when both inputs confirmed present.

## Flow

### [WRITE] Implement Tests

**Do:**
Derive test cases from the five sub-sections of the module's test plan:

| Test Docs Sub-section | What to extract |
|---|---|
| Happy path scenarios | One test per scenario row — input → expected output |
| Error scenarios | One test per row — trigger condition → expected exception + message pattern |
| Boundary conditions | One test per explicit edge case (empty, `None`, zero, max, etc.) |
| Integration points | Tests for call contracts — input type, output type, error propagation |
| Known test gaps | `# GAP: <behavior> noted as difficult to test — no test written.` |

**Test file format:**
```python
"""
Tests for <module name>.
Derived from: docs/<subsystem>/<SYSTEM>_TEST_DOCS.md — Section: `src/path/module.py`
FR coverage: FR-X.Y, FR-X.Z
"""
import pytest
from src.path.module import FunctionName
from contracts.schemas import RelevantType

# --- Happy path ---
def test_<function>_<scenario>():
    """FR-X.Y: <scenario> per test docs happy path."""
    assert function_name(input_value) == expected_output

# --- Error scenarios ---
def test_<function>_raises_<error>_when_<condition>():
    """FR-X.Y: <error> raised on <condition> per test docs error scenarios."""
    with pytest.raises(SomeError, match="expected message pattern"):
        function_name(triggering_input)

# --- Boundary conditions ---
def test_<function>_handles_empty_input():
    """Boundary: empty input per test docs boundary conditions."""
    assert function_name([]) == expected_empty_result

# --- Known gaps ---
# GAP: <behavior> noted as difficult to test in test docs — no test written.
```

**Don't:**
- Don't write tests for behavior not stated in the test plan.
- Don't reuse variable names across test cases in a way that creates hidden state.

**Exit:** → [VERIFY] when all test cases written and file saved.

### [VERIFY] Confirm New Tests Fail

**Do:**
1. Run: `pytest tests/path/test_module.py -v`
2. Expected result: ALL new tests FAIL (new coverage against existing implementation).
3. If any new test passes immediately: flag it as a potential coverage duplicate — note which scenario it may overlap. Do NOT count it as new coverage.

**Don't:**
- Don't treat a passing test as success without investigating.
- Don't modify the implementation to make tests pass — that is the job of the implementer.

**Exit:** → [END]

### [END] Report

**Do:**
Return a structured summary:
- Test file path written
- Counts by category: happy path / error scenarios / boundary / integration
- Known gaps listed (verbatim from `# GAP:` comments)
- Pytest run result: FAIL count and PASS count (passes flagged as duplicates)

**Don't:**
- Don't auto-route to `/code-test-runner` or any other skill.
- Don't suppress gaps or pass counts from the summary.
