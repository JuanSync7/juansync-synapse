# docs-claim-doc-writer

Rewrite-stage agent for the `docs-claim-doc-shrinker` workflow. Recomposes a claim-based markdown doc against a fixed kept-claim set, preserving every source heading and never introducing assertions outside the input set. Does not self-verify — the `docs-claim-claim-judge` sibling owns entailment.

| Agent | Description | Status | Consumers |
|-------|-------------|--------|-----------|
| [docs-claim-doc-writer](docs-claim-doc-writer.md) | Rewrites a claim-based doc compressed against a fixed kept-claim set. Preserves headings; never introduces new claims; for style sub-type, matches voice via 3–5 anchor sentences. | draft | docs-claim-doc-shrinker |

## Layout

| Path | Purpose |
|------|---------|
| [docs-claim-doc-writer.md](docs-claim-doc-writer.md) | Agent body — frontmatter, contract, do/don't, edge cases, reuse-review checkpoint |
| [EVAL.md](EVAL.md) | Structural + output criteria + T1–T6 blind prompts |
| [references/](references/README.md) | Companion files (test fixtures) |
| [change_requests/](change_requests/) | Decision memo + design doc that produced this agent |

## Reuse Review Checkpoint

Per design doc §12, this agent is the weakest reuse case of the four shrinker siblings — its contract is tightly coupled to the audit-then-compress flow. A 3-month review on **2026-08-13** decides whether a second consumer has emerged. If none has, the agent is demoted to an inline prompt in `docs-claim-doc-shrinker` and this directory is removed. See the same-named section in the agent body.
