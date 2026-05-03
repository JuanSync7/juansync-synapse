# Agent Taxonomy

Controlled vocabulary for agent metadata. When creating a new agent, pick `domain` and `role` from the tables below. If nothing fits, propose an addition to this file — do not invent ad hoc values.

Agents follow the `<domain>-<concern>-<role>` naming convention (see GOVERNANCE.md).

## Domains

| Domain | Description |
|--------|-------------|
| `skill` | Skill authoring and companion-file generation |
| `skill-eval` | Skill evaluation and quality assessment |
| `docs` | Document authoring, review, and maintenance |
| `protocol-eval` | Protocol evaluation, signal-strength review, conformance testing |
| `synapse` | Synapse ecosystem management — workflow automation, manifest generation |

## Roles

| Role | Description |
|------|-------------|
| `judge` | Impartial evaluator producing binary pass/fail criteria |
| `prompter` | Generates test inputs blind to implementation |
| `auditor` | Evaluates execution/workflow behavior |
| `writer` | Produces content from a brief or specification |
| `reviewer` | Validates output against input contract and quality criteria |

## Tags

Freeform — no controlled list. Use lowercase, hyphenated multi-word tags (e.g., `blind-generation`, `conformance-testing`).
