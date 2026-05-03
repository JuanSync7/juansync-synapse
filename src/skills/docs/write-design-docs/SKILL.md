---
name: write-design-docs
description: Use when you have a spec and need to create a design document with task decomposition and code contracts before implementation. Triggered by "write design docs", "write-design-docs", "design document", "create design", "technical design".
domain: docs.design
intent: write
tags: [design, task decomposition, contracts]
user-invocable: true
argument-hint: "[system name] [spec path] [optional: output path]"
---

## Layer Context

```
Layer 3: Authoritative Spec     ← write-spec-docs (required input)
Layer 4: Design Document        ← YOU ARE HERE
Layer 5: Implementation Docs    ← write-implementation-docs (consumes this document)
Layer 6: Implementation         ← implement-code (receives pattern entries directly)
```

# Write Design Docs

## Wrong-Tool Detection

- **User wants a spec (requirements, acceptance criteria)** → redirect to `/write-spec-docs`
- **User wants implementation-level task details** → redirect to `/write-implementation-docs`
- **User wants to jump straight to code** → redirect to `/build-plan` or code directly

This skill produces the design document that bridges a specification (what to build) and implementation docs (how to build it). It answers: how should the system be decomposed into tasks, and what is the code contract surface?

The document has two parts:
- **Part A** — Task decomposition: phased tasks with descriptions, FR traceability, dependencies, and subtasks
- **Part B** — Code appendix: CONTRACT entries (exact types, stubs, exceptions) and PATTERN entries (illustrative algorithms)

**Downstream contract:** `write-implementation-docs` copies Part B CONTRACT entries verbatim into Phase 0. `implement-code` receives PATTERN entries directly — they never appear in implementation docs or reach test agents.

**Announce at start:** "I'm using write-design-docs to create the technical design document."

## Progress Tracking

At the start, create a task list:

```
TaskCreate: "Planning Stage: read inputs and derive task decomposition"
TaskCreate: "Review gate: task decomposition approval"
TaskCreate: "Sections: per-task details (Part A)"
TaskCreate: "Sections: contract entries (Part B)"
TaskCreate: "Sections: pattern entries (Part B)"
TaskCreate: "Sections: dependency graph + traceability table"
TaskCreate: "Assembly: combine approved sections into final document"
```

Mark each `in_progress` when starting, `completed` when done. Set `model:` explicitly on every Agent dispatch.

## Input Gathering

Before starting the Planning Stage, read:

1. **Spec** — extract every REQ/FR ID, its priority (MUST/SHOULD/MAY), and acceptance criteria.
2. **Codebase** — understand existing file structure, patterns, technology stack. What exists today vs what needs to be built from scratch.
3. **System name and output path** — from `$ARGUMENTS`, or defaults to `docs/<subsystem>/<SUBSYSTEM>_DESIGN.md` (or `_DESIGN_P{N}.md` if phased).
4. **Phase number** — If phased delivery, which phase? What prior phases exist?
5. **Prior phase artifacts** (P2+ only) — prior phase engineering guide (what was actually built), prior phase source code (real contracts to reference), prior phase design doc (for task numbering continuity).

If no spec is provided, request one before proceeding. Do not invent requirements.

## Scope Check

One design document per subsystem. If the spec covers multiple independent subsystems, produce separate documents. Each should be self-contained.

---

## Planning Stage (NON-SKIPPABLE)

Before writing any section, read all inputs and produce the task decomposition + `section_context_map`.

**Why this stage exists:** The task decomposition is the creative core of the design doc — it determines every downstream section. Getting it wrong means rewriting the entire document. Reading once, decomposing, getting approval, then building section contexts prevents drift and wasted work.

### Step 1: Derive task decomposition

From the spec and codebase analysis:

1. Group related requirements into implementable tasks.
2. For phased delivery (P2+): identify which requirements extend prior-phase interfaces. These tasks must list the prior-phase interface as a dependency and reference the real implementation (not stubs). Read [`references/phased-delivery.md`](references/phased-delivery.md) for cross-phase task dependency rules.
3. Assign each task a phase based on delivery order:
   - Foundation phases first (infrastructure, validation, config)
   - Logic phases next (algorithms, scoring, routing)
   - Quality phases (formatting, conflict detection)
   - Performance & observability (caching, tracing)
   - Security hardening (last)
