# src/skills/docs

Adopter skills that operate on user-facing markdown documentation. One entry per skill directory.

| Skill | Role | Description |
|-------|------|-------------|
| [docs-claim-doc-shrinker](docs-claim-doc-shrinker/SKILL.md) | shrinker | Audit and compress claim-based markdown (identity, style, principle, decision docs). Two-phase: `audit` writes a per-claim keep/cut/merge checklist; `compress` rewrites the doc preserving every kept claim with post-write entailment verification. |
