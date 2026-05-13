---
name: synapse-router-artifact-creator
description: Use when creating a new skill, protocol, agent, or tool in ai-synapse. Routes to type-specific creation flow.
domain: synapse
subdomain: router
scope: artifact
role: creator
tags: [creator, scaffold, multi-artifact, router]
user-invocable: true
argument-hint: "<skill|protocol|agent|tool> [name]"
---

# synapse-router-artifact-creator

Single entry point for creating a new ai-synapse artifact. The router commits to one artifact type before any type-specific content loads — three of the four flows never enter context for a given session. Shared mechanics (frontmatter validation, registry write, README row update, eval handoff, placement, draft-marking) run parametrically against `references/type-config.md`, never via `if $TYPE` branching.

## MUST (every turn)
- Record position: `Position: [node-id] — <context>`
- Confirm `$TYPE` ∈ {skill, protocol, agent, tool} BEFORE loading any flow file — `[ROUTE]` is a hard gate
- Validate `$NAME` against `[a-z0-9-]+` BEFORE flow load — pattern hint on failure
- Load EXACTLY ONE `references/flow-<type>.md` per session — token-budget invariant
- Run all pre-flight validations BEFORE any file is written (atomic creation)

## MUST NOT (global)
- Inline creation logic in this SKILL.md — routing only
- Branch on `$TYPE` inside `references/shared-steps.md` — type variation comes from `type-config.md` lookup
- Scaffold any file before pre-flight passes — failed pre-flight leaves zero state to clean up
- Grade produced artifact body quality — that is downstream (`write-{type}-eval` + `/synapse-router-artifact-gatekeeper`)

## Wrong-Tool Detection
- **Modifying an existing artifact** → redirect to `/synapse-skill-skill-improver <path>`
- **Idea exploration without a chosen artifact yet** → redirect to `/synapse-router-artifact-brainstormer`
- **Asking whether an existing artifact passes promotion bar** → redirect to `/synapse-router-artifact-gatekeeper <path>`
- **Creating multiple artifacts in one session** → reject; dispatch one parallel `synapse-router-artifact-creator` per artifact

## Concurrency contract
ONE artifact per invocation. Multi-artifact sessions use parallel `synapse-router-artifact-creator` agents.

## Progress Tracking

At session start, create router-level tasks:

```
TaskCreate: "[ROUTE] Determine artifact type and validate name"
TaskCreate: "Execute flow-<TYPE> lifecycle"
```

Mark `[ROUTE]` task `in_progress` when entering the node, `completed` after successful exit to a flow file. Mark the flow task `in_progress` at flow `[START]` and `completed` at flow `[END]`. The flow file owns its own sub-task creation if its lifecycle has 3+ phases.

## Entry

### [NEW] Fresh session
Do:
  1. Apply Wrong-Tool Detection — match user request against the four redirect cases above. If any matches, surface the redirect and exit to `[END]`.
  2. If user intent is ambiguous, ask before proceeding — do not assume creation.
  3. Otherwise → `[ROUTE]`.
Don't:
  - Skip wrong-tool check — every session passes through it before routing.
  - Treat ambiguous intent as a creation request.
Exit:
  → `[END]` : wrong-tool match (redirect surfaced)
  → `[ROUTE]` : creation intent confirmed

## Flow

### [ROUTE] — type detection and flow load
Load: `references/type-config.md`
Brief: Determine artifact type, validate name, load the matching flow. Single decision node. Nothing else happens here.
Do:
  1. If `$TYPE` arg missing → prompt: "What type? [skill | protocol | agent | tool]"
  2. Validate `$TYPE` against type-config valid values (one of skill/protocol/agent/tool); fail loudly with valid list on mismatch
  3. If `$NAME` arg missing → prompt for it
  4. Validate `$NAME` matches `[a-z0-9-]+`; fail with pattern hint on mismatch
  5. Load `references/flow-<TYPE>.md`
  6. Jump to that flow's `[START]`
Don't:
  - Continue without confirmed, valid `$TYPE` and `$NAME`
  - Inline any creation, validation, or scaffolding logic — that lives in flow files and shared-steps
  - Load more than one flow file
  - Auto-infer type from natural language ("make me a skill that…") — explicit arg or interactive prompt only
Exit:
  → `flow-<TYPE>:[START]` (single exit; flow file owns the rest of the lifecycle and its own `[END]`)

### [END]
Do:
  1. If exited from `[NEW]` wrong-tool match — surface the redirect message and stop. No artifact created.
  2. If exited from `[ROUTE]` validation failure — surface the failure (invalid `$TYPE` or `$NAME`) and stop. No artifact created.
Don't:
  - Reach `[END]` after `[ROUTE]` succeeds — successful routing transfers control to the flow file's lifecycle, which owns its own `[END]`.

## What this skill produces

| Output | Count | Purpose |
|--------|-------|---------|
| Artifact spec file (`SKILL.md` / `PROTOCOL.md` / agent `.md` / `TOOL.md`) | 1 | Primary artifact definition |
| Companion scaffold (`references/`, `templates/`, `rules/`, `test/`) | 1 set | Type-specific companion directories and stubs |
| Registry row | 1 | Adds artifact to type-specific registry |
| Domain README row | 1 | Adds artifact to domain catalog |
| EVAL.md or `test/` scaffold | 1 | Evaluation handoff (per-type via `write-{type}-eval`) |

All outputs land at `status: draft`; promotion to `stable` requires `/synapse-router-artifact-gatekeeper` certification.
