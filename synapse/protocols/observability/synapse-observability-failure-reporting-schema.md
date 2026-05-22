---
name: synapse-observability-failure-reporting-schema
description: "Standardized failure tag format for agents and protocols — enables grepping, aggregation, and surfacing across multi-agent workflows"
domain: synapse
subdomain: observability
subject: failure-reporting
kind: schema
version: 1
tags: [failure-reporting, agent-failure, protocol-failure, observability]
---

# Failure Reporting Protocol

Standardized tags for reporting failures across multi-agent workflows. Any agent or protocol observer that encounters a failure MUST use the tag formats below. This enables callers to grep for failures, aggregate them into summary tables, and surface them to users with consistent formatting.

## Tag Formats

### Agent Failure

An agent could not complete its task or is rejecting its input.

```
AGENT FAILURE: [agent-name] <free-form context> [reason]
```

- **agent-name** (MUST): the agent definition that failed (e.g., `spec-section-writer`, `spec-section-reviewer`)
- **free-form context** (OPTIONAL): agent-specific detail — section ID, phase, what was attempted
- **reason** (MUST): why it failed — specific, actionable, not vague

Examples:
```
AGENT FAILURE: spec-section-writer sec:req_auth brief missing token lifecycle info — cannot write auth requirements without token refresh/expiry semantics
AGENT FAILURE: spec-section-reviewer sec:req_errors REQ-305 has untestable acceptance criteria — "works properly" is not verifiable
```

### Protocol Failure

A protocol contract was violated.

```
PROTOCOL FAILURE: [protocol-name] <free-form context> [reason]
```

- **protocol-name** (MUST): the protocol that was violated (e.g., `synapse-memory-external-memory-contract`, `synapse-observability-execution-trace`)
- **free-form context** (OPTIONAL): where/when the violation occurred
- **reason** (MUST): what contract was broken

Examples:
```
PROTOCOL FAILURE: synapse-memory-external-memory-contract subagent wrote directly to notepad — only the planner may write to the notepad file
PROTOCOL FAILURE: synapse-observability-failure-reporting-schema agent returned untagged error — all failures must use AGENT FAILURE: prefix
```

## Behavior Contract

1. **Continue, don't bail.** When an agent encounters a failure, it MUST continue working through remaining items, accumulate all failures, and return a complete failure summary. Do not stop at the first problem.
2. **Tag every failure.** Every distinct failure gets its own tagged line. Do not bundle multiple failures into one tag.
3. **Caller aggregates.** The calling agent (planner/orchestrator) collects all tagged failures from subagent outputs and decides how to act — retry, revise, escalate, or surface to user.
4. **Final surfacing.** When failures reach the user, present them as a structured table with: source agent, context, reason, and resolution status (resolved/needs-manual).
