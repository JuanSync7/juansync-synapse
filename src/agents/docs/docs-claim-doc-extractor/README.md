# docs-claim-doc-extractor

Read-only structured-extraction agent for the `docs-claim-doc-shrinker` workflow. Turns a claim-based markdown doc into a deterministic list of atomic claim objects, plus auto-flagged contradictions and redundancies, consumed by the shrinker's audit phase.

| Agent | Description | Status | Consumers |
|-------|-------------|--------|-----------|
| [docs-claim-doc-extractor](docs-claim-doc-extractor.md) | Extracts atomic claims from a claim-based markdown doc. Returns a list of claim objects anchored by source heading, plus auto-flagged contradictions and redundancies. Read-only. | draft | docs-claim-doc-shrinker |

## Layout

| Path | Purpose |
|------|---------|
| [docs-claim-doc-extractor.md](docs-claim-doc-extractor.md) | Agent body — frontmatter, contract, do/don't, edge cases |
| [EVAL.md](EVAL.md) | Structural + output criteria + T1–T4 blind prompts |
| [references/](references/README.md) | Companion files (test fixtures with expected outputs) |
| [change_requests/](change_requests/README.md) | Decision memo + design doc that produced this agent |
