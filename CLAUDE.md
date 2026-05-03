# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

A **central library** for Claude Code skills — both a home for standalone skills and a registry that submodules skill suites from external repos. Skills are organized into domain directories and installed as symlinks into `~/.claude/skills/`.

Two kinds of artifacts live here:
- **Framework artifacts** — the meta-tools that build, evaluate, and govern artifacts (skill-creator, gatekeeper, eval generators, orchestrator, etc.). These live under `synapse/`.
- **Adopter artifacts** — repo-specific skills, agents, protocols, and tools. These live under `src/`.
- **External suites** — multi-artifact projects with shared config, templates, and CI. These live in their own repos and are wired in as git submodules under `external/`.

## Repository Layout

```
identity/                     # Personal identity files (SOUL.md, STAKEHOLDER.md)
synapse/                      # Framework artifacts (the meta-tools shipped by ai-synapse)
  skills/<domain>/<name>/     # Framework skills (skill-creator, gatekeeper, ...)
  agents/<domain>/            # Framework agents (skill-eval, protocol-eval, ...)
  protocols/<domain>/         # Framework protocols (observability, memory)
  tools/<domain>/             # Framework tools (synapse-cr-dispatcher)
  SKILLS_REGISTRY.yaml        # Pipeline routing metadata (pipeline-routable skills only)
src/                          # Adopter artifacts (this repo's own skills/agents/...)
  skills/<domain>/<name>/     # Adopter skills (docs, code, frameworks, ...)
  agents/<domain>/            # Adopter agents
  protocols/<domain>/         # Adopter protocols (typically empty)
  tools/<domain>/             # Adopter tools (typically empty)
external/                     # Externally-owned submodule suites
  <suite-name>/               # git submodule — may contain skills/, agents/, protocols/
```

Each skill directory has the same shape under either root: `SKILL.md`, optional `EVAL.md`, `references/`, `templates/`, and `agents/` (symlinks to agent definitions used by this skill).

**Identity files (`identity/`):**
- `SOUL.md` — personal identity file: background, worldview, opinions, thinking style, blind spots, tensions, boundaries
- `SOUL.template.md` — blank skeleton with guidance for creating your own SOUL.md
- `STAKEHOLDER.md` — decision proxy persona: priorities, expertise map, heuristics, red flags, escalation triggers

**Registry files (`registry/`):**
- `registry/SKILL_REGISTRY.md` — full skill catalog (all skills, human-readable)
- `registry/AGENTS_REGISTRY.md` — agent discovery table
- `registry/PROTOCOL_REGISTRY.md` — protocol discovery table

**Taxonomy files (`taxonomy/`):**
- `taxonomy/SKILL_TAXONOMY.md` — controlled vocabulary for skill `domain` and `intent` metadata fields
- `taxonomy/AGENT_TAXONOMY.md` — controlled vocabulary for agent `domain` and `role` metadata fields
- `taxonomy/PROTOCOL_TAXONOMY.md` — controlled vocabulary for protocol `domain` and `type` metadata fields

**Root files:**
- `GOVERNANCE.md` — repo-level governance: promotion criteria, contribution workflow, naming conventions
- `scripts/install.sh` — CLI for installing/managing skill symlinks
- `Makefile` — repo setup (`make init` configures git hooks)
- `.githooks/` — git hooks for structural validation on commit

## synapse/ vs src/ vs external/

- **`synapse/`** — framework artifacts. The meta-tools (skill-creator, gatekeeper, eval generators, orchestration) that ship with ai-synapse. Convention-enforced and consumed by adopters as a dependency.
- **`src/`** — adopter artifacts owned by this specific repo. Convention-enforced (pre-commit hook). Skills, agents, and protocols organized by domain. May be empty in a pure framework distribution.
- **`external/`** — externally-owned submodule suites. Each suite is a git submodule with its own structure (may contain `skills/`, `agents/`, `protocols/`). Their internal layout is owned by the external repo.

**When to keep an artifact in `src/`:** It's standalone — no shared config, no multi-artifact coordination.

