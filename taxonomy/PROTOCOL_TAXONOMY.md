# Protocol Taxonomy

Naming and metadata rules for protocols. The controlled vocabulary for each slug slot lives in [`registry/PROTOCOL_VOCABULARY.md`](../registry/PROTOCOL_VOCABULARY.md). The inventory of protocols currently in the repo lives in [`registry/PROTOCOL_REGISTRY.md`](../registry/PROTOCOL_REGISTRY.md). This file defines the *shape*; vocabulary holds the *values*; registry holds the *inventory*.

## Naming convention

`{domain}-{subdomain}-{subject}-{kind}` — lowercase-hyphenated. All four slots required.

- **`domain`** — ecosystem (e.g., `synapse`).
- **`subdomain`** — category within the domain (e.g., `observability`, `memory`).
- **`subject`** — noun naming what the protocol describes (e.g., `execution`, `failure-reporting`, `external-memory`).
- **`kind`** — noun naming the structural type (e.g., `trace`, `schema`, `contract`, `format`, `spec`, `standard`).

**Versioning.** When protocols version, append `-v{n}`: `payment-contract-v2`, `audit-log-schema-v3`.

## Examples

| Slug | Description |
|------|-------------|
| `synapse-observability-execution-trace` | Self-reported trace format capturing agent dispatch flow |
| `synapse-memory-externalization-contract` | Behavioral contract for offloading state across compaction boundaries |

**Anti-patterns:**

| Slug | Why it's wrong |
|------|----------------|
| `synapse-observability-trace-execution` | Slot order reversed — kind before subject. Reads "the trace execution"; should be `execution-trace`. |
| `synapse-observability-execution-tracer` | `tracer` is an agentive noun (a persona). Protocols are passive structures, not actors — use the structural noun `trace`. |

## Frontmatter

Required fields on every protocol `.md` file:

```yaml
name: <slug>           # must equal filename AND match {domain}-{subdomain}-{subject}-{kind}
domain: <value>
subdomain: <value>
subject: <noun>        # what the protocol describes
kind: <value>          # structural type (trace | schema | contract | format | spec | standard)
version: <int>         # integer; bump on breaking change. Slug suffix `-v{n}` must match.
```

## Tags

Freeform — no controlled list. Use lowercase, hyphenated multi-word tags (e.g., `execution-trace`, `self-reported`).
