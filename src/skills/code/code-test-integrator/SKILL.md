---
name: code-test-integrator
description: "consume IntegrationStrategy from code-test-evaluator and convert mock-integration tests to real-service tests one item at a time — pattern selection, ephemeral spin-up, conversion, flakiness check, hard-gate PR per item; never auto-merges, never points at production"
domain: code
scope: test
role: integrator
tags: [test, integrate, real-services, testcontainers, vcrpy, hard-gate, hitl]
user-invocable: true
argument-hint: "[--strategy-dir PATH] [--item ID] [--rerecord] [--retry-rejected] [--notify CHANNEL]"
---

Sixth and final stage of the test coverage engine. Consumes `IntegrationStrategy` documents from `code-test-evaluator`; for each strategy item, picks one lifecycle pattern, spins up an ephemeral service (or records a cassette), converts the mock-integration test to real-integration, validates flakiness over ≥10 reruns, then opens a hard-gate PR and **stops**. Engine never auto-merges; human approval is the only path forward.

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

## MUST (every turn)
- Load `rules/integration-constraints.md` — read at session start, enforced at [SPIN-UP] and [CONVERT]
- Record position: `Position: [node-id] — <context>`
- Process strategy items sequentially through the hard gate; never parallelize across [HARD-GATE]
- Assign exactly one lifecycle pattern per strategy item

## MUST NOT (global)
- Auto-merge a PR — `[HARD-GATE]` requires explicit human approval, no exceptions, no timeout
- Run real tests against a production endpoint — ephemeral testcontainers or recorded cassettes only
- Reuse a shared/long-lived testcontainer across test sessions — every container is ephemeral
- Commit a vcrpy cassette without scrubbing secrets (Authorization, X-API-Key, vendor headers, cookies, tokens)
- Delete the original mock-integration test before the real test is human-approved and merged
- Apply more than one lifecycle pattern to a single strategy item
- Process the next strategy item while a hard gate is open

## Wrong-Tool Detection
- **No `IntegrationStrategy` documents on disk** → `/code-test-evaluator` first, then return here
- **User wants the classification, not the conversion** → `/code-test-evaluator`
- **User wants to write fresh mock-integration tests** → `/code-test-generator`
- **User wants to evaluate test code quality / lint** → `/code-test-linter`

## Entry

### [NEW] Fresh session
Do:
  1. Parse arguments: `--strategy-dir` (default `project/coverage/state/integration-strategies/`), `--item` (single item id; default = process all), `--rerecord` (re-record vcrpy cassettes for items where dependency version changed), `--retry-rejected` (re-attempt items previously marked `human-rejected`), `--notify` (notification channel; default `gh-pr-review`).
  2. Discover `IntegrationStrategy` documents in `--strategy-dir`; verify each parses against `src/skills/code/code-test-evaluator/schemas.py` `IntegrationStrategy` model.
  3. Verify `project/coverage/state/COVERAGE_STATE.yaml` exists and parses against `CoverageState` model.
  4. Confirm engine tools available: `flakiness_checker`, `coverage_analyzer`, `secret_scanner`. Abort if missing.
  5. Build per-item work queue ordered by source `IntegrationStrategy` ranking (replacement_value descending). Filter out items already merged (`status: merged`), already rejected (`status: human-rejected`) unless `--retry-rejected`, and currently flaky-quarantined within SLA window.
  6. If queue empty → print "no strategy items to integrate — nothing to do" and exit.
Don't: Modify source or tests; proceed if any `IntegrationStrategy` fails schema parse.
Exit: → [PICK-PATTERN] (first item in queue)

## Flow

### [PICK-PATTERN] Select lifecycle pattern for this item
Load: rules/integration-constraints.md, references/lifecycle-patterns.md, references/testcontainers-patterns.md, references/vcrpy-patterns.md
Do: Read the strategy item's dependency category and `recommended_pattern`. Confirm exactly one pattern from the table:
  - **DB:** `transaction-rollback` (default) | `schema-per-test` (DDL or auto-commit only)
  - **External API:** `vcrpy` record/replay
  - **Queue / whole-system:** `ephemeral-container` (Testcontainers / docker-compose) — including framework harnesses (`WorkflowEnvironment`, Celery test harness) when indicated
  - **File:** `tmp_path` | real-FS for permission-sensitive paths
  - **CLI:** subprocess fixture
If the strategy item's `recommended_pattern` conflicts with the category table → abort item, log `pattern-mismatch` in run summary, advance to next item.
Don't: Apply more than one pattern; substitute "ephemeral-container" when a cheaper pattern fits; improvise patterns not in the table.
Exit: → [SPIN-UP]

### [SPIN-UP] Stand up ephemeral service or open recorder
Load: rules/integration-constraints.md, references/testcontainers-patterns.md, references/vcrpy-patterns.md, references/docker-ci.md
Do:
  - **Container patterns:** Start an ephemeral testcontainer scoped to the test class (DB image pinned to project version; resource limits per `references/docker-ci.md`). Confirm container is reachable; record container handle for teardown.
  - **vcrpy patterns:** Set cassette path under `tests/cassettes/<module>/<test_name>.yaml`. Configure scrubbing filters before opening recorder: `Authorization`, `X-API-Key`, vendor-specific headers, cookies, query-string secrets. Verify endpoint URL is **not** a production host (compare against `rules/integration-constraints.md` production-host blocklist; abort item with `production-endpoint-detected` error if matched).
  - If `--rerecord` AND the item has an existing cassette: delete the prior cassette and open recorder fresh.
