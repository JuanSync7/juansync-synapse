# code

Code generation, testing, and execution skills. Produces execution plans, test code, runs test suites, and operates the multi-stage test-coverage engine.

## Skills

| Skill | Role | Description |
|-------|------|-------------|
| [build-plan](build-plan/) | planner | Bias-free execution plan with agent isolation phases |
| [write-module-tests](write-module-tests/) | writer | Implements pytest test code from test-docs spec |
| [test-runner](test-runner/) | runner | Runs pytest suites with structured output and fix loop |
| [test-lint](test-lint/) | linter | Read-only lint sweep (ruff/mypy/bandit/vulture/detect-secrets + descriptive-test docstring validator) — produces LintReport feeding test-fix |
| [test-audit](test-audit/) | auditor | Read-only diagnostic audit of test coverage health — produces AuditGapReport feeding test-generate/evaluate/integrate |
| [test-fix](test-fix/) | fixer | Per-category lint remediation (ruff→mypy→bandit→vulture→secrets) with re-verification |
| [test-generate](test-generate/) | generator | Per-gap test generation with HARD-GATE intent review |
| [test-evaluate](test-evaluate/) | evaluator | Per-module mock-vs-real classification — emits IntegrationStrategy |
| [test-integrate](test-integrate/) | integrator | Per-item conversion of mock-integration tests to real-service tests; HITL-gated |
