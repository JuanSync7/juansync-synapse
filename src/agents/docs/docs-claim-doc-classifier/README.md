# docs-claim-doc-classifier

Read-only entry-gate agent for the `docs-claim-doc-shrinker` workflow. Classifies a markdown file's structural genre and (when claim-based) its sub-type, with a confidence score consumed by the shrinker.

| Agent | Description | Status | Consumers |
|-------|-------------|--------|-----------|
| [docs-claim-doc-classifier](docs-claim-doc-classifier.md) | Classifies a markdown file's structural genre (claim-based, narrative, reference, tutorial, template, mixed) and the claim sub-type (identity, style, principle, decision). Read-only. | draft | docs-claim-doc-shrinker |

## Layout

| Path | Purpose |
|------|---------|
| [docs-claim-doc-classifier.md](docs-claim-doc-classifier.md) | Agent body — frontmatter, contract, do/don't, edge cases |
| [EVAL.md](EVAL.md) | Structural + output criteria + T1–T5 blind prompts |
| [references/](references/README.md) | Companion files (test fixtures) |
| [change_requests/](change_requests/) | Decision memo + design doc that produced this agent |