3. Identify dependencies between tasks.
4. Verify the dependency graph is a valid DAG — no cycles.
5. Assign complexity: S (single module, <1 day) / M (multiple components, 1-3 days) / L (cross-cutting, >3 days).
6. Assign target file paths for each task.

Output: a task list with phase assignments, names, 1-sentence descriptions, FR assignments, dependencies, complexity, and target files.

### Step 2: Task decomposition review gate

The task decomposition must be reviewed and approved before any detail sections are written. Bad decomposition propagates to every section — fixing it later means rewriting all of them.

Present the decomposition as a summary table and wait for approval.

### Step 3: Build `section_context_map`

After approval, build the per-section context map.

### `section_context_map` schema

| Field | Type | Purpose |
|---|---|---|
| `id` | string | Unique identifier — `"task_1_1"`, `"contracts"`, `"dep_graph"`, etc. |
| `title` | string | Section heading for the output document |
| `order` | int | Dispatch sequence (lower = earlier) |
| `depends_on` | [id, ...] | Section IDs whose approved outputs must be injected before dispatch |
| `model_tier` | haiku \| sonnet | haiku for mechanical extraction; sonnet for reasoning tasks |
| `source_content` | string | Verbatim text from spec + decomposition for this section only |
| `prior_slots` | [id, ...] | Section IDs whose outputs fill `{{slot_id}}` markers in `prompt` |
| `prompt` | string | Complete, self-contained prompt for this section agent |

### Section execution order

```
Order 1, 2, ... (one per task, phase order):
  task_<X.Y>    → Per-task detail section (Part A)
                  source: task name + description + FRs + ACs from spec + deps + target files
                  model_tier: haiku (mechanical given the decomposition plan)
                  depends_on: []

Order N (after all task sections approved):
  contracts     → Part B contract entries (grouped by component)
                  source: all task descriptions + target file paths + relevant spec types
                  model_tier: sonnet (must reason about the interface surface)
                  depends_on: [all task sections]

Order N+1:
  patterns      → Part B pattern entries (grouped by component)
                  source: all task descriptions + contract entries for type references
                  model_tier: sonnet (must reason about algorithmic approaches)
                  depends_on: [contracts]

Order N+2, N+3:
  dep_graph     → Dependency Graph (ASCII DAG with critical path)
                  source: all task IDs + Dependencies fields
                  model_tier: haiku
  traceability  → Task-to-REQ Traceability Table
                  source: all task IDs + Requirements Covered fields + full REQ list from spec
                  model_tier: haiku
```

> **Do not dispatch any section agent until the full map is in session.**

---

## Execution Stage

Execute the `section_context_map` sequentially — one section at a time, reviewed and approved before the next begins.

```
For each entry in section_context_map (ascending order):
  1. Fill {{slot_id}} markers in prompt with prior approved outputs
  2. Dispatch section agent (model: per model_tier)
  3. Agent writes its section only — no file reads (all context inlined in prompt)
  4. Review output against the criteria below
  5. Approved → record output, advance to next section
  6. Issues → provide specific feedback, agent revises, re-review (max 3 then escalate)
```

**Why sequential, not parallel:** Contract entries depend on task sections (need to know what each task builds). Pattern entries depend on contracts (reference defined types). The traceability table compiles all prior sections. Parallel execution produces inconsistent sections.

### Review criteria per section

| Section | What to verify before approving |
|---|---|
| `task_<X.Y>` | Description focuses on deliverable, not approach. Subtasks use imperative voice and are independently verifiable. FR refs match spec. Dependencies match decomposition plan. Complexity justified. |
| `contracts` | All stubs use `raise NotImplementedError("Task X.Y")`. TypedDict fields tagged with FR comments. Exception docstrings explain when raised. Pure utilities fully implemented. Imports shown at top. |
| `patterns` | 50-120 lines. Self-contained. Shows design pattern, not full implementation. Includes "Key design decisions" explaining rationale. Labelled with "Illustrative pattern" comment. |
| `dep_graph` | Matches every task's Dependencies field. Valid DAG (no cycles). Critical path identified with `[CRITICAL]`. |
| `traceability` | Every REQ/FR from spec has at least one row. Every task listed. No orphan tasks (task without REQ). |

### Section agent isolation contract

Each section agent receives ONLY:
1. Its pre-built `prompt` (source content inlined, prior outputs injected via `{{slot_id}}`)
2. No file reads — everything needed is in the prompt

Must NOT receive: the full spec, the full codebase, other sections' source material, or the full `section_context_map`.

