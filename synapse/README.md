# synapse

Framework artifacts — the meta-tools that build, evaluate, and govern skills/agents/protocols. These ship with ai-synapse and are consumed as a dependency by adopter repos. Adopter content lives in [`../src/`](../src/).

## [skills/](skills/)

Framework skills — artifact creation, gatekeeping, eval generation, suite validation, and skill improvement. Flat layout (no subdomains); see [`skills/README.md`](skills/README.md) for the catalog.

## [agents/](agents/)

Internal recipes dispatched by framework skills.

| Domain | Description |
|--------|-------------|
| [synapse/](agents/synapse/) | Ecosystem maintenance plus subdomain agents (skill, skill-eval, protocol, meta) |

## [protocols/](protocols/)

Shared conventions and schemas injected into agent prompts.

| Domain | Description |
|--------|-------------|
| [memory/](protocols/memory/) | External memory conventions |
| [observability/](protocols/observability/) | Execution tracing and failure reporting |

## [tools/](tools/)

Mechanical capabilities used by framework skills.

| Domain | Description |
|--------|-------------|
| [synapse/](tools/synapse/) | Synapse-internal tooling (CR dispatcher) |

## SKILLS_REGISTRY.yaml

Pipeline routing metadata consumed by an adopter-supplied orchestrator skill. Lists pipeline-routable skills with their stage inputs/outputs and dependency edges.
