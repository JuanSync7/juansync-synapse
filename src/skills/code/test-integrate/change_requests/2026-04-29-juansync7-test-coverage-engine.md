# Decision Memo — test-integrate

> Artifact type: skill | Memo type: creation | Design doc: `.brainstorms/2026-04-28-test-strategy-improvements/design.md`

---

## What I want

A skill that takes the `IntegrationStrategy` document produced by `test-evaluate` and converts mock-integration tests into real integration tests — one lifecycle pattern per dependency category — then stops and waits for a human to validate the result before merging.

Key constraints baked into the intent:

- **Least autonomous of all 6 skills.** Real services are involved. The engine must never proceed autonomously when spinning up infrastructure or recording live cassettes.
- **HITL hard gate.** After generating and flakiness-checking the real integration tests, the skill opens a PR and stops. No merge, no further action, until a human approves.
- **Real services only via ephemeral testcontainers or recorded vcrpy cassettes.** Never auto-run against a production endpoint. Never reuse a shared cluster.
- **One lifecycle pattern per dependency category** (not all patterns for each dep) — keeps the test suite coherent and avoids redundancy.
- **Edge-coverage feedback loop.** After each integration test lands, recompute `EDGE_COVERAGE.yaml`. If no new cross-package edge is exercised, surface a warning.
- **Staged rollout.** Day 1 = lifecycle pattern + tests. Flake tracking and tiered CI are introduced only after 20 tests land or after the first flake incident, whichever comes first.

---

## Why Claude needs it

Without this skill, Claude's baseline behavior for integration testing has two failure modes:

1. **Skips real integration entirely.** Claude defaults to mocking all external dependencies because mocks are faster and require no infrastructure. The 5–8% of behavior that only manifests with a real DB (serialization quirks, constraint violations, transaction edge cases) or a live API (latency shaping, auth flow, real response structure) goes permanently untested.

2. **Runs tests against arbitrary endpoints unsafely.** When Claude does attempt real integration tests without explicit policy, it has no concept of production vs. ephemeral scope, no secret-scrubbing requirement for cassettes, no distinction between "spin up a testcontainer" and "use the staging database URL from the environment." This creates a silent risk of running tests against production or committing cassettes with embedded secrets.

There is also no lifecycle pattern selection logic in Claude's baseline. Claude does not know that DB tests should default to transaction rollback, that schema-per-test is only needed for DDL/autocommit cases, or that ephemeral-container-per-class is the slowest pattern and should be used sparingly. Without injected policy, Claude either applies one pattern everywhere or picks arbitrarily.

The skill closes all three gaps: lifecycle selection logic, production-safe infrastructure policy, and a hard human gate before any real tests merge.

---

## Injection shape

- **Workflow:** Per-strategy-item iteration with a 6-step loop. Each item in the `IntegrationStrategy` document goes through pattern selection → service spin-up → test conversion → flakiness check → hard gate → (on approval) merge. The hard gate is blocking: the engine emits a PR and waits. No items are processed in parallel across the gate boundary.
- **Policy:** Three always-loaded rules enforced at runtime:
  1. Never auto-run against production endpoints — ephemeral containers or cassettes only.
  2. testcontainers are always ephemeral (no shared cluster reuse across test sessions).
  3. vcrpy cassettes must be scrubbed of secrets before commit.
  Additional judgment rule: if an integration test lands and `EDGE_COVERAGE.yaml` shows no new cross-package edge exercised, emit a redundancy warning before committing.

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| Real integration test files | 1 per strategy item | Yes | Replace or supplement mock-integration tests with real-service tests |
| Updated `COVERAGE_STATE.yaml` | 1 | Yes | Reflect which mocks have been promoted to real integration tests |
| Updated `EDGE_COVERAGE.yaml` | 1 per item | Yes | Track new cross-package edges exercised by real integration tests |
| vcrpy cassette files | 0–N | Yes | Recorded API responses for external-API strategy items (secrets scrubbed) |
| Pull request (per hard gate) | 1 per strategy item | No | Human review gate with flakiness data and lifecycle pattern rationale |
| `FLAKE_HISTORY.csv` entries | N per test | Yes | Populated after 20 tests land or first flake incident |

---

## Flow graph

```
IntegrationStrategy
        |
        v
[PICK-PATTERN] — select lifecycle pattern for this item
        |
        v
[SPIN-UP] — start testcontainer OR record vcrpy cassette
        |
        v
[CONVERT] — rewrite mock-integration test to real-integration test
        |
        v
[FLAKE-CHECK] — run ≥10 reruns via flakiness_checker
        |
        v
[HARD-GATE] — open PR, notify human (Slack/email), STOP AND WAIT
        |
   (approve)           (reject)
        |                  |
        v                  v
[MERGE + UPDATE]    mark item as "human-rejected",
COVERAGE_STATE      surface reason, move to next item
EDGE_COVERAGE
        |
        v
[EDGE-FEEDBACK] — recompute EDGE_COVERAGE.yaml;
                   if no new edge → emit redundancy warning
        |
        v
  next item in IntegrationStrategy
```

