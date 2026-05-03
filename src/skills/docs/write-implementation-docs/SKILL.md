---
name: write-implementation-docs
description: Use when you have a spec AND a design doc and need to produce the implementation source-of-truth before touching code. Triggered by "write implementation docs", "write-implementation-docs", "impl docs", "create implementation reference", "implementation source of truth".
domain: docs.impl
intent: write
tags: [implementation, source-of-truth, handoff]
user-invocable: true
argument-hint: "[system name] [spec path] [design doc path] [optional: output path]"
---

## Layer Context

```
Layer 3: Authoritative Spec     ← write-spec-docs (required input)
Layer 4: Design Document        ← write-design (required input)
Layer 5: Implementation Docs    ← YOU ARE HERE
Layer 6: Implementation         ← implement-code (reads this document)
```

# Write Implementation Docs

## Wrong-Tool Detection

- **User wants a design doc (task decomposition, contracts)** → redirect to `/write-design-docs`
- **User wants an execution plan for parallel agents** → redirect to `/build-plan`
- **User wants to write the code** → proceed without this skill or use `/parallel-agents-dispatch`

This skill produces the single reference document that `implement-code` agents use. Its core design constraint: **every task section must be a complete, standalone handoff doc** — an agent receiving only that section should have everything needed to implement the task without any other context.

The dependency graph in the output tells `implement-code` which tasks can run in parallel (no dependencies between them) and which must wait (downstream tasks).

**Announce at start:** "I'm using the write-implementation-docs skill to create the implementation source-of-truth."

## Progress Tracking

At the start, create a task list:

```
TaskCreate: "Planning Stage: read inputs and produce section_context_map"
TaskCreate: "Section phase_0: Phase 0 contract definitions"
TaskCreate: "Sections task_N: Per-task sections (topological order)"
TaskCreate: "Section module_map: Module boundary map"
TaskCreate: "Section dep_graph: Dependency graph"
TaskCreate: "Section traceability: Task-to-FR traceability table"
TaskCreate: "Assembly: combine approved sections into final document"
```

Mark each `in_progress` when starting, `completed` when done. Set `model:` explicitly on every Agent dispatch.

## Input Gathering

Before starting the Planning Stage, read:

1. **Spec** — extract every FR/REQ ID and its acceptance criteria.
2. **Design doc** — extract Part A task list (descriptions, FR assignments, dependencies, file targets) and all Part B CONTRACT entries verbatim. Ignore pattern entries — they go directly to `implement-code` task agents, never into this document.
3. **System name and output path** — from `$ARGUMENTS`, or defaults to `docs/<subsystem>/<SUBSYSTEM>_IMPLEMENTATION_DOCS.md` (or `_IMPLEMENTATION_DOCS_P{N}.md` if phased).
4. **Phase number** — If phased delivery, which phase?
5. **Prior phase source code** (P2+ only) — the actual codebase with real implementations of prior-phase contracts.
6. **Prior phase engineering guide** (P2+ only) — `_ENGINEERING_GUIDE.md` showing what was actually built.

## Scope Check

One implementation docs file per subsystem. If the design doc covers multiple independent subsystems, produce separate files.

---

## Planning Stage (NON-SKIPPABLE)

Before writing any section, read all inputs and produce a `section_context_map`. Each entry is one section agent's complete, pre-built context.

**Why this stage exists:** Reading the full spec and design doc for each section independently causes context accumulation and drift in late sections. Reading once and extracting per-section content into the map lets each section agent start immediately with only the content it needs — no file reads, no drift.

### `section_context_map` schema

| Field | Type | Purpose |
|---|---|---|
| `id` | string | Unique identifier — `"phase_0"`, `"task_1"`, `"dep_graph"`, etc. |
| `title` | string | Section heading for the output document |
| `order` | int | Dispatch sequence (lower = earlier); determines which sections block others |
| `depends_on` | [id, ...] | Section IDs whose approved outputs must be injected before dispatch |
| `model_tier` | haiku \| sonnet | haiku for mechanical extraction; sonnet for reasoning tasks |
| `source_content` | string | Verbatim text from spec + design doc for THIS section only. Never a file path. |
| `prior_slots` | [id, ...] | Section IDs whose outputs fill `{{slot_id}}` markers in `prompt` |
| `prompt` | string | Complete, self-contained prompt for this section agent |

