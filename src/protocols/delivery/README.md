# delivery

Behavioral contracts governing sequential, TDD-disciplined plan-execution loops. Two subdomain groups: `execution` (subagent-side) and `orchestration` (main-agent-side). All consumed by `delivery-orchestration-plan-executor`.

## Protocols

| Protocol | Kind | Description |
|----------|------|-------------|
| [delivery-orchestration-dispatch-contract](delivery-orchestration-dispatch-contract.md) | contract | Sequential-by-default subagent dispatch — 8 mandatory prompt slots, 4 pre-dispatch checks, explicit model selection, parallel escape hatch with three named conditions |
