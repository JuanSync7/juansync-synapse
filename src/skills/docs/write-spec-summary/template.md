## 1) Generic System Overview

<!-- SCRAPEABLE SECTION — must be tech-agnostic. No FR-IDs, no technology names, no file names, no threshold values. Written from scratch. 250–450 words across all five sub-sections. -->

### Purpose

[What problem this system solves. What role it plays in the larger platform. Why it was built — what fails or degrades without it. 2–4 sentences.]

### How It Works

[Walk through the system end-to-end. Describe what happens to the input as it moves through each processing stage. Name stages by what they do, not what technology implements them. Include conditional or optional paths. Be specific enough that a new engineer could form a mental model without reading the spec.]

### Tunable Knobs

[What operators and engineers can configure to change system behaviour. For each configurable dimension: what it controls, why someone would want to change it, and what the system does at its default. Describe dimensions conceptually — do not list parameter names or config file paths.]

### Design Rationale

[Why the system is designed this way. What constraints, principles, or past failures drove the key architectural decisions. What alternatives were implicitly rejected and why.]

### Boundary Semantics

[Entry point: what triggers this system and what it receives as input. Exit point: what it produces and hands off. What state is maintained vs. discarded. Where responsibility ends and the next system begins.]

---

# [System/Subsystem Name] — Specification Summary

**Companion document to:** `[spec_filename.md]` (v[X.Y.Z])
**Purpose:** Requirements-level digest for stakeholders, reviewers, and implementers.
**See also:** [List any companion documents — implementation guide, engineering guide, onboarding checklist, etc.]

---

## 2) Scope and Boundaries

**Entry point:** [What triggers the system — file, request, event, etc.]
**Exit points:**

- [Primary output]
- [Secondary output, if any]

### In scope

- [Item — match the spec's in-scope list exactly]
- [Item]

### Out of scope

- [Item — match the spec's out-of-scope list exactly]
- [Item]

<!-- If the spec distinguishes "out of scope for this spec" from "out of scope for the project", preserve that distinction here with a second list. -->

---

<!-- CONDITIONAL: Include only if the spec defines a pipeline, staged architecture, or component topology -->

## 3) Architecture / Pipeline Overview

<!-- Prefer an ASCII diagram (plain fenced code block, no language tag) for pipelines.
     Keep it compact: one line per stage, mark optional stages, show terminal outputs with arrows. -->

```
    [Source / Trigger]
           │
           ▼
    ┌──────────────────────────────┐
    │  [1]  [Stage Name]           │
    │  [2]  [Stage Name]           │
    │  [3]  [Stage Name]       *   │
    │  ...                         │
    │  [N]  [Final Stage]      *   │
    └──────────────┬───────────────┘
                   │
                   ▼
            [Output Store]

    * = optional / configurable
```

[1–2 sentences on cross-cutting stage properties — e.g., shared state model, error isolation, conditional routing.]

---

<!-- CONDITIONAL: Include only if the spec uses a formal requirement framework (IDs, priority keywords, rationale/AC) -->

## 4) Requirement Framework

[Describe how the spec structures requirements — ID conventions, priority keywords (e.g., RFC 2119), whether rationale and acceptance criteria are present, and whether a traceability matrix exists.]

- [Bullet per structural element: ID families, priority scheme, rationale/AC, traceability]

---

<!-- CONDITIONAL: Include only if the spec has grouped functional requirement sections -->

## 5) Functional Requirement Domains

[Intro sentence: what the functional requirements cover at a high level.]

- [Domain name] (`PREFIX-range`)
- [Domain name] (`PREFIX-range`)

---

<!-- CONDITIONAL: Include only if the spec has NFR and/or security/compliance sections -->

## 6) Non-Functional and Security Themes

### Non-functional areas (`NFR-*`)

- [Category — e.g., Performance (brief parenthetical)]
- [Category]

### Security/compliance (`SC-*`)

- [Theme — e.g., Auditability]
- [Theme]

---

<!-- CONDITIONAL: Include only if the spec defines design principles -->

## 7) Design Principles

- **[Principle name]**: [one-line implication]
- **[Principle name]**: [one-line implication]

---

<!-- CONDITIONAL: Include only if there are notable architectural decisions worth surfacing -->

## 8) Key Decisions Captured by the Spec

- [Decision — e.g., DAG orchestration for conditional routing]
- [Decision]

---

<!-- CONDITIONAL: Include only if the spec defines acceptance criteria, evaluation, or feedback sections -->

## 9) Acceptance, Evaluation, and Feedback

[State what measurability the spec provides — acceptance criteria, evaluation framework, feedback loops — without repeating specific thresholds.]

- [Bullet per category: acceptance criteria, evaluation framework, feedback mechanism]

---

<!-- CONDITIONAL: Include only if the spec lists external dependencies -->

## 10) External Dependencies

**Required:** [Brief list — service type, not product names unless the spec is product-specific]
**Optional:** [Brief list]
**Downstream contract only:** [Brief description of downstream consumers, if any]

---

## 11) Companion Documents

| Document | Role |
|----------|------|
| `[spec_filename.md]` | Authoritative requirements baseline |
| `[impl_filename.md]` | Implementation guide (phased tasks + code appendix) |
| `[this_filename.md]` | This document — requirements digest |

---

## 12) Sync Status

Aligned to `[spec_filename.md]` v[X.Y.Z] as of [YYYY-MM-DD].
