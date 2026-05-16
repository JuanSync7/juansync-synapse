# Skill Vocabulary

Controlled values for the four slug slots defined in [`taxonomy/SKILL_TAXONOMY.md`](../taxonomy/SKILL_TAXONOMY.md): `{domain}-{subdomain}-{scope}-{role}`.

These values apply to **skills only** — they are NOT shared with agents, protocols, or tools. Each artifact type has its own independent slot vocabulary.

When creating a new skill, pick values from the tables below. If nothing fits, propose a new row in this file in the same PR — do not invent ad hoc values.

## Domains

| Domain | Description |
|--------|-------------|
| `synapse` | Framework-internal skills shipped by ai-synapse |
| `docs` | User-facing documentation skills |

## Subdomains

| Subdomain | Description |
|-----------|-------------|
| `router` | Cross-cutting routing/orchestration skills (artifact-creator, gatekeeper, eval-writer, suite-validator) |
| `skill` | Skills that operate on skill artifacts (skill-improver) |
| `claim` | Claim-based docs (identity, style, principle, decision sub-types) |

## Scopes

| Scope | Description |
|-------|-------------|
| `artifact` | Operates over any artifact type (skill, agent, protocol, tool) |
| `eval` | Operates over EVAL.md generation |
| `suite` | Operates over multi-artifact suites (external/) |
| `skill` | Operates over a single SKILL.md |
| `doc` | Operates on a single markdown doc |

## Roles

| Role | Description |
|------|-------------|
| `brainstormer` | Explores an idea before commitment to build |
| `creator` | Scaffolds a new artifact from scratch |
| `gatekeeper` | Certifies an artifact against the promotion bar |
| `writer` | Generates a specific artifact file (e.g., EVAL.md) |
| `validator` | Asserts conformance against rules |
| `improver` | Iterates on an existing artifact against its eval |
| `shrinker` | Lossless density increase against a kept-claim set |
