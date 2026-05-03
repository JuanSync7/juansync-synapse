# docs

Documentation authoring skills. Produces scope docs, architecture docs, specs, summaries, design docs, implementation docs, engineering guides, and test planning docs.

## Skills

| Skill | Intent | Description |
|-------|--------|-------------|
| [doc-authoring](doc-authoring/) | route | Router — identifies which doc skill to invoke based on role and layer |
| [write-scope-docs](write-scope-docs/) | write | Scope document — what to build, what to defer, how to phase delivery |
| [write-architecture-docs](write-architecture-docs/) | write | Architecture doc with technology decisions, component boundaries, and data flow patterns |
| [write-spec-docs](write-spec-docs/) | write | Formal requirements specification with FR/NFR traceability |
| [write-spec-summary](write-spec-summary/) | summarize | Concise spec summary synced with companion spec |
| [write-design-docs](write-design-docs/) | write | Design document with task decomposition and code contracts |
| [write-implementation-docs](write-implementation-docs/) | write | Implementation source-of-truth before touching code |
| [write-engineering-guide](write-engineering-guide/) | write | Post-implementation engineering guide |
| [write-test-docs](write-test-docs/) | write | Test planning document for module test specs |
| [write-test-coverage](write-test-coverage/) | write | Living test coverage register — maps acceptance criteria to test scenarios |
| [patch-docs](patch-docs/) | improve | Diff-driven incremental doc patcher — targeted section updates from git diffs |
| [write-postmortem](write-postmortem/) | write | Structured blameless postmortem document from incident facts |

## Layer Chain

```
write-scope-docs → write-architecture-docs → write-spec-docs → write-spec-summary → write-design-docs → write-implementation-docs → (code/build-plan) → write-engineering-guide → write-test-docs
```

`patch-docs` operates cross-cutting: updates any layer incrementally from a git diff.
