# Task Section Template

One section per task from the decomposition plan. Each task must trace to at least
one spec requirement and have actionable, verifiable subtasks.

---

### Task X.Y: [Descriptive Task Name]

**Description:** [What this task builds — one paragraph, focus on the deliverable, not the approach.]

**Requirements Covered:** REQ-xxx, REQ-yyy, REQ-zzz
_(Every REQ/FR this task addresses. Must not be empty — every task traces to at least one requirement.)_

**Dependencies:** Task M.N _(or "None" if this task can start independently)_

**Complexity:** S / M / L
_(S: single module, <1 day. M: multiple components, 1-3 days. L: cross-cutting, >3 days.)_

**Subtasks:**
1. [Atomic, independently verifiable step — imperative voice: "Define...", "Implement...", "Wire..."]
2. [Atomic step]
3. [Atomic step]

**Risks:** [For M and L tasks: what could go wrong → mitigation. Omit for S tasks.]

**Testing Strategy:** [Brief approach: unit / integration / E2E. Omit when obvious.]

---

## Example — Well-Written Task

### Task 2.1: Input Validation Guard

**Description:** Build a validation layer that rejects malformed requests before they reach the processing pipeline. Returns structured error responses for rejected inputs.

**Requirements Covered:** REQ-101, REQ-105

**Dependencies:** Task 1.2

**Complexity:** M

**Subtasks:**
1. Define a `ValidationResult` dataclass with `is_valid`, `error_code`, and `error_message` fields
2. Implement length checks (reject inputs exceeding 10,000 characters per REQ-101)
3. Implement encoding validation (reject non-UTF-8 input per REQ-105)
4. Wire validator as the first stage in the request pipeline
5. Return structured error response for rejected inputs

**Risks:** Edge cases in encoding detection for mixed-encoding payloads → mitigate with strict UTF-8 enforcement and explicit rejection.

**Testing Strategy:** Unit test each validation rule with boundary inputs (0, 9999, 10000, 10001 chars); integration test with pipeline to verify rejected requests never reach downstream stages.

---

## Anti-Pattern — What NOT to Write

### Task 1: Setup

**Description:** Set up the project and get everything working.

**Requirements Covered:** All

**Dependencies:** None

**Complexity:** L

**Subtasks:**
1. Set up the project
2. Make it work
3. Test everything

**Problems:** Vague description (no deliverable), "All" is not traceable, subtasks are not actionable or verifiable, complexity is inflated because scope is undefined.

---

## Field Guidelines

- **Description:** What the task produces. Not how — the subtasks cover that.
- **Requirements Covered:** List the REQ-xxx / FR-xxx IDs from the companion spec.
- **Dependencies:** Reference other tasks by number (e.g., "Task 2.1"). "None" if independent.
- **Complexity:** S (single module, <1 day), M (multiple components, 1-3 days), L (cross-cutting, >3 days).
- **Subtasks:** 3-6 specific steps. Each independently verifiable. Imperative voice.
- **Risks:** (Optional) For M and L tasks. What could go wrong + mitigation. 1-2 bullets.
- **Testing Strategy:** (Optional) Brief approach note — not test code, just the kind of testing needed.
