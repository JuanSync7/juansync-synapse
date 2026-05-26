# delivery

Behavioral contracts governing sequential, TDD-disciplined plan-execution loops. Two subdomain groups: `execution` (subagent-side) and `orchestration` (main-agent-side). All consumed by `delivery-orchestration-plan-executor`.

## Protocols

| Protocol | Kind | Description |
|----------|------|-------------|
| [delivery-execution-slice-contract](delivery-execution-slice-contract.md) | contract | Normative definition of a slice — required fields, size bounds, violation signatures; enforced by main agent pre-dispatch |
| [delivery-execution-tdd-contract](delivery-execution-tdd-contract.md) | contract | Subagent discipline collapsing TDD, Ralph loop, and validable-end-goal into one contract — test-first, iterate-to-green, cap-aware-`blocked` |
| [delivery-orchestration-closeout-schema](delivery-orchestration-closeout-schema.md) | schema | YAML structure subagents emit at dispatch end — dual-target atomic write (file before inline), extends synapse-observability-execution-trace |
| [delivery-orchestration-dispatch-contract](delivery-orchestration-dispatch-contract.md) | contract | Sequential-by-default subagent dispatch — 8 mandatory prompt slots, 4 pre-dispatch checks, explicit model selection, parallel escape hatch with three named conditions |
