# Score Card Format

Use these formats when presenting results at [END]. Separate structural, behavioral, and execution scores.

---

## Structural Pass

```
Structural Cycle 1: 7/11 baseline (+ 2/5 extended, + 3/4 EVAL-S, + 6/9 flow-graph)
Failing:
  - description not third-person (line 3)
  - EVAL-S02: no boundary behavior guidance (missing section)
  - flow-graph: per-node Don'ts missing on [B] and [C]
→ fixing...

Structural Cycle 2: 11/11 (+ 5/5 extended, + 4/4 EVAL-S, + 9/9 flow-graph) → structural pass complete
```

Distinguish baseline, extended, EVAL-S, and flow-graph conformance scores as separate tallies.

---

## Behavioral Pass

```
Behavioral Cycle 1: 42/60 criteria passed across 6 prompts
Failing patterns:
  - EVAL-O03 fails on all naive prompts (traceability incomplete)
  - EVAL-O07 fails on adversarial prompt (didn't push back on compound scope)
Root causes:
  - Missing verification step for traceability
  - No instruction for scope-splitting when input is compound
→ fixing SKILL.md...

Behavioral Cycle 2: 58/60 → improving
Behavioral Cycle 3: 60/60 → behavioral pass complete
```

---

## Execution Pass (when EVAL-E criteria exist)

```
Execution Cycle 1: 3/5 EVAL-E criteria passed
Failing:
  - EVAL-E02: Phase 1 subagents dispatched with model: opus (should be sonnet)
  - EVAL-E05: Phase 1 prompt includes acceptance criteria (context isolation violated)
Root causes:
  - No explicit model instruction in Phase 1 dispatch
  - Phase 1 prompt template includes AC by default
→ fixing SKILL.md...

Execution Cycle 2: 5/5 → execution pass complete
```
