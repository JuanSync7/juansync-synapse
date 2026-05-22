---
name: synapse-skill-skill-improver
description: "Use when a skill needs quality improvement. Triggered by 'improve this skill', 'fix the skill', 'review skill quality', 'make the skill better'."
domain: synapse
subdomain: skill
scope: skill
role: improver
tags: [skill, quality, score-fix-loop]
user-invocable: true
argument-hint: "[path to SKILL.md] [optional: --structural-only | --behavioral-only]"
---

Applies the autoresearch loop (modify → measure → keep if improved → repeat) to any SKILL.md. Two passes: structural (checklist scoring) and behavioral (run skill on test prompts, grade outputs). The fix is always in SKILL.md — never in the eval criteria.

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

## MUST (every turn)
- Record position: `Position: [node-id] — <context>`
- Create tasks at session start (per Progress Tracking) and update at phase transitions
- Set `model:` explicitly on every subagent dispatch
- Apply structure-preserving edit rules when fixing flow-graph targets

## MUST NOT (global)
- Change functional content — only fix items that fail criteria
- Rewrite instructions just to "improve" phrasing — conciseness is itself a quality criterion
- Modify test prompts or EVAL.md criteria to make them pass — the fix is always in SKILL.md
- Guess when domain knowledge is missing — surface as blocker

## Wrong-Tool Detection
- **User wants to create a new skill** → redirect to `/synapse-router-artifact-creator`
- **User wants to generate or regenerate EVAL.md** → redirect to `/synapse-router-eval-writer skill [path]`
- **User wants to run a skill** → invoke the skill directly

## Progress Tracking

At the start, create a task list:

```
TaskCreate: "Pass 1: Structural — score against baseline checklist"
TaskCreate: "Pass 2: Behavioral — run skill on test prompts, grade outputs"
```

Mark each `in_progress` when starting, `completed` when done.

## Entry

### [NEW] Fresh session
Do:
  1. Parse arguments — target SKILL.md path and flags (`--structural-only`, `--behavioral-only`)
  2. Create tasks per Progress Tracking section
Don't: Start scoring without completing [P] precondition check.
Exit:
  → [P] : arguments parsed

## Flow

### [P] Precondition Check
Do:
  1. Verify target SKILL.md exists and is readable
  2. Verify all file references in target skill directory resolve (use `scripts/check-links.sh` or check directly)
  3. Detect structure: flow-graph or prose — if prose, flag as structural finding and recommend `/synapse-router-artifact-creator` for migration
  4. Check for EVAL.md in target directory:
     - **Present** → use its EVAL-Sxx criteria in [S], EVAL-O/EVAL-E criteria and test prompts in [B]
     - **Absent** and behavioral pass needed → offer to dispatch `/synapse-router-eval-writer skill <path>` as isolated subagent (model: sonnet, no session context — bias control)
Don't:
  - Proceed with broken symlinks or unresolvable Load targets — FAIL LOUDLY with paths listed
  - Auto-convert prose to flow-graph — flag the finding, continue scoring against prose checklist
Exit:
  → [S] : default path (or `--structural-only`)
  → [B] : `--behavioral-only` flag set
  → FAIL : target does not exist → redirect to `/synapse-router-artifact-creator`

### [S] Structural Pass
Load: `references/structural-checklist.md`, `references/flow-graph-pattern.md`, `references/writing-conventions.md`, `references/structure-preserving-edits.md`
Do:
  1. Score target against full structural checklist (baseline + extended + principles + flow-graph conformance) plus EVAL-Sxx criteria if EVAL.md exists
  2. List each failing item with one-line reason
  3. Fix SKILL.md to address failures — if fix requires new companion file, dispatch `synapse-skill-companion-writer` (model: sonnet; Load: `agents/synapse-skill-companion-writer.md`, `references/companion-dispatch-protocol.md`)
  4. Re-score — if not at 100%, return to step 2
Don't:
  - Continue past 2 fix cycles on the same failing item — surface as blocker
  - Fix items that pass — do not rewrite passing content
Exit:
  → [S] : failing items remain and < 2 cycles on those items
  → [B] : structural pass complete (unless `--structural-only`)
  → [END] : `--structural-only` flag and structural pass complete

### [B] Behavioral Pass
Load: `references/behavioral-trace-procedure.md`, `references/structure-preserving-edits.md`
Brief: Requires EVAL.md with output criteria and test prompts (verified at [P]).
Do:
  1. Run skill on each test prompt via subagent per trace procedure
  2. Grade outputs against EVAL-O criteria; grade execution traces against EVAL-E criteria if present
  3. Trace each failure back to a specific SKILL.md instruction (or its absence)
  4. Fix SKILL.md to address root causes — apply structure-preserving edits
  5. Re-run and re-grade
Don't:
  - Continue past ceiling (2 consecutive cycles with identical pass rate) — surface as blockers
  - Run more than 3 cycles with no improvement — stop and report
Exit:
  → [B] : score improving and failures remain
  → [END] : all criteria pass OR ceiling reached OR 3 cycles with no improvement

### [END]
Load: `templates/score-card-format.md`
Do:
  1. Present structural score card (if structural pass ran) — separate baseline, extended, EVAL-S, and flow-graph conformance tallies
  2. Present behavioral score card (if behavioral pass ran) — per-prompt per-criterion table
  3. Surface remaining blockers with specific failing items and what's needed to resolve them
  4. Suggest next steps (prose, not deterministic routing)
Don't:
  - End without presenting score cards
  - Auto-route to next skill — suggest, don't dispatch
