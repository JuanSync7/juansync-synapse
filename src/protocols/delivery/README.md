# delivery

Behavioral contracts governing sequential, TDD-disciplined plan-execution loops. Two subdomain groups: `execution` (subagent-side) and `orchestration` (main-agent-side). All consumed by `delivery-orchestration-plan-executor`.

## Protocols

| Protocol | Kind | Description |
|----------|------|-------------|
| [delivery-orchestration-replan-contract](delivery-orchestration-replan-contract.md) | contract | Closeout-driven plan-surface mutation rules — firing signals, allowed/forbidden mutations, mandatory CHANGELOG audit, M=3 escalation bound (skill-overridable) |
