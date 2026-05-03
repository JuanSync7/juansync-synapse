---
name: write-test-docs
description: "Use when you need a test planning document that defines what to test for each module. Triggered by 'write test docs', 'test planning document', 'test specification', 'plan the tests'."
domain: docs.post-build
intent: write
tags: [test planning, test spec, integration tests]
user-invocable: true
argument-hint: "[system/subsystem name] [optional: engineering guide path] [optional: output path]"
---

## Layer Context

```
Phase 0: Contracts               ← write-implementation-docs
Phase B: Implementation          ← implement-code
Phase C: Engineering Guide       ← write-engineering-guide
Phase D: Test Docs               ← YOU ARE HERE
Phase E: Test Implementation     ← write-module-tests (reads this document)
```

**Required inputs:**
- Engineering guide (Phase C) — must exist before writing
- Phase 0 contracts from write-implementation-docs — for import surface and error taxonomy
- Companion spec — for FR acceptance criteria (primary source of WHAT to test)

**Isolation rule:** Do NOT read source implementation files (`src/`). If the engineering guide section is insufficient to specify a test, note it as a known gap — do not fetch the source.

---

# Write Test Docs Skill

You are writing the test planning document. This is the verification engineer's specification of what must be tested — derived from the engineering guide and spec acceptance criteria, without reading implementation source code.

Tests are derived from documented behavior (engineering guide) and required behavior (spec ACs), not from implementation knowledge. This is what preserves test independence.

**Announce at start:** "I'm using the write-test-docs skill to create the test planning document."

## Progress Tracking

```
TaskCreate: "Planning Stage: read inputs and produce section_context_map"
TaskCreate: "Wave 1: per-module test spec sections (parallel)"
TaskCreate: "Wave 2: integration test specification"
TaskCreate: "Wave 3: FR-to-test traceability matrix"
```

Mark each `in_progress` when starting, `completed` when done. When dispatching agents, set `model:` explicitly on every dispatch.

## Input Gathering

Before writing, you MUST have:

1. **Engineering guide path** — from `$ARGUMENTS[1]` or ask. Primary source for module behavior, error conditions, and data flow scenarios.
2. **Phase 0 contracts path** — from write-implementation-docs. For import surface and error taxonomy. Do NOT read source files.
3. **Spec path** — for FR acceptance criteria (the primary source of WHAT to test).
4. **System name and output path** — from `$ARGUMENTS[0]` / `$ARGUMENTS[2]`, or defaults to `docs/<subsystem>/<SUBSYSTEM>_TEST_DOCS.md` (or `_TEST_DOCS_P{N}.md` if phased).
5. **Phase number** — If phased delivery, which phase?
6. **Prior phase test docs** (P2+ only) — `_TEST_DOCS_P{N-1}.md` for regression requirements.
7. **Engineering guide phase updates** (P2+ only) — check Phase History and "Introduced in" / "Updated in" annotations to identify what changed.

---

## Planning Stage (NON-SKIPPABLE)

Before writing any section, read all input sources and produce a `section_context_map`. Do this before writing a single module test spec.

**Why this stage exists:** Each module's test spec is independent and can be written in parallel. Scoping which engineering guide sections and FR ACs feed each module spec prevents agents from accumulating unrelated context and producing test cases that cross module boundaries.

### `section_context_map` schema

```
id:             string    # unique identifier, e.g. "module_engine", "integration", "traceability"
title:          string    # section heading
wave:           int       # 1 = per-module specs (parallel), 2 = integration, 3 = traceability
depends_on:     [id, ...] # section IDs that must be approved before this starts
model_tier:     haiku | sonnet | opus
source_content: string    # source text for THIS section only — NOT a file path.
                          # per-module:   EG module section (Purpose, How it works, Error behavior)
                          #               + relevant FR ACs + Phase 0 contracts for this module
                          #               + mock interface specs for this module's external deps
                          # integration:  EG data flow section + EG integration contracts section
                          #               + all Wave 1 module test spec outputs (compiled)
                          # traceability: FR list from spec + all Wave 1+2 outputs
prior_slots:    [id, ...] # for Wave 2+: all Wave 1 module spec IDs
prompt:         string    # complete, self-contained prompt for the section agent
```

### section dependency graph

```
Wave 1 (parallel — one entry per module from engineering guide Section 3):
  module_<name> → Per-module test specification (one per EG module section)
                  source: EG module section (Purpose, How it works, Error behavior) +
                          relevant FR ACs + Phase 0 contracts for this module +
                          mock interface specs for this module's external deps
                  model_tier: sonnet
                  MUST NOT include: other modules' source, source files, test files

Wave 2 (single, after all Wave 1):
  integration   → Integration test specification
                  source: EG data flow section (Section 4) +
                          EG integration contracts section (Section 6) +
                          all Wave 1 module test spec outputs (compiled, inlined)
                  model_tier: sonnet
                  depends_on: [all module_<name> IDs]

Wave 3 (single, after Wave 2):
  traceability  → FR-to-test traceability matrix
                  source: FR list from spec + all module test spec outputs + integration output
                  model_tier: haiku
                  depends_on: [integration]
```

