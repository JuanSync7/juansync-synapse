# test-evaluate constraints

Hard normative invariants for the `test-evaluate` skill. Always loaded. All rules are hard unless explicitly marked `(soft)`.

## 1. Read-only execution

Never write test files, source files, or fixtures. The only filesystem writes permitted are `project/coverage/state/integration-strategies/*.md` and updates to `COVERAGE_STATE.yaml`. Any other write is a contract violation — abort and surface the attempted path.

## 2. No service spin-up

Never start containers, databases, queues, HTTP servers, or any runtime dependency during evaluation. This skill is static analysis only; live probing belongs to `test-integrate`. Reject any plan step that calls `docker`, `compose`, `testcontainers`, server bootstraps, or network connects.

## 3. Two-tier boundary detection only

Boundary classification combines two signals: logical (presence in `__all__` exports) AND runtime (decorator pattern or IO-call grep — DB clients, HTTP clients, queue producers, file IO, CLI entrypoints). No heuristic guessing, no LLM-vibes inference. If neither signal fires, the function is internal. Period.

## 4. Internal functions excluded from strategies

Functions resolved to `boundary_tier=0` are internal and MUST NOT appear in any `IntegrationStrategy` document. Existing mocks that target internal functions are recorded as `over_mocking_warning` entries on the strategy index — surfaced for the reviewer, never converted into integration recommendations.

## 5. Scoring formula is fixed

`replacement_value = boundary_tier × external_dependency_risk × current_mock_coverage_gap`. Boundary weights: runtime=3, logical=2, internal=0. External-dependency risk weights: DB=5, API=4, queue=3, file=2, CLI=1. These weights are frozen — never invent new tiers, never override per-project, never tune at runtime. Coverage gap is `1 - existing_integration_coverage_ratio` clamped to `[0, 1]`.

## 6. One lifecycle pattern per dependency

Each external dependency receives exactly one recommended lifecycle pattern (session/module/function-scoped, ephemeral container, in-memory fake, etc.). No stacking, no "either/or" recommendations. The decision rules in `references/lifecycle-patterns.md` are authoritative — apply them deterministically.

## 7. Soft gate at PR (soft)

The engine does not block on reviewer response. After emitting strategies, open the PR and continue to `test-integrate`. Reviewer feedback is async and applied on the next rerun. This contrasts with `test-generate`, which hard-gates on reviewer approval before touching test code.

## 8. Source-hash delta on rerun

When invoked with `--rerun-mode source-changed` (the default), compare each module's current source hash against the value recorded in `COVERAGE_STATE.yaml` from the prior run. Modules with matching hashes MUST be skipped — preserve their prior `IntegrationStrategy` verbatim. Re-classify only on hash mismatch, newly discovered modules, or explicit `--rerun-mode all`.

## 9. Strategy is documentation, not code

`IntegrationStrategy` documents are plain English plus the structured ranked-candidate table. No test code, no diffs, no fixture skeletons, no import stubs, no pytest decorators. Code generation is `test-integrate`'s job. If a recommendation cannot be expressed in prose, it does not belong here.

## 10. No mock quality judgement

Mock correctness, vacuous-assertion detection, assertion strength, and overall test quality are out of scope — `test-lint` and `test-audit` own those. This skill classifies boundary tier and recommends a lifecycle pattern. Do not flag weak mocks, brittle assertions, or stylistic test issues; ignore them even when obvious.
