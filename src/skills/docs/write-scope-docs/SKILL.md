---
name: write-scope-docs
description: "Writes or updates the scope document for a system — what to build, what to defer, and how to phase delivery. Use when defining project scope, breaking work into phases, deciding what's in/out, or when scope decisions emerge during planning conversations."
domain: docs.scope
intent: write
tags: [scope, phases, planning, decisions]
user-invocable: true
argument-hint: "[system/subsystem name] [optional: output path]"
---

# Scope Document Skill

A scope document is external memory for planning conversations. It captures what to build, what to defer, and how to phase delivery — then gates the transition from "still deciding" to "ready to build." Without this skill, the agent writes scope-like content but loses state across turns, never tracks open questions, and cannot judge when planning is complete.

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

## Wrong-Tool Detection

- **Tech stack or component decisions** (databases, frameworks, service boundaries) --> redirect to `/write-architecture-docs`
- **Formal requirements with FR/NFR IDs and acceptance criteria** --> redirect to `/write-spec-docs`
- **User wants to implement or write code** --> scope should be finalized first. Say: "Finalize scope before implementation. Run `/write-scope-docs` checkpoint to verify readiness."
- **User wants a quick summary of an existing scope doc** --> not this skill; read the doc and summarize directly

## Progress Tracking

At the start, create a task list:

```
TaskCreate: "Phase 1: Determine mode and gather inputs"
TaskCreate: "Phase 2: Write or update scope document"
TaskCreate: "Phase 3: Checkpoint readiness and hand off"
```

Mark each task `in_progress` when starting, `completed` when done.

## Three Modes

Determine which mode applies before doing anything else:

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Create** | No scope doc exists at the target path | Gather inputs, write from template |
| **Update** | Scope doc exists, user provides new information | Surgical edits to affected sections only. Never rewrite unchanged sections. |
| **Checkpoint** | User asks "are we ready?" or all questions appear resolved | Verify readiness, present summary, mark Ready on confirmation |

**Mode detection rules:**
1. Check if `{SUBSYSTEM}_SCOPE.md` exists at the expected path. If not --> Create.
2. If it exists and the user provides a new decision, answered question, or scope change --> Update.
3. If it exists and the user asks about readiness, or you judge sufficient context has accumulated --> Checkpoint.

## Conversational Capture

This skill fires on explicit invocation AND during planning conversations. When you recognize scope-relevant decisions emerging in conversation (phase boundaries, in/out scope calls, deferral decisions), capture them into the scope document without waiting for the user to invoke the skill. Announce what you captured: "Captured scope decision: [summary]. Updated [section] in {SUBSYSTEM}_SCOPE.md."

## Create Mode

### Input Gathering

Before writing, gather these inputs. Ask for missing essentials; infer the rest from context.

**Essential -- always clarify if not provided:**
1. **System/subsystem name** -- what is being scoped
2. **Problem statement** -- what problem this solves and why existing approaches fail
3. **Goals** -- measurable outcomes (not features)

**Important -- ask when relevant:**
4. **Known scope boundaries** -- what is explicitly in or out
5. **Phase structure** -- is this single-phase or multi-phase? What does Phase 1 deliver?
6. **Key decisions already made** -- technology, approach, or constraint choices

**Conditional -- ask only when clearly needed:**
7. **Cross-phase dependencies** -- capabilities that span phases
8. **Stakeholders** -- who approves scope decisions
9. **Companion documents** -- existing architecture docs, specs, or prior scope docs to reference

### Writing

> **Read [`templates/scope-template.md`](templates/scope-template.md)** for the output structure.

Write the scope document following the template. Key rules:

