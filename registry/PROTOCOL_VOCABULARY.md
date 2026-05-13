# Protocol Vocabulary

Controlled values for the four slug slots defined in [`taxonomy/PROTOCOL_TAXONOMY.md`](../taxonomy/PROTOCOL_TAXONOMY.md): `{domain}-{subdomain}-{subject}-{kind}`.

These values apply to **protocols only** — they are NOT shared with skills, agents, or tools. Each artifact type has its own independent slot vocabulary.

When creating a new protocol, pick values from the tables below. If nothing fits, propose a new row in this file in the same PR — do not invent ad hoc values.

## Domains

| Domain | Description |
|--------|-------------|
| `synapse` | Framework-internal protocols shipped by ai-synapse |

## Subdomains

| Subdomain | Description |
|-----------|-------------|
| `observability` | Execution traces, failure tags, telemetry schemas |
| `memory` | Working memory, state externalization, compaction-safe storage |

## Subjects

| Subject | Description |
|---------|-------------|
| `execution` | Subagent dispatch and execution flow |
| `external-memory` | File-based working memory that survives compaction |
| `failure-reporting` | Standardized failure tag emission |

## Kinds

| Kind | Description |
|------|-------------|
| `trace` | Self-reported execution record format |
| `schema` | Structured data shape (fields, types, validation) |
| `contract` | Behavioral rules an agent must follow |
| `format` | Wire/output format specification |
| `spec` | Reference specification for a behavior or artifact |
| `standard` | Shared cross-cutting convention |
