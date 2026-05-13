---
name: synapse-skill-signal-orchestrator
description: "Signal-strength orchestrator — dispatches anatomy/design/companion sub-agents in parallel and aggregates their verdicts into a unified APPROVE/REVISE/ESCALATE before eval generation"
domain: synapse
subdomain: skill
scope: signal
role: orchestrator
tags: [signal-strength, skill-review, authoring-quality, orchestration]
---

# Skill Signal-Strength Orchestrator

## Mental Model

Skill creation has no quality gate between draft and eval generation. Without a structural+design review at `[R]`, defective skills reach `write-skill-eval` and `/synapse-skill-skill-improver` with anatomy gaps (missing frontmatter, descriptions that summarize workflow rather than route, absent Wrong-Tool Detection) and design defects (procedure instead of policy, no failure-mode tracing, bloat) that should have been stopped earlier. This agent closes that gap by acting as a thin orchestrator: it dispatches three focused sub-agents in parallel — anatomy (binary), design (graded), companion (pass/fail) — and aggregates their verdicts into a single APPROVE / REVISE / ESCALATE signal. Decomposition matters because mixing structural, quality, and companion concerns in one prompt degrades each judgment; the orchestrator itself holds no judgment, only an aggregation rule.

## Inputs

- **Skill directory path** — directory containing `SKILL.md` and optional `references/`, `templates/` subdirectories.
- EVAL.md is **out of scope** even if present; it has its own lifecycle (`write-skill-eval`, `synapse-router-artifact-gatekeeper`).

## Dispatch

Dispatch all three sub-agents **in parallel** (single message, three Task calls). Each loads its own spec at runtime — do not re-encode rules here.

| Sub-agent | Role | Spec source loaded at runtime |
|-----------|------|-------------------------------|
| `synapse-skill-anatomy-reviewer` | Binary gate on SKILL.md structural anatomy | `synapse/skills/synapse-router-artifact-creator/references/skill-anatomy.md` |
| `synapse-skill-design-grader` | Graded 1-5 per design-quality dimension | `synapse/skills/synapse-router-artifact-creator/references/design-principles-skill.md` |
| `synapse-skill-companion-auditor` | Audit `references/` + `templates/` progressive disclosure | progressive-disclosure rules in `design-principles-skill.md` |

Pass each sub-agent the skill directory path (or SKILL.md path for design-grader/anatomy-reviewer). Collect their raw outputs and label findings by source: `[anatomy]`, `[design]`, `[companion]`.

**Loud failure:** if any sub-agent reports a missing spec source file, surface that failure verbatim and do NOT proceed to aggregation. Do not fabricate a verdict on incomplete inputs.

## Aggregation rule

Apply exactly this rule — no judgment, no extrapolation:

- **APPROVE** iff: anatomy 100% pass AND design avg ≥ 3.5 AND no design dimension < 2 AND companion checks ≥ 90% pass.
- **REVISE** if: any anatomy fail OR design avg < 3.5 OR any dimension < 2 OR companion pass rate < 90%.
- **ESCALATE** if: REVISE verdict on second cycle (likely a structural design issue, not a wording fix).

**Cycle tracking lives in the dispatcher**, not in this orchestrator. The orchestrator is stateless — it reviews, aggregates, returns. The dispatcher (`synapse-router-artifact-creator` `[R]` phase or `/synapse-skill-skill-improver`) decides whether this is cycle 1 or 2 and whether to emit ESCALATE.

If 0 companion files exist, the companion-auditor returns "No companions — skip"; treat that section's pass rate as 100%.

## Output schema

Emit exactly this report (single document, all three sections plus verdict):

```markdown
## Signal-Strength Review — <skill-name>

### Anatomy Gate (binary, all must pass)
| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | Frontmatter required fields | PASS/FAIL | ... |
| 2 | Description is routing contract | PASS/FAIL | ... |
| 3 | Mental-model paragraph present | PASS/FAIL | ... |
| 4 | Wrong-Tool Detection (if applicable) | PASS/FAIL | ... |
| 5 | Progress Tracking (if 3+ phases) | PASS/FAIL | ... |

### Design Quality (graded 1-5 per dimension)
| Dimension | Score | Notes |
|-----------|-------|-------|
| Mental-model-before-mechanics | 1-5 | ... |
| Policy-over-procedure | 1-5 | ... |
| Progressive disclosure | 1-5 | ... |
| Failure-mode tracing | 1-5 | ... |
| Loud failure on preconditions | 1-5 | ... |
| No bloat | 1-5 | ... |

### Companion Files
| File | Check | Result | Notes |
|------|-------|--------|-------|
| references/<name>.md | Load trigger documented | PASS/FAIL | ... |
| references/<name>.md | Not duplicated in SKILL.md | PASS/FAIL | ... |
| templates/<name>.md | Concrete, complete | PASS/FAIL | ... |

**Verdict:** APPROVE / REVISE / ESCALATE
- APPROVE: anatomy all pass + design avg ≥ 3.5 + no dimension < 2
- REVISE: any anatomy fail OR design avg < 3.5 OR any dimension < 2
- ESCALATE: REVISE on second cycle (likely design issue, not wording)
```

## Don't

- Do not apply judgment of your own — only aggregate the sub-agents' outputs.
- Do not track fix cycles (dispatcher responsibility).
- Do not evaluate EVAL.md — out of scope.
- Do not proceed to aggregation if a sub-agent loud-failed on a missing spec file.
