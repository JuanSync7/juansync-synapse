---
name: write-engineering-guide
description: "POST-IMPLEMENTATION ONLY. Use when source code already exists and you need to document what was built, why decisions were made, and how components work. A non-skippable existence check refuses to run if the source files don't exist or are stubs. Triggered by 'write an engineering guide', 'document the implementation', 'post-implementation doc', 'engineering guide'."
domain: docs.post-build
intent: write
tags: [engineering guide, maintenance, post-implementation]
user-invocable: true
argument-hint: "[system/subsystem name] [optional: source directory path] [optional: output path]"
---

## Progress Tracking

At the start, create a task list:

```
TaskCreate: "Phase C-parallel: dispatch module doc agents"
TaskCreate: "Phase C-cross: synthesize into final guide"
TaskCreate: "Review and finalize engineering guide"
```

Mark each `in_progress` when starting, `completed` when done. When dispatching module doc agents, set `model:` explicitly (e.g., `model: haiku` for single-module docs, `model: sonnet` for cross-module synthesis).

---

## Layer Context

This skill produces a **Layer 5 — Engineering Guide** in the documentation hierarchy:

```
Layer 1: Platform Spec           (manual)
Layer 2: Spec Summary            ← write-spec-summary
Layer 3: Authoritative Spec      ← write-spec-docs
Layer 4: Implementation Plan     ← write-impl / build-plan
Layer 5: Engineering Guide       ← YOU ARE HERE (post-implementation)
```

**Critical distinction from Layer 4:**
- Layer 4 is a **pre-implementation plan** — tasks to build, reference stubs, technology-agnostic, no real filenames.
- Layer 5 is a **post-implementation reference** — what was actually built, real file paths, actual code, actual decisions made.

**Before writing, you MUST:**
- Read the actual source files for the system (not the spec or plan — the code itself)
- Read the companion spec (Layer 3) for context on requirements and intent
- Read the companion design document if one exists

**Companion spec is strongly recommended but not blocking.** If no formal spec exists, document the system based on what the code does and what the design document (if any) intended. Note the absence of a spec in the document header.

## Wrong-Tool Detection

- **User wants a spec** → redirect to `/write-spec-docs`
- **User wants test planning** → redirect to `/write-test-docs`
- **User wants pre-implementation docs** → redirect to `/write-implementation-docs`
- **This skill is for POST-implementation documentation only.**

---

## Implementation Existence Check (NON-SKIPPABLE)

> **NON-SKIPPABLE GATE:** Before any other action — before reading the spec, before the Planning Stage, before creating tasks — verify that an implementation actually exists. Writing an engineering guide for code that has not been written produces speculative fiction, not reference documentation. This gate exists because that failure mode has occurred in production.
>
> **Exemption rule:** Skip this gate ONLY when invoked in Phase C of `build-plan` with an upstream Phase B (implement-code) marked complete in the same session. In every other case — standalone invocation, orchestrator dispatch, subagent invocation — run the gate.

### Step 1: Identify source files

From the subsystem name / source directory argument, enumerate the candidate source files (not tests, not docs, not `__init__.py` re-exports). Build a list of at least **3 concrete file paths** (e.g., `src/foo/bar.py`, `src/foo/baz.py`, `src/foo/qux.py`) — not directory names.

If the subsystem is small and fewer than 3 source files exist, the system may be too trivial to warrant an engineering guide — redirect the user to `/write-design-docs` or ask whether a brief section in an existing guide would suffice.

### Step 2: Verify each file exists and is implemented

For each candidate path:

1. Read the file. If `Read` fails, the file does not exist.
2. Measure the line count of non-trivial content. A file qualifies as "implemented" only if:
   - It exists
   - It contains **more than 20 lines** of real code (not counting blank lines, comments, `@summary` blocks, or single-statement stubs like `pass` / `raise NotImplementedError`)
   - It is not a pure re-export facade (`__init__.py` that only imports from submodules does not count)

