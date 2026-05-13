# AGENTS.md

This file provides guidance to OpenAI Codex when working with code in this repository.

## What This Repo Is

A central library of reusable agent skills — composable units of behavior for autonomous doc authoring, code generation, testing, and multi-agent pipelines. Framework artifacts live under `synapse/`; adopter artifacts under `src/`.

## Repository Layout

```
synapse/                      # Framework artifacts (meta-tools shipped by ai-synapse)
  skills/<domain>/<name>/     # SKILL.md + EVAL.md + references/ + templates/ + agents/
  agents/<domain>/            # Internal agents dispatched by framework skills
  protocols/<domain>/         # Shared schemas (observability, memory)
  tools/<domain>/             # Mechanical capabilities
  SKILLS_REGISTRY.yaml        # Pipeline metadata and stage dependencies
src/                          # Adopter artifacts (this repo's own skills/agents/...)
  skills/<domain>/<name>/     # Same shape as synapse/skills/<domain>/<name>/
  agents/<domain>/
  protocols/<domain>/
  tools/<domain>/
```

Root files: `AGENTS_REGISTRY.md` (agent discovery), `SKILL_TAXONOMY.md` (domain/intent vocabulary), `GOVERNANCE.md` (promotion criteria).

## Skill Anatomy

Every SKILL.md has YAML frontmatter followed by a markdown body:

```yaml
---
name: skill-name
description: "Trigger conditions — when this skill fires"
domain: docs.spec           # from SKILL_TAXONOMY.md
intent: write               # from SKILL_TAXONOMY.md
tags: [lowercase, hyphenated]
user-invocable: true
argument-hint: "[args]"
---
```

The `description` field is a routing contract: it specifies when the skill fires, not what it does.

## Three-Tier Taxonomy

| Concept | Location | Frontmatter | Taxonomy | Purpose |
|---------|----------|-------------|----------|---------|
| **Skills** | `{synapse,src}/skills/<domain>/<skill-name>/SKILL.md` | name, description, domain, intent | `SKILL_TAXONOMY.md` | User-facing recipes — invoked by name |
| **Agents** | `{synapse,src}/agents/<domain>/<agent>.md` | name, description, domain, role | `AGENT_TAXONOMY.md` | Internal recipes dispatched by skills — not user-invocable |
| **Protocols** | `{synapse,src}/protocols/<domain>/<protocol>.md` | name, description, domain, type | `PROTOCOL_TAXONOMY.md` | Shared conventions injected into agents by observers |

All three artifact types require YAML frontmatter, taxonomy-validated metadata, and gatekeeper review for promotion. Skills declare agent dependencies via symlinks in their `agents/` folder pointing to `{synapse,src}/agents/`.

## Pipeline System

End-to-end pipeline metadata lives in `synapse/SKILLS_REGISTRY.yaml`. Each stage has typed inputs/outputs and dependency chains (`requires_all`/`requires_any`). Named presets (`full`, `feature`, `bugfix`, `docs-only`) are trusted stage sequences. The framework defines the contract; an adopter-supplied orchestrator skill consumes it.

## Skill Design Principles

1. **Context injection, not programming** — only include what the agent can't derive from training
2. **Mental model before mechanics** — conceptual framing paragraph before rules
3. **Policy over procedure** — teach judgment, not step-by-step mechanics
4. **Progressive disclosure** — SKILL.md carries always-on info; companion files load at decision points
5. **Every instruction traces to a failure mode** — no instruction without a concrete reason
6. **Loud failure on preconditions** — check inputs and fail clearly; never proceed silently

## After Modifying a Skill

Two validation layers apply:

1. **Pre-commit (structural)** — frontmatter fields present, domain/intent in SKILL_TAXONOMY.md, EVAL.md exists
2. **PR-time (quality)** — new skills run full creation pipeline; modified skills run score-fix loop

## Conventions

- Skill names must be globally unique (flat discovery directory, no namespacing)
- EVAL.md files contain structural criteria, output criteria, and test prompts
- Pipeline-routable skills must be registered in `synapse/SKILLS_REGISTRY.yaml`
- Domain and intent values must come from `SKILL_TAXONOMY.md`
