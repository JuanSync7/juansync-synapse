---
name: build-plan
description: "Use when you have implementation docs and need an execution plan that breaks work into independent tasks before writing code. Triggered by 'build plan', 'execution plan', 'create a plan from the implementation docs'."
domain: code.plan
intent: plan
tags: [execution, phases, agent isolation, bias-free]
user-invocable: true
argument-hint: "[path to spec] [path to design document]"
---

# Write Implementation Plan

## Overview

Generate six-phase implementation plans that prevent test bias through agent context isolation. The plan separates contract definition, test writing, implementation, documentation, white-box testing, and full suite verification into phases with explicit information barriers — the test agent never sees implementation code, and the implementation agent works against pre-written tests it didn't author.

This skill extends the `writing-plans` pattern (checkboxes, exact file paths, bite-sized steps, TDD) with a structural guarantee: **no single agent context ever holds both the test logic and the implementation logic for the same component.**

**Why this matters:** When the same agent writes both test and implementation, it writes tests that validate its own mental model — not the spec's requirements. Separating them forces the test agent to derive test cases from the contract and spec alone, producing tests that are an independent verification rather than a mirror of the implementation.

**Announce at start:** "I'm using the build-plan skill to create a bias-free implementation plan."

## Progress Tracking

At the start, create a task list:

```
TaskCreate: "Phase 0: Contract definitions"
TaskCreate: "Review gate: Phase 0 human review"
TaskCreate: "Phase A: Spec tests (parallel agents)"
TaskCreate: "Phase B: Implementation (against tests)"
TaskCreate: "Phase C: Engineering guide"
TaskCreate: "Phase D: White-box tests (parallel agents)"
TaskCreate: "Phase E: Full suite verification"
```

Mark each `in_progress` when starting, `completed` when done. When dispatching agents, set `model:` explicitly on every Agent dispatch — do not rely on the session default.

**Input requirements:**
1. An implementation docs document (from `write-implementation-docs`) — the source of truth for contracts, task sections, and dependency graph
2. The companion spec — for FR number reference during test phase planning

**Save plans to:** `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md`
- User preferences for plan location override this default.

## Layer Context

```
Layer 1: Platform Spec          (manual)
Layer 2: Spec Summary           ← write-spec-summary
Layer 3: Authoritative Spec     ← write-spec-docs
Layer 4: Design Document        ← write-design-docs
Layer 5: Implementation Docs    ← write-implementation-docs (required input)
Layer 6: Build Plan             ← YOU ARE HERE (build-plan)
```

## Wrong-Tool Detection

- **User has only a spec or feature request, no design document** → redirect to `/writing-plans`
- **User wants interleaved test+implement steps for a small feature** → redirect to `/writing-plans`
- **User has a design document from `write-design-docs`** → this skill is correct; proceed

## Scope Check

One plan per pipeline/subsystem. If the input covers multiple independent subsystems, produce separate plans.

## The Five Phases

```
Phase 0 ──► [REVIEW GATE] ──► Phase A ──► Phase B ──► Phase C ──► Phase D ──► Phase E
 Contracts                  Spec tests   Impl only   Eng guide   WB tests   Full suite
                                         (parallel)  (parallel   (parallel)
                                                      + cross)
```

### Phase 0 — Contract Definitions

Phase 0 contracts are already defined in the implementation docs. Copy them verbatim — do not re-derive from the design doc. Organize them into implementable files as the shared type surface both test and implementation agents work against.

**What it contains:**
- State TypedDicts — copied from implementation docs contract entries
- Config dataclasses — copied from implementation docs contract entries
- Exception types — copied from implementation docs contract entries
- Function signature stubs — bodies are `raise NotImplementedError("Task B-X.Y")`
- Pure utility functions — copied fully implemented from implementation docs

**Phase 0 code is complete, copy-pasteable Python.** It comes from the implementation docs' contract entries — the plan organizes them into file-by-file creation steps.

**Review gate:** Phase 0 must be human-reviewed before Phase A begins.

### Phase A — Tests (Isolated from Implementation)

Write test specifications that verify spec requirements using only contracts and spec — never implementation knowledge.

**The isolation contract — include verbatim at the top of Phase A:**

```markdown
**Agent isolation contract:** The test agent receives ONLY:
1. The spec requirements (FR numbers + acceptance criteria)
2. The contract files from Phase 0 (TypedDicts, signatures, exceptions)
3. The task description from the design document

**Must NOT receive:** Any implementation code, any pattern entries from the
design doc's code appendix, any source files beyond Phase 0 stubs.
```