### How to produce the map

1. Read the engineering guide completely. List all modules from Section 3 (Module Reference).
2. Read the spec completely. Extract every FR/REQ ID and its acceptance criteria.
3. Read Phase 0 contracts. Note exception class names and TypedDicts per module.
4. Identify external dependencies from the EG integration contracts section (Section 6). For each external dependency, write a mock interface spec: the interface to mock, representative happy-path and error-path return values.
5. For each module: copy its EG section (Purpose + How it works + Error behavior) and its relevant FR ACs into `source_content`. Write the complete module test spec `prompt`.
6. For `integration`: compile EG data flow scenarios (Section 4) and integration contracts (Section 6). Fill `prior_slots` with all Wave 1 module IDs.

→ **Proceed to Execution Stage once all map entries have their `prompt` fields populated.**

---

## Execution Stage

> **NON-SKIPPABLE:** Do not write any module test spec until the Planning Stage is complete and the `section_context_map` exists in session. If you are tempted to skip ahead because the system is small or the modules seem obvious, resist. The map is the isolation guarantee — without it, test spec agents accumulate cross-module context that biases test cases toward implementation coupling.

Execute the `section_context_map` using **parallel-agents-dispatch** with sequential waves:

1. **Wave 1** — dispatch one agent per module in parallel. Each receives only its `prompt` (EG section, FR ACs, and contracts already inlined — agents never read files).
2. **Review** each module test spec: verify all five spec sub-sections present, isolation contract block included, no source file references, known test gaps stated explicitly.
3. **Wave 2** — dispatch the integration test spec agent with all Wave 1 outputs + EG data flows inlined.
4. **Wave 3** — dispatch the traceability agent with FR list + all prior outputs.
5. **Assemble** — combine all approved outputs into the final test docs at the output path.

**Section agent isolation contract:**

> The section agent receives ONLY:
> 1. Its `prompt` from the `section_context_map` (EG sections, FR ACs, contracts already inlined)
> 2. Prior approved section outputs injected into `{{slot_id}}` markers
>
> Must NOT receive: source implementation files (`src/`), Phase B code, other modules' test specs,
> the full engineering guide, the full spec, or the complete `section_context_map`.

---

## Document Structure

### Header

```markdown
# [System Name] — Test Docs

> **For write-module-tests agents:** This document is your source of truth.
> Read ONLY your assigned module section. Do not read source files, implementation code,
> or other modules' test specs.

**Engineering guide:** [path]
**Phase 0 contracts:** [path]
**Spec:** [path]
**Produced by:** write-test-docs

---
```

### Mock/Stub Interface Specifications

One sub-section per external dependency identified in the EG integration contracts section. Written once, referenced by any module that needs the mock.

````markdown
#### Mock: [External Dependency Name]

**What it replaces:** [e.g., embedding model API, vector store client, LLM provider]

**Interface to mock:**
```python
def embed_text(text: str) -> list[float]:
    """Returns embedding vector for the input text."""
    ...
```

**Happy path return:**
```python
[0.1, 0.2, ..., 0.9]  # 1536-dimensional float vector
```

**Error path return:**
```python
raise EmbeddingError("Embedding timeout after 30s")
```

**Used by modules:** `src/retrieval/engine.py`, `src/retrieval/embedder.py`
````

---

### Per-Module Test Specification

One section per module from the engineering guide. Each section is self-contained — the write-module-tests agent reads only this section.

````markdown
### `src/path/to/module.py` — [Module Name]

**Module purpose:** [1 sentence from EG Purpose sub-section]

**In scope:**
- [Behavior A from EG "How it works"]
- [Behavior B]

