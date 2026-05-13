---
name: synapse-skill-eval-auditor
description: "Execution criteria for orchestration patterns (EVAL-Exx)"
domain: synapse
subdomain: skill
scope: eval
role: auditor
tags: [execution-criteria, orchestration, trace-grading]
---

# Skill Eval Auditor

Generates binary pass/fail criteria for evaluating **how a skill orchestrates its execution** — not what it produces. You look for orchestration patterns in the SKILL.md and produce EVAL-E criteria that can be graded against a self-reported execution trace.

Not all skills have execution criteria. Only skills with orchestration patterns need them.

## What You See

- The full SKILL.md of the target skill
- Any companion files that describe workflow details (e.g., subagent prompt templates)

## What You Look For

Scan the SKILL.md for these orchestration patterns:

### Subagent Dispatch
Does the skill dispatch Agent() calls for specific subtasks?
- Per-item dispatch (one agent per file, module, section) vs batch
- Parallel vs sequential dispatch
- What context each subagent receives

### Model Selection
Does the skill specify different models for different phases?
- Mechanical tasks on sonnet vs judgment tasks on opus
- Explicit `model:` parameter on Agent dispatch

### Phase Gates
Does the skill have precondition checks before advancing phases?
- Input validation (files exist, required fields present)
- Output validation (phase N output meets criteria before phase N+1)

### Conditional Shortcuts
Does the skill skip phases based on input characteristics?
- Thresholds (e.g., "<10 files → skip subagent dispatch")
- Fallbacks (e.g., "no spec → use eng-guide → use docstrings")

### Context Isolation
Does the skill deliberately exclude information from subagent prompts?
- Separation of concerns (e.g., Phase 1 agents don't see acceptance criteria)
- Bias prevention (e.g., test prompt generator doesn't see SKILL.md body)

## When to Return Empty

If the skill has **none** of the above patterns (single-phase, no subagent dispatch, no model selection, no conditional logic), return:

```
No execution criteria — this skill has no orchestration patterns.
```

The caller will omit the Execution Criteria section from EVAL.md.

## Output Format

Use this exact format for each criterion:

```markdown
- [ ] **EVAL-Exx:** [Short descriptive name]
  - **Test:** [How to verify from the execution trace — must be observable, not inferred]
  - **Fail signal:** [Observable symptom in the trace when criterion is not met]
```

## Worked Example

From write-test-coverage (a skill with two-phase subagent dispatch):

```markdown
- [ ] **EVAL-E01:** Phase 1 subagents dispatch per test file, not as a single-pass scan
  - **Test:** For repos with >=10 test files, observe that the skill spawns one Agent call per test file (or per small batch). Each Agent call targets a specific test file path.
  - **Fail signal:** A single Agent call or inline Read loop processes all test files in one context — no per-file dispatch observed.

- [ ] **EVAL-E02:** Phase 1 subagents use `model: sonnet` (mechanical extraction tier)
  - **Test:** Inspect each Phase 1 Agent dispatch. The `model` parameter is explicitly set to `sonnet`.
  - **Fail signal:** Phase 1 subagents dispatch without an explicit `model` parameter (inheriting opus) or explicitly set to `opus`.

- [ ] **EVAL-E03:** Phase 2 cross-matching runs on `model: opus` (judgment tier)
  - **Test:** If Phase 2 is dispatched as a subagent, verify `model` is set to `opus`. If Phase 2 runs in the main context, verify the main context is opus-tier.
  - **Fail signal:** Phase 2 cross-matching dispatches with `model: sonnet` or another non-frontier model.

- [ ] **EVAL-E04:** Small repo shortcut skips subagent dispatch for <10 test files
  - **Test:** For repos with fewer than 10 test files, observe that the skill performs a single-pass scan without spawning per-file subagents.
  - **Fail signal:** Per-file subagents are dispatched for a repo with only 3-5 test files — unnecessary orchestration overhead.

- [ ] **EVAL-E05:** Phase 1 subagents receive no acceptance criteria
  - **Test:** Inspect the prompt sent to each Phase 1 subagent. It contains the test file path and language conventions but no AC list, spec content, or eng-guide content.
  - **Fail signal:** A Phase 1 subagent prompt includes acceptance criteria, spec excerpts, or eng-guide content — violating the two-phase context isolation invariant.
```

**Pattern mapping:** E01 = subagent dispatch, E02-E03 = model selection, E04 = conditional shortcut, E05 = context isolation.

## Quality Checks

Before finalizing:
- [ ] Every criterion maps to a specific orchestration pattern in the SKILL.md
- [ ] Criteria are observable from an execution trace (not from inspecting the output)
- [ ] No criterion duplicates what EVAL-O already covers (output quality is EVAL-O's job)
- [ ] If the skill has no orchestration patterns, return empty rather than inventing criteria
- [ ] Criteria use the EVAL-Exx prefix (not EVAL-Oxx or EVAL-Sxx)
