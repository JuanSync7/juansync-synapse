# code

Code generation, testing, and execution skills. Produces execution plans, test code, runs test suites, and operates the multi-stage test-coverage engine.

## Skills

| Skill | Role | Description |
|-------|------|-------------|
| [code-build-planner](code-build-planner/) | planner | Bias-free execution plan with agent isolation phases |
| [code-test-writer](code-test-writer/) | writer | Implements pytest test code from test-docs spec |
| [code-test-runner](code-test-runner/) | runner | Runs pytest suites with structured output and fix loop |
| [code-test-linter](code-test-linter/) | linter | Read-only lint sweep (ruff/mypy/bandit/vulture/detect-secrets + descriptive-test docstring validator) — produces LintReport feeding code-test-fixer |
| [code-test-auditor](code-test-auditor/) | auditor | Read-only diagnostic audit of test coverage health — produces AuditGapReport feeding code-test-generator/evaluate/integrate |
| [code-test-fixer](code-test-fixer/) | fixer | Per-category lint remediation (ruff→mypy→bandit→vulture→secrets) with re-verification |
| [code-test-generator](code-test-generator/) | generator | Per-gap test generation with HARD-GATE intent review |
| [code-test-evaluator](code-test-evaluator/) | evaluator | Per-module mock-vs-real classification — emits IntegrationStrategy |
| [code-test-integrator](code-test-integrator/) | integrator | Per-item conversion of mock-integration tests to real-service tests; HITL-gated |
