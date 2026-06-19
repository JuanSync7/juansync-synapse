# Script Taxonomy

Controlled vocabulary for script metadata. When creating a new script, pick `audience`, `action`, and `scope` from the tables below. If nothing fits, propose an addition to this file — do not invent ad hoc values.

## Audiences

| Audience | Description |
|----------|-------------|
| `consumer` | End users loading synapses into their environment |
| `contributor` | People creating or modifying artifacts |
| `maintainer` | Repo hygiene, drift detection, structural repair |
| `automation` | CI/CD pipelines and scheduled jobs (reserved) |

## Actions

| Action | Description |
|--------|-------------|
| `install` | Put synapses into a harness or environment |
| `create` | Scaffold new artifacts or pathways |
| `inspect` | Read-only analysis — list, validate, audit, doctor |
| `repair` | Write operations that fix drift or clean state |
| `release` | Cut, promote, or verify version tags and releases |

## Scopes

| Scope | Description |
|-------|-------------|
| `synapse` | Individual artifacts (skills, agents, protocols, tools) |
| `pathway` | Named bundles of synapses |
| `repo` | Repository structure (registries, READMEs, taxonomies) |
| `harness` | Installed symlinks in target environment (claude, codex, gemini) |
| `identity` | Identity files (SOUL.md, STAKEHOLDER.md) |

## Tags

Freeform — no controlled list. Use lowercase, hyphenated multi-word tags.
