---
name: synapse-router-eval-writer
description: Use when generating an EVAL.md for a skill, protocol, agent, or tool.
domain: synapse
subdomain: router
scope: eval
role: writer
tags: [eval-md, criteria, test-prompts, multi-artifact, router]
user-invocable: true
argument-hint: "<skill|protocol|agent|tool> <path-to-artifact>"
---

# synapse-router-eval-writer

Single entry point for generating an `EVAL.md` against an existing artifact (skill, protocol, agent, tool). The router commits to one type before any flow file loads — three of the four flows never enter context for a given session. The skill produces criteria; it does NOT grade the artifact (that is `/synapse-router-artifact-gatekeeper`).

The four flows are asymmetric by design:
- `skill` flow = **dispatch** (~120 LOC): invokes `skill-eval-{prompter,judge,auditor}` agents and assembles their outputs.
- `protocol` / `agent` flows = **transcription** (~50–60 LOC): read the canonical `synapse-router-artifact-gatekeeper` checklist for the type and translate it into `EVAL-Sxx` + type-specific tier criteria.
- `tool` flow = **transcription+** (~60 LOC): structural rules from gatekeeper + `EVAL-Xxx` scaffold around the tool's `test/` directory.

## MUST (every turn)
- Record position: `Position: [node-id] — <context>`
- Confirm `$TYPE ∈ {skill, protocol, agent, tool}` BEFORE loading any flow file — `[ROUTE]` is a hard gate
- Validate `$ARTIFACT_PATH` exists BEFORE flow load
- Load EXACTLY ONE `references/flow-<type>.md` per session — token-budget invariant
- Atomic write: assemble EVAL.md fully in memory, write once
- Treat source artifact as read-only: extract name + frontmatter header only

## MUST NOT (global)
- Inline eval-generation logic in this SKILL.md — routing only
- Branch on `$TYPE` inside `references/shared-steps.md` — type variation comes from `references/type-config.md` lookup
- Modify the artifact being evaluated — read-only operation
- Validate taxonomy values on the source artifact — that is `/synapse-router-artifact-gatekeeper`'s job; this skill only confirms the file exists and extracts the artifact name
- Grade the artifact — produce criteria, do not apply them
- Fall back to baked-in criteria if a gatekeeper checklist file is missing — fail loud with the unresolved Load path; no silent fallback

## Wrong-Tool Detection
- **Improving a skill against an existing EVAL.md** → redirect to `/synapse-skill-skill-improver <path>`
- **Certifying an artifact for promotion** → redirect to `/synapse-router-artifact-gatekeeper <path>`
- **Brainstorming what eval to write** → redirect to `/synapse-router-artifact-brainstormer`
- **Path points at an existing EVAL.md, not the source artifact** → clarify and redirect to source artifact path
- **Multiple artifacts in one session** → reject; dispatch one parallel `synapse-router-eval-writer` per artifact

## Concurrency contract
ONE artifact per invocation. Multi-artifact sessions use parallel `synapse-router-eval-writer` agents.

## Progress Tracking

At session start, create router-level tasks:

```
TaskCreate: "[ROUTE] Validate type and artifact path"
TaskCreate: "Execute flow-<TYPE> lifecycle"
```

Mark `[ROUTE]` `in_progress` on entry, `completed` after exit to a flow file. Mark the flow task `in_progress` at flow `[START]` and `completed` at flow `[END]`.

## Entry

### [NEW] Fresh session
Do:
  1. Apply Wrong-Tool Detection — match user request against the redirects above. If any matches, surface the redirect and exit to `[END]`.
  2. If user intent is ambiguous, ask before proceeding — do not assume eval generation.
  3. Otherwise → `[ROUTE]`.
Don't:
  - Skip wrong-tool check — every session passes through it.
  - Treat ambiguous intent as an eval-generation request.
Exit:
  → `[END]` : wrong-tool match (redirect surfaced)
  → `[ROUTE]` : eval-generation intent confirmed

## Flow

