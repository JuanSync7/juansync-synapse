# Integration Constraints

Read-only invariants. Loaded at session start. Re-checked at [SPIN-UP] and [CONVERT] nodes. Violations halt the engine.

1. **NEVER auto-run real-integration tests against production endpoints.** Real tests MUST target either an ephemeral testcontainer or a recorded vcrpy cassette. Direct hits to production are categorically forbidden, even read-only — there is no "safe" production probe.

2. **Every strategy item MUST declare a non-production endpoint** before [SPIN-UP] proceeds. Reject any item whose endpoint matches the production blocklist: `*.prod.*`, `api.<company>.com` without a sandbox/staging prefix, raw IP literals inside production CIDR ranges, or any pattern enumerated in the project's `tests/integration/blocklist.yaml`. Project-specific patterns live in project config; the skill MUST load and enforce them.

3. **Testcontainers MUST be ephemeral.** Scope a container to one test class at most — never a session, never a module shared across files, never reused across runs. Always register teardown in the same fixture that spun it up. Reuse leaks state and breaks reproducibility.

4. **Vcrpy cassettes MUST be scrubbed before commit.** Required filter list: `Authorization` header, `X-API-Key` header, vendor-specific auth headers (`X-Anthropic-*`, `X-OpenAI-*`, `X-AWS-*`, etc.), all cookies, query-string secrets (`api_key`, `token`, `key`, `access_token`), and body fields (`password`, `token`, `secret`, `api_key`). Configure `filter_headers`, `filter_query_parameters`, and a `before_record_response` body scrubber on every cassette.

5. **Run `secret_scanner` against every cassette after recording.** Any positive detection MUST reject the [CONVERT] step — no manual override, no "false positive" flag. Re-record after fixing the scrubber config.

6. **One lifecycle pattern per strategy item.** A test uses *either* a testcontainer *or* a cassette — never both, never partial-record-partial-live. Mixing lifecycles produces tests that pass in CI and fail on replay.

7. **The hard human gate is blocking and absolute.** No auto-merge, no timeout-based advance, no "CI green = approved" shortcut. A human MUST explicitly approve each [CONVERT] before the engine advances. Gate state persists across sessions.

8. **NEVER delete the original mock-integration test before the real-integration replacement is merged to main.** The mock stays as the safety net until the real test has landed and run successfully on at least one nightly. Deleting earlier risks a coverage gap if the real test is reverted.

9. **Quarantine SLA is 7 days for items with fail rate ≥ 2%.** Quarantined items are excluded from required CI but remain tracked in `FLAKE_HISTORY.csv`. Revisit at SLA expiry — either fix or downgrade to mock-only with a documented reason.

10. **The engine MUST NOT advance to the next strategy item while a hard gate is open.** Gates are serial, not parallel — concurrent open gates indicate state corruption and require manual reconciliation.

11. **Real-integration tests run on merge-to-main and nightly only.** They are NOT part of per-push CI. This policy was adopted after integration-tier CI runtime exceeded 5 minutes; the staged rollout trades feedback latency for developer velocity. Do not re-enable per-push without explicit policy revision.

12. **Writes during execution are restricted.** The skill may write only to: `tests/cassettes/`, the new test file path declared in the strategy item, `COVERAGE_STATE.yaml`, `EDGE_COVERAGE.yaml`, and `FLAKE_HISTORY.csv`. NEVER modify source files, CI config, or unrelated tests — those changes belong in separate, human-authored PRs.
