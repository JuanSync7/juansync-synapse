# [System Name] — Engineering Guide

> **Document type:** Post-implementation engineering reference
> **Companion spec:** `[docs/path/to/SPEC.md]` *(or "None — guide based on implemented behavior")*
> **Companion design:** `[docs/path/to/DESIGN.md]` *(or "None")*
> **Source location:** `[src/subsystem/]`
> **Last updated:** YYYY-MM-DD

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Decisions](#2-architecture-decisions)
3. [Module Reference](#3-module-reference)
4. [End-to-End Data Flow](#4-end-to-end-data-flow)
5. [Configuration Reference](#5-configuration-reference)
6. [Integration Contracts](#6-integration-contracts)
7. [Testing Guide](#7-testing-guide)
8. [Operational Notes](#8-operational-notes)
9. [Known Limitations](#9-known-limitations)
10. [Extension Guide](#10-extension-guide)

---

## 1. System Overview

### Purpose

[1–2 paragraphs: What problem does this system solve? Who uses it? What does it receive as input and produce as output? What are its key responsibilities? Keep this at the WHAT level — do not describe internal mechanisms here.]

### Phase History

<!-- Include this sub-section only for phased delivery projects. Omit for single-phase projects. -->

| Phase | Delivered | Date |
|-------|-----------|------|
| P1 | [summary of what P1 built] | YYYY-MM-DD |

### Architecture at a Glance

```
[ASCII diagram showing the major components and their relationships.
Use arrows to show data flow. Label each component with its role.]

Input
  │
  ▼
┌─────────────────┐
│  [Component A]  │  [brief role]
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  [Component B]  │  [brief role]
└─────────────────┘
         │
         ▼
Output
```

### Design Goals

The following goals shaped implementation choices throughout this system:

1. **[Goal 1]** — [Why this goal mattered. What trade-offs it forced.]
2. **[Goal 2]** — [...]
3. **[Goal 3]** — [...]

### Technology Choices

| Technology | Role in This System | Why Chosen Over Alternatives |
|-----------|--------------------|-----------------------------|
| [Tech/Library] | [What it does here] | [Why this over X or Y] |
| [Tech/Library] | [What it does here] | [Why this over X or Y] |

---

## 2. Architecture Decisions

*Decisions in this section span multiple modules. Module-specific decisions are documented within each module's section in Section 3. Heuristic: if changing the decision would require modifying multiple files, it belongs here.*

---

### Decision: [Short title]

**Context:** [Why this decision had to be made. What constraints or requirements drove it.]

**Options considered:**
1. **[Option A]** — [what it enables; what it costs]
2. **[Option B]** — [what it enables; what it costs]
3. **[Option C]** — [what it enables; what it costs]

**Choice:** [Option X]

**Rationale:** [Why this option over the others. Be specific about the deciding factors.]

**Consequences:**
- **Positive:** [What this enables or simplifies]
- **Negative:** [What this costs, constrains, or makes harder]
- **Watch for:** [What to revisit if circumstances change — e.g., scale, new requirements]

---

### Decision: [Short title]

*(Repeat for each cross-cutting architectural decision)*

---

## 3. Module Reference

*Each section below is self-contained. You can read any section independently without reading others.*

---

### `src/[path]/[file].py` — [Module Name]

**Purpose:**

[One paragraph explaining what this module does and why it exists in the system. What problem does it solve? What role does it play in the overall pipeline?]

**How it works:**

[Step-by-step walkthrough of the core logic. Walk through what happens from the moment this module receives input to when it produces output. Use numbered steps for sequential logic. Reference real function and class names. Include short code snippets for non-obvious algorithms. Trace public interface and key internal logic — skip trivial helpers.]

For example:
1. [First thing that happens]
2. [Second thing, explaining why]
3. [Third thing, including any branching logic]

```python
# Short snippet from actual source (10–25 lines) for non-obvious logic
# Annotate non-obvious lines with comments
```

**Key design decisions:**

| Decision | Alternatives Considered | Why This Choice |
|----------|------------------------|-----------------|
| [what was decided] | [other options that were evaluated] | [reason this was chosen] |

**Configuration:**

| Parameter | Type | Default | Effect |
|-----------|------|---------|--------|
| `[param_name]` | `[type]` | `[default]` | [what changes when this is modified] |

*If this module has no configurable parameters, write: "This module has no configurable parameters."*

**Error behavior:**

[What exceptions this module raises. Under what conditions each is raised. What callers should do when they receive each. Which failures are retried internally vs. surfaced to callers.]

**Test guide:**

- **Behaviors to test:** [Specific, verifiable behaviors. Not "test the module" — e.g., "verify that X input produces Y output", "verify that Z condition raises ValueError"]
- **Mock requirements:** [What external dependencies must be mocked and why — e.g., "mock the Weaviate client because it requires a live connection"]
- **Boundary conditions:** [Inputs at the edges: empty collections, None values, zero, maximum values, single-element inputs]
- **Error scenarios:** [Which error paths produce observable, testable output — e.g., "when the LLM returns malformed JSON, the node falls back to keyword extraction"]
- **Known test gaps:** [Behaviors that are difficult to test and why — e.g., "timeout behavior requires real network latency; use a sleep mock"]

---

### `src/[path]/[file].py` — [Module Name]

*(Repeat the full six-section module block for each source file with non-trivial logic)*

---

### `src/[path]/types.py` — [Type Definitions]

*(For type/schema files: Purpose + code block of type definitions + key design decisions if non-obvious. Skip How it works, Error behavior, Test guide.)*

**Purpose:**

[What types this file defines and why they exist as a separate file.]

```python
# Key type definitions from actual source
```

**Key design decisions:**

| Decision | Alternatives Considered | Why This Choice |
|----------|------------------------|-----------------|
| [e.g., TypedDict over dataclass] | [other option] | [reason] |

---

## 4. End-to-End Data Flow

### Scenario 1: [Happy path — e.g., "Factual query with high-confidence answer"]

**Input:**

```python
# What the caller provides to the system entry point
{
    "query": "...",
    "session_id": "...",
    # ... other fields with realistic values
}
```

**Stage-by-stage trace:**

**Stage 1: [Stage Name]** (`src/path/to/stage.py`)

State entering this stage:
```python
{
    "field_a": "value",
    "field_b": None,   # not yet populated
}
```

Action: [What this stage does in 1–2 sentences]

State after this stage:
```python
{
    "field_a": "value",
    "field_b": "now populated",  # ← changed
}
```

---

**Stage 2: [Stage Name]** (`src/path/to/stage.py`)

State entering this stage:
```python
{ ... }
```

Action: [...]

State after this stage:
```python
{ ... }
```

---

*(Continue for each stage)*

**Final output:**

```python
# What the system returns to the caller
{
    "answer": "...",
    "confidence": 0.87,
    # ...
}
```

---

### Scenario 2: [Error/fallback path — e.g., "Query blocked by guardrail" or "LLM timeout with fallback"]

**Input:**

```python
# An input that triggers error handling or early termination
{ ... }
```

**Stage-by-stage trace:**

*(Same format as Scenario 1, but show where the flow diverges — which stage detects the error, what state changes, and what the caller receives)*

**Divergence point:** [Stage name] at [condition] → [what happens differently]

**Final output:**

```python
# What the caller receives in this error case
{ ... }
```

---

### Scenario 3 (optional): [Edge case — e.g., "Low-confidence routing" or "Empty document set"]

*(Same format. Include when the system has a notable conditional branch worth illustrating.)*

---

### Branching Points Summary

| Condition | Path Taken | Where It's Decided |
|-----------|-----------|-------------------|
| [e.g., confidence < 0.4] | [e.g., routes to no_answer handler] | [`src/path/router.py:42`] |
| [e.g., guardrail triggered] | [e.g., returns blocked response immediately] | [`src/path/guardrail.py:88`] |

---

## 5. Configuration Reference

*All configuration parameters for this system. Grouped by the module they control.*

### [Module Name] Parameters

| Parameter | Type | Default | Valid Range / Options | Effect |
|-----------|------|---------|----------------------|--------|
| `[param]` | `[type]` | `[default]` | `[range or enum]` | [precise behavioral description] |

### [Next Module] Parameters

| Parameter | Type | Default | Valid Range / Options | Effect |
|-----------|------|---------|----------------------|--------|
| `[param]` | `[type]` | `[default]` | `[range or enum]` | [precise behavioral description] |

---

## 6. Integration Contracts

*This section covers the **system boundary** — how external callers interact with this system. Internal module-to-module contracts are documented in each module's section in Section 3.*

### What callers must provide

```python
# Entry point signature and required input shape
def entry_point(
    query: str,            # required; max N characters
    session_id: str,       # required; UUID format
    config: Config,        # required; see Section 5
    # ...
) -> OutputType:
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `[field]` | `[type]` | Yes / No | [e.g., max length, valid values] |

### What callers receive

```python
# Output shape
{
    "answer": str,           # the generated response
    "confidence": float,     # 0.0–1.0
    "sources": list[str],    # source URIs used
    # ...
}
```

| Field | Type | Always Present | Notes |
|-------|------|---------------|-------|
| `[field]` | `[type]` | Yes / No | [when it may be absent or None] |

### External dependency contracts

| Dependency | Role | What This System Assumes |
|-----------|------|--------------------------|
| [Service/Library] | [What it does] | [What behavior this system relies on — e.g., "returns embeddings in < 500ms", "raises ConnectionError on timeout"] |

---

## 7. Testing Guide

### Component Testability Map

| Module | Unit-Testable | Needs Integration Test | External Dep Required | Notes |
|--------|:------------:|:---------------------:|:--------------------:|-------|
| `[module.py]` | Y | N | N | |
| `[module.py]` | Y | Y | Y | Requires live [service] |

### Mock Boundary Catalog

**Mock these:**

| Dependency | Why Mock | Recommended Mock Pattern |
|------------|----------|-------------------------|
| [e.g., Weaviate client] | [External service, requires network] | [e.g., `unittest.mock.MagicMock` with `return_value=...`] |

**Do NOT mock these:**

| Component | Why Real Is Better |
|-----------|-------------------|
| [e.g., confidence scoring] | [Deterministic pure function; mocking removes test value] |

### Critical Test Scenarios

These scenarios must always be covered. A regression here would be high-severity.

1. **[Scenario name]**
   - Input: [concrete description]
   - Expected behavior: [precise, verifiable outcome]
   - Why it matters: [what breaks if this regresses]

2. **[Scenario name]**
   - Input: [...]
   - Expected behavior: [...]
   - Why it matters: [...]

*(List 8–12 scenarios)*

### State Invariants

These properties must be true at every stage regardless of input:

- [ ] [e.g., `state["errors"]` is always a list, never None]
- [ ] [e.g., `state["source_key"]` is set before Phase 2 runs]

### Regression Scenario Catalog

| Scenario | What Would Break | Guard Test |
|----------|-----------------|-----------|
| [e.g., empty document list reaching storage node] | [NullPointerError in storage] | [`test_empty_chunks_skips_storage`] |

### Test Data Guidance

[What kinds of inputs produce meaningful test coverage. Key considerations:]
- [e.g., "Use documents with 0, 1, and N chunks to cover all paths through the chunking node"]
- [e.g., "Real embeddings can be replaced with random unit vectors for unit tests"]
- [e.g., "Test corpus for integration tests is in `tests/fixtures/`"]

---

## 8. Operational Notes

### Running the System

[How to start or invoke the system. Key configuration needed for a working run. Any required environment variables or external services.]

```bash
# Minimal working invocation
[command]
```

### Monitoring Signals

| Log Event / Metric | What It Means | Normal Range | Action If Outside Range |
|-------------------|--------------|-------------|------------------------|
| `[event=...]` | [what's happening] | [e.g., < 1% of queries] | [what to do] |

### Common Failure Modes

| Symptom | Root Cause | Debug Path |
|---------|-----------|-----------|
| [What you observe] | [Why it happens] | [How to diagnose: which logs, which config to check] |

---

## 9. Known Limitations

*This section is intentional — documenting what the system doesn't do prevents future engineers from assuming it does.*

| Limitation | Impact | Workaround / Future Path |
|-----------|--------|-------------------------|
| [What the system cannot do or does not handle] | [Who is affected and how] | [Current workaround if any; what would be needed to lift this limit] |

---

## 10. Extension Guide

### Adding a [New Component Type — e.g., New Pipeline Stage]

[Step-by-step instructions. Be specific: name the files to create or modify, in what order, and what each change must contain.]

1. **[Step 1]** — Create `src/[path]/[new_file].py`
   - Must implement: [interface or contract to satisfy]
   - Must expose: [function or class signature]

2. **[Step 2]** — Register in `src/[path]/workflow.py`
   - Add: [exact code or pattern to follow]

3. **[Step 3]** — Update state in `src/[path]/state.py`
   - Add field: [field name, type, default]

4. **[Step 4]** — Add tests in `tests/[path]/test_[new_file].py`
   - Cover: [minimum required test cases]

5. **[Step 5]** — Update documentation
   - Add a module section to this guide (Section 3)
   - Update the architecture diagram (Section 1)

**Pitfalls:**
- [Thing 1 that trips people up — e.g., "Forgetting to add the new state field causes a KeyError in the next stage"]
- [Thing 2]
- [Thing 3]

---

## Appendix: Requirement Coverage

*Include this appendix if a companion spec exists. Omit if no spec.*

| Spec Requirement | Covered By (Module Section) |
|------------------|-----------------------------|
| [REQ-101] | `src/path/module.py` — [Module Name] |
| [REQ-102] | `src/path/other.py` — [Other Module] |
| [REQ-103] | Not implemented — see Known Limitations |
