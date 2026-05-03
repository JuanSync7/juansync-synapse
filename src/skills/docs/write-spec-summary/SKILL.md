---
name: write-spec-summary
description: Write or update a concise specification summary document that stays in sync with a companion spec. Use when the user needs to create a spec summary, update a spec summary, sync a summary with its spec, or asks for a "spec summary". Triggered by requests like "write a spec summary", "summarize the spec", "update spec summary", "sync summary with spec".
domain: docs.spec
intent: summarize
tags: [summary, digest, overview]
user-invocable: true
argument-hint: "[path to spec document] [optional: output path for summary]"
---

## Wrong-Tool Detection

- **User wants to write a full spec from scratch** → redirect to `/write-spec-docs`
- **User wants a design doc** → redirect to `/write-design-docs`

## Layer Context

This skill produces a **Layer 2 — Spec Summary** in the 4-layer doc hierarchy:

```
Layer 1: Platform Spec          (manual)
Layer 2: Spec Summary           ← YOU ARE HERE
Layer 3: Authoritative Spec     ← write-spec-docs (required input — must exist)
Layer 4: Implementation Guide   ← write-impl
```

**Before writing, verify:**
- The companion spec (Layer 3) exists — read it completely before writing anything
- §1 Generic System Overview must contain no FR-IDs, no technology names, no file names
- §1 covers all five dimensions: purpose, pipeline flow, tunable knobs, design rationale, boundary semantics
- §2+ scope lists must match the spec exactly — do not add or remove items

**§1 is scrapeable.** It is designed to be extracted by a script and assembled into a platform-level overview document. Keep the section boundary clean: content starts immediately after the `## 1)` heading and ends before the `---` rule.

---

# Specification Summary Skill

You are writing (or updating) a concise specification summary document. The summary is a standalone digest of a companion specification — it captures intent, scope, structure, and key decisions without duplicating requirement-level detail.

## Progress Tracking

At the start, create a task list:

```
TaskCreate: "Read spec and extract key information"
TaskCreate: "Write system overview (§1)"
TaskCreate: "Draft remaining sections from template"
TaskCreate: "Trim, cross-check scope, and verify"
```

Mark each `in_progress` when starting, `completed` when done.

## Input Gathering

Before writing, you MUST have:

1. **Source spec path** — The companion specification document to summarize. If the user has not provided one, ask.
2. **Output path** — Where to write the summary. Default: same directory as the spec, with `_SUMMARY` appended to the filename (e.g., `MY_SPEC.md` → `MY_SPEC_SUMMARY.md`; `MY_SPEC_P2.md` → `MY_SPEC_SUMMARY_P2.md`).
3. **Existing summary** — If a summary already exists at the output path, read it to understand what changed.
4. **Phase number** — If phased delivery, which phase? The companion spec will have a `_P{N}` suffix.
5. **Prior phase summaries** — For P2+: read prior summaries to ensure §1 builds on them coherently.

If the user provides `$ARGUMENTS`, treat the first argument as the spec path and the second (if provided) as the output path.

## Reading the Spec

Read the full source specification. Extract the following from it:

| What to Extract | Where It Typically Lives |
|-----------------|--------------------------|
| System name and version | Document header / version table |
| Problem statement / intent | Section 1 (Scope & Definitions) |
| Entry/exit points | Scope section |
| In-scope / out-of-scope | Scope section |
| Architecture or pipeline stages | System Overview section |
| Requirement ID convention and families | Requirement Format section |
| Requirement section names and ID ranges | Requirement sections or ID range table |
| Design principles | Design Principles section |
| NFR categories | Non-Functional Requirements section |
| Security/compliance themes | Security section or SC-prefixed requirements |
| Acceptance criteria | System-Level Acceptance Criteria section |
| Evaluation/feedback framework | Evaluation/Feedback sections (if present) |
| External dependencies | External Dependencies section |
| Implementation phasing | Appendix (if present) |
| Open questions | Appendix (if present) |
| Companion documents | Document References appendix or header |

Not all specs will have every section. Adapt — include only what the spec provides.

## Document Structure

The summary MUST follow the template in [template.md](template.md). Read it before writing.

The template defines these sections:

1. **Generic System Overview** — Full-detail, tech-agnostic description written from scratch. See §1 rules below — this is the most important section and has strict constraints.
2. **Header** — Companion reference, version, purpose, see-also links
3. **Scope and Boundaries** — Entry/exit points, in-scope, out-of-scope
4. **Architecture / Pipeline Overview** — ASCII diagram and/or compact stage list
5. **Requirement Framework** — How requirements are structured (IDs, priority keywords, rationale/AC presence)
6. **Functional Requirement Domains** — Grouped by ID range with brief coverage description
7. **Non-Functional and Security Themes** — Category bullets, not individual requirements
8. **Design Principles** — One-liner per principle
9. **Key Decisions** — Architectural choices captured by the spec
10. **Acceptance, Evaluation, and Feedback** — What measurability the spec provides
11. **External Dependencies** — Required / optional / downstream contract
12. **Companion Documents** — How this summary relates to the spec and companion docs
13. **Sync Status** — Version the summary is aligned to, and date