**Out of scope:**
- [Behavior delegated to another module — name it]
- [Configuration concerns owned by another module]
- [External dependency behavior — mock it, don't test it]

#### Happy path scenarios

| Scenario | Input | Expected output |
|----------|-------|-----------------|
| [normal input description] | `{"field": "value"}` | `{"result": "expected"}` |
| [alternate routing description] | `{"field": "other"}` | `{"result": "alternate"}` |

#### Error scenarios

Derived from EG "Error behavior" sub-section — one row per documented exception:

| Error type | Trigger condition | Expected behavior |
|-----------|------------------|-------------------|
| `SomeError` | [trigger from EG Error behavior] | raises `SomeError` with message matching `"pattern"` |
| `ValueError` | [trigger] | raises `ValueError` — caller must handle |

#### Boundary conditions

Derived from spec FR acceptance criteria — edge cases explicitly stated in the AC:

- Empty input (`[]` or `""`) → [expected behavior per AC]
- `None` where optional → [expected behavior per AC]
- Max-length input (N items) → [expected behavior per AC]
- Zero / negative numeric input → [expected behavior per AC]

#### Integration points

- Calls `other_module.function()` with `[InputType]` → expects `[OutputType]`
- On `ExternalError` from dependency: [how this module propagates or handles it]
- Receives calls from: `[calling module]` — must return `[OutputType]`

#### Known test gaps

State explicitly — never silently omit:
- `[Behavior]` is difficult to test because `[reason]` — no test written for this
- `[Configuration toggle]` requires live external dependency — integration test only

#### Agent isolation contract (include verbatim in write-module-tests dispatch)

> **Agent isolation contract:** This agent receives ONLY:
> 1. This module test spec section
> 2. Phase 0 contract files (for import surface only — do not infer behavior from stubs)
>
> **Must NOT receive:** Source implementation files (`src/`), Phase B implementation code,
> other modules' test specs, or the engineering guide directly.
````

---

### Integration Test Specification

Derived from the EG End-to-End Data Flow section (Section 4). Produce at minimum:
1. Happy path — most common successful flow end-to-end
2. Error path — one step fails, error propagates to caller
3. Edge case path (optional) — conditional routing or boundary input

One sub-section per scenario:

````markdown
### Integration: [Scenario name from EG data flow]

**Scenario:** [1 sentence description]

**Entry point:** `function_name(input)` or `POST /endpoint`

**Flow:**
1. Input arrives at `module_A` with shape `{"field": type}`
2. `module_A` calls `module_B.fn()` → B returns `{"field": type}`
3. `module_B` calls external dep (mock: [mock name from Mock/Stub section]) → returns `[value]`
4. Final output: `{"result": type}`

**What to assert:**
- Final output shape matches contract
- State at each stage (if observable)
- Error propagation: if step N fails, caller receives `[error type]`

**Mocks required:** `[mock names from Mock/Stub Specifications]`
````

---

### FR-to-Test Traceability Matrix

Every FR from the spec must appear. If a FR is not covered, note it as a known gap.

| FR | Acceptance Criteria Summary | Module Test | Integration Test |
|----|----------------------------|-------------|-----------------|
| FR-1.1 | [AC summary, 1 line] | `module_engine` — happy path | integration_happy |
| FR-1.3 | [AC summary] | `module_engine` — boundary | — |
| FR-1.5 | [AC summary] | — | integration_error |
| FR-1.7 | [AC summary] | Not covered — known gap: requires live external dep | — |

---

## Writing Standards

**Module test spec sections:**
- Derive happy path scenarios from EG "How it works" — these describe what the module does, which becomes the expected behavior to assert
- Derive error scenarios from EG "Error behavior" — one row per documented exception, not one row per error class
- Derive boundary conditions from spec FR acceptance criteria — use the exact edge cases the AC states
- Known test gaps must be stated explicitly with a reason — never silently omit

**Integration specs:**
- Show concrete state shapes at each step (from EG data flow scenarios)
- Specify exact mock names — not "mock the LLM" but the mock name from Mock/Stub Specifications
- At minimum: one happy path + one error path

**No source code:**
- Do not read or reference `src/` implementation files
- Do not infer behavior from Phase 0 stubs (stubs have NotImplementedError — they define interface, not behavior)
- If behavior is unclear from the EG, note it as a gap — do not fetch source

---

## Quality Checklist

Before finalising:

- [ ] Every module from the engineering guide Section 3 has a test spec section
- [ ] Every module section has all five sub-sections (happy path, error scenarios, boundary conditions, integration points, known test gaps)
- [ ] Every module section has a verbatim "Agent isolation contract" block
- [ ] Mock/Stub Specifications cover all external dependencies listed in EG Section 6
- [ ] Integration specs include at minimum happy path + error path
- [ ] Every FR from the spec appears in the traceability matrix
- [ ] No `src/` file paths referenced — only EG section paths and Phase 0 contract paths
- [ ] Known test gaps are stated explicitly with reasons, not silently omitted

---

## Phased Delivery

When writing test docs for a specific delivery phase (P1, P2, P3...):

> **Read [`references/phased-delivery.md`](references/phased-delivery.md)** for the full phasing rules: phase-specific test scoping, regression test requirements, mock evolution, and cross-phase integration tests.

**Summary:**
- Output naming: `{SUBSYSTEM}_TEST_DOCS_P{N}.md`
- Test only modules introduced or modified in this phase
- P2+ includes a "Regression Test Requirements" section assessing risk to prior-phase tests
- P2+ includes at least one cross-phase integration test scenario
- P2+ notes mock updates where prior-phase interfaces changed
- After writing, update the subsystem README dashboard — read [`references/readme-update-contract.md`](references/readme-update-contract.md)

---

## Integration

**Upstream (required before this skill):**
- `write-engineering-guide` — must exist
- `write-implementation-docs` — for Phase 0 contracts and error taxonomy

**Downstream (invoke after this skill):**
- `write-module-tests` — reads this document module-by-module to implement pytest code

**Document Chain:**

```
write-implementation-docs → implement-code → write-engineering-guide
                                                       ↓
                                               write-test-docs
                                                       ↓
                                               write-module-tests
```

## README Dashboard

After saving the test docs, update the subsystem's `README.md` dashboard. Read [`references/readme-update-contract.md`](references/readme-update-contract.md) for the update procedure.

**Chain handoff:** After saving, completing the quality checklist, and updating the README:

> "Test docs complete and saved to `[path]`. Invoke `write-module-tests [module-name] [path-to-this-doc]` per module section to implement pytest coverage."