### Section execution order

```
Order 1 (single section):
  phase_0       → Phase 0: Contract Definitions
                  source: all Part B CONTRACT entries verbatim (not pattern entries)
                  model_tier: haiku
                  depends_on: []

Order 2, 3, ... (one per task, topological order):
  task_<N>      → Per-task implementation section
                  source: task description + FR text + ACs + relevant Phase 0 stubs for this task
                  model_tier: sonnet
                  depends_on: [phase_0] + [predecessor task IDs from design doc]
                  prior_slots: [phase_0] + [predecessor task IDs]

Order N, N+1 (after all task sections approved):
  module_map    → Module Boundary Map
                  source: compiled task IDs + source file paths (inlined)
                  model_tier: haiku
  dep_graph     → Dependency Graph (ASCII DAG)
                  source: compiled task IDs + Dependencies fields (inlined)
                  model_tier: haiku

Order N+2:
  traceability  → Task-to-FR Traceability Table
                  source: full FR list + all task IDs + their FR coverage (inlined)
                  model_tier: haiku
                  depends_on: [module_map, dep_graph]
```

### How to produce the map

1. Record every FR/REQ ID and AC from the spec.
2. List every Part A task: description, FR assignments, dependency references, file targets.
3. Collect all Part B CONTRACT entries verbatim into `phase_0.source_content`.
4. For each task: copy its description, FR text, and only the Phase 0 stubs relevant to this task into `source_content`. Write the full prompt using the task section template.

> **Read [`templates/task-section.md`](templates/task-section.md)** for the exact task section prompt format.

5. Assign `order` by topological sort: tasks with no task dependencies get order 2; tasks depending on order-2 tasks get order 3; etc.
6. Verify the dependency graph is a valid DAG before proceeding.

→ **Do not dispatch any section agent until the full map is in session.**

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
  6. Issues → provide specific feedback, agent revises, re-review (max 3 iterations then escalate)
```

**Why sequential, not parallel:** Sections are not independent. Task sections reference Phase 0 contracts from the prior approved output. The `dep_graph` must match every task's `Dependencies` field. The `traceability` table compiles all prior sections. Parallel execution would produce sections that contradict each other.

### Review criteria per section

| Section | What to verify before approving |
|---|---|
| `phase_0` | All stubs use `raise NotImplementedError("Task N")` — no `pass`, no bodies. Error taxonomy covers every exception class. Integration contracts show directional `A → B` arrows with error propagation. Pure utilities fully implemented. |
| `task_<N>` | Isolation contract block present verbatim. File paths exact (no `src/path/` placeholders). Every implementation step tagged with an FR number. Phase 0 contracts inlined — no "see Phase 0" cross-references. No implementation hints in stub bodies. |
| `module_map` | Every task's source files listed. `CREATE` vs `MODIFY` annotated correctly. |
| `dep_graph` | Matches every task's `Dependencies` field. Valid DAG — no cycles. |
| `traceability` | Every FR from spec appears. Every task listed. No orphan tasks (task without FR). |

### Section agent isolation contract

Each section agent receives ONLY:
1. Its pre-built `prompt` (source content already inlined, prior outputs injected via `{{slot_id}}`)
2. No file reads — everything needed is in the prompt

Must NOT receive: the full spec, the full design doc, other sections' source material, pattern entries, or the full `section_context_map`.

---

## Document Structure

> **Read [`templates/doc-header.md`](templates/doc-header.md)** for the document header format.
> **Read [`templates/task-section.md`](templates/task-section.md)** for the per-task section format.

```
# [System Name] — Implementation Docs
[Header with goal, spec path, design doc path]

