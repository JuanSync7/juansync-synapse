# Decision Memo — <topic>

<!--
  Memo structure is SHAPE-SPECIFIC. Populate only the sections for the outcome shape classified at Done Signal.
  Produced ONCE at Done Signal from the notepad — not drafted incrementally.

  For Defer and Abandon outcomes: do NOT produce a full memo. Record a short status note in meta.yaml instead.
-->

**Shape:** Decision | Plan | Spec | Reframe | Decompose
**Type:** decision | exploratory | problem | creative | planning
**Session:** `<YYYY-MM-DD-<slug>>`

---

## For shape = Decision

### Question
<the decision being made — what, specifically, was being chosen>

### Options considered
- **Option A:** <short description>
- **Option B:** <short description>
- **Option C:** <short description, if applicable>

### Tradeoffs (per lens)

| Lens | Option A | Option B | Option C |
|---|---|---|---|
| Stakeholder | <assessment> | <assessment> | <assessment> |
| Alternative | <assessment> | <assessment> | <assessment> |
| <type-lens 1> | <assessment> | <assessment> | <assessment> |
| <type-lens 2> | <assessment> | <assessment> | <assessment> |

### Recommendation
<the picked option, with the single strongest reason>

### Rationale
<1-3 paragraphs on why this option over the others, citing the lens tradeoffs>

### Risks accepted
<what we're accepting along with this choice — the known downsides we decided to live with>

---

## For shape = Plan

### Goal
<what the plan achieves>

### Steps
1. **Step 1:** <description, dependencies, who owns it>
2. **Step 2:** ...
3. **Step 3:** ...

### Sequencing rationale
<why this order — what depends on what, what can parallelize, what must come first>

### Known risks per step
- Step 1: <risk + mitigation>
- Step 2: <risk + mitigation>

### Success criteria
<how we'll know each step succeeded; what triggers moving to the next>

---

## For shape = Spec

### What to build
<high-level description of the artifact>

### Requirements
- **Functional:** <what it must do>
- **Non-functional:** <how well it must do it — performance, reliability, usability>

### Constraints
<hard limits that scope the design>

### Audience / users
<who consumes this artifact, what they need from it>

### Acceptance criteria
<concrete, testable conditions for "this is done">

---

## For shape = Reframe

### Original framing
<how the user came in — the question they first asked>

### Revised framing
<the question we're actually answering instead>

### Why the reframe
<what surfaced during the brainstorm that showed the original framing was wrong>

### What's next
<does the user need a new brainstorm on the revised framing, or is the reframe itself the deliverable?>

---

## For shape = Decompose

### Original topic
<the too-big question>

### Sub-topics (for separate brainstorms)
- **Sub-topic 1:** <short description, why independent>
- **Sub-topic 2:** ...
- **Sub-topic 3:** ...

### Recommended sequence
<which sub-topic to brainstorm first, and why — what unblocks the others>

### Dependencies between sub-topics
<where decisions in one affect another>

---

## Common Sections (all shapes)

### What surfaced along the way
<insights, tensions, or observations that aren't the core decision but matter for context>

### Open questions
<things still uncertain — known unknowns the user should be aware of>

### You might consider next
<!-- PROSE suggestion, NOT a deterministic shape→skill map. Examples:
     - "If you want to turn this Spec into requirements, `/write-spec-docs` is a good next step."
     - "This Plan is a good candidate for `/build-plan` to decompose into tasks."
     - "For the Decision, just go execute. No handoff needed."
     - "If this Reframe is the deliverable, no handoff; if you want to brainstorm the revised question, invoke `/brainstorm` again."
-->

### Artifacts
- Notepad: `<path>/notepad.md`
- Meta: `<path>/meta.yaml`

---

<!-- ═══════════════════════════════════════════════════════════════════
     PER-THREAD MEMO — used when coach offers multi-memo output
     for planning/decompose brainstorms with deliverable-shaped threads.
     One file per thread: T1-<slug>.md, T2-<slug>.md, etc.
     Summary memo still produced alongside these.
     ═══════════════════════════════════════════════════════════════════ -->

# Thread Memo — <thread title>

> Thread: T<n> | Session: `<YYYY-MM-DD-<slug>>` | Summary memo: `<path>`

---

## What this is
<!-- One paragraph: what deliverable/component/file this thread represents. -->

## Why it matters
<!-- What problem this solves or what breaks without it. -->

## Key decisions
<!-- Resolved positions from this thread's Zone 2 section.
     Each bullet self-contained enough for an implementor to act on. -->

## Edge cases considered
<!-- From lens rotation — what was pressure-tested and how it's handled. -->

| Edge case | Handling |
|---|---|
| <edge case> | <how> |

## Verbatim blocks
<!-- VERBATIM -->
<!-- Structural content copied exactly from notepad Zone 2.
     Schemas, interfaces, decision tables, comparison matrices. -->

## Dependencies
<!-- What this thread depends on (other threads, external systems). -->

## Open questions
<!-- Remaining uncertainties for the implementor. -->