---

## Node specifications

**[PICK-PATTERN]** — Load: `references/lifecycle-patterns.md`, `references/testcontainers-patterns.md`, `references/vcrpy-patterns.md`. Do: read the strategy item's dependency category and select exactly one lifecycle pattern using the category table (transaction rollback for most DB tests; schema-per-test for DDL/autocommit; vcrpy record/replay for external APIs; ephemeral container per class for whole-system). Do not: apply more than one pattern per strategy item; do not default to ephemeral container when a cheaper pattern fits. Exit: pattern selected → SPIN-UP.

**[SPIN-UP]** — Load: `references/testcontainers-patterns.md`, `references/docker-ci.md`, `references/vcrpy-patterns.md`, `rules/integration-constraints.md`. Do: for container-based patterns, start an ephemeral testcontainer scoped to the test class; for vcrpy patterns, set cassette path and begin record mode pointed at a non-production endpoint. Do not: reuse a shared container across test sessions; point a recorder at a production URL; skip secret-scrubbing configuration before recording. Exit: service available → CONVERT.

**[CONVERT]** — Load: `templates/integration-test.md`, `templates/recorded-response.md`, `references/real-api-testing.md`. Do: locate the existing mock-integration test for this strategy item; rewrite it to use the real service (or cassette replay); apply `@pytest.mark.integration` marker; ensure teardown is correctly scoped (rollback / container stop / cassette close). Do not: delete the mock-integration test before human approval; leave secrets inline in cassette files; produce a test that passes only because the mock was left in place. Exit: test file written → FLAKE-CHECK.

**[FLAKE-CHECK]** — Load: `ai-synapse/tools/testing/schemas.py` (for `FlakinessSummary`). Do: run the new integration test ≥10 times using `flakiness_checker`; record outcomes; compute fail rate. Do not: skip reruns even if the first 10 all pass; suppress intermittent failures. Exit: fail rate < 2% → HARD-GATE; fail rate ≥ 2% → quarantine item (mark as flaky in `COVERAGE_STATE.yaml`, defer to next sprint, move to next strategy item without opening PR).

**[HARD-GATE]** — Load: none (this is a coordination node). Do: open a PR with the test diff, lifecycle pattern rationale, and flakiness result; send a blocking notification (Slack/email); stop all further processing on this strategy item. Do not: merge autonomously under any condition; proceed to the next item while this gate is open; time out the gate without human input. Exit: human approves → MERGE + UPDATE; human rejects → mark item as "human-rejected" with reason, move to next item.

**[MERGE + UPDATE]** — Load: `ai-synapse/tools/testing/schemas.py`. Do: merge the approved PR; update `COVERAGE_STATE.yaml` to reflect the promoted integration test; recompute `EDGE_COVERAGE.yaml` for the newly exercised cross-package edges. Do not: update coverage state before the PR is merged. Exit: state updated → EDGE-FEEDBACK.

**[EDGE-FEEDBACK]** — Load: `references/edge-coverage-analysis.md` (from `audit` references). Do: compare pre- and post-merge `EDGE_COVERAGE.yaml`; if the integration test exercises at least one new `(caller_module, callee_module)` edge, record it; if no new edge is exercised, emit a warning message: "integration test didn't expand edge coverage — is it redundant?" and surface it as a review comment on the merged PR. Do not: block the merge retroactively; treat the warning as a gate (it is advisory only at this stage). Exit: warning emitted or new edge recorded → move to next strategy item.

---

## Entry gates

| Transition | Gate |
|---|---|
| Start → PICK-PATTERN (first item) | `IntegrationStrategy` document is present and non-empty; `COVERAGE_STATE.yaml` exists (post-generate). |
| FLAKE-CHECK → HARD-GATE | Fail rate < 2% over ≥10 reruns. |
| FLAKE-CHECK → quarantine | Fail rate ≥ 2%. Item marked flaky; skip to next item without opening PR. |
| HARD-GATE → MERGE + UPDATE | **Hard gate. Human explicitly approves the PR.** Engine does not proceed without explicit approval signal. |
| HARD-GATE → next item | Human explicitly rejects. Item marked "human-rejected" with reason. |
| MERGE + UPDATE → EDGE-FEEDBACK | PR merged; state files updated. |
| EDGE-FEEDBACK → next item | Warning emitted (if applicable) and acknowledged; edge coverage file written. |

---

## Edge cases considered

