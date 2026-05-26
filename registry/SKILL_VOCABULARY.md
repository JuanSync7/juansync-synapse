# Skill Vocabulary

Controlled values for the four slug slots defined in [`taxonomy/SKILL_TAXONOMY.md`](../taxonomy/SKILL_TAXONOMY.md): `{domain}-{subdomain}-{scope}-{role}`.

These values apply to **skills only** — they are NOT shared with agents, protocols, or tools. Each artifact type has its own independent slot vocabulary.

When creating a new skill, pick values from the tables below. If nothing fits, propose a new row in this file in the same PR — do not invent ad hoc values.

## Domains

| Domain | Description |
|--------|-------------|
| `synapse` | Framework-internal skills shipped by ai-synapse |
| `docs` | User-facing documentation skills |
| `code` | Source-code authoring, modification, and execution skills |
| `creative` | Visual or interactive output (HTML/CSS/JS pages, animations) |
| `framework` | Skills targeted at a specific external framework or library |
| `meta` | Cross-cutting meta-utilities (brainstorming, routing) |
| `optimization` | Iterative measure-and-improve loops |
| `integration` | External-service integration skills |
| `delivery` | Plan-to-code execution — orchestrating subagents to deliver work against a plan |

## Subdomains

| Subdomain | Description |
|-----------|-------------|
| `router` | Cross-cutting routing/orchestration skills (artifact-creator, gatekeeper, eval-writer, suite-validator) |
| `skill` | Skills that operate on skill artifacts (skill-improver) |
| `claim` | Claim-based docs (identity, style, principle, decision sub-types) |
| `spec` | Requirements specs and spec summaries |
| `design` | Technical design documents |
| `impl` | Implementation plans |
| `arch` | Architecture documents |
| `scope` | Scoping documents |
| `post-build` | Post-implementation docs (engineering guide, test docs, postmortem, test coverage) |
| `test` | Test-related code skills (lint, audit, fix, generate, evaluate, integrate, run, write) |
| `plan` | Build/implementation planning skills |
| `harness` | AI harness / orchestration framework skills (LangGraph, etc.) |
| `general` | Catch-all for skills with no narrower subdomain |
| `orchestration` | Manager-side coordination of subagents, closeouts, and plan mutation |
| `execution` | Worker-side concern — what one subagent does inside a single dispatch |

## Scopes

| Scope | Description |
|-------|-------------|
| `artifact` | Operates over any artifact type (skill, agent, protocol, tool) |
| `eval` | Operates over EVAL.md generation |
| `suite` | Operates over multi-artifact suites (external/) |
| `skill` | Operates over a single SKILL.md |
| `doc` | Operates on a single markdown doc |
| `module` | Operates on a code module |
| `repo` | Operates on a whole repository |
| `page` | Operates on a single web page artifact |
| `workflow` | Operates on a workflow / state graph |
| `process` | Operates on a development process (research loop, brainstorm session) |
| `plan` | Operates on a plan-shaped artifact (work-package list, slice graph) |

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
| `summarizer` | Produces a concise digest from a longer source |
| `patcher` | Applies targeted updates from a diff or change set |
| `router` | Dispatches user intent to the right downstream artifact |
| `planner` | Decomposes an objective into an ordered task plan |
| `linter` | Static-analysis pass that emits a findings report |
| `auditor` | Read-only diagnostic of artifact health |
| `fixer` | Applies remediation against a findings report |
| `generator` | Produces new artifacts from a specification |
| `evaluator` | Scores/classifies inputs against criteria |
| `integrator` | Converts mock-based artifacts into real-service ones |
| `runner` | Executes an artifact in a controlled environment |
| `designer` | Designs an artifact's structure before implementation |
| `animator` | Builds animated interactive page artifacts |
| `researcher` | Runs an autonomous measure-and-keep improvement loop |
| `executor` | Drives end-to-end execution of a plan through sequential subagent dispatch |
