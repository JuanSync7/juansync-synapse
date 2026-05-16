# docs-claim-doc-shrinker

Two-phase orchestrator that audits and compresses claim-based markdown (identity, style, principle, decision docs) preserving every kept claim via post-write entailment verification.

| Skill | Description | Status | Consumers |
|-------|-------------|--------|-----------|
| [docs-claim-doc-shrinker](SKILL.md) | Audit and compress claim-based markdown. Run `audit` to produce a per-claim keep/cut/merge checklist; edit it; run `compress` to rewrite the doc preserving every kept claim. | draft | — |

## Layout

| Path | Purpose |
|------|---------|
| [SKILL.md](SKILL.md) | Skill body — frontmatter, dispatch flow, gates, refusal messages |
| [EVAL.md](EVAL.md) | Structural + output criteria + T1–T8 blind prompts |
| [references/](references/README.md) | Companion files (thresholds, schemas, audit-checklist template, fixtures) |
| [change_requests/](change_requests/README.md) | Decision memo + design doc that produced this skill |

## Dispatched agents

The skill dispatches four sibling agents under `src/agents/docs/`:

- `docs-claim-doc-classifier` — entry-gate classifier
- `docs-claim-doc-extractor` — atomic-claim extractor
- `docs-claim-doc-writer` — claim-preserving rewriter
- `docs-claim-claim-judge` — per-claim entailment verifier
