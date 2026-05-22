# Agent Taxonomy

Naming and metadata rules for agents. The controlled vocabulary for each slug slot lives in [`registry/AGENT_VOCABULARY.md`](../registry/AGENT_VOCABULARY.md). The inventory of agents currently in the repo lives in [`registry/AGENTS_REGISTRY.md`](../registry/AGENTS_REGISTRY.md). This file defines the *shape*; vocabulary holds the *values*; registry holds the *inventory*.

## Naming convention

`{domain}-{subdomain}-{scope}-{role}` — lowercase-hyphenated. All four slots required.

- **`domain`** — ecosystem (e.g., `synapse`).
- **`subdomain`** — category within the domain (e.g., `skill`).
- **`scope`** — noun naming what the agent operates on (e.g., `companion`, `eval`, `readme`).
- **`role`** — agentive noun naming what the agent is (e.g., `judge`, `auditor`, `writer`).

## Examples

| Slug | Description |
|------|-------------|
| `synapse-skill-companion-auditor` | Audits skill companion files against load-trigger and modularity rules |
| `synapse-skill-design-grader` | Grades a SKILL.md on design-principle dimensions |

**Anti-patterns:**

| Slug | Why it's wrong |
|------|----------------|
| `synapse-skill-judge-design` | Slot order reversed — reads "the judge design" (Yoda speak). Should be `design-judge`. |
| `synapse-skill-design-validate` | `validate` is a verb. Role slot must be an agentive noun (`validator`). |

## Frontmatter

Required fields on every agent `.md` file:

```yaml
name: <slug>           # must equal filename AND match {domain}-{subdomain}-{scope}-{role}
domain: <value>
subdomain: <value>
scope: <noun>          # what the agent operates over
role: <noun>           # what the agent IS
```

## Tags

Freeform — no controlled list. Use lowercase, hyphenated multi-word tags (e.g., `blind-generation`, `conformance-testing`).
