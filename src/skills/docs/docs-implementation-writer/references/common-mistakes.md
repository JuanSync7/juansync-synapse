# Common Mistakes

| Mistake | Consequence | Fix |
|---|---|---|
| Pattern entries copied into Phase 0 | implement-code agents biased toward reference implementation; test agents compromised if they see patterns | Copy ONLY Contract entries verbatim; pattern entries do not appear in this document |
| Phase 0 stubs have implementation hints (comments, pseudocode, `pass`) | Agents bias toward the hint, not the spec | Stubs: signature + docstring + `raise NotImplementedError("Task N")` only — strip everything else |
| Phase 0 skipped or rushed past review gate | Bad contracts propagate to every task section; fixing Phase 0 after task sections are written requires rewriting all affected sections | Phase 0 review gate is mandatory — never write a task section until Phase 0 is approved |
| Task section missing isolation contract block | implement-code dispatcher must construct its own isolation prompt, creating inconsistency across tasks | Every task section includes the verbatim isolation contract block from the template |
| Phase 0 contracts not inlined in task section (references "see Phase 0") | implement-code agent must read full Phase 0 to find its contracts, violating isolation and increasing context | Inline only the relevant stubs for this task directly in the task section |
| Task implementation steps not FR-tagged | No post-implementation traceability; can't verify which FRs were addressed | Every implementation step references at least one FR number |
| Integration contracts use "A and B interact" | Ambiguous caller/callee; agents may invert call direction | Always `A → B` format with explicit error propagation expectation |
| Error taxonomy missing Retryable column | Callers inconsistently implement retry logic | Every error row must have a Retryable value; "Unknown — caller decides" is acceptable |
| Task sections written out of dependency order | Section agent for Task 3 references Phase 0 contracts not yet approved and injected | Strict ascending order by topological sort; each section only references already-approved prior outputs |
| Dependency graph not checked for cycles | Invalid DAG; implement-code deadlocks trying to follow circular dependencies | Verify DAG property during Planning Stage before producing any `order` assignments |
| Orphan task (no FR reference) | Task has no traceability; can't verify it satisfies a real requirement | Every task section must reference at least one FR/REQ ID in "Spec requirements" |
| Document scope not checked before starting | One giant doc covering multiple subsystems; task sections from different subsystems mixed | One docs file per subsystem — if design doc covers multiple, produce separate files |
