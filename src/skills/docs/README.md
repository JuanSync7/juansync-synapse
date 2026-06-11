# src/skills/docs

Adopter skills that operate on user-facing markdown documentation. One entry per skill directory.

| Skill | Role | Description |
|-------|------|-------------|
| [docs-claim-shrinker](docs-claim-shrinker/SKILL.md) | shrinker | Audit and compress claim-based markdown (identity, style, principle, decision docs). Two-phase: `audit` writes a per-claim keep/cut/merge checklist; `compress` rewrites the doc preserving every kept claim with post-write entailment verification. |
| [docs-doc-router](docs-doc-router/SKILL.md) | route | Router — identifies which doc skill to invoke based on role and layer |
| [docs-scope-writer](docs-scope-writer/SKILL.md) | write | Scope document — what to build, what to defer, how to phase delivery |
| [docs-architecture-writer](docs-architecture-writer/SKILL.md) | write | Architecture doc with technology decisions, component boundaries, and data flow patterns |
| [docs-spec-writer](docs-spec-writer/SKILL.md) | write | Formal requirements specification with FR/NFR traceability |
| [docs-spec-summarizer](docs-spec-summarizer/SKILL.md) | summarize | Concise spec summary synced with companion spec |
| [docs-design-writer](docs-design-writer/SKILL.md) | write | Design document with task decomposition and code contracts |
| [docs-implementation-writer](docs-implementation-writer/SKILL.md) | write | Implementation source-of-truth before touching code |
| [docs-engineering-guide-writer](docs-engineering-guide-writer/SKILL.md) | write | Post-implementation engineering guide |
| [docs-test-plan-writer](docs-test-plan-writer/SKILL.md) | write | Test planning document for module test specs |
| [docs-coverage-writer](docs-coverage-writer/SKILL.md) | write | Living test coverage register — maps acceptance criteria to test scenarios |
| [docs-doc-patcher](docs-doc-patcher/SKILL.md) | improve | Diff-driven incremental doc patcher — targeted section updates from git diffs |
| [docs-postmortem-writer](docs-postmortem-writer/SKILL.md) | write | Structured blameless postmortem document from incident facts |

## Layer Chain

```
docs-scope-writer → docs-architecture-writer → docs-spec-writer → docs-spec-summarizer → docs-design-writer → docs-implementation-writer → (code/code-build-planner) → docs-engineering-guide-writer → docs-test-plan-writer
```

`docs-doc-patcher` operates cross-cutting: updates any layer incrementally from a git diff.