Each Phase A task specifies:
1. **"Agent input (ONLY these):"** — exact FR numbers with brief descriptions, exact contract file paths
2. **"Must NOT receive:"** — explicit list of forbidden files/directories
3. **"Files:" → Create:** — exact test file path
4. **Test cases** — bulleted list tagged with FR numbers
5. **Pytest command** with expected FAIL outcome

**Why test cases are listed but not pre-coded:** The plan specifies *what* to test (from spec). The test agent writes *how*. Pre-coded tests would reflect the plan author's bias from having read the design doc's pattern entries.

**All Phase A tasks can run in parallel.**

### Phase B — Implementation (Against Tests)

Each Phase B task specifies:
1. **"Agent input:"** — task description from design doc, specific Phase A test file, Phase 0 contracts, FR numbers
2. **"Must NOT receive:"** — test files for OTHER tasks
3. **"Files:" → Modify:** — exact source file path
4. **Implementation steps** — bite-sized, FR-tagged
5. **Pytest command** with expected ALL PASS
6. **Completion report** — return:
   - Task ID
   - Files modified (exact paths)
   - Pytest command run + PASS confirmation
   - Commit hash

Phase B follows the dependency graph from the design document.

### Phase C — Engineering Guide

Phase C runs after ALL Phase B tasks complete. It has two sub-phases:

**Phase C-parallel** (one agent per module, all parallel):

Each agent receives ONLY:
1. Its module's source file(s) — exact paths listed per task
2. The companion spec (FR numbers for coverage mapping)

Must NOT receive: Any other module's source, any test files, the design doc's pattern entries.

Each agent writes: one module section document covering Purpose, How it works, Key decisions, Configuration, Error behavior, Test guide.

**Agent isolation contract — include verbatim in each Phase C-parallel task:**
> The module doc agent receives ONLY its assigned source file(s) and the spec.
> Must NOT receive: other modules' source, any test files, the design doc.

**Phase C-cross** (single agent, after all C-parallel complete):

Receives ONLY:
1. All Phase C-parallel module section documents
2. The companion spec

Must NOT receive: any source files directly.

Writes: System Overview, Architecture Decisions, Data Flow (2-3 scenarios), Integration Contracts, Testing Guide (testability map, critical scenarios), Operational Notes, Known Limitations, Extension Guide.

Assembles final engineering guide at `docs/<subsystem>/<SUBSYSTEM>_ENGINEERING_GUIDE.md`.

**Invoke:** `write-engineering-guide` skill for both sub-phases.

### Phase D — White-Box Tests (Isolated from Source)

Phase D runs after Phase C-cross completes. All Phase D tasks run in parallel.

**Agent isolation contract — include verbatim at top of Phase D:**
> The Phase D test agent receives ONLY:
> 1. The module section from the engineering guide (Purpose, Error behavior, Test guide sub-sections)
> 2. The Phase 0 contract files (TypedDicts, signatures, exceptions)
> 3. FR numbers from the spec
>
> Must NOT receive: Any source files, any Phase A test files.

Each Phase D task specifies:
1. **"Agent input (ONLY these):"** — exact module section path, exact contract file paths, FR numbers
2. **"Must NOT receive:"** — explicit list of forbidden source files
3. **"Files:" → Create:** — exact test file path (e.g., `tests/path/test_module_coverage.py`)
4. **Test cases** — bulleted list derived from the guide's Error behavior and Test guide sub-sections
5. **Pytest command** with expected FAIL outcome (tests are new — implementation already exists)

**Invoke:** `write-module-tests` skill per task.

All Phase D tasks can run in parallel.

### Phase E — Full Suite Verification

After ALL Phase D tasks complete:

- [ ] Run full suite:
  ```bash
  pytest tests/ -v
  ```
  Expected: ALL Phase A tests PASS + ALL Phase D tests PASS

- [ ] If any fail: diagnose which phase's tests are failing and fix in the relevant phase
- [ ] Commit:
  ```bash
  git add tests/
  git commit -m "test: add Phase D white-box coverage tests"
  ```

## Parallel Phase Review Model

Sequential tasks (single-agent execution) use a per-task review loop. Parallel phases use a different model: reviews run in parallel as agents complete, with a **phase gate** before the next phase starts.

### Phase Gate Rule

Before any phase can start, ALL agents from the previous phase must be:
1. Complete (returned a result)
2. Reviewed (spec compliance confirmed)
3. Approved (no open issues)

A single unapproved agent blocks the entire next phase. Fix the issue before proceeding.

### Per-Agent Review (runs as agents complete)

As each parallel agent finishes, dispatch its spec compliance reviewer immediately — do not wait for other agents. Reviews run in parallel with remaining agents.

**Review weight by phase:**

