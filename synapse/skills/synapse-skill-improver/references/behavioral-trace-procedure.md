# Behavioral Trace Procedure

How to run a skill on test prompts, grade outputs, trace failures back to SKILL.md instructions, and decide when to stop.

---

## Running the Skill

For each test prompt from EVAL.md, spawn a subagent:

```
Execute this task using the skill at [path-to-skill]:
- Task: [test prompt from EVAL.md]
- Save output to: [workspace]/run-[N]/prompt-[ID]/output/
```

Set `model:` explicitly on every dispatch.

### Trace Injection (conditional)

If the target skill's EVAL.md contains an `## Execution Criteria` section, append to the subagent prompt:

```
---
After completing the task above, append an `## Execution Trace` section to your response. Record in YAML format:
- phases_executed: list of phases that ran
- agents_dispatched: for each Agent() call, record phase, purpose, target, and model
- workflow_decisions: for each key branching decision, record what was decided, what was chosen, and why
- precondition_checks: for each input validation, record what was checked and pass/fail
- context_isolation: boolean flags for what was deliberately excluded from subagent prompts
Nesting: shallow (trace only top-level execution, not recursive subagent traces).
---
```

If no Execution Criteria section exists in EVAL.md, do not inject the trace protocol.

---

## Grading

### Output Grading (EVAL-O)

For each output, evaluate every EVAL-Oxx criterion (binary pass/fail):

```markdown
| Prompt | EVAL-O01 | EVAL-O02 | EVAL-O03 | ... | Pass Rate |
|--------|----------|----------|----------|-----|-----------|
| Naive 1 | PASS | FAIL | PASS | ... | 8/10 |
| Expert 1 | PASS | PASS | PASS | ... | 10/10 |
| Adversarial 1 | FAIL | FAIL | PASS | ... | 5/10 |
```

### Execution Grading (EVAL-E — when Execution Criteria exist)

For each output that includes an execution trace, evaluate every EVAL-Exx criterion:

```markdown
| Prompt | EVAL-E01 | EVAL-E02 | EVAL-E03 | ... | Pass Rate |
|--------|----------|----------|----------|-----|-----------|
| Naive 1 | PASS | PASS | N/A | ... | 2/2 |
| Expert 1 | PASS | FAIL | PASS | ... | 4/5 |
```

If the execution trace is missing (subagent did not append it), mark all EVAL-E criteria as FAIL for that prompt and note "trace missing" as the root cause.

---

## Tracing Failures

### Output Failures → SKILL.md Instructions

When an output criterion fails, trace backward:

1. **What failed?** — e.g., EVAL-O03 "traceability matrix is complete" failed for Naive 1
2. **What's in the output?** — The matrix is missing 3 requirements
3. **What instruction should have prevented this?** — The skill says "build the traceability matrix at the end" but doesn't say "verify every requirement appears"
4. **Fix** — Add verification instruction to SKILL.md

### Execution Failures → Dispatch Instructions

When an execution criterion fails, trace backward:

1. **What failed?** — e.g., EVAL-E02 "Phase 1 subagents use model: sonnet" failed
2. **What's in the trace?** — The trace shows model: opus for Phase 1 dispatches
3. **What instruction should have prevented this?** — The skill says "dispatch per-file agents" but doesn't specify model
4. **Fix** — Add explicit `model: sonnet` instruction to the dispatch section of SKILL.md

---

## Stop Conditions

- **All pass** — all output criteria pass across all test prompts → behavioral pass complete
- **Ceiling** — pass rate is stable across two consecutive cycles (same N/M) → surface remaining failures as blockers, do not run a third cycle
- **No improvement** — after three behavioral cycles with no improvement → stop and report
