# Tool Registry

Mechanical capabilities — scripts, MCP servers, CLI wrappers, and external integrations. Dispatched by skills/agents (and occasionally invoked directly). Before creating a new tool, check if one already covers the capability you need.

Schema: see [registry/README.md](README.md).

| Tool | Description | Status | Consumers |
|------|-------------|--------|-----------|
| [synapse-git-dispatch-cr](../synapse/tools/synapse-git-dispatch-cr/TOOL.md) | Creates per-artifact feature branches from change requests placed by synapse-router-artifact-brainstormer | draft | synapse-router-artifact-brainstormer |
| [code-test-check-flakiness](../src/tools/testing/code-test-check-flakiness/TOOL.md) | Runs a pytest test ≥10 times and computes fail rate to detect flaky tests before integration | stable | — |
| [code-test-scan-secrets](../src/tools/testing/code-test-scan-secrets/TOOL.md) | Scans a file for leaked secrets — auth headers, API keys, tokens, high-entropy strings | stable | — |
| [code-test-analyze-coverage](../src/tools/testing/code-test-analyze-coverage/TOOL.md) | Computes per-function coverage gaps and cross-package call graph edges from a test suite | stable | — |
| [code-test-report-lint](../src/tools/testing/code-test-report-lint/TOOL.md) | Aggregates ruff, mypy, bandit, and vulture into a single structured LintReport | stable | code-test-linter |
| [code-test-map-branches](../src/tools/testing/code-test-map-branches/TOOL.md) | Enumerates executable branches per public function — including transitive private helpers — for test generation | stable | code-test-generator |
| [code-test-score-assertions](../src/tools/testing/code-test-score-assertions/TOOL.md) | Scores pytest test functions by assertion strength — flags trivial, tautological, and missing assertions | stable | code-test-generator |
| [code-test-validate-logs](../src/tools/testing/code-test-validate-logs/TOOL.md) | Validates logging calls against a log archetype contract; computes log path coverage | stable | — |
| [code-test-run-mutations](../src/tools/testing/code-test-run-mutations/TOOL.md) | Generates AST mutants of a target function and runs the test suite per mutant to detect weak assertions | stable | code-test-generator |
| [code-test-generate-strategies](../src/tools/testing/code-test-generate-strategies/TOOL.md) | Emits Hypothesis @given strategies from function type hints — for property-based test generation | stable | code-test-generator |
| [code-test-classify-boundaries](../src/tools/testing/code-test-classify-boundaries/TOOL.md) | Classifies every function as boundary (runtime-exposed) or internal — directs where to apply boundary-style tests | stable | code-test-evaluator |