**When to extract to `external/`:** The artifact is part of a suite with shared infrastructure, needs its own CI, or is meant to be adopted independently by other teams.

**Adding an external suite:**
1. Create a standalone repo with the artifact(s), shared config, and its own CI
2. Add it as a git submodule under `external/`: `git submodule add <url> external/<suite-name>`
3. Register the artifact(s) in the appropriate registry (`registry/SKILL_REGISTRY.md`, `registry/AGENTS_REGISTRY.md`, etc.)
4. `scripts/install.sh` discovers artifacts in both `src/` and `external/` automatically

**Modifying an external artifact:**
- Make changes in the suite's own repo, not here
- Update the submodule pointer in this repo after the external change lands

**Registration is intentional, not automatic.** Artifacts land in ai-synapse only after review, with an EVAL.md, via a PR that adds the submodule + registry entry. External repos are where free iteration happens; ai-synapse is where you promote to.

## Setup

After cloning, run `make init` to configure git hooks.

## Install Commands

### Claude Code (default)

```bash
./scripts/install.sh install all                          # install all skills
./scripts/install.sh install synapse/skills/skill synapse/skills/protocol # install specific domains
./scripts/install.sh agents                               # install agent definitions
./scripts/install.sh identity                             # install identity files (SOUL.md, stakeholder.md)
./scripts/install.sh list                                 # show installed skills
./scripts/install.sh available                            # show all available skills
./scripts/install.sh clean                                # remove all symlinks (all harnesses)
```

Target directory: `$CLAUDE_SKILLS_DIR` (default: `~/.claude/skills/`).

### Codex CLI

```bash
./scripts/install.sh codex all                            # install to ~/.codex/skills/ (global)
./scripts/install.sh codex-project all                    # install to .agents/skills/ (project)
```

Target directory: `$CODEX_SKILLS_DIR` (default: `~/.codex/skills/`).

### Multi-Harness Support

ai-synapse supports multiple AI coding harnesses. SKILL.md is the universal authoring format — extra Claude-specific frontmatter fields are ignored by other harnesses. See `references/harness-mappings.yaml` for the full compatibility table.

## Skill Anatomy

Every SKILL.md has YAML frontmatter followed by a markdown body:

```yaml
---
name: skill-name
description: "Trigger conditions — when this skill fires (not a workflow summary)"
domain: docs.spec           # from SKILL_TAXONOMY.md
intent: write               # from SKILL_TAXONOMY.md
tags: [lowercase, hyphenated]
user-invocable: true
argument-hint: "[args]"
---
```

The `description` field is a **routing contract**: it specifies when the skill fires, not what it does. If the description could replace reading the body, it's too broad.

## Pipeline System

The autonomous orchestrator drives end-to-end pipelines using stages defined in `synapse/SKILLS_REGISTRY.yaml`. Each stage has typed inputs/outputs and dependency chains (`requires_all`/`requires_any`). Named presets (e.g., `full`, `feature`, `bugfix`) are trusted stage sequences that bypass dependency resolution. A stakeholder-reviewer gates stage transitions.

## Skill Design Principles

These are the core principles for writing and modifying skills (full reference: `synapse/skills/skill/skill-creator/references/skill-design-principles.md`):

1. **Context injection, not programming** — only include what the agent can't derive from training. Token bloat degrades output quality.
2. **Mental model before mechanics** — lead with a conceptual framing paragraph, then rules.
3. **Policy over procedure** — teach judgment ("when X, prioritize Y over Z because...") not step-by-step mechanics.
4. **Progressive disclosure** — SKILL.md carries always-on info; companion files in `references/` load at specific decision points.
5. **Every instruction traces to a failure mode** — no instruction without "without this, the agent does X which causes Y."
6. **Loud failure on preconditions** — check inputs and fail clearly; never proceed silently with bad data.

## After Modifying an Artifact

Whenever any file inside a skill directory, agent file, or protocol file changes, two layers of validation apply:

### Layer 1: Structural checks (enforced by pre-commit hook)

These run automatically on every commit — no LLM needed:

