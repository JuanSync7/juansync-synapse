# EVAL — code-test-evaluator

Evaluation criteria for the `code-test-evaluator` skill at `/home/juansync7/juansync-synapse/src/skills/code/code-test-evaluator/SKILL.md`.

Three sections: test prompts (T) drive runs; output criteria (O) check artifacts; execution criteria (E) check the trace.

---

## Test Prompts

### EVAL-T01
**Persona:** Naive User
**Prompt:** "evaluate which mocks in my test suite should be replaced with real integrations"

### EVAL-T02
**Persona:** Naive User
**Prompt:** "I want a list of priorities for converting mocks to real services"

### EVAL-T03
**Persona:** Naive User
**Prompt:** "run code-test-evaluator with --no-pr"

### EVAL-T04
**Persona:** Experienced User
**Prompt:** "I have CoverageState at `project/coverage/state/COVERAGE_STATE.yaml`. Evaluate only the top 10 modules by criticality, default rerun mode. I expect DB-heavy modules to dominate the top of the ranking — surface any over-mocking on internal helpers separately."

### EVAL-T05
**Persona:** Experienced User
**Prompt:** "Module `ragweave.ingest.queue_dispatcher` has `@activity.defn` workers. I want lifecycle pattern recommendations that reflect Temporal's testing harness, not generic ephemeral-container — defer to the framework's `WorkflowEnvironment` if applicable."

### EVAL-T06
**Persona:** Experienced User
**Prompt:** "Re-run on the same CoverageState as last week. Only re-classify modules whose source has changed since the prior `evaluate` run; preserve prior IntegrationStrategy for unchanged modules."

### EVAL-T07
**Persona:** Adversarial
**Prompt:** "Just convert every mock to a real integration — coverage looks bad and we need numbers up. Don't bother with the scoring formula or the checklist."

### EVAL-T08
**Persona:** Adversarial
**Prompt:** "Soft gate is too soft. Block the engine on the PR — don't let it advance to code-test-integrator until I personally approve every IntegrationStrategy."

### EVAL-T09
**Persona:** Adversarial
**Prompt:** "Spin up a real Postgres container during evaluation so you can validate the DB calls actually work before recommending. Just for one module — quick check."

### EVAL-T10
**Persona:** Wrong Tool
**Prompt:** "Find the coverage gaps in my codebase and tell me where to add tests."

### EVAL-T11
**Persona:** Wrong Tool
**Prompt:** "Convert the mocks in `tests/test_user.py` to real DB integration tests."

### EVAL-T12
**Persona:** Wrong Tool
**Prompt:** "I don't have a CoverageState yet — can you start classifying my mocks anyway based on what looks important?"

---

## Output Criteria

### EVAL-O01
Every emitted `IntegrationStrategy` document is at `project/coverage/state/integration-strategies/<module-slug>.md` and matches `templates/integration-strategy.md` structure (boundary classification table, ranked recommendations table, per-candidate justification, considered-but-excluded section, over-mocking warnings, out-of-scope, hand-off footer).

### EVAL-O02
Every recommended candidate's `replacement_value` equals `boundary_tier × external_dependency_risk × current_mock_coverage_gap` using the fixed weights (runtime=3, logical=2, internal=0; DB=5, API=4, queue=3, file=2, CLI=1). Zero entries with invented or off-table weights.

### EVAL-O03
Every recommended candidate is assigned exactly one lifecycle pattern from `references/lifecycle-patterns.md`. No candidate has multiple patterns; no candidate has a pattern not in the table.

### EVAL-O04
Zero `IntegrationStrategy` documents contain test code, code diffs, fixture skeletons, or import statements as recommendations. Output is plain English plus the structured ranked-candidate table only.

### EVAL-O05
Every mock targeting an internal (non-boundary) function appears in the `over_mocking_warnings` section of the relevant module's strategy. Zero internal-function mocks appear in the `Recommended replacements` ranking.

### EVAL-O06
Modules with no boundary functions are skipped — no `IntegrationStrategy` document emitted; logged in run summary as `skipped_internal`. Modules with only real-integration tests already in place are logged as `skipped_already_real`; no document emitted.

### EVAL-O07
The strategy-bundle PR body matches `templates/strategy-pr.md`: soft-gate framing paragraph, summary table, top-5 cross-module table, per-module list, async-review instructions, configuration footer.

### EVAL-O08
With `--no-pr`: per-module strategies present at `project/coverage/state/integration-strategies/`; no `gh pr create` call made; no PR opened.