### Step 3: Hard-fail on gap

If fewer than 3 files pass the verification, emit exactly the following message and halt:

```
PRE-IMPL DOCUMENTATION BLOCKED

The write-engineering-guide skill is post-implementation only. The following paths do not resolve to implemented source files:

<list each failed path and the reason: "does not exist", "stub only (N lines)", "re-export facade", etc.>

Options:
- If the code has not been written yet, write it first. The engineering guide derives from the actual implementation — not from specs or design docs.
- If you need pre-implementation design rationale, invoke /write-design-docs instead.
- If the implementation exists but at different paths, re-invoke this skill with the correct paths as explicit arguments.
```

Do NOT proceed to the Planning Stage. Do NOT dispatch module agents. Do NOT write any section.

### Step 4: Record the verified paths

Once 3+ files pass, record the verified path list in session. Pass this list (and nothing else as source truth) to the Planning Stage's `section_context_map` — every `source_content` field must be populated from these verified files, never from specs, design docs, or implementation planning docs.

**Why this matters:** The engineering guide's value is that it describes *what exists*. A guide derived from a spec describes *what was intended*. They are different documents with different audiences. Conflating them produces documentation that is plausible but wrong — precisely the failure mode this gate prevents.

---

## Dispatch Modes

This skill operates in two modes depending on context:

### Standalone mode (default)

When invoked directly by the user (not from `build-plan`), use the Planning Stage + wave execution model below. This mirrors Phase C of `build-plan` — the same context isolation applies regardless of invocation source.

#### Planning Stage (NON-SKIPPABLE)

Before writing any section, read all source files and produce a `section_context_map`. Do this before writing a single module section.

> **NON-SKIPPABLE:** Do not write any module section until the Planning Stage is complete and the `section_context_map` exists in session. The map is the isolation guarantee — without it, agents receive unscoped context and context drift will degrade late-document sections.

**`section_context_map` schema:**

```
id:             string    # unique identifier, e.g. "module_retrieval", "cross_cut"
title:          string    # section heading
wave:           int       # 1 = module sections (parallel), 2 = cross-cutter (single)
depends_on:     [id, ...] # section IDs that must be approved before this starts
model_tier:     haiku | sonnet | opus
source_content: string    # source text for THIS section only — NOT a file path.
                          # module sections: the module's source file content + spec FR numbers.
                          # cross-cutter: filled at runtime from Wave 1 outputs + spec.
                          # Agents never read files.
prior_slots:    [id, ...] # Wave 1 module section IDs (for the Wave 2 cross-cutter only)
prompt:         string    # complete, self-contained prompt for the section agent
```

**write-engineering-guide section dependency graph:**

```
Wave 1 (parallel — one entry per module):
  module_<name> → One Module Reference section per source module
                  (5 sub-sections: Purpose, How it works, Key decisions,
                  Configuration, Error behavior — Test guide is in write-test-docs)
                  source: that module's source file content + spec FR numbers ONLY
                  MUST NOT include: other modules' source, test files, design doc patterns
                  model_tier: sonnet
                  depends_on: []

Wave 2 (single cross-cutter agent — after all Wave 1 complete):
  cross_cut     → System Overview, Architecture Decisions, End-to-End Data Flow,
                  Configuration Reference, Integration Contracts,
                  Operational Notes, Known Limitations, Extension Guide,
                  Requirement Coverage appendix
                  source: all Wave 1 module section outputs + companion spec ONLY
                  MUST NOT include: source files directly
                  model_tier: sonnet
                  depends_on: [all module_<name> IDs]
```

**How to produce the map:**

1. List the source directory to identify all modules.
2. For each module, read its source file and copy the content into the module entry's `source_content` field. Note which spec FR numbers it addresses.
3. Write the module agent's `prompt`: include the module's source content, the relevant spec FR numbers, and the 6-sub-section format requirements from this skill.
4. Record all `module_<name>` IDs — these become the cross-cutter's `prior_slots`.