Sections 4–11 are conditional — include only when the source spec has corresponding content.

---

## §1 Generic System Overview — Rules

§1 is a full, technology-agnostic specification of the system. It is **written from scratch by Claude** based on the spec's functional content — not summarised, not copied. It must stand alone as an explanation of what the system does, how it works, what can be tuned, and why it is designed the way it is.

### What to Write

Cover all five dimensions using `###` sub-headings:

**### Purpose**
What problem this system solves. What role it plays in the larger platform. Why it was built — what fails or degrades without it. 2–4 sentences.

**### How It Works**
Walk through the system end-to-end. What happens to the input as it moves through each stage? Describe stages generically — name them by what they do, not what technology implements them (e.g., "text extraction stage" not "PyMuPDF extraction"). Include conditional or optional paths. Be specific enough that a new engineer could form a mental model without reading the spec.

**### Tunable Knobs**
What operators and engineers can configure to change system behaviour. For each configurable dimension, explain: what it controls, why someone would want to change it, and what the system does if it is left at its default. Do not list specific parameter names or config file paths — describe the dimensions at a conceptual level.

**### Design Rationale**
Why is the system designed this way? What constraints, principles, or past failures drove the key architectural decisions? What alternatives were implicitly rejected and why? This section explains the "why" behind the shape of the system.

**### Boundary Semantics**
Entry point: what triggers this system and what it receives as input. Exit point: what it produces and hands off. What state is maintained vs. discarded. Where responsibility ends and the next system begins.

### Length

250–450 words across all five sub-sections. This is full detail — not condensed. It is the longest section in the summary.

### Hard Constraints

**Must NOT contain:**
- Requirement IDs of any kind (FR-xxx, NFR-xxx, SC-xxx, REQ-xxx)
- Specific technology names (e.g., LangGraph, Qdrant, OpenAI, PyMuPDF, FastAPI, Redis, Postgres)
- Implementation file names, class names, or function names
- Specific threshold values, metric targets, or SLA numbers
- Project-specific jargon that only makes sense inside this codebase

**Scrapeable boundary rule:** Do not use content that bleeds across the `---` separator. The entire §1 block — from `## 1)` to `---` — must be self-contained and extractable as a unit.

---

## Quality Standards

### Content Rules (§2 onward)

- **Summarize, do not duplicate.** §2 onward points readers to the spec for detail. It does not restate individual requirements.
- **No requirement IDs in prose.** Use ID ranges and family prefixes (`FR-100 to FR-1399`) to reference groups, not individual requirement IDs.
- **No acceptance-criteria values.** Thresholds, metric targets, and concrete numbers belong in the spec. The summary says "the spec defines acceptance criteria for X" — it does not repeat the numbers.
- **Preserve scope fidelity.** The in-scope / out-of-scope lists must exactly match the spec. Do not add or omit items.
- **Match the spec's terminology.** Use the same term the spec uses (e.g., if the spec says "review tier", do not write "trust level").

### Tone and Length

- **§1 target:** 250–450 words. Full detail.
- **Total document target:** 150–250 lines of markdown.
- **Audience:** Technical stakeholders who need the shape of the spec without reading every requirement.
- **Voice:** Neutral, declarative, third-person. No marketing language.

### Formatting

- Use `##` for top-level sections, `###` for subsections.
- Use `---` horizontal rules between major sections.
- Use bullet lists for scope items, domain lists, and dependency lists.
- Use bold for emphasis sparingly — principle names, requirement family prefixes, and key terms only.
- Do not use numbered section labels like "Section 3.1" — use descriptive headings.
- **Prefer ASCII diagrams over Mermaid** for pipeline/architecture visuals. ASCII renders universally and stays readable in diffs. Use a plain fenced code block (no language tag). Keep the diagram compact — one line per stage/component, mark optional stages, show terminal outputs with arrows.

## Planning Stage (NON-SKIPPABLE)

Before writing any section, produce a `reading_plan` — a per-section record that scopes which parts of the source spec are relevant to each output section. This keeps each section's working context focused.

**Why this stage exists:** write-spec-summary is a short document (150-250 lines), so per-section subagent dispatch would add disproportionate overhead. However, scoping which spec sections to read per output section still improves quality by preventing the agent from holding the full spec in active context for every section.

### `reading_plan` schema

For each output section, produce one entry:

```
section:               string    # output section identifier (e.g. "§1", "§3 Scope")
spec_sections_to_read: [string]  # spec section names/headings relevant to this output section
write_order:           int       # execution order (1 = first)
notes:                 string    # synthesis notes (e.g. "write from scratch — do not copy")
```