| Phase | Review type | What to check |
|---|---|---|
| Phase A (spec tests) | Spec compliance only | All FR numbers covered? Each test tagged with FR? Tests expected to FAIL? |
| Phase B (implementation) | Full two-stage: spec compliance + code quality | Spec: all FRs implemented, nothing extra. Quality: clean code, TDD followed, tests pass. |
| Phase C-parallel (module docs) | Spec compliance only | All 6 sub-sections present? Error behavior documented? Test guide has boundary conditions? |
| Phase D (white-box tests) | Spec compliance only | Tests derived from guide's Error behavior + Test guide sub-sections? Known gaps noted? Tests FAIL? |

### Review Loop Per Agent

For each parallel agent:
1. Agent completes → dispatch spec reviewer immediately
2. If ❌ Issues: re-dispatch the same agent to fix, then re-review
3. If ✅ Approved (spec): for Phase B only, dispatch code quality reviewer
4. If ✅ Approved (quality): mark agent done
5. Record agent as approved in the phase gate tracker

### Phase Gate Tracker

Maintain a simple checklist after dispatching each parallel phase:

```markdown
Phase A gate — all must be ✅ before Phase B starts:
- [ ] Task A-1: spec review ✅
- [ ] Task A-2: spec review ✅
- [ ] Task A-3: spec review ✅
```

Do not advance to the next phase until all boxes are checked.

## Plan Document Format

### Header

```markdown
# [Feature Name] — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development.
> This plan has six phases: Phase 0 (contracts), Phase A (spec tests), Phase B (implementation),
> Phase C (engineering guide), Phase D (white-box tests), Phase E (full suite).
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence]

**Architecture:** [2-3 sentences]

**Tech Stack:** [Key technologies]

---
```

### File Structure Section

> **Read [`templates/plan-template.md`](templates/plan-template.md)** for the complete template.

Map all files organized by phase:

```markdown
## File Structure

### Contracts (Phase 0)
[files with CREATE/MODIFY annotations]

### Source (Phase B — stubs become implementations)
[source files]

### Tests (Phase A)
[test files with CREATE annotations]
```

### Dependency Graph

ASCII graph showing Phase 0 → review gate → Phase A (parallel) → Phase B (critical path + parallel).

### Task-to-Requirement Mapping Table

| Task | Phase 0 contracts | Phase A test file | Phase B source file | Phase C module doc | Phase D test file | FR numbers |

## Deriving Phase 0 from the Design Document

The design document's Part B contains two types of entries:
- **Contract entries** (TypedDicts, dataclasses, stubs) → copy verbatim into Phase 0
- **Pattern entries** (illustrative code) → do NOT copy; these inform Phase B but must not leak to Phase A

If the design doc lacks contract entries, derive them from task descriptions and spec requirements.

## Review Loop

After writing, dispatch a reviewer:

> **Read [`references/reviewer-prompt.md`](references/reviewer-prompt.md)** for the dispatch template.

The reviewer checks:
- Every spec requirement in at least one Phase A test task
- Every Phase A task has "Must NOT receive" clause
- Every Phase B task references its Phase A test file
- Phase 0 contracts match the design doc's contract entries
- Dependency graph matches the design doc

Max 3 iterations before surfacing to human.

## Execution Handoff

**"Plan complete. Six execution phases:**

**Phase 0:** Implement contracts in this session (human review before proceeding).

**Phase A:** Dispatch one test agent per task in parallel. Each receives ONLY spec + Phase 0 contracts.

**Phase B:** Dispatch implementation agents following the dependency graph. Each receives ONLY task + Phase A test file + contracts.

**Phase C-parallel:** Dispatch one module doc agent per module in parallel. Each receives ONLY its module source + spec.

**Phase C-cross:** Dispatch one cross-cutter agent after all C-parallel complete. Receives ONLY module docs + spec.

**Phase D:** Dispatch one white-box test agent per module in parallel. Each receives ONLY its module section from the guide + Phase 0 contracts.

**Phase E:** Run full suite in this session. All Phase A + Phase D tests must pass.

**Ready to start with Phase 0?"**

## Common Mistakes

| Mistake | Consequence | Fix |
|---------|------------|-----|
| Phase A agent receives pattern entries | Tests mirror reference implementation | Only pass FR numbers + contract entries |
| Phase 0 stubs have implementation hints | Implementation agent biased | Stubs: signature + docstring + NotImplementedError only |
| Phase A test cases lack FR tags | Can't verify spec coverage | Every bullet references an FR number |
| Phase B task receives other tasks' tests | Shaped by unrelated expectations | Each agent gets ONLY its own test file |
| Phase 0 skips review gate | Bad contracts propagate | Always announce review gate |
| Pure utilities left as stubs | Block both phases | Copy fully implemented from design doc |