→ **Proceed to Execution Stage once all map entries exist.**

**Execution Stage:**

Execute the `section_context_map` using **parallel-agents-dispatch**:

1. **Wave 1** — dispatch one agent per module in parallel. Each receives ONLY its `prompt` (module source already inlined). Apply the agent isolation contract from the Parallel mode section below.
2. **Review** each module section: verify all 6 sub-sections present, no cross-section references (`"see Section X"` is forbidden).
3. **Wave 2** — dispatch the cross-cutter agent with all Wave 1 outputs + spec inlined. Apply the Phase C-cross isolation contract from the Parallel mode section below.
4. **Assemble** — the cross-cutter agent assembles the final guide at the standard output path.

### Parallel mode (Phase C of build-plan)
Used when invoked from `build-plan`'s Phase C. Two sub-phases:

**Phase C-parallel — module agents (all parallel):**

Each agent receives ONLY:
1. Its assigned source file(s)
2. The companion spec (FR numbers for coverage mapping)

Must NOT receive: other modules' source, test files, design doc pattern entries.

Each agent writes one module section document (5 sub-sections: Purpose, How it works, Key decisions, Configuration, Error behavior — Test guide is in write-test-docs) and saves it to `docs/tmp/module-<name>.md`. Returns the file path on completion.

**Agent isolation contract — include verbatim in each Phase C-parallel task:**
> The module doc agent receives ONLY its assigned source file(s) and the spec FR numbers.
> Must NOT receive: other modules' source files, any test files, the design doc.

**Phase C-cross — cross-cutter agent (single, sequential after all C-parallel complete):**

Receives ONLY:
1. All Phase C-parallel module section documents (paths listed explicitly)
2. The companion spec

Must NOT receive: source files directly.

Writes: System Overview, Architecture Decisions, Data Flow (2-3 scenarios), Integration Contracts, Testing Guide (testability map + critical scenarios), Operational Notes, Known Limitations, Extension Guide.

Assembles the final engineering guide at `docs/<subsystem>/<SUBSYSTEM>_ENGINEERING_GUIDE.md` by combining the module section docs with the cross-cutting sections.

---

# Engineering Guide Skill

You are writing a post-implementation engineering guide for a system that has already been built. This document serves three audiences:

1. **Maintainers and upgraders** — Engineers who need to understand, debug, or extend the system
2. **Onboarding developers** — New team members reading this code for the first time

> **Test planning documentation** (testability maps, mock boundaries, critical scenarios) belongs in `write-test-docs`, which reads this guide as its primary input.

## Output Path Convention

Default output path: `docs/<subsystem>/<SUBSYSTEM>_ENGINEERING_GUIDE.md`

Examples:
- Retrieval pipeline → `docs/retrieval/RETRIEVAL_ENGINEERING_GUIDE.md`
- Ingestion pipeline → `docs/ingestion/INGESTION_PIPELINE_ENGINEERING_GUIDE.md`

If the user provides `$ARGUMENTS`, treat the first argument as the system/subsystem name, the second as the source directory to explore, and the third as the output file path (overrides the default).

## Input Gathering

> **Prerequisite:** The Implementation Existence Check (non-skippable gate above) must have passed. The verified source file list from Step 4 of that gate is the input to this stage. If you reached this section without running the gate, stop and go back — the gate is not optional.

Before writing anything, you MUST have:

1. **The source code** — Read all source files in the system. Do not write the guide without reading the actual implementation. Start with `README.md` files, then `@summary` blocks at file tops, then full files.
2. **The companion spec** (Layer 3) — Provides requirements context and intent. If no spec exists, note this in the document header and proceed based on the code and any design documents.
3. **The design document** (if it exists) — Provides architectural intent.
4. **Subsystem name and output path** — From `$ARGUMENTS` or from asking the user.

