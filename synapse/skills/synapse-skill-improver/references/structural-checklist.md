# Structural Checklist

Score every item as PASS or FAIL. List each failure with a one-line reason and the line number in SKILL.md where the fix applies.

---

## Baseline Checklist

### Description (frontmatter)
- [ ] Written in third person ("Processes X" not "I can help with X")
- [ ] Includes WHAT (specific capabilities) and WHEN (trigger scenarios/keywords)
- [ ] Specific enough for skill discovery — no vague verbs like "helps with" or "assists"

### Body
- [ ] SKILL.md body is under 500 lines
- [ ] No time-sensitive information (no dates, version cutoffs, "currently X")
- [ ] Consistent terminology — one term per concept, used throughout
- [ ] Concrete examples present — not abstract descriptions of what examples would look like
- [ ] File references are one level deep (SKILL.md → reference.md, not deeper)

### Structure
- [ ] Progressive disclosure: essential content in SKILL.md, detail in companion files
- [ ] Workflows use clear numbered steps or checklists
- [ ] No Windows-style paths (`scripts/helper.py`, not `scripts\helper.py`)

### Progress & Visibility (conditional — only if skill has multiple phases OR dispatches agents)
- [ ] Multi-step skills have a Progress Tracking section with explicit TaskCreate examples
- [ ] Skills that dispatch agents require `model:` set explicitly on every Agent dispatch

---

## Extended Criteria

- [ ] No internal redundancy — the same instruction does not appear in two places
- [ ] DRY within body — if guidance appears in both a "do this" and "don't do this" form, keep only one
- [ ] Good/bad contrast examples — examples show both correct and incorrect forms
- [ ] Input/decision points are prioritized — grouped or tiered so the agent knows what to address first
- [ ] All format examples have concrete filled-in content, not just empty templates

---

## Principles Alignment
<!-- Source of truth: synapse-router-artifact-creator/references/design-principles-skill.md
     Update these criteria when the source principles change. -->

- [ ] Mental model present — skill opens with a conceptual framing paragraph before any rules or workflow steps
- [ ] Description is trigger-only — frontmatter description contains trigger conditions/keywords, not a workflow summary or capability list
- [ ] Scope boundary stated — skill explicitly says what it does NOT do, or names the sibling skill that handles the adjacent case
- [ ] Instructions are traceable — each major instruction can be linked to a failure mode (what goes wrong without it); flag instructions with no apparent failure consequence
- [ ] Policy/procedure balance — workflow steps that involve judgment use policy framing ("when X, prioritize Y because...") rather than rigid mechanical sequences
- [ ] Preconditions checked — if the skill requires input artifacts, there is an explicit check-and-fail instruction, not silent assumption
- [ ] Token-budget boundary correct — detail needed only at one decision point lives in a companion file, not inline in SKILL.md body (distinct from the baseline "progressive disclosure" check which verifies companion files exist; this checks the always-on vs on-demand split is right)
- [ ] Tone matches function — constraints, gates, and prohibitions use commitment language (MUST/NEVER/DO NOT); judgment calls and coaching use policy language. Flag enforcement points using soft language ("should", "consider", "ideally") or coaching sections using unnecessary commitment language

---

## Flow-Graph Conformance
<!-- Source of truth: synapse-router-artifact-creator/references/flow-skill.md
     Read the pattern file to understand the full specification behind each item. -->

- [ ] Top-level sections present: MUST, MUST NOT, Entry, Flow (Wrong-Tool Detection also expected)
- [ ] Node IDs explicit and unique — every flow node has a `### [ID] Name` heading
- [ ] Per-node Don'ts co-located — guardrails appear inside their node, not extracted into a global section. Exception: some nodes may genuinely have no guardrails — Don't is the only section that can be absent.
- [ ] Exit conditions explicit — every node has an Exit block with labeled edges and conditions on each edge
- [ ] Self-loops declared — any iteration that stays on the same node has an explicit `→ [X] : <condition>` self-loop in the Exit block
- [ ] [END] is a real node — has Do steps (output, cleanup, summary), Don't guardrails, and no Exit (session ends)
- [ ] Position tracking in MUST — MUST block includes "Record position: `Position: [node-id] — <context>`"
- [ ] Per-node Load declarations — companion files are loaded inside each node at point of use, not consolidated into a global preamble
- [ ] SKILL.md under 500-line hard cap — ~80 lines is the target (advisory, not a gate)
