# Skill Taxonomy

Naming and metadata rules for skills. The controlled vocabulary for each slug slot lives in [`registry/SKILL_VOCABULARY.md`](../registry/SKILL_VOCABULARY.md). The inventory of skills currently in the repo lives in [`registry/SKILL_REGISTRY.md`](../registry/SKILL_REGISTRY.md). This file defines the *shape*; vocabulary holds the *values*; registry holds the *inventory*.

## Naming convention

`{domain}-{subdomain}-{scope}-{role}` — lowercase-hyphenated. All four slots required.

- **`domain`** — ecosystem (e.g., `synapse`, `docs`).
- **`subdomain`** — category within the domain (e.g., `skill`, `router`).
- **`scope`** — noun naming what the skill operates on (e.g., `artifact`, `postmortem`, `eval`).
- **`role`** — agentive noun naming what the skill is (e.g., `writer`, `reviewer`, `gatekeeper`).

## Examples

| Slug | Description |
|------|-------------|
| `synapse-router-artifact-gatekeeper` | Certifies any artifact type against the promotion bar |
| `synapse-skill-skill-improver` | Iterates on an existing skill against its EVAL.md |

**Anti-patterns:**

| Slug | Why it's wrong |
|------|----------------|
| `synapse-eval-writer` | Missing subdomain; `eval` placed in the subdomain slot but it's actually the scope. Should be `synapse-router-eval-writer`. |
| `synapse-skill-skill-improve` | `improve` is a verb. Role slot must be an agentive noun (`improver`). |

## Frontmatter

Required fields on every `SKILL.md`:

```yaml
name: <slug>           # must equal directory name AND match {domain}-{subdomain}-{scope}-{role}
domain: <value>
subdomain: <value>
scope: <noun>          # what the skill operates over
role: <noun>           # what the skill IS
```

## Tags

Freeform — no controlled list. Use lowercase, hyphenated multi-word tags (e.g., `test-planning`, `source-of-truth`).
