# Tool Vocabulary

Controlled values for the four slug slots defined in [`taxonomy/TOOL_TAXONOMY.md`](../taxonomy/TOOL_TAXONOMY.md) (`{domain}-{subdomain}-{action}-{target}`) plus the frontmatter-only `kind` field.

These values apply to **tools only** — they are NOT shared with skills, agents, or protocols. Each artifact type has its own independent slot vocabulary.

When creating a new tool, pick values from the tables below. If nothing fits, propose a new row in this file in the same PR — do not invent ad hoc values.

## Domains

| Domain | Description |
|--------|-------------|
| `synapse` | Framework-internal tools shipped by ai-synapse |
| `code` | Tools that operate on source code and test suites |

## Subdomains

| Subdomain | Description |
|-----------|-------------|
| `git` | Git/branch/CR automation |
| `test` | Test-suite quality, coverage, and generation support |

## Actions

| Action | Description |
|--------|-------------|
| `dispatch` | Routes work onto branches or queues |
| `analyze` | Computes structured metrics or reports from inputs |
| `check` | Repeated/empirical verification of a runtime property |
| `classify` | Assigns each input element to a category |
| `generate` | Emits new code or data artifacts |
| `map` | Enumerates structural elements into an index |
| `report` | Aggregates multiple sources into a single structured report |
| `run` | Executes a workload and collects results |
| `scan` | Pattern-searches content for findings |
| `score` | Assigns quality scores against a rubric |
| `validate` | Checks inputs against a contract and reports violations |

## Targets

| Target | Description |
|--------|-------------|
| `cr` | Change requests placed in `change_requests/` |
| `assertions` | Assertion statements in test functions |
| `boundaries` | Runtime-exposed (boundary) vs internal functions |
| `branches` | Executable branches in source functions |
| `coverage` | Test coverage data and call-graph edges |
| `flakiness` | Test fail-rate stability across repeated runs |
| `lint` | Lint findings from static-analysis tools |
| `logs` | Logging calls and log-contract conformance |
| `mutations` | AST mutants of source functions |
| `secrets` | Leaked credentials, tokens, and high-entropy strings |
| `strategies` | Hypothesis `@given` strategies for property-based tests |

## Kinds

| Kind | Description |
|------|-------------|
| `external` | Code lives elsewhere (MCP servers, CLI wrappers, npm/pip packages) |
| `internal` | Ships code — the tool IS the script or program |
| `wrapper` | Shell or Python wrapper around an external CLI |