Don't: Reuse a shared cluster; point a recorder at production; skip secret-scrubbing config; spin up before pattern is confirmed.
Exit: → [CONVERT]

### [CONVERT] Rewrite mock-integration test as real-integration test
Load: rules/integration-constraints.md, templates/integration-test.md, templates/recorded-response.md, references/real-api-testing.md
Do:
  1. Locate the existing mock-integration test referenced by the strategy item (`mock_target` → test file path).
  2. Render a **new** test file using `templates/integration-test.md` (or `templates/recorded-response.md` for vcrpy items): `@pytest.mark.integration` marker, fixture pattern matching the lifecycle pattern, scoped teardown (rollback / container stop / cassette close).
  3. Verify the new test calls the real service: AST-scan the new test for any residual `@patch`, `Mock(...)`, `monkeypatch.setattr` targeting the boundary dependency. If found → reject conversion, abort item with `mock-still-active` error.
  4. Keep the original mock-integration test in place — it stays until the new test is merged at [MERGE-UPDATE].
  5. For vcrpy items: after the test runs once to record, run `secret_scanner` against the cassette. If any secret is detected → fail conversion, abort item with `cassette-secret-leak` error, delete the cassette.
Don't: Delete the mock test now; emit a test that passes only because the mock was left in place; leave secrets inline in cassettes.
Exit: → [FLAKE-CHECK]

### [FLAKE-CHECK] Validate stability over ≥10 reruns
Load: rules/integration-constraints.md, src/tools/testing/flakiness_checker/schemas.py
Do: Invoke `flakiness_checker` to run the new integration test ≥10 times in isolation. Compute fail rate (failures / total runs). Record outcomes into a `FlakinessSummary` per `src/tools/testing/flakiness_checker/schemas.py`.
  - **Fail rate < 2%** → proceed to [HARD-GATE].
  - **Fail rate ≥ 2%** → mark item `flaky-quarantined` with 7-day SLA in `COVERAGE_STATE.yaml`; teardown service; advance to next item without opening PR. Quarantined items are excluded from required CI; revisited after SLA expiry.
Don't: Stop early after the first 10 pass; suppress intermittent failures; lower the threshold mid-run.
Exit: → [HARD-GATE] (fail rate < 2%) | → next item (quarantined)

### [HARD-GATE] Open PR and STOP
Load: templates/integration-pr.md
Do:
  1. Create a feature branch and open one PR per strategy item using `templates/integration-pr.md`. PR body includes: lifecycle pattern + rationale, flakiness summary (runs, failures, fail rate), test diff, list of new boundary call sites exercised, secret-scan attestation for cassettes.
  2. Apply blocking GitHub label `integration-real-services-review`.
  3. Send notification per `--notify` channel (default: GitHub PR review request).
  4. **STOP processing this item.** Do not advance to the next item until the PR receives an approval or rejection signal.
  5. On resume:
     - **Approval signal** (PR `APPROVED` review by maintainer) → [MERGE-UPDATE].
     - **Rejection signal** (PR `CHANGES_REQUESTED` review with `decline` keyword, or PR closed without merge) → mark item `human-rejected` with the reviewer's reason in `COVERAGE_STATE.yaml`; teardown service; advance to next item.
Don't: Auto-merge; time the gate out; merge based on CI green alone; advance to next item while this gate is open.
Exit: → [MERGE-UPDATE] (approved) | → next item (rejected)

### [MERGE-UPDATE] Merge approved PR and update state
Load: src/skills/code/code-test-evaluator/schemas.py
Do:
  1. Merge the approved PR (squash merge on default branch).
  2. Delete the original mock-integration test (it's now superseded by the merged real test).
  3. Update `COVERAGE_STATE.yaml` for the promoted module: set status `real-integrated`, record `real_test_path`, `lifecycle_pattern`, `flake_summary`, `integrate_run_id`, `merged_sha`.
  4. Append `(test_id, merged_sha, outcome=passed)` row to `FLAKE_HISTORY.csv` if staged-rollout threshold reached (≥20 tests already landed OR a prior flake incident triggered tracking).
Don't: Update state before merge confirmation; squash unrelated commits; leave the mock test behind.
Exit: → [EDGE-FEEDBACK]

### [EDGE-FEEDBACK] Recompute edge coverage and surface redundancy warning
Load: references/edge-coverage-analysis.md
Do: Run `coverage_analyzer --edges` against the merged commit. Compare new `EDGE_COVERAGE.yaml` against the pre-merge snapshot. If at least one new `(caller_module, callee_module)` edge is exercised → record edges and proceed. If zero new edges → emit advisory warning as a comment on the merged PR: "integration test exercised no new cross-package edge — verify it isn't redundant with existing coverage." Track in `EDGE_COVERAGE.yaml` audit log.
Don't: Block or revert the merge; treat the warning as a gate; gate further items on this signal.
Exit: → next item (back to [PICK-PATTERN]) | → [END] (queue empty)

### [END]
Do: Print run summary table: items processed, merged, human-rejected, flaky-quarantined, pattern-mismatch, production-endpoint-detected, cassette-secret-leak, mock-still-active. List PR URLs for merged items. Surface any redundancy warnings from [EDGE-FEEDBACK]. Suggest manual review of quarantined items past SLA.
Don't: Auto-route to another skill; auto-revisit quarantined items in this run.
