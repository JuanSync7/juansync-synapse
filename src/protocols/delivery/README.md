# delivery

Behavioral contracts governing sequential, TDD-disciplined plan-execution loops. Two subdomain groups: `execution` (subagent-side) and `orchestration` (main-agent-side). All consumed by `delivery-orchestration-plan-executor`.

## Protocols

| Protocol | Kind | Description |
|----------|------|-------------|
| [delivery-execution-slice-contract](delivery-execution-slice-contract.md) | contract | Normative definition of a slice — required fields, size bounds, violation signatures; enforced by main agent pre-dispatch |
| [delivery-execution-tdd-contract](delivery-execution-tdd-contract.md) | contract | Subagent discipline collapsing TDD, Ralph loop, and validable-end-goal into one contract — test-first, iterate-to-green, cap-aware-`blocked` |
| [delivery-execution-coding-contract](delivery-execution-coding-contract.md) | contract | Subagent code-quality discipline — YAGNI, neighbors-first, no-dead-code, fail-loudly, green-tree-exit (lint+typecheck), security-tripwires; complements tdd-contract |
| [delivery-orchestration-closeout-schema](delivery-orchestration-closeout-schema.md) | schema | YAML structure subagents emit at dispatch end — dual-target atomic write (file before inline), extends synapse-observability-execution-trace |
| [delivery-orchestration-dispatch-contract](delivery-orchestration-dispatch-contract.md) | contract | Sequential-by-default subagent dispatch — 8 mandatory prompt slots, 4 pre-dispatch checks, explicit model selection, parallel escape hatch with three named conditions |
| [delivery-orchestration-replan-contract](delivery-orchestration-replan-contract.md) | contract | Closeout-driven plan-surface mutation rules — firing signals, allowed/forbidden mutations, mandatory CHANGELOG audit, M=3 escalation bound (skill-overridable) |
| [delivery-orchestration-gate-contract](delivery-orchestration-gate-contract.md) | contract | Customer-handoff gate between pipeline stages — block shape, 4 decision tokens (approve/revise/pause/abort), audit row, non-overrideable hold rule; consumed by delivery-program-orchestrator |
