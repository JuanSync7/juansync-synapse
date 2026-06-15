<!-- Template for design-doc-producer subagent. Sections after S3 are domain-specific — include what applies. -->

# Design Document — <topic>

> Brainstorm slug: `<YYYY-MM-DD>-<slug>`
> Status: **complete** | Artifact: <type> (<creation|change_request>) | Target: `<target-path>`

---

## 1. Problem Statement

<!-- What's broken or missing? Be concrete — not aspirational.
     Include numbered root causes.
     End with "What changes" — one sentence summarizing the shift. -->

---

## 2. Design Principles

<!-- Load-bearing decisions that drove the design. Not aspirational values —
     these are decisions where changing one likely invalidates downstream choices.
     Each principle gets a heading, a paragraph of reasoning, and an **Implication:** line
     showing the downstream effect. -->

---

## 3. Architecture

### 3.1 Flow Graph

<!-- VERBATIM — copy from notepad Memo-ready sections.
     ASCII art preferred — no Mermaid.
     Must show all nodes, transitions, entry points, and loops. -->

### 3.2 Node Specifications

<!-- One subsection per node. Each follows the format:
     Load: <companion files read at this node>
     Do: <numbered actions>
     Don't: <constraints — what the node must avoid>
     Exit: <transition conditions with target nodes> -->

### 3.3 Entry Gates

<!-- Transition conditions table — only include gates that are enforced
     (not every transition, just the ones with preconditions). -->

| Transition | Gate conditions |
|---|---|
| <from → to> | <preconditions that must be true> |

---

<!-- ═══════════════════════════════════════════════════════════════════
     Sections 4 through N are domain-specific. Include what applies
     to the artifact(s) being designed. Common patterns listed below.
     Number sequentially from 4.
     ═══════════════════════════════════════════════════════════════════ -->

<!-- ## 4. Notepad Architecture
     Include for skills with working memory (notepads, structured state).
     Cover: zones/sections, evolution pattern, distillation rules,
     verbatim conventions, compaction safety. -->

<!-- ## N. Naming Conventions
     Include for artifacts with naming decisions.
     Cover: pattern, segment breakdown, taxonomy source, validation rules, examples. -->

<!-- ## N. Companion Model
     Include for artifacts with tier 2+ companions.
     Cover: tier definitions, promotion rules, detection mechanisms,
     file inventory with load points. -->

<!-- ## N. Output Production
     Include for artifacts that dispatch subagents or produce multiple outputs.
     Cover: output types, subagent dispatch model, placement rules,
     failure handling. -->

<!-- ## N. Supporting Infrastructure
     Include for artifacts with tooling needs (scripts, CI, validation).
     Cover: script inventory, subcommands, integration points. -->

---

## N-2. Accepted Tensions

<!-- Trade-offs acknowledged and accepted — not resolved, not deferred indefinitely.
     Each tension has a "revisit when" trigger so it's not forgotten. -->

| Tension | Decision | Revisit when |
|---|---|---|
| <tension> | <accepted/deferred> | <trigger for revisiting> |

---

## N-1. Dependencies

<!-- What this artifact consumes from and produces for other artifacts.
     Direction is relative to this artifact. -->

| Artifact | Direction | Contract |
|---|---|---|
| <artifact> | <consumes/produces for> | <contract> |

---

## N. What Changed From Original

<!-- Include only for change_requests — numbered changes with rationale.
     Documents post-memo resolutions from the brainstorm continuation. -->

| # | Change | Rationale |
|---|---|---|
| <n> | <what changed> | <why> |
