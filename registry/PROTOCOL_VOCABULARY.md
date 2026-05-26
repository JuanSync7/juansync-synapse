# Protocol Vocabulary

Controlled values for the four slug slots defined in [`taxonomy/PROTOCOL_TAXONOMY.md`](../taxonomy/PROTOCOL_TAXONOMY.md): `{domain}-{subdomain}-{subject}-{kind}`.

These values apply to **protocols only** — they are NOT shared with skills, agents, or tools. Each artifact type has its own independent slot vocabulary.

When creating a new protocol, pick values from the tables below. If nothing fits, propose a new row in this file in the same PR — do not invent ad hoc values.

## Domains

| Domain | Description |
|--------|-------------|
| `synapse` | Framework-internal protocols shipped by ai-synapse |
| `delivery` | Plan-to-code execution — contracts governing slices, TDD discipline, closeouts, dispatch, and replan |

## Subdomains

| Subdomain | Description |
|-----------|-------------|
| `observability` | Execution traces, failure tags, telemetry schemas |
| `memory` | Working memory, state externalization, compaction-safe storage |
| `execution` | Worker-side contracts — what a single subagent does inside one dispatch |
| `orchestration` | Manager-side contracts — coordination, dispatch, closeout ingestion, plan mutation |

## Subjects

| Subject | Description |
|---------|-------------|
| `execution` | Subagent dispatch and execution flow |
| `external-memory` | File-based working memory that survives compaction |
| `failure-reporting` | Standardized failure tag emission |
| `slice` | The dispatchable leaf unit of work — one validable outcome, one subagent, one closeout |
| `tdd` | Test-driven development discipline collapsed with Ralph loop and validable-end-goal |
| `closeout` | Per-dispatch subagent report — validation result, files touched, lessons, next moves |

## Kinds

| Kind | Description |
|------|-------------|
| `trace` | Self-reported execution record format |
| `schema` | Structured data shape (fields, types, validation) |
| `contract` | Behavioral rules an agent must follow |
| `format` | Wire/output format specification |
| `spec` | Reference specification for a behavior or artifact |
| `standard` | Shared cross-cutting convention |
