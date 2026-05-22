# Tool Vocabulary

Controlled values for the four slug slots defined in [`taxonomy/TOOL_TAXONOMY.md`](../taxonomy/TOOL_TAXONOMY.md) (`{domain}-{subdomain}-{action}-{target}`) plus the frontmatter-only `kind` field.

These values apply to **tools only** — they are NOT shared with skills, agents, or protocols. Each artifact type has its own independent slot vocabulary.

When creating a new tool, pick values from the tables below. If nothing fits, propose a new row in this file in the same PR — do not invent ad hoc values.

## Domains

| Domain | Description |
|--------|-------------|
| `synapse` | Framework-internal tools shipped by ai-synapse |

## Subdomains

| Subdomain | Description |
|-----------|-------------|
| `git` | Git/branch/CR automation |

## Actions

| Action | Description |
|--------|-------------|
| `dispatch` | Routes work onto branches or queues |

## Targets

| Target | Description |
|--------|-------------|
| `cr` | Change requests placed in `change_requests/` |

## Kinds

| Kind | Description |
|------|-------------|
| `external` | Code lives elsewhere (MCP servers, CLI wrappers, npm/pip packages) |
| `internal` | Ships code — the tool IS the script or program |
| `wrapper` | Shell or Python wrapper around an external CLI |