**Reading strategy — do this before writing a single line of the guide:**
1. List the source directory contents to understand the module landscape.
2. Read each file's `@summary` block (top of file) before reading the full source.
3. Read full source files for major components. Focus on: public interfaces, key algorithms, decision points, configuration parameters, error conditions.
4. Note design decisions as you read — anything that looks non-obvious is a decision worth documenting.
5. If a companion spec exists, note which spec requirements each module addresses — you will need this for the coverage verification.

---

## Document Structure

Follow the structure in [template.md](template.md). The 10 sections are:

1. **System Overview** — Purpose, architecture diagram, design goals, technology choices
2. **Architecture Decisions** — Cross-cutting decisions using ADR format
3. **Module Reference** — One self-contained section per module (the core of the document)
4. **End-to-End Data Flow** — Walk through 2–3 concrete scenarios with state shapes
5. **Configuration Reference** — Complete parameter table
6. **Integration Contracts** — System boundary only: what callers provide, what they receive, external dependency assumptions
7. **Operational Notes** — Running, monitoring signals, failure modes with debug paths
8. **Known Limitations** — Explicit scope bounds and edge cases
9. **Extension Guide** — How to add new components safely

> **Test planning documentation** (testability maps, mock boundary catalogs, critical test scenarios) is NOT part of this guide. Invoke `write-test-docs` after this document is complete — it reads this guide as its primary input.

### Scaling to System Size

Not every system needs 10 fully expanded sections. Scale the document to the system's complexity:

| System Size | Guidance |
|-------------|----------|
| **Small** (1–5 source files) | Sections 2, 5, 8, 9 may be brief or combined. Section 10 may be a single paragraph. Module Reference is still required for each file. |
| **Medium** (6–20 source files) | All 10 sections at full depth. This is the default. |
| **Large** (20+ source files) | Consider splitting into sub-guides per subsystem (e.g., one for guardrails, one for memory). Each sub-guide follows the same template. A root guide ties them together with a directory-level overview. |

---

## The Core Requirement: Self-Contained Module Sections

**Every Module Reference section (Section 3) MUST be self-contained.** A reader should be able to read one module section and fully understand that component — without reading any other section of the document.

This means each module section MUST contain all five sub-sections:

| Sub-section | What it must cover |
|-------------|-------------------|
| **Purpose** | What this module does and why it exists in the system. One paragraph. Plain language. |
| **How it works** | Step-by-step walkthrough of the algorithm or logic. Walk through what happens from input to output. Reference actual function/class names. Include short code snippets for non-obvious logic. A beginner should be able to follow. Appropriate depth: trace the public interface and key internal logic, but do not line-by-line walk through trivial helpers. |
| **Key design decisions** | WHY specific choices were made. Include alternatives that were considered. Use the decisions table format. This is the most valuable sub-section — it prevents future engineers from re-litigating closed decisions. |
| **Configuration** | Every parameter that changes this module's behavior. Type, default, effect. |
| **Error behavior** | What exceptions this module raises, when, and what callers should expect. Which errors are retried internally vs. surfaced to callers. |

> **Test guide sub-section is NOT part of the engineering guide.** Test planning belongs in `write-test-docs`, which reads the Error behavior sub-section to derive test cases.

**Section isolation rule:** Module sections may NOT say "see Section X for details." If context from elsewhere is needed to understand this module, repeat it. Each section is standalone.

**Writing standard:** Write for a developer who has never seen this code before. Precise, concrete, no jargon without definition. If an algorithm has a name (e.g., "sliding window", "exponential backoff"), explain what it means in context.

### What Counts as a Module Section

Not every file warrants a full 6-sub-section treatment. Use this heuristic:

| File type | Treatment |
|-----------|-----------|
| **Core logic files** — contain algorithms, business rules, state transforms, pipeline stages | Full 5-sub-section module section |
| **Type/schema files** — define TypedDicts, dataclasses, enums, constants | Brief section: Purpose + the type definitions themselves (code block) + key design decisions if non-obvious. Skip How it works, Error behavior, Test guide. |
| **Thin wrappers / re-exports** — `__init__.py` facades, import-only files | Mention in System Overview or parent module section. No standalone section. |
| **Small related utilities** — 2–3 files that serve one purpose together | Group into a single module section. Name it after the shared concern, list all files. |