### write-spec-summary section-to-source mapping

```
Write order 1 — §1 Generic System Overview:
  spec_sections_to_read: [full spec — synthesize, do not copy]
  notes: Write from scratch in your own words. No FR-IDs, no technology names, no file names.

Write order 2 — §2 Header, §3 Scope and Boundaries, §4 Architecture / Pipeline Overview:
  spec_sections_to_read: [Section 1 Scope & Definitions, Section 2 System Overview]

Write order 3 — §5 Requirement Framework, §6 Functional Requirement Domains:
  spec_sections_to_read: [Section 1.4-1.5 requirement format, all requirement sections]

Write order 4 — §7 Non-Functional and Security Themes, §8 Design Principles, §9 Key Decisions:
  spec_sections_to_read: [Non-Functional Requirements section, Section 1.7 Design Principles]

Write order 5 — §10 Acceptance / Evaluation / Feedback, §11 External Dependencies:
  spec_sections_to_read: [System-Level Acceptance Criteria, External Dependencies section]

Write order 6 — §12 Companion Documents, §13 Sync Status:
  spec_sections_to_read: [Document References appendix, spec version table / header]
```

→ **Proceed to Writing Process once the reading_plan is complete.**

---

## Writing Process

> **NON-SKIPPABLE:** Do not write §1 or any section until the Planning Stage is complete and the `reading_plan` exists in session. For each step below, read only the spec sections listed in the reading_plan for that section — not the full spec. This keeps each section's working context focused.

1. **Read** the source spec completely (for Planning Stage only — subsequent section writes use scoped reads per the reading_plan).
2. **Read** the template.
3. **Write §1 first** — synthesize the Generic System Overview from scratch using the five dimensions. Use the spec as source material to understand the system, but write §1 in your own words without copying.
4. **Extract** information for §2+ per the extraction table above, reading only the spec sections listed in the reading_plan for each section.
5. **Draft** each template section using extracted content.
6. **Trim** — cut anything that restates individual requirements or repeats threshold values.
7. **Cross-check scope** — verify in-scope/out-of-scope lists match the spec exactly.
8. **Verify §1 constraints** — confirm §1 contains no FR-IDs, no technology names, no file names.
9. **Set sync status** — record the spec version and today's date.
10. **Lint** — check the output for markdown lint errors and fix them.

## Updating an Existing Summary

When the user asks to "update" or "sync" a summary:

1. Read the current summary AND the current spec.
2. Identify structural drift: new sections in the spec, removed sections, renamed sections, version bumps.
3. Update the summary to match. Do not rewrite sections that are already correct.
4. If the spec's functional scope changed significantly, rewrite §1 from scratch to reflect the new shape of the system.
5. Update the sync status section with the new spec version.

## Additional Guidelines

- The summary MUST be standalone — readable without opening the spec, but not a replacement for it.
- Do NOT include a table of contents — the document is short enough to scan.
- Do NOT include the spec's traceability matrix, glossary, or open questions in the summary. Mention their existence if relevant.
- If the spec has implementation phasing, mention the phase structure in one sentence but do not reproduce the phase details.

## Phased Delivery

When writing a summary for a phase-specific spec (`_SPEC_P{N}.md`):

> **Read [`references/phased-delivery.md`](references/phased-delivery.md)** for the full phasing rules: §1 evolution across phases, phase context section, and scope handling.

**Summary:**
- Output naming: `{SUBSYSTEM}_SPEC_SUMMARY_P{N}.md`
- §1 describes the full system after this phase (not just the delta) — grows richer each phase
- Add a "Phase Context" section between §1 and §2 with prior-phase summaries
- §2+ sections scope to this phase's spec only
- After writing, update the subsystem README dashboard — read [`references/readme-update-contract.md`](references/readme-update-contract.md)

## Integration

**Upstream (required before this skill):**
- `write-spec-docs` — the companion spec must exist before writing a summary

**Downstream (invoke after this skill):**
- `write-design` — generate a technical design document with task decomposition and contracts

## README Dashboard

After saving the summary, update the subsystem's `README.md` dashboard. Read [`references/readme-update-contract.md`](references/readme-update-contract.md) for the update procedure.

**Chain handoff:** After saving the summary and updating the README:

> "Spec summary complete and saved to `[path]`. Next step: `/write-design` to begin task decomposition, or update the summary later with `/write-spec-summary` when the spec changes."

## Document Chain

```
Unphased:
write-spec-docs  →  write-spec-summary  →  write-design  →  build-plan
 _SPEC.md            _SPEC_SUMMARY.md       _DESIGN.md       _IMPLEMENTATION.md

Phased:
write-spec-docs  →  write-spec-summary  →  write-design  →  write-implementation-docs
 _SPEC_P1.md         _SPEC_SUMMARY_P1.md    _DESIGN_P1.md    _IMPLEMENTATION_DOCS_P1.md
```