### [ROUTE] — type detection, validation, flow load
Load: `references/type-config.md`
Brief: Validate `$TYPE` and `$ARTIFACT_PATH`, apply existing-EVAL guard, load the matching flow. Single decision node.
Do:
  1. If `$TYPE` arg missing → prompt: "What type? [skill | protocol | agent | tool]"
  2. Validate `$TYPE` against type-config valid keys; fail loudly with valid list on mismatch
  3. If `$ARTIFACT_PATH` missing → prompt for it
  4. Verify `$ARTIFACT_PATH` exists and matches `type-config[$TYPE].artifact_shape` (directory vs flat file); fail with type/path mismatch hint on miss
  5. Read source frontmatter — extract artifact name only; do NOT validate taxonomy values
  6. Resolve target eval path via `type-config[$TYPE].output_path_shape` + `output_filename`; if a file already exists at that path, fail with: "EVAL.md exists; use `--force` to overwrite or `/synapse-skill-skill-improver` to refine via measurement"
  7. Load EXACTLY ONE `references/flow-<TYPE>.md`
  8. Jump to that flow's `[START]`
Don't:
  - Continue without confirmed `$TYPE` and `$ARTIFACT_PATH`
  - Inline any eval-generation logic — that lives in flow files
  - Validate taxonomy values against `SKILL_TAXONOMY.md` / `AGENT_TAXONOMY.md` etc.
  - Load more than one flow file
  - Auto-infer type from natural language — explicit arg or interactive prompt only
Exit:
  → `flow-<TYPE>:[START]` (single exit; flow file owns its lifecycle and `[END]`)

### [END]
Do:
  1. If exited from `[NEW]` wrong-tool match — surface the redirect and stop. No EVAL.md created.
  2. If exited from `[ROUTE]` validation failure — surface the failure (invalid `$TYPE`, missing path, type/path mismatch, existing EVAL.md) and stop. No EVAL.md created.
Don't:
  - Reach `[END]` after `[ROUTE]` succeeds — successful routing transfers control to the flow file's lifecycle, which owns its own `[END]`.

## What this skill produces

| Output | Count | Purpose |
|--------|-------|---------|
| `EVAL.md` (or `<name>.eval.md` for flat artifacts) | 1 per invocation | Evaluation criteria + (skill only) test prompts |

Output path semantics (encoded in `references/type-config.md`):
- `skill`, `tool`: `<artifact-dir>/EVAL.md`
- `agent`, `protocol`: `<artifact-name>.eval.md` adjacent to the flat `.md` file

Exit signal: file path + tier-count summary (e.g., "Wrote EVAL.md with 12 EVAL-S, 7 EVAL-O, 4 test prompts").

## Examples

**Valid invocation (skill):**
```
/synapse-router-eval-writer skill synapse/skills/synapse-skill-skill-improver
→ Wrote synapse/skills/synapse-skill-skill-improver/EVAL.md with 14 EVAL-S, 9 EVAL-O, 6 test prompts
```

**Invalid `$TYPE`:**
```
/synapse-router-eval-writer pathway synapse/pathways/full.yaml
→ FAIL: $TYPE='pathway' invalid. Expected one of: skill, protocol, agent, tool.
```

**Type/path mismatch (`$TYPE=skill` but path is a flat .md):**
```
/synapse-router-eval-writer skill synapse/agents/synapse/skill-eval/synapse-skill-eval-judge.md
→ FAIL: $TYPE='skill' expects a directory containing SKILL.md, got a flat .md file.
  If this is an agent, use: /synapse-router-eval-writer agent synapse/agents/synapse/skill-eval/synapse-skill-eval-judge.md
```

**Existing EVAL.md (no `--force`):**
```
/synapse-router-eval-writer skill synapse/skills/synapse-router-artifact-gatekeeper
→ FAIL: EVAL.md exists at synapse/skills/synapse-router-artifact-gatekeeper/EVAL.md.
  Use --force to overwrite, or /synapse-skill-skill-improver to refine via measurement.
```
