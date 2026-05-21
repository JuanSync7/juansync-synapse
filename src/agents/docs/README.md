# src/agents/docs

User-facing documentation agents — claim-shrinker sub-agents and spec-doc section writers/reviewers.

| Agent | Role | Description |
|-------|------|-------------|
| [docs-claim-doc-classifier](docs-claim-doc-classifier.md) | classifier | Entry-gate classifier — returns structural genre (claim-based, narrative, reference, tutorial, template, mixed), claim sub-type, and confidence for a markdown file |
| [docs-claim-doc-extractor](docs-claim-doc-extractor.md) | extractor | Read-only structured-extraction agent — returns deterministic atomic claims plus auto-flagged contradictions and redundancies for a claim-based markdown doc |
| [docs-claim-claim-judge](docs-claim-claim-judge.md) | judge | Judges whether a single claim is semantically preserved in a rewritten document. Returns entailed \| partial \| dropped with evidence span. Designed for batch dispatch (one call per claim). |
| [docs-claim-doc-writer](docs-claim-doc-writer.md) | writer | Rewrites a claim-based doc compressed against a fixed kept-claim set. Does NOT generate from scratch. Does NOT introduce claims outside the input set. Preserves section headings. For style-sub-type docs, preserves cadence via voice anchors. |
| [docs-spec-section-writer](docs-spec-section-writer.md) | writer | Writes one spec section from a planner brief — requirement format, acceptance criteria, traceability |
| [docs-spec-section-reviewer](docs-spec-section-reviewer.md) | reviewer | Three-way evaluator — brief alignment, section quality, deviation justification |
| [docs-spec-coherence-reviewer](docs-spec-coherence-reviewer.md) | reviewer | Doc-level coherence review — alignment, flow, cross-references, traceability |
