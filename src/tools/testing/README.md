# src/tools/testing

Adopter tools for the test coverage engine — mechanical analyzers, scanners, and runners dispatched by the `code-test-*` skills. One entry per tool directory.

| Tool | Description |
|------|-------------|
| [code-test-analyze-coverage](code-test-analyze-coverage/TOOL.md) | Computes per-function coverage gaps and cross-package call graph edges from a test suite |
| [code-test-check-flakiness](code-test-check-flakiness/TOOL.md) | Runs a pytest test ≥10 times and computes fail rate to detect flaky tests before integration |
| [code-test-classify-boundaries](code-test-classify-boundaries/TOOL.md) | Classifies every function as boundary (runtime-exposed) or internal — directs where to apply boundary-style tests |
| [code-test-generate-strategies](code-test-generate-strategies/TOOL.md) | Emits Hypothesis @given strategies from function type hints — for property-based test generation |
| [code-test-map-branches](code-test-map-branches/TOOL.md) | Enumerates executable branches per public function — including transitive private helpers — for test generation |
| [code-test-report-lint](code-test-report-lint/TOOL.md) | Aggregates ruff, mypy, bandit, and vulture into a single structured LintReport |
| [code-test-run-mutations](code-test-run-mutations/TOOL.md) | Generates AST mutants of a target function and runs the test suite per mutant to detect weak assertions |
| [code-test-scan-secrets](code-test-scan-secrets/TOOL.md) | Scans a file for leaked secrets — auth headers, API keys, tokens, high-entropy strings |
| [code-test-score-assertions](code-test-score-assertions/TOOL.md) | Scores pytest test functions by assertion strength — flags trivial, tautological, and missing assertions |
| [code-test-validate-logs](code-test-validate-logs/TOOL.md) | Validates logging calls against a log archetype contract; computes log path coverage |
