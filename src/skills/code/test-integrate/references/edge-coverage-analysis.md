# Edge Coverage Analysis

Loaded at `[EDGE-FEEDBACK]`. Defines methodology for the post-merge advisory check.

## Edge definition

- An "edge" is a `(caller_module, callee_module)` tuple where one module's function calls into another module's public function.
- Tracked granularity: module-to-module, not function-to-function (keeps the metric tractable).
- Public function = function in the callee's `__init__.py` `__all__` OR public-API surface.

## Source of truth

- `project/coverage/state/EDGE_COVERAGE.yaml` — ledger of edges currently exercised by the test suite.
- Each entry: `{caller: <dotted_path>, callee: <dotted_path>, exercised_by: [<test_id>...], first_seen_run: <run_id>}`.

## Computation

- Run `coverage_analyzer --edges` against the merged commit. Tool produces a fresh edge set.
- Diff against pre-merge `EDGE_COVERAGE.yaml` snapshot.
- New edges = post-merge edges minus pre-merge edges.

## Advisory rule (NOT a gate)

- If the merged integration test produces >=1 new edge -> record edges, no warning.
- If 0 new edges -> emit advisory warning as a comment on the merged PR: "integration test exercised no new cross-package edge — verify it isn't redundant with existing coverage."
- The warning is **advisory only** at the test-integrate stage. Don't block; don't revert. Track in `EDGE_COVERAGE.yaml` audit log for periodic review.

## Why advisory not gate

- Some real-integration tests legitimately exercise the same edges as mocked tests (the value is the real-service behavior, not new edges).
- Hard-gating on edges would punish DB serialization tests, error-path tests, latency tests — all of which add value without new edges.
- The audit log lets a future review identify systematic redundancy across runs.

## Audit log entry

- `{run_id, test_id, merged_sha, new_edges_count, warning_emitted: bool}` appended per item.

## Anti-patterns

- Treating edge count as a primary quality metric — it's a redundancy check, not a goodness measure.
- Blocking the merge retroactively on the warning.
- Ignoring repeated zero-edge warnings — investigate after 3+ in a row from the same module.

## Out of scope

- Computing edge coverage from scratch — that's `test-audit`'s job.
- Hard-gating coverage thresholds — `test-audit` and `test-evaluate` decide what's worth promoting; this stage is post-merge feedback.
