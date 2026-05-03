# Change Request: README update agent

## Problem

Creator skills (`skill-creator`, `agent-creator`, `protocol-creator`) create new synapses but consistently forget to update the domain README.md with a row for the new artifact. The pre-commit hook catches the missing row, but by then the contributor has to manually figure out the right format and add it.

## Proposed Change

Create a focused agent (`synapse-readme-writer` or similar) that:

1. Reads the newly created/updated synapse (frontmatter: name, description, intent/role/type/action)
2. Reads the domain README.md
3. Decides: does the README need a new row, an updated row, or no change?
4. Writes the update if needed — matching the existing table format

The agent would be dispatched by any `*-creator` skill after synapse creation/update, as a final step before the skill completes.

## Scope

- New agent definition in `src/agents/synapse/` (or appropriate domain)
- Each `*-creator` skill gains a final step: dispatch the README agent
- Also useful for `improve-skill` when changes affect frontmatter (description, intent)
- The agent reads the synapse and the README — no other context needed

## Why

Domain READMEs are enforced structural indexes (pre-commit hook validates rows exist). Missing rows block commits. An agent that handles this automatically removes a friction point from the creation workflow and ensures consistency — the README row is written by looking at the synapse, not by the contributor remembering to do it.
