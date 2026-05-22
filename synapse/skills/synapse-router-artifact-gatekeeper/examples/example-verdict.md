# Example Verdicts — synapse-router-artifact-gatekeeper

Five worked examples — three for skills, one for an agent, one for a protocol. Each shows the full certification report output, illustrating the expected format for each artifact type and verdict.

---

## Example 1 — APPROVE

**Input:** `/synapse-router-artifact-gatekeeper synapse/skills/synapse-router-artifact-creator --score 84`

---

```
VERDICT: APPROVE

## Certification Report — synapse-router-artifact-creator

### Structural                    ✓
- [x] SKILL.md exists
- [x] EVAL.md exists
- [x] Frontmatter complete (name, description, domain, intent)
- [x] domain `skill.create` in SKILL_TAXONOMY.md
- [x] intent `write` in SKILL_TAXONOMY.md
- [x] tags well-formed: [skill, creation, scaffolding, eval]
- [x] user-invocable: true
- [x] argument-hint present: "<skill-name> [--domain <domain>]"
- [x] Domain README (synapse/skills/README.md) has row for synapse-router-artifact-creator
- [x] Name globally unique — no collision in registry/SKILL_REGISTRY.md

### Quality                       ✓
- [x] Description is routing contract ("Use when building a new skill from scratch...")
- [x] Eval score ≥ 80 (provided: 84)
- [x] SKILL.md under 500 lines (412 lines)
- [x] Instructions trace to failure modes
- [x] Wrong-Tool Detection section present
- [x] references/ used correctly (skill-design-principles.md loaded at Phase 3)

### Registry                      ✓
- [x] Not pipeline-routable — inventory entry present with explanatory comment
- [x] No stage_name conflict applicable
```

---

## Example 2 — REVISE

**Input:** `/synapse-router-artifact-gatekeeper synapse/skills/synapse-router-eval-writer --score 76`

---

```
VERDICT: REVISE

## Certification Report — synapse-router-eval-writer

### Structural                    ✓
- [x] SKILL.md exists
- [x] EVAL.md exists
- [x] Frontmatter complete (name, description, domain, intent)
- [x] domain `skill.eval` in SKILL_TAXONOMY.md
- [x] intent `generate` in SKILL_TAXONOMY.md
- [x] tags well-formed: [eval, skill, test-prompts, output-criteria]
- [x] user-invocable: true
- [x] argument-hint present: "<skill-path>"
- [x] Domain README (synapse/skills/README.md) has row for synapse-router-eval-writer
- [x] Name globally unique — no collision in registry/SKILL_REGISTRY.md

### Quality                       ✗
- [x] Description is routing contract
- [ ] Eval score ≥ 80 (provided: 76 — below threshold)
- [x] SKILL.md under 500 lines (338 lines)
- [x] Instructions trace to failure modes
- [x] Wrong-Tool Detection section present
- [x] references/ used correctly

### Registry                      ✓
- [x] Not pipeline-routable — inventory entry present with explanatory comment

## Gaps

1. **Eval score below threshold (76/80):** Run `/synapse-skill-skill-improver synapse/skills/synapse-router-eval-writer` to identify and fix quality gaps. Re-run `/synapse-router-artifact-gatekeeper` with the updated score once it reaches ≥ 80.
```

---

## Example 3 — REJECT

**Input:** `/synapse-router-artifact-gatekeeper src/skills/docs/write-scope-docs`

*(EVAL.md is absent in this scenario)*

---

```
VERDICT: REJECT

## Certification Report — write-scope-docs

### Structural                    ✗
- [x] SKILL.md exists
- [ ] EVAL.md exists — ABSENT (REJECT)
- [x] Frontmatter complete (name, description, domain, intent)
- [x] domain `docs.scope` in SKILL_TAXONOMY.md
- [x] intent `write` in SKILL_TAXONOMY.md
- [x] tags well-formed
- [x] user-invocable: true
- [x] argument-hint present
- [x] Domain README has row for write-scope-docs
- [x] Name globally unique

### Quality                       — skipped (EVAL.md absent)

### Registry                      — skipped (EVAL.md absent)

## Gaps

1. **EVAL.md missing:** No certification is possible without an EVAL.md. Run `/synapse-router-eval-writer skill src/skills/docs/write-scope-docs` to generate one, then re-run `/synapse-router-artifact-gatekeeper` with a measured eval score.
```

---

## Example 4 — Agent APPROVE

**Input:** `/synapse-router-artifact-gatekeeper synapse/agents/synapse/skill-eval/synapse-skill-eval-judge.md`

---

```
VERDICT: APPROVE

## Certification Report — synapse-skill-eval-judge (agent)

### Structural                    ✓
- [x] Agent file exists and is non-empty
- [x] Frontmatter complete (name, description, domain, role)
- [x] domain `synapse` in AGENT_TAXONOMY.md
- [x] role `judge` in AGENT_TAXONOMY.md
- [x] tags well-formed: [output-criteria, binary-grading, impartial]
- [x] Name follows `<domain>-<concern>-<role>` convention
- [x] Name globally unique in AGENTS_REGISTRY.md
- [x] Listed in AGENTS_REGISTRY.md with correct description and consumers
- [x] Domain README (synapse/agents/synapse/skill-eval/README.md) has row for synapse-skill-eval-judge

### Quality                       ✓
- [x] Clear persona ("impartial judge" mindset in opening paragraph)
- [x] Instructions trace to failure modes
- [x] Under 300 lines (98 lines)
- [x] Consumer skills identified (synapse-router-artifact-creator, synapse-router-eval-writer, synapse-skill-skill-improver)
- [x] No user-facing language

### Registry                      N/A
```

---

## Example 5 — Protocol REVISE

**Input:** `/synapse-router-artifact-gatekeeper synapse/protocols/observability/synapse-observability-execution-trace.md`

---

```
VERDICT: REVISE

## Certification Report — synapse-observability-execution-trace (protocol)

### Structural                    ✓
- [x] Protocol file exists and is non-empty
- [x] Frontmatter complete (name, description, domain, subdomain, subject, kind, version)
- [x] domain `synapse` in PROTOCOL_TAXONOMY.md
- [x] subdomain `observability` in PROTOCOL_TAXONOMY.md
- [x] kind `trace` in PROTOCOL_TAXONOMY.md
- [x] tags well-formed: [execution-trace, self-reported, subagent-observability]
- [x] Mental model paragraph present
- [x] Contract section present
- [x] Failure assertion present
- [x] Domain README (synapse/protocols/observability/README.md) has row for synapse-observability-execution-trace

### Conformance                   ✗
- [x] Contract is unambiguous
- [x] Contract uses imperative language
- [ ] Failure assertion is imperative — assertion describes the failure but does not instruct the agent to output `PROTOCOL FAILURE: synapse-observability-execution-trace — [reason]`
- [x] Zero-overhead design confirmed

### Registry                      N/A

## Gaps

1. **Failure assertion not imperative:** The failure assertion describes what goes wrong but does not instruct the agent to output the standardized `PROTOCOL FAILURE: synapse-observability-execution-trace — [reason]` tag. Rewrite as an imperative instruction per `synapse/protocols/observability/synapse-observability-failure-reporting-schema.md`.
```