**Skills:**
- SKILL.md frontmatter has required fields (`name`, `description`, `domain`, `intent`)
- `domain` and `intent` values exist in `taxonomy/SKILL_TAXONOMY.md`
- Domain README.md has a row matching the skill
- EVAL.md exists alongside SKILL.md
- Listed in `registry/SKILL_REGISTRY.md`

**Agents** (`{synapse,src}/agents/<domain>/<agent>.md`):
- Frontmatter has required fields (`name`, `description`, `domain`, `role`)
- `domain` and `role` values exist in `AGENT_TAXONOMY.md`
- Domain README.md has a row matching the agent
- Listed in `registry/AGENTS_REGISTRY.md`

**Protocols** (`{synapse,src}/protocols/<domain>/<protocol>.md`):
- Frontmatter has required fields (`name`, `description`, `domain`, `type`)
- `domain` and `type` values exist in `PROTOCOL_TAXONOMY.md`
- Domain README.md has a row matching the protocol

### Layer 2: Quality evaluation

The evaluation tier depends on the type of change:

- **New skill or external import** → run `/skill-creator` (full pipeline: baseline test, design principles, eval generation, improvement loop), then `/synapse-gatekeeper` for certification
- **Modified existing skill** (SKILL.md, references/, templates/) → run `/improve-skill` (score-fix loop against existing EVAL.md)
- **New or modified agent/protocol** → run `/synapse-gatekeeper <artifact-path>` for certification
- **Trivial changes** (typos, formatting-only) → Layer 1 is sufficient

**New artifacts must be certified before merging.** Run `/synapse-gatekeeper <artifact-path> [--score <score>]` and include the APPROVE verdict in the PR description. If not ready for certification, mark it `status: draft` in the appropriate registry — this is tracked and must be resolved before the artifact is considered production-ready. See `GOVERNANCE.md` for full promotion criteria.

## Directory README Convention

Every directory in the repo must have a README.md. Exceptions: dot-directories (`.git`, `.claude`, `.brainstorms`) and generated/transient directories (`dist`).

**README.md files are enforced indexes, not freeform docs.** They are the same class of artifact as taxonomy files — authoritative, structural, validated by the pre-commit hook. The hook checks that domain README.md tables have a row for every artifact in that directory. Treat a missing or stale row as a structural error, not a documentation gap.

**Leaf directories** (domain directories that contain artifact files directly):
- One-line description of the domain at the top
- A catalog table of all artifacts in that directory (name → link, role/intent, one-line description)
- Example: `synapse/agents/skill-eval/README.md` lists every agent file in that folder

**Parent directories** (directories that contain subdirectories):
- One-line description of what lives here
- A summary table per artifact class: one row per subdirectory, linking to its README
- No content duplication — the parent row is a pointer (`[domain/](domain/)` + one-liner), not a copy of the child's catalog
- Example: `src/README.md` has three tables (skills, agents, protocols), each row linking to a domain README

**The rule:** if you add a new artifact or domain, you update two READMEs — the directory it lives in, and its parent. Nothing higher up needs to change; the summary propagates by link traversal, not by copy.

## Conventions

- **Skill names must be globally unique.** Claude discovers skills from a flat `~/.claude/skills/` directory — no namespacing is possible. Use domain-prefixed names (e.g., `jira-reporter`, `jira-planner`) to avoid collisions across repos. `scripts/install.sh` warns on name collisions.
- Skills with 3+ phases include a **Progress Tracking** section with `TaskCreate` examples.
- **Wrong-Tool Detection** sections redirect to sibling skills when the user's intent doesn't match.
- EVAL.md files are generated artifacts containing structural criteria, output criteria, and test prompts.
- All skills must have a row in `registry/SKILL_REGISTRY.md`. Pipeline-routable skills also register a stage entry in `synapse/SKILLS_REGISTRY.yaml` with `stage_name`, `input_type`, `output_type`, `context_type`, and `requires_*`.
- Domain and intent values must come from `SKILL_TAXONOMY.md`. If nothing fits, propose an addition there — don't invent ad hoc values.
