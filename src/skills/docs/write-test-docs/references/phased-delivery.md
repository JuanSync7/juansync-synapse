# Phased Delivery — Test Docs Layer

This reference applies when writing a test planning document for a specific delivery phase.

## When This Applies

Phased delivery is triggered when:
- The subsystem has phase-specific specs and design docs
- The engineering guide has been updated for this phase (check Phase History)
- The doc-authoring router passes phase context

## Output Naming

```
{SUBSYSTEM}_TEST_DOCS_P{N}.md
```

Example: `AUTH_TEST_DOCS_P1.md`, `AUTH_TEST_DOCS_P2.md`

## Inputs for P2+

| Input | P1 | P2+ |
|-------|-----|------|
| Engineering guide | Full guide | Same guide (cumulative — check Phase History for what's new) |
| Phase 0 contracts | `_IMPLEMENTATION_DOCS_P{N}.md` | `_IMPLEMENTATION_DOCS_P{N}.md` (includes Phase 0a/0b) |
| Spec | `_SPEC_P{N}.md` | `_SPEC_P{N}.md` |
| Prior test docs | N/A | `_TEST_DOCS_P{N-1}.md` — for regression requirements |

## Phase-Specific Test Plan

Each phase's test doc covers ONLY this phase's additions:

- **Module test specs** for modules introduced or modified in this phase
- **Integration test specs** for flows introduced in this phase
- **FR-to-test traceability** for this phase's FRs only

Identify which modules are new vs modified by checking the engineering guide's Phase History and module "Introduced in" / "Updated in" annotations.

## Regression Test Requirements (P2+ only)

P2+ test docs include an additional section after the FR-to-Test Traceability Matrix:

```markdown
## Regression Test Requirements

Tests from prior phases that must still pass after this phase's changes.

### Risk Assessment

| Prior Test | Prior Module | Risk from P{N} Changes | Regression Action |
|-----------|-------------|----------------------|-------------------|
| module_auth happy path (P1) | src/auth/token.py | HIGH — AuthToken extended with role field | Update test: add role field to fixture |
| module_session happy path (P1) | src/auth/session.py | LOW — no interface changes | Re-run as-is |
| integration_login (P1) | end-to-end | MEDIUM — login flow now includes role lookup | Update test: verify role in response |

### Actions

- **Re-run as-is** — prior test expected to pass unchanged
- **Update test** — prior test needs modification due to interface/behavior changes. Describe what changes.
- **New regression test** — new test needed to verify prior behavior still works after this phase's changes
```

### How to assess risk

1. Read this phase's spec "Prior Phase Contracts" section — any extended interfaces affect prior tests
2. Read this phase's implementation docs Phase 0a — established contracts that are used (not changed) are LOW risk
3. Any module that was updated in the engineering guide for this phase is at least MEDIUM risk
4. Any changed interface (extended TypedDict, new parameters) is HIGH risk

## Mock Evolution (P2+)

If prior-phase interfaces changed, mocks may need updating:

```markdown
#### Mock: AuthToken Factory
**Updated from P1:** Added `role` and `permissions` fields to mock return value.
**Reason:** P2 extended AuthToken TypedDict.
```

For new mocks, mark them: "**New in P{N}.**"

## Cross-Phase Integration Test (P2+ only)

P2+ integration test specs must include at least one scenario that exercises cross-phase interaction:

```markdown
### Integration: Cross-Phase — P2 Permissions Using P1 Auth Token

**Scenario:** New permission check (P2) validates against existing auth token (P1)
**Entry point:** `check_permission(token, resource)`
**Flow:**
1. Token validated by P1 session module
2. Role extracted from extended AuthToken (P2 field)
3. Permission checked against resource ACL (P2 module)
**What to assert:** P1 token validation still works with extended token format
```

## README Dashboard Update

After writing test docs, update the subsystem README dashboard. Read [`references/readme-update-contract.md`](readme-update-contract.md) for the update procedure.
