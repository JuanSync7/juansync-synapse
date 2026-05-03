---
name: write-architecture-docs
description: "Writes or updates the architecture document for a system — system-level technical decisions, component boundaries, tech stack, and data flow patterns. Use when making technology choices, defining component structure, deciding integration approaches, or when architecture decisions emerge during planning conversations."
domain: docs.arch
intent: write
tags: [architecture, tech-stack, components, decisions]
user-invocable: true
argument-hint: "[system/subsystem name] [optional: output path]"
---

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

# Write Architecture Docs

An architecture document is the external memory for technology decisions — it captures what was decided, why, and what the components look like before anyone writes a formal spec. It sits between scope ("what are we building") and spec ("what must the system do"), translating scope commitments into concrete technology choices and component structures. Without it, technology decisions scatter across chat threads and get re-litigated in every downstream document.

This is a **living document** — one cumulative file per subsystem, updated as decisions emerge. It is not a one-shot artifact.

## Wrong-Tool Detection

- **What to build/not build, phase planning** --> redirect to `/write-scope-docs`
- **Formal requirements with acceptance criteria** --> redirect to `/write-spec-docs`
- **Task decomposition and code contracts** --> redirect to `/write-design-docs`
- **Post-implementation documentation** --> redirect to `/write-engineering-guide`

## Progress Tracking

At the start, create a task list for each phase:

```
TaskCreate: "Phase 1: Determine mode and gather inputs"
TaskCreate: "Phase 2: Write or update architecture document"
TaskCreate: "Phase 3: Update README dashboard"
TaskCreate: "Phase 4: Checkpoint readiness (if requested)"
```

Mark each task `in_progress` when starting, `completed` when done.

## Layer Context

```
Layer 0:   Scope Document         <-- write-scope-docs (input to this skill)
Layer 0.5: Architecture Document  <-- YOU ARE HERE
Layer 3:   Authoritative Spec     <-- write-spec-docs (consumes this)
Layer 4:   Design Document        <-- write-design-docs (consumes this)
```

**Announce at start:** "I'm using write-architecture-docs to [create/update/checkpoint] the architecture document."

## Three Modes

Determine the mode before doing anything else:

1. **Create** — No architecture doc exists at the expected path. Gather inputs, write from template.
2. **Update** — Architecture doc exists. Apply surgical changes: add a technology decision row, add a component, answer an open question. Never rewrite unchanged sections.
3. **Checkpoint** — Verify all open questions are resolved or explicitly deferred. Present a summary. Mark "Ready" on user confirmation. Hand off to the pipeline.

**Mode detection:** Check for `{SUBSYSTEM}_ARCHITECTURE.md` in the expected output directory. If it exists, default to Update mode. If the user says "are we ready?" or "checkpoint", switch to Checkpoint mode regardless.

## Preconditions

Before writing or updating:

1. **Check for a scope doc.** Look for `{SUBSYSTEM}_SCOPE*.md` in the same docs directory. If one exists, read it — scope commitments constrain architecture decisions. If none exists, proceed but note the absence: "No scope document found. Architecture decisions may need revision if scope is defined later."
2. **If Update mode:** Read the existing architecture doc completely before making changes. Never overwrite sections you are not updating.

## Create Mode

When no architecture doc exists:

1. **Gather inputs.** The user may provide context through conversation, existing code, or documents. Extract:
   - System purpose and boundaries
   - Known technology choices (and their rationale)
   - Component structure (even if informal)
   - Integration requirements
   - Known constraints

2. **Write from template.** Use [`templates/architecture.md`](templates/architecture.md) as the output skeleton. Fill every section with available information. For sections where information is incomplete, add entries to Open Questions rather than guessing.

3. **Set Status to Draft.** A new document is never Ready — it needs at least one checkpoint pass.

**Output naming:** `{SUBSYSTEM}_ARCHITECTURE.md` — no phase suffix. This is a cumulative document.

If the user provides `$ARGUMENTS`, treat the first argument as the subsystem name and the second (if provided) as the output file path.

## Update Mode

When the architecture doc already exists:

1. **Identify what changed.** The user is adding a technology decision, a new component, answering an open question, or adjusting a data flow pattern. Determine the minimum set of sections affected.

2. **Apply surgical edits.** Update only the affected sections. Do not rewrite sections that have not changed — this avoids losing reviewed content and makes diffs reviewable.

3. **When answering an open question:** Absorb the answer into the relevant section (usually Technology Decisions or Component Boundaries), then mark the question `[x]` in the Open Questions section.

