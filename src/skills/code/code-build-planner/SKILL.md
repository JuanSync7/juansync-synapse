---
name: code-build-planner
aliases: [build-plan]
description: "Triggered by 'build plan', 'execution plan', 'create a plan from the implementation docs'. Produces a six-phase bias-free execution plan from implementation docs, breaking work into agent-isolated tasks before code is written."
domain: code
scope: build
role: planner
tags: [execution, phases, agent-isolation, bias-free]
user-invocable: true
argument-hint: "[path to spec] [path to design document]"
---

# Code Build Planner

A build plan is bias-free when no single agent context ever holds both the test logic and the implementation logic for the same component. When one agent writes both, it writes tests that validate its own mental model rather than the spec — the test becomes a mirror of the implementation, not an independent check. This skill produces a six-phase plan (contracts → spec tests → implementation → engineering guide → white-box tests → full-suite verification) whose structural guarantee is that information barriers between phases force every test to be derived from the contract and spec alone. You author the plan document here; you do not execute the phases — the completed plan hands off to execution.

## MUST (every turn)
- Record position: `Position: [node-id] — <context>`
- Verify the implementation-docs input file exists before deriving anything — it is the source of truth for contracts, tasks, and the dependency graph. Without this, the plan is fabricated.
- Copy Phase 0 contracts verbatim from the implementation docs — never re-derive them from the design doc. Re-derivation drifts the type surface the test and implementation agents share.
- Set `model:` explicitly on every Agent dispatch — never rely on the session default.
- Tag every Phase A/D test case with the FR number it verifies — untagged tests cannot be checked for spec coverage.

## MUST NOT (global)
- Let design-doc pattern entries (illustrative code) reach a Phase A test agent — tests would mirror the reference implementation instead of the spec.
- Give one agent both the test and the implementation for the same component — this collapses the isolation guarantee the whole plan exists to enforce.
- Pre-code Phase A test bodies — the plan specifies WHAT to test (FR-tagged cases); the test agent writes HOW. Pre-coding injects author bias.
- Fabricate contracts, tasks, or FR numbers from memory when the input is missing — fail loudly instead.
- Advance a phase gate while any agent from the prior phase is unreviewed or unapproved — one unapproved agent corrupts everything built on top of it.

## Progress Tracking

At the start, create the phase task list:

```
TaskCreate: "Phase 0: Contract definitions"
TaskCreate: "Review gate: Phase 0 human review"
TaskCreate: "Phase A: Spec tests (parallel agents)"
TaskCreate: "Phase B: Implementation (against tests)"
TaskCreate: "Phase C: Engineering guide"
TaskCreate: "Phase D: White-box tests (parallel agents)"
TaskCreate: "Phase E: Full suite verification"
```

Mark each `in_progress` when starting, `completed` when done.

## Wrong-Tool Detection
- **Only a spec or feature request, no implementation docs** → `/docs-implementation-writer` (produces the required input for this skill)
- **Wants a vertical-slice story breakdown for parallel delivery** → `/delivery-plan-writer`
- **Wants interleaved test+implement steps for a small single-module feature** → over-engineered for that; use standard TDD in session
- **Has a design document from `docs-design-writer`** → this skill is correct; proceed

## Entry

### [NEW] Fresh session
Brief: Announce and verify inputs before any authoring.
Do:
  1. Announce: "I'm using the code-build-planner skill to create a bias-free implementation plan."
  2. Precondition — if no implementation-docs path is provided: stop and ask "Which implementation docs file should I use as input? (Typically from `docs-implementation-writer`)"
  3. Precondition — if a path is provided but the file does not exist: surface "Implementation docs not found at `<path>`. Cannot proceed without this input." and stop.
  4. Confirm scope: one plan per pipeline/subsystem; if the input spans multiple independent subsystems, produce separate plans.
Don't:
  - Proceed past a missing or non-existent input file.
  - Fabricate contracts or tasks from memory.
Exit:
  → [DERIVE] : implementation-docs input confirmed present

## Flow

### [DERIVE] Derive Phase 0 contracts
Load: references/phase-spec.md
Brief: Extract the shared type surface both the test and implementation agents build against.
Do:
  1. Copy contract entries (State TypedDicts, config dataclasses, exception types, fully-implemented pure utilities) verbatim from the implementation docs into Phase 0 file-creation steps.
  2. Render function stubs as signature + docstring + `raise NotImplementedError("Task B-X.Y")` — no implementation hints.
  3. Separate pattern entries (illustrative code) — they inform Phase B only and must NOT leak to Phase A.
Don't:
  - Re-derive contracts from the design doc when the implementation docs already define them.
  - Leave pure utilities as stubs — copy them fully implemented (stubbing blocks both phases).
Exit:
  → [DRAFT] : Phase 0 contract surface assembled

### [DRAFT] Author the six-phase plan
Load: references/phase-spec.md, templates/plan-template.md
Brief: Write the plan document — every phase, every task, every isolation contract.
Do:
  1. Write the plan to `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md` (a user location preference overrides this default).
  2. Author Phases 0, A, B, C, D, E per `phase-spec.md` — each parallel-phase task carries its "Agent input (ONLY these)" and "Must NOT receive" clauses verbatim.
  3. Build the header, File Structure section, dependency graph, and task-to-requirement mapping table from `plan-template.md`.
Don't:
  - Pre-code Phase A test bodies — list FR-tagged cases only.
  - Emit a plan whose tasks lack a "Must NOT receive" clause on any isolated phase.
Exit:
  → [DRAFT] : design has not yet converged (self-loop)
  → [REVIEW] : plan document written

### [REVIEW] Review loop
Load: references/reviewer-prompt.md
Brief: Dispatch a reviewer against the written plan; iterate to convergence.
Do:
  1. Dispatch the reviewer (model set explicitly) using the prompt template.
  2. Reviewer checks: every spec requirement appears in ≥1 Phase A task; every Phase A task has a "Must NOT receive" clause; every Phase B task references its Phase A test file; Phase 0 contracts match the implementation docs; the dependency graph matches the design.
  3. On issues, revise the plan and re-review.
Don't:
  - Exceed 3 review iterations without surfacing to a human.
  - Mark complete with open reviewer issues.
Exit:
  → [DRAFT] : reviewer found issues — revise
  → [HANDOFF] : reviewer approves (or 3 iterations reached → surface to human and proceed)

### [HANDOFF] Execution handoff
Load: references/phase-review-model.md
Brief: Present the phase-by-phase execution offer and the parallel-phase review model the executor will follow.
Do:
  1. Present the six-phase handoff summary (Phase 0 in-session + review gate; A / C-parallel / D dispatch one agent per task in parallel; B follows the dependency graph; C-cross after C-parallel; E full suite in session).
  2. State the phase-gate rule: a phase starts only when every agent from the prior phase is complete, reviewed, and approved.
  3. Ask: "Ready to start with Phase 0?"
Don't:
  - Auto-start execution — wait for the user.
  - Begin a downstream phase before the prior phase's gate is fully green.
Exit:
  → [END] : handoff presented

### [END]
Do:
  1. Print what was produced: plan path, phase count, and the review verdict.
  2. Remind: Phase 0 requires human review before Phase A begins.
Don't:
  - End without the plan path and handoff summary.
  - Auto-route to an execution skill — offer, do not dispatch.
