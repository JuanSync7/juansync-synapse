# src

Adopter artifacts for AI-Synapse. Framework artifacts live in [`synapse/`](../synapse/) — this directory holds the artifacts owned by this specific repo (or by an adopter that uses ai-synapse as a framework).

## [skills/](skills/)

User-invocable recipes organized by domain.

| Domain | Description |
|--------|-------------|
| [code/](skills/code/) | Code generation and testing |
| [creative/](skills/creative/) | Visual and interactive output |
| [docs/](skills/docs/) | Documentation authoring pipeline |
| [frameworks/](skills/frameworks/) | Technology-specific skills |
| [integration/](skills/integration/) | External service integrations (submoduled suites) |
| [meta/](skills/meta/) | Adopter meta-utilities (e.g. brainstorm) |
| [optimization/](skills/optimization/) | Iterative improvement loops |

## [agents/](agents/)

Internal recipes dispatched by skills — not user-invocable.

| Domain | Description |
|--------|-------------|
| [docs/](agents/docs/) | Agents for documentation review and writing |

## [protocols/](protocols/)

Shared conventions and schemas. Adopter protocols only — framework protocols (memory, observability) live in [`synapse/protocols/`](../synapse/protocols/).

(no adopter protocols yet)

## [tools/](tools/)

Mechanical capabilities. Adopter tools only — framework tools live in [`synapse/tools/`](../synapse/tools/).

(no adopter tools yet)