When in doubt: if the file has logic that a test team needs to understand, it gets a full section.

---

## Architecture Decision Boundary: Section 2 vs Section 3

Decisions belong in **Section 2 (Architecture Decisions)** when they:
- Span multiple modules (e.g., "use LangGraph for all pipeline orchestration")
- Set a system-wide pattern (e.g., "all state is TypedDict, not dataclass")
- Constrain the entire system (e.g., "all LLM calls go through a single retry wrapper")

Decisions belong in **Section 3 (Module Reference → Key design decisions)** when they:
- Are specific to one module's implementation (e.g., "use regex before LLM for keyword extraction")
- Don't affect any other module's behavior
- Are about internal algorithm choice, not system-level architecture

**Heuristic:** If changing the decision would require modifying multiple files, it belongs in Section 2. If only one file changes, it belongs in Section 3.

---

## Module Section Format

> **Read [`references/module-section-format.md`](references/module-section-format.md)** when writing or reviewing a Module Reference section (Section 3).

---

## Architecture Decision Format

> **Read [`references/architecture-decision-format.md`](references/architecture-decision-format.md)** when writing Architecture Decisions (Section 2).

---

## End-to-End Data Flow Section

> **Read [`references/data-flow-format.md`](references/data-flow-format.md)** when writing the End-to-End Data Flow section (Section 4).

---

## Integration Contracts Section (Section 6)

> **Read [`references/integration-contracts-format.md`](references/integration-contracts-format.md)** when writing Integration Contracts (Section 6).

---

## Configuration Reference (Section 5)

> **Read [`references/configuration-reference-format.md`](references/configuration-reference-format.md)** when writing the Configuration Reference (Section 5).

---

## Writing Standards

**Beginner accessibility without sacrificing precision:** Lead with plain-language explanations. Follow with precise technical details. Never sacrifice precision for simplicity — provide both.

**Tone:** Technical and direct. No marketing language ("powerful", "robust", "seamlessly"). Active voice. Concrete over abstract.

**Language-agnostic:** Use the project's language and type system for all code snippets, type annotations, and examples. Do not assume Python — adapt to whatever language the system is built in.

**Code snippets:**
- Pull from the actual source — do not invent examples
- Keep to 10–30 lines per snippet
- Annotate non-obvious lines with inline comments
- Use real function and class names from the module

**Section headers for modules:** Use the file's actual path in backticks:
`### \`src/retrieval/confidence/engine.py\` — Confidence Engine`

---

## Spec Requirement Coverage Verification

> **Read [`references/spec-coverage-verification.md`](references/spec-coverage-verification.md)** when verifying spec coverage after writing the guide (or during the review loop).

---

## Review Loop

After writing the complete guide, run a review cycle:

1. **Self-verify against the quality checklist** (below). Fix any failures before proceeding.
2. **Dispatch a reviewer subagent** using [reviewer-prompt.md](reviewer-prompt.md). Provide:
   - Path to the engineering guide document
   - Path to the companion spec (if any)
   - Path to the source directory
3. If the reviewer finds issues (**ISSUES FOUND**): fix them and re-dispatch the reviewer.
4. If the loop exceeds 3 iterations, surface unresolved issues to the user for guidance.
5. Once the reviewer approves (**APPROVED**): update the README dashboard, commit the document, and inform the user.

## README Dashboard

After writing or updating the engineering guide, update the subsystem's `README.md` dashboard. Read [`references/readme-update-contract.md`](references/readme-update-contract.md) for the update procedure.

---

## Updating an Existing Guide

When the code has changed and the guide needs updating:

