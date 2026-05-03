---
name: write-module-tests
description: "Use when you have a test plan and need to implement the actual pytest code for a specific module. Triggered by 'write module tests', 'implement the tests', 'create pytest code for this module'."
domain: code.test
intent: write
tags: [pytest, module tests, test code]
user-invocable: false
---

# Write Module Tests

Implements pytest test code for a single module, working exclusively from the test plan as its source of truth. The agent never reads source code — tests are derived from documented behavior and contracts, ensuring they verify the specification, not the implementation.

**Preconditions — stop and surface an error if any are missing:** (1) Test plan section for this module from write-test-docs, (2) Phase 0 contracts for the module's interfaces. If either is missing, tell the user: "Cannot write tests for [module] — missing [artifact]. Run /write-test-docs first."

## Purpose

Implement pytest test code for an already-implemented module. Tests are derived from the module's `write-test-docs` section — specifically the happy path scenarios, error scenarios, boundary conditions, and integration points — not from reading source code.

This ensures tests verify documented behavior (what was specified in write-test-docs), not implementation details.

**Announce at start:** "I'm using the write-module-tests skill to implement test code."

## Layer Context

```
Phase 0: Contracts               (write-implementation-docs)
Phase B: Implementation          (implement-code)
Phase C: Engineering Guide       (write-engineering-guide)
Phase D: Test Docs               (write-test-docs)
Phase E: Test Implementation     ← YOU ARE HERE
```

## Isolation Contract

**Include verbatim at the top of every task:**

> **Agent isolation contract:** This agent receives ONLY:
> 1. The module section from write-test-docs (happy path, error scenarios, boundary conditions, integration points, known gaps)
> 2. Phase 0 contract files (TypedDicts, signatures, exceptions — for import surface only)
>
> **Must NOT receive:** Source implementation files (`src/`), the engineering guide, other modules' test specs.

## Input Requirements

Before writing tests, you MUST have:
1. **The module's write-test-docs section** — read all sub-sections: happy path scenarios, error scenarios, boundary conditions, integration points, known test gaps
2. **Phase 0 contract files** — for import surface only (do not infer behavior from stubs)

Do NOT read source files. If the write-test-docs section is insufficient to write a test, note it as a known gap — do not fetch source.

## What to Test

Derive test cases from these sub-sections of the module's write-test-docs section:

| Test Docs Sub-section | What to extract |
|---|---|
| **Happy path scenarios** | One test per table row — input → expected output |
| **Error scenarios** | One test per row — trigger condition → expected exception + message pattern |
| **Boundary conditions** | Tests for each explicitly stated edge case (empty, None, zero, max, etc.) |
| **Integration points** | Tests for call contracts — input type, output type, error propagation |
| **Known test gaps** | Note in a comment — do NOT skip silently |

## Test File Format

```python
"""
Tests for <module name>.
Derived from: docs/<subsystem>/<SYSTEM>_TEST_DOCS.md — Section: `src/path/module.py`
FR coverage: FR-X.Y, FR-X.Z
"""
import pytest
from src.path.module import FunctionName
from contracts.schemas import RelevantType

# --- Happy path tests ---

def test_<function>_<scenario>():
    """FR-X.Y: <scenario description> per test docs happy path."""
    result = function_name(input_value)
    assert result == expected_output

# --- Error scenario tests ---

def test_<function>_raises_<error>_when_<condition>():
    """FR-X.Y: <error> raised when <condition> per test docs error scenarios."""
    with pytest.raises(SomeError, match="expected message pattern"):
        function_name(triggering_input)

# --- Boundary condition tests ---

def test_<function>_handles_empty_input():
    """Boundary: empty input per test docs boundary conditions."""
    result = function_name([])
    assert result == expected_empty_result

# --- Known gaps (do not skip silently) ---
# GAP: <behavior> is noted as difficult to test in test docs — no test written.
```

## Expected Outcome

All tests must **FAIL** when first run — the implementation exists but these test cases are new. If a test passes immediately without changes, verify it is not duplicating existing coverage (note and flag it, do not count as new).

Run after writing:
```bash
pytest tests/path/test_module_coverage.py -v
```
Expected: FAIL (new tests against existing implementation)

## Task Exit Format

Return:
- Test file path created
- Count of tests written per category (happy path / error scenarios / boundary / integration)
- List of known gaps noted in comments
- Pytest command run + FAIL confirmation
