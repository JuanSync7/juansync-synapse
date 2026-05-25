# delivery

Behavioral contracts governing sequential, TDD-disciplined plan-execution loops. Two subdomain groups: `execution` (subagent-side) and `orchestration` (main-agent-side). All consumed by `delivery-orchestration-plan-executor`.

## Protocols

| Protocol | Kind | Description |
|----------|------|-------------|
| [delivery-orchestration-closeout-schema](delivery-orchestration-closeout-schema.md) | schema | YAML structure subagents emit at dispatch end — dual-target atomic write (file before inline), extends synapse-observability-execution-trace |