## Phase 0: Contract Definitions        ← TypedDicts, exceptions, stubs, utilities,
                                            error taxonomy, integration contracts

## Task 1: [Name]                        ← one per task from design doc
  ...
## Task N: [Name]

## Module Boundary Map                   ← task → source files (feeds write-engineering-guide)
## Dependency Graph                      ← ASCII DAG (feeds implement-code parallelism)
## Task-to-FR Traceability Table         ← FR → task → source file
```

---

## Phase 0: Contract Definitions

Phase 0 is the most important section. Every `implement-code` task agent works against these definitions — bad contracts here propagate to every task.

> **Read [`references/phase0-guide.md`](references/phase0-guide.md)** for how to derive Phase 0 from design doc Part B: contract vs pattern distinction, error taxonomy table format, integration contracts format, and stub rules.

For phased delivery (P2+): Phase 0 splits into Phase 0a (established contracts from prior phases as import references) and Phase 0b (new stubs for this phase). Read [`references/phased-delivery.md`](references/phased-delivery.md) for the full Phase 0 evolution rules.

**Phase 0 review gate:** Phase 0 must be reviewed and approved before any task section agent is dispatched. If Phase 0 has errors, stop and fix — task sections inline these contracts.

---

## Quality Checklist

Before assembling the final document:

- [ ] Phase 0 approved before any task section was written
- [ ] All stubs use `raise NotImplementedError("Task N")` — no `pass`, no comment bodies
- [ ] Error taxonomy covers every exception class in Phase 0
- [ ] Integration contracts use directional `A → B` arrows with error propagation expectations
- [ ] Every task section has a verbatim "Agent isolation contract" block
- [ ] Every task section has its Phase 0 contracts inlined (no cross-section references)
- [ ] Dependency graph is a valid DAG
- [ ] Dependency graph matches every task's `Dependencies` field
- [ ] Every FR from the spec appears in the traceability table
- [ ] No orphan tasks (every task traces to at least one FR)
- [ ] Module boundary map lists all source files that will be created or modified
- [ ] No design doc pattern entries appear anywhere in the document

---

## Common Mistakes

> **Read [`references/common-mistakes.md`](references/common-mistakes.md)** for the full table of common mistakes and fixes.

---

## Phased Delivery

When writing implementation docs for a specific delivery phase (P1, P2, P3...):

> **Read [`references/phased-delivery.md`](references/phased-delivery.md)** for the full phasing rules: Phase 0a/0b split, established vs new contracts, error taxonomy accumulation, and cross-phase traceability.

**Summary:**
- Output naming: `{SUBSYSTEM}_IMPLEMENTATION_DOCS_P{N}.md`
- P2+ Phase 0 splits into 0a (prior-phase real code as imports) and 0b (new stubs)
- Error taxonomy accumulates across phases
- Task numbering continues from prior phase
- Traceability covers this phase's FRs only, noting prior-phase extensions
- After writing, update the subsystem README dashboard — read [`references/readme-update-contract.md`](references/readme-update-contract.md)

---

## Integration

**Upstream (required before this skill):**
- `write-design` — must exist and have Part A tasks + Part B contract entries

**Downstream (in order):**
1. **Human review of Phase 0** — required before `implement-code` begins
2. `implement-code` — reads task sections; uses `parallel-agents-dispatch` following the dependency graph
3. `write-engineering-guide` — module boundary map tells it which source files to document
4. `write-test-docs` — reads engineering guide + Phase 0 contracts from this document
5. `write-module-tests` — reads write-test-docs module sections to implement pytest code

**Document chain:**
```
write-spec-docs → write-design → write-implementation-docs
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

After saving the implementation docs, update the subsystem's `README.md` dashboard. Read [`references/readme-update-contract.md`](references/readme-update-contract.md) for the update procedure.

**Chain handoff:** After saving, completing the quality checklist, and updating the README:

> "Implementation docs complete and saved to `[path]`. Phase 0 contracts are ready for human review — approve Phase 0 before proceeding. After approval, invoke `implement-code [system] [path]` to begin implementation."
