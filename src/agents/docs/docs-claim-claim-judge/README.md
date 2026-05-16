# docs-claim-claim-judge

Read-only entailment-verification agent for the `docs-claim-doc-shrinker` workflow. Judges whether a single claim survives a rewritten document — verdict, verbatim evidence span, and confidence — designed for batch dispatch (one call per kept claim).

| Agent | Description | Status | Consumers |
|-------|-------------|--------|-----------|
| [docs-claim-claim-judge](docs-claim-claim-judge.md) | Judges whether a single claim is semantically preserved in a rewritten document. Returns entailed \| partial \| dropped with evidence span. Designed for batch dispatch (one call per claim). | draft | docs-claim-doc-shrinker |

## Layout

| Path | Purpose |
|------|---------|
| [docs-claim-claim-judge.md](docs-claim-claim-judge.md) | Agent body — frontmatter, contract, do/don't, edge cases |
| [EVAL.md](EVAL.md) | Structural + output criteria + T1–T6 blind prompts |
| [references/](references/README.md) | Companion files (test fixtures) |
| [change_requests/](change_requests/) | Decision memo + design doc that produced this agent |
