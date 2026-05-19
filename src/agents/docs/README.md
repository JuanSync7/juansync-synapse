# src/agents/docs

User-facing documentation agents. Currently dedicated to the `docs-claim-doc-shrinker` workflow.

| Name | Role | Description |
|------|------|-------------|
| [docs-claim-doc-writer](docs-claim-doc-writer.md) | writer | Rewrites a claim-based doc compressed against a fixed kept-claim set. Does NOT generate from scratch. Does NOT introduce claims outside the input set. Preserves section headings. For style-sub-type docs, preserves cadence via voice anchors. |
