# Protocol Registry

Behavioral contracts injected into agents by consuming skills. Before creating a new protocol, check if one already covers the behavioral contract you need.

Schema: see [registry/README.md](README.md).

| Protocol | Description | Status | Consumers |
|------|-------------|--------|-----------|
| [synapse-observability-execution-trace](../synapse/protocols/observability/synapse-observability-execution-trace.md) | Structured self-report trace appended by subagents when an observer requests execution observability | draft | synapse-observability-failure-reporting-schema |
| [synapse-memory-external-memory-contract](../synapse/protocols/memory/synapse-memory-external-memory-contract.md) | Behavioral contract for file-based working memory — enables skills to externalize state into files that survive auto-compaction and context limits | draft | synapse-observability-failure-reporting-schema |
| [synapse-observability-failure-reporting-schema](../synapse/protocols/observability/synapse-observability-failure-reporting-schema.md) | Standardized failure tag format for agents and protocols — enables grepping, aggregation, and surfacing across multi-agent workflows | draft | synapse-memory-external-memory-contract, synapse-router-artifact-brainstormer, synapse-skill-companion-auditor |
| [delivery-orchestration-closeout-schema](../src/protocols/delivery/delivery-orchestration-closeout-schema.md) | YAML data shape every subagent emits at dispatch end — required fields, dual-target atomic write (file before inline), extends synapse-observability-execution-trace | draft | delivery-orchestration-plan-executor, delivery-orchestration-dispatch-contract, delivery-orchestration-replan-contract |
