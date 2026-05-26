# delivery

Plan-to-code execution. Skills here orchestrate sequential, TDD-disciplined subagent dispatch to deliver a multi-slice plan, with closeout-driven plan mutation and resumable audit trail on the filesystem.

## Skills

| Skill | Role | Description |
|-------|------|-------------|
| [delivery-orchestration-plan-executor](delivery-orchestration-plan-executor/) | executor | Sequential plan-execution loop — dispatches one subagent per slice, ingests closeouts, mutates plan via replan-contract, terminates on stop conditions |
