# Task Section Template

One section per task from the design doc. Each section is self-contained — the
implement-code agent reads only this section and nothing else.

---

## Task N: [Component Name]

**Description:** [What this task builds — one paragraph, plain language, no implementation hints.]

**Spec requirements:** FR-X.Y, FR-X.Z
_(Every FR this task addresses. Must not be empty — every task traces to at least one FR.)_

**Dependencies:** Task M _(or "none")_
_(implement-code uses this field to decide which tasks can run in parallel.)_

**Source files:**
- CREATE `src/path/component.py`
- MODIFY `src/path/config.py`

---

**Phase 0 contracts (inlined — implement these stubs):**

```python
from contracts.schemas import ComponentState, ComponentError

def component_function(state: ComponentState) -> ComponentState:
    """[Full docstring from Phase 0 — copy verbatim.]

    Args:
        state: [description]

    Returns:
        [description]

    Raises:
        ComponentError: [condition from error taxonomy]
        ValueError: [condition]
    """
    raise NotImplementedError("Task N")
```

_(Include only the stubs relevant to this task. Do not reference "see Phase 0" — inline them here.)_

---

**Implementation steps:**

1. [FR-X.Y] [Atomic step — 2–5 minutes each. Imperative: "Implement...", "Define...", "Wire..."]
2. [FR-X.Y] [Atomic step]
3. [FR-X.Z] [Atomic step — raise `ComponentError` on ...]
4. Add `@summary` block and module-level docstring

**Completion criteria:**
- [ ] All stubs implemented — no `NotImplementedError` remaining in this task's files
- [ ] Integration contracts honored: input/output shapes match Phase 0 contract surface
- [ ] `@summary` block at top of each new file
- [ ] Module-level docstring present on each file

---

**Agent isolation contract (copy verbatim into implement-code dispatch):**

> **Agent isolation contract:** This agent receives ONLY:
> 1. This task section (description, FRs, Phase 0 contracts inlined above, implementation steps)
>
> **Must NOT receive:** Other task sections, other source files, design doc pattern entries,
> the full spec, the full design doc, or the complete implementation docs.

---

## Notes on filling this template

**Description:** Describe the deliverable, not the approach. "Implement the embedding module that converts query strings to vectors using the configured model" is good. "Set up the embedder stuff" is not.

**Dependencies:** If this task can start at the same time as other tasks with no inter-task dependency, write "none". This directly controls whether `implement-code` runs this task in the same parallel wave as others.

**Phase 0 contracts:** Extract only the stubs that this task will implement. If a task has no stubs (e.g., it only modifies config), this section can say "No stubs — see Source files above."

**Implementation steps:** 3–6 steps, each 2–5 minutes of work. Every step tagged with an FR number. The last step is always documentation (docstrings + `@summary`).

**Isolation contract:** Copy verbatim. The implement-code dispatcher copies this block directly into its agent prompt — any modification breaks the contract.
