# src/skills/docs

Adopter skills that operate on user-facing markdown documentation. One entry per skill directory.

| Skill | Role | Description |
|-------|------|-------------|
| [docs-claim-doc-shrinker](docs-claim-doc-shrinker/SKILL.md) | shrinker | Audit and compress claim-based markdown (identity, style, principle, decision docs). Two-phase: `audit` writes a per-claim keep/cut/merge checklist; `compress` rewrites the doc preserving every kept claim with post-write entailment verification. |
| [doc-authoring](doc-authoring/SKILL.md) | route | Router — identifies which doc skill to invoke based on role and layer |
| [write-scope-docs](write-scope-docs/SKILL.md) | write | Scope document — what to build, what to defer, how to phase delivery |
| [write-architecture-docs](write-architecture-docs/SKILL.md) | write | Architecture doc with technology decisions, component boundaries, and data flow patterns |
| [write-spec-docs](write-spec-docs/SKILL.md) | write | Formal requirements specification with FR/NFR traceability |
| [write-spec-summary](write-spec-summary/SKILL.md) | summarize | Concise spec summary synced with companion spec |
| [write-design-docs](write-design-docs/SKILL.md) | write | Design document with task decomposition and code contracts |
| [write-implementation-docs](write-implementation-docs/SKILL.md) | write | Implementation source-of-truth before touching code |
| [write-engineering-guide](write-engineering-guide/SKILL.md) | write | Post-implementation engineering guide |
| [write-test-docs](write-test-docs/SKILL.md) | write | Test planning document for module test specs |
| [write-test-coverage](write-test-coverage/SKILL.md) | write | Living test coverage register — maps acceptance criteria to test scenarios |
| [patch-docs](patch-docs/SKILL.md) | improve | Diff-driven incremental doc patcher — targeted section updates from git diffs |
| [write-postmortem](write-postmortem/SKILL.md) | write | Structured blameless postmortem document from incident facts |

## Layer Chain

```
write-scope-docs → write-architecture-docs → write-spec-docs → write-spec-summary → write-design-docs → write-implementation-docs → (code/build-plan) → write-engineering-guide → write-test-docs
```

`patch-docs` operates cross-cutting: updates any layer incrementally from a git diff.