4. **When a new question emerges:** Add it to Open Questions with today's date: `- [ ] {Question}? (raised {YYYY-MM-DD})`

5. **When an architecture decision changes scope:** Flag it explicitly: "This technology decision affects scope — {explain the impact}." If a scope doc exists, update it too or instruct the user to do so.

## Checkpoint Mode

When the user asks "are we ready?" or explicitly requests a checkpoint:

1. **Count open questions.** Parse the Open Questions section.
   - **Zero open questions** --> proceed to step 2.
   - **Open questions remain** --> list each one. Ask the user: "These questions are unresolved. Should any be deferred? Deferred questions are noted but do not block readiness."

2. **Present a summary.** Show:
   - Component count and names from Section 2
   - Technology decision count from Section 3
   - Data flow pattern count from Section 4
   - Integration point count from Section 5
   - Any deferred questions

3. **If user confirms:**
   - Set Status to "Ready" in the header table
   - Remove the Open Questions section entirely (deferred questions move to a "Deferred Questions" note in the Readiness Checkpoint section)
   - Update the Readiness Checkpoint section with final counts
   - Hand off: "Architecture finalized. Invoke `/write-spec-docs` to begin formal requirements, or `/write-design-docs` if you already have a spec."

4. **If user does not confirm:** Stay in Draft. Keep Open Questions section. Ask what needs to change.

## Dual Trigger

This skill fires on both explicit invocation AND conversational capture:

- **Explicit:** "Document the architecture", "write architecture docs", "what's our tech stack for this"
- **Conversational:** When the LLM recognizes that a planning conversation has produced architecture decisions (technology choices, component boundaries, integration approaches). In this case, offer to capture the decisions: "These look like architecture decisions. Want me to create/update the architecture doc?"

When firing conversationally, always ask before writing. Never silently create an architecture document from conversation context.

## Scope Integration

The architecture doc and scope doc are siblings that reference each other:

- **Scope drives architecture:** "We're building auth in P1" (scope) --> "Auth uses JWT with Redis session store" (architecture). Read scope commitments before making technology decisions.
- **Architecture can change scope:** If a technology choice makes a scope commitment infeasible (e.g., "this database can't support the offline mode promised in scope"), flag it immediately. Do not silently proceed with an incompatible architecture.
- **Both can update in one turn:** If you update the architecture doc and the change affects scope, update the scope doc in the same operation (or instruct the user to do so).

## Phased Delivery

This is a cumulative document — one living file per subsystem, not one per phase. When new phases introduce new components or technology decisions:

- Add new rows to existing tables (Component Boundaries, Technology Decisions, Integration Points)
- Add new Data Flow Patterns sections as needed
- Note the phase that introduced each decision in the Technology Decisions table's Decided column (e.g., "2026-04-09 (P2)")

The architecture doc also owns the **Carry-Forward Contracts** table in the README — when interfaces are established at the architecture level (e.g., "the API contract between frontend and backend is REST with OpenAPI 3.0"), record them so downstream phases inherit the contract.

## README Dashboard

After any create or update, update `docs/{subsystem}/README.md`:

1. **Architecture row:** Always shows `[Current]({SUBSYSTEM}_ARCHITECTURE.md)` — no phase suffix since it is cumulative.
2. **Carry-Forward Contracts table:** When a new interface is established at the architecture level, add a row:

```markdown
| Interface | Established In | Contract | Status |
|-----------|---------------|----------|--------|
| {interface name} | {phase or date} | {link or description} | Active |
```

If the README does not exist yet, create it with at minimum the architecture row and the Carry-Forward Contracts table.

## Template

> **Read [`templates/architecture.md`](templates/architecture.md)** before generating output — it defines the exact section structure and table formats.

## Quality Standards

- **Technology Decisions must have rationale and alternatives.** A decision without rationale is an assertion. A decision without alternatives considered is unexamined.
- **Component Boundaries must be non-overlapping.** If two components share ownership of the same resource, the boundary is wrong — clarify or merge.
- **ASCII diagrams must show data flow direction.** A box diagram without arrows does not communicate architecture.
- **Open Questions must have dates.** Without a raised date, questions accumulate without urgency signals.
- **Every section must have content or an explicit "None identified" marker.** Empty sections are ambiguous — the reader cannot tell if nothing applies or if the author forgot.

## Downstream Handoff

After the architecture doc is marked Ready:

- **`write-spec-docs`** reads the architecture for technology decisions and component boundaries when writing formal requirements
- **`write-design-docs`** reads the architecture for component structure when decomposing tasks into implementation units

State the handoff explicitly when transitioning to Ready status.
