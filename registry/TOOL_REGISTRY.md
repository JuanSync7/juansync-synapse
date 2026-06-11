# Tool Registry

Mechanical capabilities — scripts, MCP servers, CLI wrappers, and external integrations. Dispatched by skills/agents (and occasionally invoked directly). Before creating a new tool, check if one already covers the capability you need.

Schema: see [registry/README.md](README.md).

| Tool | Description | Status | Consumers |
|------|-------------|--------|-----------|
| [synapse-git-dispatch-cr](../synapse/tools/synapse-git-dispatch-cr/TOOL.md) | Creates per-artifact feature branches from change requests placed by synapse-router-artifact-brainstormer | draft | synapse-router-artifact-brainstormer |
| [flakiness-checker](../src/tools/testing/flakiness_checker/) | Runs a pytest test ≥10 times and computes fail rate to detect flaky tests before integration | draft | — |
| [secret-scanner](../src/tools/testing/secret_scanner/) | Scans a file for leaked secrets — auth headers, API keys, tokens, high-entropy strings | draft | — |
| [coverage-analyzer](../src/tools/testing/coverage_analyzer/) | Computes per-function coverage gaps and cross-package call graph edges from a test suite | draft | — |
| [lint-reporter](../src/tools/testing/lint_reporter/) | Aggregates ruff, mypy, bandit, and vulture into a single structured LintReport | draft | code-test-linter |
| [branch-mapper](../src/tools/testing/branch_mapper/) | Enumerates executable branches per public function — including transitive private helpers — for test generation | draft | code-test-generator |
| [assertion-quality](../src/tools/testing/assertion_quality/) | Scores pytest test functions by assertion strength — flags trivial, tautological, and missing assertions | draft | code-test-generator |
| [log-contract-validator](../src/tools/testing/log_contract_validator/) | Validates logging calls against a log archetype contract; computes log path coverage | draft | — |
| [mutation-runner](../src/tools/testing/mutation_runner/) | Generates AST mutants of a target function and runs the test suite per mutant to detect weak assertions | draft | code-test-generator |
| [hypothesis-strategy-generator](../src/tools/testing/hypothesis_strategy_generator/) | Emits Hypothesis @given strategies from function type hints — for property-based test generation | draft | code-test-generator |
| [boundary-classifier](../src/tools/testing/boundary_classifier/) | Classifies every function as boundary (runtime-exposed) or internal — directs where to apply boundary-style tests | draft | code-test-evaluator |
