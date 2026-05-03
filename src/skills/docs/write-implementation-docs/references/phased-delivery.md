# Phased Delivery — Implementation Docs Layer

This reference applies when writing implementation docs for a specific delivery phase (P1, P2, P3...).

## When This Applies

Phased delivery is triggered when:
- The companion spec and design doc have phase suffixes
- The doc-authoring router passes phase context
- Prior phase implementation docs exist in the same directory

If none apply, write unphased implementation docs as normal — ignore this reference.

## Output Naming

```
{SUBSYSTEM}_IMPLEMENTATION_DOCS_P{N}.md
```

Example: `AUTH_IMPLEMENTATION_DOCS_P1.md`, `AUTH_IMPLEMENTATION_DOCS_P2.md`

## Inputs for P2+

| Input | P1 | P2+ |
|-------|-----|------|
| Phase spec | `_SPEC_P{N}.md` | `_SPEC_P{N}.md` |
| Phase design doc | `_DESIGN_P{N}.md` | `_DESIGN_P{N}.md` |
| Prior phase source code | N/A | **The actual codebase** — real implementations of prior-phase contracts |
| Prior eng guide | N/A | `_ENGINEERING_GUIDE.md` — what was actually built |

**Critical:** For P2+, the source of truth for prior-phase interfaces is the REAL CODE, not prior implementation docs. Prior Phase 0 stubs are now implemented.

## Phase 0 Evolution (most important change)

Phase 0 is the foundation all task sections build against. In phased delivery, it evolves:

### P1: Normal Phase 0

Standard rules: TypedDicts, exception classes, function stubs with `raise NotImplementedError("Task N")`, error taxonomy, integration contracts.

### P2+: Split Phase 0

Phase 0 splits into two sub-sections:

```markdown
## Phase 0: Contract Definitions

### Phase 0a: Established Contracts (from prior phases)

Interfaces from prior phases that this phase's tasks build against. These are REAL CODE — 
reference by import path, not as stubs.

| Interface | Source File | Established In | Used By (This Phase) |
|-----------|-----------|---------------|---------------------|
| AuthToken | src/auth/models.py | P1 Task 1.2 | Tasks 5.1, 5.2 |
| SessionState | src/auth/session.py | P1 Task 2.1 | Task 5.3 |
| validate_session() | src/auth/validation.py | P1 Task 2.3 | Task 5.2 |

Import block for task agents:
\```python
from auth.models import AuthToken, SessionState
from auth.validation import validate_session
\```

### Phase 0b: New Contracts (this phase)

New interfaces introduced in this phase. Standard Phase 0 rules apply — stubs with 
`raise NotImplementedError("Task X.Y")`.

[TypedDicts, exceptions, stubs as normal...]
```

### Rules for Phase 0a

- List ONLY interfaces that this phase's tasks actually use — not the entire prior codebase
- Show the import path and source file, not the full implementation
- If this phase EXTENDS a prior interface (adds fields/methods), show the FULL updated definition in Phase 0b with comments marking inherited vs new:

```python
# Extended from P1 AuthToken (src/auth/models.py)
class AuthToken(TypedDict):
    user_id: str           # P1 — inherited
    session_id: str        # P1 — inherited  
    role: str              # P2 — new
    permissions: list[str] # P2 — new
```

### Rules for Phase 0b

- Standard Phase 0 rules: stubs with `raise NotImplementedError("Task X.Y")`
- Error taxonomy ACCUMULATES: include prior-phase exception classes (as imports from 0a) plus new ones
- Integration contracts: show new `A → B` arrows for this phase, reference prior-phase arrows as "established"

## Task Numbering

Continues from prior phase — same global uniqueness rule as the design layer. If P1 ended at Task 4.3, P2 starts at Task 5.1.

## Task Sections for P2+

Each task section's isolation contract is the same, but the inlined Phase 0 content now includes:
- Phase 0a imports (prior-phase real interfaces this task uses)
- Phase 0b stubs (new interfaces this task implements)

Task sections should note prior-phase dependencies: "This task extends AuthToken (P1, Task 1.2) — the existing implementation is at `src/auth/models.py`."

## Traceability

The traceability table covers only this phase's FRs. But note which prior-phase FRs are being extended:

```markdown
| Task | FR (This Phase) | Extends (Prior Phase) | Source Files |
|------|-----------------|----------------------|-------------|
| 5.1 | FR-201 | FR-102 (P1) | src/auth/roles.py (CREATE) |
| 5.2 | FR-203 | FR-105 (P1) | src/auth/permissions.py (CREATE) |
```

## README Dashboard Update

After writing implementation docs, update the subsystem README dashboard. Read [`references/readme-update-contract.md`](readme-update-contract.md) for the update procedure.
