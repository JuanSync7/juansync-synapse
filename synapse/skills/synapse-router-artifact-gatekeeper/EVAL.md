# EVAL.md — synapse-router-artifact-gatekeeper

## Output Criteria

| ID | Criterion | Pass | Fail |
|----|-----------|------|------|
| EVAL-O01 | Verdict is the first line | Output begins with the literal string `VERDICT: APPROVE`, `VERDICT: REVISE`, or `VERDICT: REJECT` — no preamble before it | Any text, heading, or blank line appears before the verdict line |
| EVAL-O02 | Report has three labeled tiers | Output contains headings for Structural, Quality, and Registry tiers (or notes that a tier was skipped with reason) | One or more tiers are absent without explanation |
| EVAL-O03 | Each tier shows per-item checklist | Each tier section contains `[x]` or `[ ]` prefixed items for individual checks | A tier shows only a summary statement without per-item checklist |
| EVAL-O04 | REVISE/REJECT include Gaps section | When verdict is REVISE or REJECT, a `## Gaps` section appears with specific, actionable items | Verdict is REVISE or REJECT but Gaps section is absent or contains only vague statements |
| EVAL-O05 | APPROVE has no open gaps | When verdict is APPROVE, no `[ ]` unchecked items appear in any tier, and Gaps section is omitted or states "None" | Verdict is APPROVE but checklist contains unchecked items or Gaps section lists open items |
| EVAL-O06 | Missing EVAL.md triggers immediate REJECT | When EVAL.md is absent, verdict is REJECT and Quality and Registry tiers are skipped (noted as skipped) | Missing EVAL.md produces REVISE, or Quality/Registry tiers are evaluated despite missing EVAL.md |
| EVAL-O07 | No score → quality tier unverified, verdict ≤ REVISE | When no `--score` is provided, the quality tier is marked `unverified` and the verdict is REVISE or REJECT — never APPROVE | No score provided but verdict is APPROVE, or quality tier is shown as fully passing without a score |
| EVAL-O08 | Name collision → REJECT | When the skill name already exists in `SKILLS_REGISTRY.yaml`, verdict is REJECT | Name collision produces REVISE or APPROVE |
| EVAL-O09 | Score below 80 → at least REVISE on quality tier | When `--score` value is below 80, the eval score check in the quality tier is unchecked `[ ]` and verdict is at least REVISE | Score below 80 is shown as passing or verdict is APPROVE |

---

## Test Prompts

### EVAL-T01 — Missing EVAL.md → REJECT

**Prompt:**
```
/synapse-router-artifact-gatekeeper src/skills/docs/write-scope-docs
```
*(Assume write-scope-docs has a SKILL.md but no EVAL.md in this test scenario)*

**Expected behavior:**
- Verdict is REJECT
- Verdict is the first line of output
- Quality and Registry tiers are skipped (noted as skipped due to missing EVAL.md)
- Gaps section instructs running `/write-skill-eval` to generate EVAL.md

---

### EVAL-T02 — All checks pass with score 84 → APPROVE

**Prompt:**
```
/synapse-router-artifact-gatekeeper synapse/skills/synapse-router-artifact-creator --score 84
```

**Expected behavior:**
- Verdict is APPROVE
- All three tiers show `✓` with all items checked `[x]`
- Gaps section is omitted or states "None"
- No preamble before the verdict line

---

### EVAL-T03 — Score 76, structural clean, not pipeline-routable → REVISE

**Prompt:**
```
/synapse-router-artifact-gatekeeper synapse/skills/synapse-router-eval-writer --score 76
```

**Expected behavior:**
- Verdict is REVISE
- Structural tier passes (`✓`)
- Quality tier shows `✗` with eval score check unchecked `[ ]`
- Registry tier passes (skill is not pipeline-routable, absence of pipeline block is correct)
- Gaps section identifies score below 80 and instructs running `/synapse-skill-skill-improver` to raise it

---

### EVAL-T04 — Name collision with existing registry entry → REJECT

**Prompt:**
```
/synapse-router-artifact-gatekeeper synapse/skills/synapse-router-artifact-creator
```
*(Assume a second skill named `synapse-router-artifact-creator` is being evaluated for promotion, but that name already exists in SKILLS_REGISTRY.yaml)*

**Expected behavior:**
- Verdict is REJECT
- Structural tier shows `✗` with name uniqueness check unchecked `[ ]`
- Gaps section identifies the name collision and requires renaming before promotion
- Quality and Registry tiers may still be evaluated but REJECT stands

---

### EVAL-T05 — EVAL.md present, structural clean, no score → REVISE

**Prompt:**
```
/synapse-router-artifact-gatekeeper synapse/agents/synapse/skill-eval/synapse-skill-eval-judge.md
```
*(No --score argument provided)*

**Expected behavior:**
- Verdict is REVISE
- Structural tier passes (`✓`)
- Quality tier is marked `unverified` (no score available)
- Registry tier is evaluated and passes
- Gaps section instructs providing a score via `/synapse-skill-skill-improver` or auto-research before APPROVE can be issued