1. **Read the current guide** and the changed source files.
2. **Identify stale sections:**
   - Module sections for files that changed — update How it works, Configuration, Error behavior, Test guide.
   - Module sections for files that were added — write new sections.
   - Module sections for files that were deleted — remove and note in a changelog or commit message.
   - Architecture Decisions — update if a cross-cutting decision changed.
   - Data Flow — update if the pipeline stages or routing changed.
   - Configuration Reference — update if parameters were added, removed, or changed defaults.
3. **Re-run the quality checklist** on modified sections.
4. **Update the "Last updated" date** in the document header.

Do NOT rewrite unchanged sections. Surgical updates preserve review history and reduce diff noise.

### Phased Delivery Updates

When updating for a new delivery phase (P2, P3...):

> **Read [`references/phased-delivery.md`](references/phased-delivery.md)** for the full cumulative update rules: what to add, what to update, what to leave alone, and phase provenance marking.

**Summary:**
- The engineering guide is cumulative — one file, no phase suffix (`_ENGINEERING_GUIDE.md`)
- Add new module sections for this phase's new modules
- Update existing module sections only if this phase changed them
- Add a Phase History row to Section 1
- Mark new modules with "Introduced in: P{N}" and updated modules with "Updated in P{N}"
- After updating, update the subsystem README dashboard — read [`references/readme-update-contract.md`](references/readme-update-contract.md)

---

## Quality Checklist

Before finalizing the document, verify:

- [ ] Every module with non-trivial logic has a section in Module Reference (Section 3)
- [ ] Every full module section contains all five sub-sections (Purpose, How it works, Key decisions, Configuration, Error behavior)
- [ ] No Test guide sub-section present — test planning belongs in write-test-docs
- [ ] No module section says "see Section X" — each is standalone
- [ ] Architecture Decisions covers all cross-cutting choices (technology, thresholds, patterns)
- [ ] Architecture Decisions are in Section 2; module-specific decisions are in Section 3
- [ ] Data Flow section has 2–3 concrete scenarios with actual state shapes at each stage
- [ ] Configuration Reference covers every configurable parameter in the system
- [ ] Integration Contracts (Section 6) covers only the system boundary, not internal module contracts
- [ ] Extension Guide gives step-by-step instructions with specific file paths and pitfalls
- [ ] No undefined jargon anywhere in the document
- [ ] Code snippets are from actual source, not invented
- [ ] Known Limitations are explicit statements, not vague hedges
- [ ] If a companion spec exists, every spec requirement is covered or noted in Known Limitations
- [ ] Document size is scaled appropriately to system complexity

---

## Anti-Patterns

**Section isolation violation:**
"For details on the confidence engine, see Section 3.4." Each section is standalone. Repeat necessary context.

**Decisions without rationale:**
"We chose LangGraph." Why? What else was considered? Future engineers will replace it if they don't know why it was chosen.

**Vague test guidance:**
"Test the confidence scoring." Instead: "Test that a composite score below 0.4 routes to `no_answer` regardless of document count; that exactly 0.4 routes to `low_confidence`; that above 0.7 with at least one document routes to `full_answer`."

**Implementation leakage in overview:**
Section 1 explains WHAT. Section 3 explains HOW. Do not describe internal mechanisms in the System Overview.

**Generic operational notes:**
"Monitor the logs for errors." Instead: "The guardrail emits `event=guardrail_blocked, reason=<rule_name>` on each blocked query. A sustained spike (>5% of queries) indicates either an active probe or a misconfigured risk taxonomy."

**Missing alternatives in decision tables:**
If only one option appears under "Alternatives Considered," either the decision was trivial (omit it) or research was insufficient (document the real alternatives you weighed).

**Documenting internal contracts in Section 6:**
Section 6 is the system boundary — what external callers need. Internal module-to-module contracts belong in each module's Purpose and Error behavior sub-sections in Section 3.

**Single data flow scenario:**
One happy-path trace is insufficient. Include at least one error/fallback path so the test team can see how failures propagate.