---

## Document Structure

> **Read [`templates/doc-header.md`](templates/doc-header.md)** for the document header format.
> **Read [`templates/task-section.md`](templates/task-section.md)** for the Part A task section format (includes good/bad examples).
> **Read [`templates/code-appendix.md`](templates/code-appendix.md)** for the Part B contract and pattern entry formats.

```
# [System Name] — Design Document
[Header: metadata, spec reference, document intent]

# Part A: Task-Oriented Overview

## Phase 1 — [Name]
### Task 1.1: [Name]
### Task 1.2: [Name]

## Phase 2 — [Name]
### Task 2.1: [Name]
...

## Task Dependency Graph          ← ASCII DAG with [CRITICAL] path
## Task-to-Requirement Mapping    ← REQ/FR → task table

# Part B: Code Appendix

## B.1: [State Schema — Contract]
## B.2: [Exception Types — Contract]
## B.3: [Function Stubs — Contract]
## B.4: [Pipeline Graph — Pattern]
...
```

---

## Contract vs Pattern Entries

Part B has two entry types with different rules and different consumers.

> **Read [`references/contract-vs-pattern.md`](references/contract-vs-pattern.md)** for the full classification guide, format rules, and examples.

Quick summary: CONTRACT entries are exact, complete, copied verbatim into Phase 0 (types, stubs, exceptions). PATTERN entries are illustrative, 50-120 lines, passed to implement-code only (algorithms, workflows, integration approaches).

---

## Quality Checklist

Before assembling the final document:

- [ ] Task decomposition approved before any detail sections written
- [ ] Every REQ/FR from the spec covered by at least one task
- [ ] Every task references at least one REQ/FR (no orphan tasks)
- [ ] Task dependencies form a valid DAG (no cycles)
- [ ] Dependency graph matches every task's Dependencies field
- [ ] Critical path identified in dependency graph
- [ ] Risks noted for all L complexity tasks
- [ ] Contract TypedDict fields have FR-tagged comments
- [ ] All stubs use `raise NotImplementedError("Task X.Y")` — no `pass`, no bodies
- [ ] Exception docstrings explain when each is raised
- [ ] Pure utility functions fully implemented (not stubs)
- [ ] Pattern entries include "Key design decisions" with rationale
- [ ] No pattern entries labelled as contracts or vice versa
- [ ] Contract entries include imports at top of each entry

---

## Common Mistakes

> **Read [`references/common-mistakes.md`](references/common-mistakes.md)** for the full table of mistakes, consequences, and fixes.

---

## Phased Delivery

When writing a design document for a specific delivery phase (P1, P2, P3...):

> **Read [`references/phased-delivery.md`](references/phased-delivery.md)** for the full phasing rules: task numbering continuity, contract references to real code, cross-phase dependency markers, and phase context header.

**Summary:**
- Output naming: `{SUBSYSTEM}_DESIGN_P{N}.md`
- P2+ references real code from prior phases, not stubs
- Task numbering continues from prior phase (globally unique across all phases)
- Part B contracts for P2+ reference prior-phase real implementations as imports
- Cross-phase dependencies marked with a "Prior Phase Boundary" in the DAG
- After writing, update the subsystem README dashboard — read [`references/readme-update-contract.md`](references/readme-update-contract.md)

---

## Integration

**Upstream (required before this skill):**
- `write-spec-docs` — the spec (Layer 3) must exist. Extract all REQ/FR IDs before writing.

**Downstream (in order):**
1. `write-implementation-docs` — copies Part B CONTRACT entries into Phase 0, writes isolated task sections
2. `implement-code` — receives PATTERN entries directly (never through implementation docs)
3. `write-engineering-guide` — documents what was built
4. `write-test-docs` → `write-module-tests`

**Document chain:**
```
write-spec-docs → write-design-docs → write-implementation-docs
                                        ↓
                                  implement-code
                                        ↓
                              write-engineering-guide
                                        ↓
                                 write-test-docs
                                        ↓
                               write-module-tests
```

## README Dashboard

After saving the design document, update the subsystem's `README.md` dashboard. Read [`references/readme-update-contract.md`](references/readme-update-contract.md) for the update procedure.

**Chain handoff:** After saving, completing the quality checklist, and updating the README:

> "Design document complete and saved to `[path]`. Next step: invoke `/write-implementation-docs [system] [spec path] [this design doc path]` to create the implementation source-of-truth."
