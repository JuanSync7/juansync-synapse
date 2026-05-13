# Agent Vocabulary

Controlled values for the four slug slots defined in [`taxonomy/AGENT_TAXONOMY.md`](../taxonomy/AGENT_TAXONOMY.md): `{domain}-{subdomain}-{scope}-{role}`.

These values apply to **agents only** — they are NOT shared with skills, protocols, or tools. Each artifact type has its own independent slot vocabulary.

When creating a new agent, pick values from the tables below. If nothing fits, propose a new row in this file in the same PR — do not invent ad hoc values.

## Domains

| Domain | Description |
|--------|-------------|
| `synapse` | Framework-internal agents shipped by ai-synapse |

## Subdomains

| Subdomain | Description |
|-----------|-------------|
| `skill` | Agents that operate on skill artifacts |
| `protocol` | Agents that operate on protocol artifacts |
| `meta` | Cross-cutting maintenance agents (readme-maintainer, etc.) |

## Scopes

| Scope | Description |
|-------|-------------|
| `anatomy` | SKILL.md structural anatomy (frontmatter, sections) |
| `companion` | Skill companion files (references/, templates/) |
| `design` | Design-quality dimensions of a SKILL.md |
| `eval` | EVAL.md output and execution criteria |
| `signal` | Signal-strength orchestration / review |
| `readme` | Directory README indexes |

## Roles

| Role | Description |
|------|-------------|
| `auditor` | Per-file/per-section pass-fail audit |
| `grader` | Graded scoring on multiple dimensions |
| `judge` | Impartial binary grader |
| `maintainer` | Keeps an invariant true across changes |
| `orchestrator` | Dispatches sub-agents and aggregates verdicts |
| `prompter` | Generates blind test prompts |
| `reviewer` | Signal-strength reviewer |
| `writer` | Generates the artifact |
