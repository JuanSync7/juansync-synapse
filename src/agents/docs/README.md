# src/agents/docs

User-facing documentation agents. Currently dedicated to the `docs-claim-doc-shrinker` workflow.

| Name | Role | Description |
|------|------|-------------|
| [docs-claim-claim-judge](docs-claim-claim-judge.md) | judge | Judges whether a single claim is semantically preserved in a rewritten document. Returns entailed \| partial \| dropped with evidence span. Designed for batch dispatch (one call per claim). |
