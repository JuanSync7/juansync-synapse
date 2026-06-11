# Generation Constraints

Normative invariants enforced at every generation node. All rules are hard unless marked soft.

---

1. **No per-line tests.** Tests target branches, not lines. Generate exactly one test per leaf branch (if/else arm, raise path, early return, with-block exit). Never decompose a branch further into per-line cases; never merge two leaf branches into one test.

2. **No vacuous assertions.** `assert True`, `assert 1`, `assert x == x`, and `assert isinstance(x, type(x))` are banned unconditionally. Any assertion whose truth value is independent of the unit under test's behavior is banned. If an assertion cannot fail under any valid input, discard it.

3. **Minimum assertion count.** Every test must contain at least two assertions: one structural (type, shape, or key presence) and one value-level (equality, `pytest.raises`, or `mock.assert_called_with`). For parametrized tests, the minimum applies per parametrize case, not per test function.

4. **Mock by default.** All external dependencies — network I/O, filesystem, time, subprocess, and database — must be mocked unless the test is explicitly classified as a real-integration test by `code-test-evaluator`. Never mock the unit under test itself; mocking the SUT invalidates the test.

5. **Descriptive docstring required.** Every generated test must carry a docstring with exactly five tags: `@tests`, `@scenario`, `@asserts`, `@layer`, and `@generation_id`. No test may be committed without a conformant docstring. No tags may be abbreviated or omitted. The exact format is defined in `references/descriptive-test-schema.md`; that schema is authoritative.

6. **Public-API-only coverage of private symbols.** Functions prefixed with `_` must be exercised through their public callers, never called directly in test code. Direct invocation of `_private` symbols in test bodies is banned. If a private function has no public caller, classify the gap as `implementation-coupled` in the gap log and skip without generating a test.

7. **One test file per module.** Never create a new test file for a module that already has one. Append new tests to the existing file. If the existing file cannot be located, raise a resolution error rather than creating a duplicate.

8. **Hypothesis target of ≥30% of unit tests per gap.** This is a soft target tracked per gap; it does not block generation. Apply property-based tests when a generative invariant exists for the gap. Never force Hypothesis on single-mapping cases where no invariant can be stated.

9. **Failing tests are never committed.** The green-run gate is hard. A generated test that fails is rewritten once; if it still fails, it is discarded and the gap is logged as `unresolvable` for that cycle. No failing test may enter the working tree under any circumstance.

10. **Mutation gate is scoped per gap.** Mutation analysis targets only the lines directly covered by the current gap (~5–20 lines). Full-project mutation runs are the nightly job. Running full-project mutation inside the generation loop is banned.

11. **Hard gate is the only commit path.** No test reaches the working tree without explicit reviewer approval of the descriptive-intent list for that batch. Auto-approval is banned. Timeout-based approval is banned. Approval must be a discrete affirmative action.

12. **No re-attempt after human rejection.** A gap marked `human-rejected` is closed for the current cycle. It may not be retried, reformulated, or re-queued without a fresh `AuditGapReport` or an explicit re-trigger signal from the operator. Autonomous re-attempt after rejection is banned.
