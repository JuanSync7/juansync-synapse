# Common Mistakes

| Mistake | Consequence | Fix |
|---|---|---|
| Orphan task (no REQ reference) | Task has no traceability — can't verify it satisfies a real requirement | Every task must reference at least one REQ/FR ID |
| Uncovered requirement | Spec requirement not assigned to any task — will be missed during implementation | Cross-check traceability table against full spec REQ list |
| Circular dependencies between tasks | Invalid DAG — implement-code deadlocks trying to follow dependency chain | Verify DAG property during Planning Stage before writing task sections |
| Vague task description ("set up and configure") | Implementing agent doesn't know the deliverable — produces wrong or incomplete output | Description states what the task produces, not what it does |
| Subtasks not independently verifiable | Can't confirm progress — "make it work" has no checkpoint | Each subtask is atomic and verifiable: "Define X", "Implement Y", "Wire Z" |
| Pattern entry labelled as contract | implement-code agents receive implementation hints in Phase 0, biasing approach and compromising test agents | Use the bias test: "Would showing this to a test-writing agent compromise the test?" |
| Contract entry labelled as pattern | write-implementation-docs Phase 0 is missing types/stubs — agents can't build against incomplete interfaces | Contracts define interfaces (types, stubs, exceptions); patterns show algorithms |
| Contract stubs with implementation hints | Agents bias toward the hint instead of reasoning from the spec | Stubs: signature + docstring + `raise NotImplementedError("Task X.Y")` only — strip everything else |
| TypedDict fields missing FR tags | No traceability from code surface back to requirements | Every field gets an inline `# FR-xxx` comment |
| Dependency graph missing critical path | Implementing team can't identify bottleneck tasks for prioritization | Mark longest dependency chain with `[CRITICAL]` |
| Task decomposition not reviewed before detail sections | Bad decomposition propagates to every section — fixing it means rewriting all | Task decomposition review gate is mandatory — never write detail sections until approved |
| Single mega-task covering half the spec | Can't parallelize — one agent gets everything, others wait | Split until each task is S or M complexity (3-6 subtasks each) |
| Scope not checked — one doc covering multiple subsystems | Document grows unwieldy, mixed concerns, different subsystems' tasks interdepend | One design doc per subsystem — if spec covers multiple, produce separate files |
| Risks not noted for L complexity tasks | Team blindsided by integration failures or edge cases | All L tasks must have a Risks field with what could go wrong and mitigation |
