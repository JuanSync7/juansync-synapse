# delivery

Behavioral contracts governing sequential, TDD-disciplined plan-execution loops. Two subdomain groups: `execution` (subagent-side) and `orchestration` (main-agent-side). All consumed by `delivery-orchestration-plan-executor`.

## Protocols

| Protocol | Kind | Description |
|----------|------|-------------|
| [delivery-execution-slice-contract](delivery-execution-slice-contract.md) | contract | Normative definition of a slice — required fields, size bounds, violation signatures; enforced by main agent pre-dispatch |