| Edge case | Handling |
|---|---|
| Quarantine SLA | Flaky tests (fail rate ≥ 2%) are quarantined for up to 1 week (default; creator picks project-specific SLA). Quarantined tests are excluded from required CI. After SLA expires, creator decides: fix or delete. |
| vcrpy re-recording on dependency upgrade | Re-recording strategy (record-once vs. re-record on dep upgrade) is left to creator. The skill must always scrub secrets from cassettes regardless of recording mode. |
| Integration test exercises no new edge | Emit advisory redundancy warning as a review comment on the merged PR. Do not block or revert. Track in `EDGE_COVERAGE.yaml` comments for future audit. |
| Staged rollout triggers | Day 1: lifecycle pattern + tests only. After 20 tests land OR after first flaky incident (whichever is first): activate `FLAKE_HISTORY.csv` tracking. After CI runtime exceeds 5 minutes on the integration tier: introduce tiered CI (unit+mock on push; real integration on merge to main; nightly full suite). |
| Production endpoint accidentally in strategy item | `rules/integration-constraints.md` must catch this at SPIN-UP. If a strategy item's recorded endpoint resolves to a production URL, abort the item, emit an error, and surface it to the human as a configuration issue — do not record or run. |
| Mock left in place after conversion | CONVERT node verifies the test actually calls the real service (not the mock). If the mock is still active in the test body, the test is rejected before FLAKE-CHECK. |

---

## Companion files anticipated

**Always-loaded (every node):**
- `rules/integration-constraints.md` — never auto-run against production, always ephemeral testcontainers, secret scrubbing required for all cassettes. Loaded at skill start; enforced at SPIN-UP and CONVERT.

**References (loaded at relevant nodes):**
- `references/testcontainers-patterns.md` — ephemeral container setup, scope, teardown patterns. Loaded at PICK-PATTERN and SPIN-UP.
- `references/vcrpy-patterns.md` — cassette record/replay, scrubbing configuration, re-record triggers. Loaded at PICK-PATTERN and SPIN-UP.
- `references/lifecycle-patterns.md` — verbatim copy of the Real Integration Lifecycle category table (transaction rollback / schema-per-test / vcrpy / ephemeral container per class). Loaded at PICK-PATTERN. Sourced from notepad cross-cutting section "Real Integration Lifecycle"; cite design doc §Real Integration Lifecycle for authoritative table.
- `references/real-api-testing.md` — external API test patterns (auth, error handling, timeout behavior). Loaded at CONVERT.
- `references/docker-ci.md` — CI configuration for Docker-dependent tests (resource limits, layer caching, network setup). Loaded at SPIN-UP.

**Templates:**
- `templates/integration-test.md` — test file scaffold for real integration tests (marker, fixture pattern, teardown). Loaded at CONVERT.
- `templates/recorded-response.md` — cassette file structure and scrubbing checklist. Loaded at CONVERT for vcrpy items.

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `test-evaluate` | consumes | `IntegrationStrategy` document — per-module classification of which mocks to replace, with which lifecycle pattern, and why. This is the primary input to the skill. |
| `ai-synapse/tools/testing/flakiness_checker` | consumes | `FlakinessSummary` pydantic model — fail rate over N reruns per test. Used at FLAKE-CHECK. |
| `ai-synapse/tools/testing/coverage_analyzer` | consumes | Edge coverage delta — verify new integration test exercises at least one new cross-package edge. Used at EDGE-FEEDBACK. |
| `ai-synapse/tools/testing/schemas.py` | consumes | Shared pydantic models: `IntegrationStrategy`, `FlakinessSummary`, `CoverageState`, `EdgeCoverageReport`. |
| Real integration test branch | produces for human | PR with test diff, lifecycle pattern rationale, and flakiness result. Human is the final node — they validate and approve or reject. |
| `project/coverage/state/COVERAGE_STATE.yaml` | produces | Updated to reflect promoted integration tests (mock → real). |
| `project/coverage/state/EDGE_COVERAGE.yaml` | produces | Updated with newly exercised cross-package call graph edges. |
| `project/coverage/state/FLAKE_HISTORY.csv` | produces | Populated with `(test_id, sha, outcome)` tuples after staged rollout threshold is reached. |

---

## Open questions

1. **Quarantine SLA duration.** The notepad specifies 1 week as the default but explicitly defers the final value to the creator. Choose a project-appropriate SLA and document it in `rules/integration-constraints.md`.

2. **vcrpy re-recording strategy.** Record-once (stable cassette, update manually) vs. re-record on dependency version bump (automatic but noisier). The notepad leaves this to the creator. The choice affects how `references/vcrpy-patterns.md` should be written and whether the skill needs a "re-record" sub-mode.

3. **Parallel vs. sequential item processing.** The flow graph above processes one strategy item at a time through the hard gate. The creator should decide whether items that use different lifecycle patterns (e.g., one DB test and one API test) can be batched into a single PR, or whether one PR per item is required. One-per-item is safer for human review but increases PR volume.

4. **Hard gate notification channel.** The notepad specifies "Slack/email — blocking" but does not name the channel or integration. Creator must wire this to the project's actual notification infrastructure.

5. **"Human-rejected" item disposition.** When a human rejects a PR at the hard gate, the item is marked "human-rejected" in `COVERAGE_STATE.yaml`. The creator should define whether rejected items re-enter the `IntegrationStrategy` on the next run, are permanently excluded, or require an explicit override flag to re-attempt.