- **Output naming:** `{SUBSYSTEM}_SCOPE.md` -- always uppercase subsystem, always `_SCOPE.md` suffix
- **Output location:** `docs/{subsystem}/` unless the user specifies a different path
- **Status:** Set to "Draft" on creation
- **Open Questions:** Add any unresolved items as `- [ ] Question? (raised YYYY-MM-DD)` entries. Every ambiguity you notice during writing becomes an open question -- do not silently assume answers.
- **Problem Statement is the WHY** -- 1-3 paragraphs. If you cannot articulate why this system matters, stop and ask. A scope doc without a clear problem statement produces downstream artifacts that solve the wrong problem.
- **Goals are outcomes, not features** -- "Reduce manual reconciliation from 4 hours to 15 minutes" not "Build an automated reconciliation system"
- **Scope Boundary is a three-way split:** In Scope (building this), Out of Scope (not building this, ever in this project), Deferred (not building now, but planned for a later phase). Each item gets a one-line description. If the user hasn't explicitly deferred anything, ask -- deferral decisions are the highest-value scope work.
- **Phase Plan uses a table** -- not narrative. Each row: Phase number, Name, Objective, Target Capabilities, Dependencies.
- **Key Decisions use a table** -- Decision, Chosen option, Rationale, Alternatives Considered. Record decisions even when they seem obvious -- "obvious" decisions are the ones most likely to be revisited later without a record.

## Update Mode

When the user provides new information that affects scope:

1. **Identify affected sections** -- which template sections does this information change?
2. **Apply surgical edits** -- modify only those sections. Do not rewrite the entire document.
3. **Track the change:**
   - If a decision was made --> add a row to Key Decisions
   - If a question was answered --> absorb the answer into the relevant section, mark the Open Questions entry as `[x]` with the answer and date: `- [x] Question? Answer. (resolved YYYY-MM-DD)`
   - If scope changed --> update Scope Boundary (In Scope, Out of Scope, or Deferred) and adjust Phase Plan if phases are affected
4. **Update status** -- if the document was "Ready" and scope changed, reset to "Draft"
5. **Announce the update:** "Updated {SUBSYSTEM}_SCOPE.md: [one-line summary of what changed]."

### Open Questions Lifecycle

Open Questions are the primary state-tracking mechanism during active planning:

- **Adding:** When ambiguity emerges, add: `- [ ] Question? (raised YYYY-MM-DD)`
- **Answering:** Absorb the answer into the relevant section (Goals, Scope Boundary, Phase Plan, etc.), then mark: `- [x] Question? Answer. (resolved YYYY-MM-DD)`
- **At checkpoint:** Resolved questions are removed entirely. Unresolved questions must be either deferred (moved to Deferred scope with a rationale) or declared blocking.
- **At finalization:** The Open Questions section is removed from the document. A "Ready" scope doc has no open questions.

## Checkpoint Mode

When judging readiness (or when the user asks "are we ready?"):

1. **Count open questions.** Zero unresolved = ready candidate. Any unresolved = list them and ask:
   - "These questions are still open: [list]. Can any be deferred? Which are blocking?"
2. **Present a summary:**
   - Scope boundary (in/out/deferred counts with key items)
   - Phase plan (phase count, Phase 1 objective)
   - Key decisions (count, most impactful)
3. **If confirmed ready:**
   - Set Status to "Ready"
   - Remove the Open Questions section entirely
   - Update the Readiness Checkpoint section with date and summary
   - Hand off: "Scope finalized. Invoke `/write-spec-docs` to formalize requirements or `/write-architecture-docs` for technical architecture."
4. **If not ready:** Identify what is missing and return to Update mode.

## Phased Delivery

The scope document is cumulative -- one living file, no phase suffixes. This is where phases are DEFINED, not where they are separated into files.

When a new phase begins:
1. Move relevant items from Deferred to In Scope
2. Add a new row to the Phase Plan table
3. Update Cross-Phase Dependencies if the new phase introduces or resolves dependencies
4. Reset Status to "Draft"
5. Announce: "Phase [N] scope opened. Moved [items] from Deferred to In Scope."

## README Dashboard

After any Create or Update, sync the subsystem README at `docs/{subsystem}/README.md`:

1. **Scope row:** Ensure the dashboard table has a row: `| Scope | [Current]({SUBSYSTEM}_SCOPE.md) | {status} |`
2. **Phase Map:** Sync the README's Phase Map table with the scope document's Phase Plan table. The scope document is the source of truth for phase definitions.

If the README does not exist, create it with the scope row as the first entry.

## Downstream Contracts

When this scope document is finalized, downstream skills depend on it:

- **write-spec-docs** reads: Goals, Scope Boundary (In Scope items become requirements candidates), Phase Plan (which phase is being specified)
- **write-architecture-docs** reads: Goals, Scope Boundary, Phase Plan, Key Decisions (technology choices inform architecture)

Ensure these sections are unambiguous enough for a downstream skill to consume without asking clarifying questions.
