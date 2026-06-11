# docs-claim-shrinker

Audit and compress claim-based markdown (identity, style, principle, decision docs). Two-phase workflow with classifier entry gate, human-editable per-claim checklist, and post-write entailment verification — lossless on the human-chosen kept-claim set.

| Skill | Role | Description |
|-------|------|-------------|
| [docs-claim-shrinker](SKILL.md) | shrinker | Two-phase: `audit` writes a per-claim keep/cut/merge checklist; `compress` rewrites the doc preserving every kept claim with post-write entailment verification. |

## Layout

| Path | Purpose |
|------|---------|
| [SKILL.md](SKILL.md) | Orchestrator spec; dispatches the four sibling agents under `src/agents/docs/`. |
| [EVAL.md](EVAL.md) | Acceptance contract — structural checks, output checks, blind prompts. |
| [references/](references/) | Companions loaded at specific nodes (thresholds, schemas, audit-checklist template, wrong-tool redirects). |
| [change_requests/](change_requests/) | Brainstorm memo and design doc that produced this skill. |

## Sibling agents (separate artifacts)

- `src/agents/docs/docs-claim-doc-classifier.md` — structural-genre classifier with the unconditional entry gate.
- `src/agents/docs/docs-claim-doc-extractor.md` — atomic-claim extractor with deterministic IDs.
- `src/agents/docs/docs-claim-claim-judge.md` — per-claim entailment judge for post-write verification.
- `src/agents/docs/docs-claim-doc-writer.md` — claim-preserving rewriter (style sub-type uses voice anchors).
