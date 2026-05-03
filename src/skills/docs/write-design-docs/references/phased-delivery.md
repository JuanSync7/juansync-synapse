# Phased Delivery — Design Layer

This reference applies when writing a design document for a specific delivery phase (P1, P2, P3...).

## When This Applies

Phased delivery is triggered when:
- The companion spec has a phase suffix (e.g., `AUTH_SPEC_P2.md`)
- The doc-authoring router passes phase context
- Prior phase design documents exist in the same directory

If none apply, write an unphased design doc as normal — ignore this reference.

## Output Naming

```
{SUBSYSTEM}_DESIGN_P{N}.md
```

Example: `AUTH_DESIGN_P1.md`, `AUTH_DESIGN_P2.md`

## Inputs for P2+

The input set expands for P2+ design documents:

| Input | P1 | P2+ |
|-------|-----|------|
| Phase spec | `_SPEC_P{N}.md` | `_SPEC_P{N}.md` |
| Codebase | Read for existing patterns | Read for existing patterns **+ prior phase's implemented code** |
| Prior eng guide | N/A | `_ENGINEERING_GUIDE.md` — shows what P1 actually built |
| Prior design doc | N/A | `_DESIGN_P{N-1}.md` — for task numbering continuity |

**Critical for P2+:** Reference REAL CODE from prior phases, not prior design doc stubs. Prior phase stubs are now implemented — the design doc must build against what actually exists.

## Task Numbering Across Phases

Task IDs are globally unique across all phases:

- P1 tasks: 1.1, 1.2, 2.1, 2.2, ... (grouped by phase/category within P1)
- P2 tasks: continue from where P1 ended. If P1 ended at Task 4.3, P2 starts at 5.1.
- This ensures traceability tables across phases never have ID collisions.

Check the prior phase's design doc to find the last task ID used.

## Part B Contract Entries for P2+

### Referencing prior-phase contracts

Prior-phase CONTRACT entries are now real code. Do not restate them as stubs. Instead:

```python
# Established in P1 — AUTH_DESIGN_P1.md B.1
# Real implementation: src/auth/models.py
from auth.models import AuthToken, SessionState
```

### New contracts in this phase

New interfaces follow normal CONTRACT rules (stubs with `raise NotImplementedError`).

### Extended interfaces

When this phase extends a prior-phase interface (adds fields, parameters):

```python
# Extended from P1 AuthToken (AUTH_DESIGN_P1.md B.1)
# New fields marked with # P2
class AuthToken(TypedDict):
    user_id: str           # P1 — established
    session_id: str        # P1 — established
    role: str              # P2 — new: user role for permission checks
    permissions: list[str] # P2 — new: granular permission list
```

## Cross-Phase Task Dependencies

Tasks may depend on prior-phase tasks. In the dependency graph:

```
--- Prior Phase Boundary (P1 complete) ---
Task 5.1: Role model         [depends on: Task 1.2 (P1)]
Task 5.2: Permission engine  [depends on: Task 5.1, Task 2.1 (P1)]
```

- Prior-phase tasks appear as completed dependencies — they are not re-executed
- Mark the phase boundary clearly in the ASCII DAG
- In task sections, note prior-phase dependencies: "Depends on Task 1.2 (P1, completed) — uses AuthToken from `src/auth/models.py`"

## Phase Context Header

Add a phase context block to the document header:

```markdown
**Phase:** P{N}
**Prior phases:** [AUTH_DESIGN_P1.md](AUTH_DESIGN_P1.md) (Tasks 1.1–4.3)
**Extends contracts:** AuthToken, SessionState (from P1 Part B)
```

## README Dashboard Update

After writing the design doc, update the subsystem README dashboard. Read [`references/readme-update-contract.md`](readme-update-contract.md) for the update procedure.
