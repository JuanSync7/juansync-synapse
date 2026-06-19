# delivery

Plan-to-code execution. Skills here orchestrate sequential, TDD-disciplined subagent dispatch to deliver a multi-slice plan, with closeout-driven plan mutation and resumable audit trail on the filesystem.

## Skills

| Skill | Role | Description |
|-------|------|-------------|
| [delivery-orchestration-plan-executor](delivery-orchestration-plan-executor/) | executor | Sequential plan-execution loop — dispatches one subagent per slice, ingests closeouts, mutates plan via replan-contract, terminates on stop conditions |
| [delivery-plan-writer](delivery-plan-writer/) | writer | Spec/PRD/intent → vertical-slice story-set + STORIES.md manifest; sits before the executor in the delivery pipeline |
| [delivery-program-orchestrator](delivery-program-orchestrator/) | orchestrator | Top-of-stack customer-facing router — drives a goal/PRD through spec → arch → scope → plan-writer → plan-executor with a non-overrideable gate between every stage; does not author artifact bodies |
