# Real-Integration Checklist

## Purpose

Real-integration tests cost real engineering time — lifecycle setup, flakiness budget, CI minutes. This checklist filters scored candidates so each recommendation in `IntegrationStrategy` is justified, not merely high-scoring on the formula. Apply as a final gate after `[SCORE]`; demote any candidate that fails.

## Pre-conditions (all must hold)

1. **Boundary tier > 0.** Internal functions are excluded — already enforced in `[SCORE]`, reaffirmed here. Tier-0 candidates never reach `IntegrationStrategy`.
2. **Coverage gap is real.** `current_mock_coverage_gap > 0.2`. If mock-only branches are <20% of boundary branches, marginal coverage gain does not justify lifecycle cost. Below the floor, keep the mock and surface as `low-marginal-gain`.
3. **Lifecycle pattern is well-defined.** The dependency must map to exactly one pattern in `references/lifecycle-patterns.md`. If no pattern applies (novel category), surface as `unsupported-category` and skip — do not improvise lifecycle.
4. **Failure mode is observable.** Bugs that real integration would catch (serialization, isolation, timeout, schema drift) must plausibly affect this code path. If the boundary call is read-only and idempotent against a static schema, surface as `low-failure-mode-risk`.
5. **CI cost is bounded.** A single test using the assigned lifecycle pattern must run under ~5s P95 in isolation. If the only viable pattern pushes the test over budget (e.g., container cold-start for one assertion), surface as `cost-exceeds-budget` and recommend keeping the mock with a soak-test note.

## Disqualifiers (any one excludes the candidate)

- Mock target resolves to an internal function → emit `over_mocking_warning`; no recommendation.
- Boundary function is wrapped in retry/circuit-breaker logic the test would have to defeat → flag `wrapper-coupling`; recommend testing the wrapper at the unit layer instead.
- Module already has real-integration tests covering the candidate (per `CoverageState` scan) → mark `already-covered`; emit no new recommendation.

## Surfacing in IntegrationStrategy

- **Recommended candidates:** ranked by `replacement_value`, with assigned lifecycle pattern and one-line justification.
- **Filtered candidates:** listed in a separate "considered but excluded" section with the disqualifier reason. Reviewers must see what was rejected and why.

## Anti-patterns

- Recommending real integration for every high-scoring candidate without applying the checklist — produces flaky, slow suites.
- Suppressing the "considered but excluded" section — strips reviewer context for re-evaluation later.
- Treating the checklist as advisory — every disqualifier is hard. Do not override.

## Re-run behavior

- On `--rerun-mode source-changed`, re-apply the checklist only to changed modules.
- Preserve prior recommendations for unchanged modules even if checklist thresholds shifted; calibration changes are out-of-band and must not silently invalidate stable recommendations.
