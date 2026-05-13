# registry

Human-readable discovery tables for all artifacts in the repo. Check here before creating a new skill, agent, protocol, tool, or script — an existing one may already cover what you need.

## Canonical schema

All registry tables share one shape:

```
| Name | Description | Status | Consumers |
```

| Column | Source | Notes |
|--------|--------|-------|
| Name | linked slug to artifact file/dir | Domain and type-specific classifiers (action, role, harness, audience, pipeline stage) are encoded in the slug — they do not get their own columns |
| Description | frontmatter `description` field | Semantic summary; not derivable from slug |
| Status | frontmatter `status` field | `draft` / `stable`. Lifecycle state |
| Consumers | derived (cross-reference scan) | Comma-separated list of artifacts that dispatch/depend on this one. `—` if none |

**Why this shape.** Domain and the type-specific classifier (Pipeline Stage / Action / Type / Harness / Audience) are recoverable from a well-formed slug, so they don't earn columns — duplication invites drift. Pipeline Stage for routable skills lives in [`synapse/SKILLS_REGISTRY.yaml`](../synapse/SKILLS_REGISTRY.yaml) where the orchestrator reads it.

**Consumer is universal.** Skills can chain into other skills, tools can be invoked from CLI, agents can be debugged directly. Every artifact has a (possibly empty) consumer set. The column is `—` when nothing chains in.

## Files

| File | Description |
|------|-------------|
| [SKILL_REGISTRY.md](SKILL_REGISTRY.md) | All skills — user-invocable recipes |
| [AGENTS_REGISTRY.md](AGENTS_REGISTRY.md) | All agents — internal recipes dispatched by skills |
| [PROTOCOL_REGISTRY.md](PROTOCOL_REGISTRY.md) | All protocols — behavioral contracts injected into agents |
| [TOOL_REGISTRY.md](TOOL_REGISTRY.md) | All tools — mechanical capabilities dispatched by skills/agents |
| [PATHWAY_REGISTRY.md](PATHWAY_REGISTRY.md) | All pathways — named synapse bundles |
| [SCRIPT_REGISTRY.md](SCRIPT_REGISTRY.md) | All scripts — repo management scripts |