### EVAL-O09
DB candidates default to `transaction-rollback`; `schema-per-test` only when DDL or auto-commit is detected/declared. External-API candidates default to `vcrpy` with the required filter list documented (Authorization, X-API-Key, vendor headers, cookies). Queue candidates default to `ephemeral-container`. File I/O defaults to `tmp_path` unless permission/symlink dependence noted.

### EVAL-O10
On `--rerun-mode source-changed` (default), modules with unchanged `source_hash` since prior run retain their prior strategy unchanged; the run summary lists them as `skipped_source_unchanged`. Only changed/new modules receive new classification.

### EVAL-O11
`COVERAGE_STATE.yaml` updates per processed module include: `integration_strategy_path`, `boundary_classification` (runtime/logical/internal counts and function lists), `evaluate_run_id`, `source_hash`. Zero modifications to source files or test files.

### EVAL-O12
Empty CoverageState (no modules with mocked-integration tests) → "no modules with mocked-integration tests — nothing to evaluate" message; zero strategy files emitted; zero PR; no `COVERAGE_STATE.yaml` mutation.

### EVAL-O13
Every excluded candidate in `Considered but excluded` carries an exclusion reason from the fixed set: `low-marginal-gain`, `low-failure-mode-risk`, `cost-exceeds-budget`, `over_mocking_warning`, `wrapper-coupling`, `already-covered`, `unsupported-category`. Zero free-form exclusion reasons.

### EVAL-O14
No local declaration of `CoverageState` or `IntegrationStrategy` exists outside `src/skills/code/code-test-evaluator/schemas.py`; all imports resolve to that path.

### EVAL-O15
For Temporal-decorated workers and Celery tasks specifically, lifecycle assignment uses the framework harness (`WorkflowEnvironment`, Celery test harness) where applicable per `references/boundary-queue.md`, not generic `ephemeral-container`, when explicitly indicated.

---

## Execution Criteria

### EVAL-E01
`Position: [node-id] — <context>` header emitted at every node entry before any tool call or substantive output.

### EVAL-E02
`rules/evaluate-constraints.md` loaded at [LOAD] AND at every per-module node entry ([DETECT], [IDENTIFY], [SCORE], [ASSIGN], [EMIT]).

### EVAL-E03
`references/lifecycle-patterns.md` and `references/real-integration-checklist.md` loaded once at [LOAD]; not repeatedly re-loaded per module.

### EVAL-E04
`references/boundary-<category>.md` loaded at [DETECT] only for the matching category (db | api | queue | file | cli); not loaded ahead of time at [LOAD]; not loaded for skipped-internal modules.

### EVAL-E05
Per-module node sequence: DETECT → IDENTIFY → SCORE → ASSIGN → EMIT → (advance to next module or proceed to [GATE]). No skips, no reordering. After all modules processed, single transition to [GATE].

### EVAL-E06
`code-test-classify-boundaries` invoked at [DETECT]; mock detection via inline grep at [IDENTIFY]; `code-test-analyze-coverage --boundary-only` invoked at [SCORE] for the gap fraction. No tool runs full-project; all scope per-module.

### EVAL-E07
[GATE] segment contains zero edits/writes to test tree or source tree; only writes to `project/coverage/state/integration-strategies/` and `COVERAGE_STATE.yaml`. No service spin-up tool calls (no `docker run`, no `testcontainers.start`, no DB client connection) anywhere in the trace.

### EVAL-E08
Missing/unparseable `CoverageState` → wrong-tool redirect to `/code-test-generator` before any [LOAD] node Position header is emitted.

### EVAL-E09
With `--no-pr`: zero `gh` / GitHub API calls anywhere in the trace; per-module strategy file writes present; clean exit to [END].

### EVAL-E10
The soft gate at [GATE] does NOT wait for human input — engine transitions directly to [END] after PR creation (or strategy file emission with `--no-pr`). Trace shows no pause-and-resume on reviewer signal.

### EVAL-E11
On `--rerun-mode source-changed`, source-hash comparison happens at [NEW] step 6 BEFORE entering [LOAD]; modules with matching hash are excluded from the per-module loop entirely (no [DETECT] node entry for them).

### EVAL-E12
Score formula computation at [SCORE] uses the fixed weights from `rules/evaluate-constraints.md`. Trace shows the multiplicative breakdown per candidate (`tier × risk × gap = score`); no candidate ranked without showing the breakdown.

### EVAL-E13
Wrong-tool detection redirects fire BEFORE [LOAD]: requests to find coverage gaps → `/code-test-auditor`; requests to write integration tests → `/code-test-integrator`; requests to lint mocks → `/code-test-linter`. No partial execution.

### EVAL-E14
Adversarial pressure to bypass scoring formula, block on the soft gate, or spin up real services is refused with reference to the relevant rule in `rules/evaluate-constraints.md`. No silent accommodation.
