---
name: test-evaluate
description: "consume post-generate CoverageState and emit per-module IntegrationStrategy documents — two-tier boundary detection, replacement-value scoring, lifecycle pattern assignment, soft-gate PR; analysis-only, never writes test code or spins up services"
domain: code
subdomain: test
scope: module
role: evaluator
tags: [test, evaluate, boundary-detection, integration-strategy, mock-classification, soft-gate]
user-invocable: true
argument-hint: "[--coverage-state PATH] [--top-n N|critical] [--rerun-mode source-changed|all] [--no-pr]"
---

Fifth stage of the 6-skill test coverage engine. Consumes `CoverageState` from `test-generate`; classifies each module's mocked dependencies through a 5-step per-module loop (detect boundary tier → identify mocks → score replacement value → assign lifecycle pattern → emit IntegrationStrategy). Produces one `IntegrationStrategy` per module, bundled into a soft-gated PR. Analysis-only — never writes test code, never modifies source, never spins up real services.

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

## MUST (every turn)
- Load `rules/evaluate-constraints.md` — read-only invariants apply at every node
- Record position: `Position: [node-id] — <context>`
- Process modules in `AuditGapReport.priority_ranking` order (critical first)
- Use the inline scoring formula exactly: `replacement_value = boundary_tier × external_dependency_risk × current_mock_coverage_gap`

## MUST NOT (global)
- Write or modify test code, source code, or fixtures — analysis only
- Spin up real services, containers, or databases during evaluation
- Score internal functions — `boundary_tier=0` excludes them; never invent weights
- Assign multiple lifecycle patterns to the same dependency
- Wait for reviewer feedback at [GATE] — this is a soft gate; engine completes without blocking
- Re-classify a module whose source is unchanged when `--rerun-mode source-changed` (default)

## Wrong-Tool Detection
- **User has no `CoverageState` on disk** → `/test-generate` first, then return here
- **User wants to write the real-integration tests** → `/test-integrate` (this skill only emits the strategy)
- **User wants to evaluate test code quality / lint** → `/test-lint`
- **User wants to find coverage gaps** → `/test-audit`

## Entry

### [NEW] Fresh session
Do:
  1. Parse arguments: `--coverage-state` (default `project/coverage/state/COVERAGE_STATE.yaml`), `--top-n` (default `critical` = all critical-tier modules from `AuditGapReport.priority_ranking`; integer also accepted), `--rerun-mode` (default `source-changed`), `--no-pr` (write strategies to disk; skip PR).
  2. Load `CoverageState` from disk; verify it parses against `src/skills/code/test-evaluate/schemas.py` `CoverageState` model. Verify at least one module has mocked-integration tests.
  3. Load `AuditGapReport.priority_ranking` if `--top-n critical`; otherwise use top-N by criticality score.
  4. If no qualifying modules → print "no modules with mocked-integration tests — nothing to evaluate" and exit (no PR, no state mutation).
  5. Confirm engine tools available in `src/tools/testing/`: `boundary_classifier`, `mock_inventory`, `coverage_analyzer`. Abort if missing.
  6. If `--rerun-mode source-changed`: load prior `IntegrationStrategy` documents; compute source-hash delta; skip unchanged modules.
Don't: Modify source or tests; proceed if `CoverageState` cannot be parsed.
Exit: → [LOAD]

## Flow

### [LOAD] Load shared rules + lifecycle table
Load: rules/evaluate-constraints.md, references/real-integration-checklist.md, references/lifecycle-patterns.md
Do: Establish read-only constraint for the session. Pre-load lifecycle pattern table (referenced at every [ASSIGN]). Initialize per-module accumulators: `strategies`, `skipped_internal`, `skipped_already_real`, `over_mocking_warnings`.
Don't: Load test files or source for modification; pre-load category boundary references (deferred to [DETECT] per module).
Exit: → [DETECT] (first module)

### [DETECT] Classify boundary tier per function
Load: rules/evaluate-constraints.md, references/boundary-<category>.md (per module category — db | api | queue | file | cli)
Do: For the current module, run `boundary_classifier`:
  - **Logical tier:** grep `__init__.py` for `__all__` exports — functions in `__all__` are logical-boundary candidates.
  - **Runtime tier:** grep source for `@app.route`, `@activity.defn`, `@click.command`, `@celery.task`, FastAPI/Flask handlers, and reads of `request` / `os.environ` / `sys.stdin` / `sys.argv` — matched functions are runtime-boundary.
  - Classify each function as `boundary-runtime`, `boundary-logical`, or `internal`.
  - If module has zero boundary-classified functions: log as `skipped_internal` ("no boundary functions detected") and advance.
Don't: Re-classify internal functions as boundary without a grep-detectable signal; descend into stdlib or third-party code.
Exit: → [IDENTIFY] (boundary functions found) | → [DETECT] (next module if all-internal)

### [IDENTIFY] Inventory mocked dependencies
Load: rules/evaluate-constraints.md
Do: Run `mock_inventory` on the test files covering this module. Enumerate every `@patch`, `Mock(spec=...)`, `MagicMock`, `monkeypatch.setattr`. Map each mock to the boundary function it shadows (by import path or attribute reference). Record:
  - Mock target (fully-qualified name)
  - Test files using the mock
  - Corresponding boundary function (or "no boundary match" → over-mock warning)
If module has no mocks (already uses real services): log as `skipped_already_real` and advance.
Don't: Evaluate mock correctness or test quality — that is `test-lint` / `test-audit`'s concern.
Exit: → [SCORE] (mock inventory non-empty) | → [DETECT] (next module if no mocks)

### [SCORE] Compute replacement value per mock
Do: For each mocked boundary dependency, compute `replacement_value = boundary_tier × external_dependency_risk × current_mock_coverage_gap`:
  - **`boundary_tier`:** runtime=3, logical=2, internal=0 (excluded — emit `over_mocking_warning` for any mock that resolves to an internal function).
  - **`external_dependency_risk`:** DB=5, external API=4, queue=3, file=2, CLI=1 (use category from [DETECT] — never invent weights).
  - **`current_mock_coverage_gap`:** fraction of boundary branches covered ONLY by mocked tests (0.0–1.0). Run `coverage_analyzer --boundary-only` against the module to derive this.
  - Rank candidates by `replacement_value`; exclude any with `replacement_value == 0`.
Don't: Score internal functions; invent risk weights not in the table; lower thresholds mid-run.
Exit: → [ASSIGN] (candidates with `replacement_value > 0`) | → [DETECT] (next module if all candidates score 0)

### [ASSIGN] Pick exactly one lifecycle pattern per candidate
Load: references/lifecycle-patterns.md
Do: For each ranked candidate, assign exactly one lifecycle pattern from the category table:
  - **DB:** prefer `transaction-rollback`; use `schema-per-test` only when DDL or auto-commit defeats transaction isolation.
  - **External API:** `vcrpy` (record/replay).
  - **Queue / whole-system:** `ephemeral-container` (Testcontainers / docker-compose).
  - **File:** `tmp_path` fixture for read/write; real FS for permission-sensitive paths.
  - **CLI:** subprocess fixture with captured stdout/stderr.
Apply decision rules verbatim from `references/lifecycle-patterns.md` — never improvise patterns.
Don't: Assign multiple patterns to one dependency; invent patterns not in the table; pick a pattern based on perceived elegance — match the rule.
Exit: → [EMIT]

### [EMIT] Write IntegrationStrategy document
Load: templates/integration-strategy.md, references/external-lib-policy.md
Do: Render `IntegrationStrategy` for the module to `project/coverage/state/integration-strategies/<module-slug>.md` using the template. Include: ranked candidate list, assigned lifecycle pattern per candidate, replacement-value score, justification (boundary tier + risk + gap), explicit out-of-scope list (internal functions skipped, third-party libs per `external-lib-policy.md`).
Don't: Emit test code, code diffs, or fixture skeletons — strategy is documentation only.
Exit: → [DETECT] (next module) | → [GATE] (all top-N modules processed)

### [GATE] Soft-gate PR with strategy bundle
Load: templates/strategy-pr.md
Do:
  1. If `--no-pr`: leave per-module strategies on disk under `project/coverage/state/integration-strategies/`; print path bundle and exit cleanly.
  2. Otherwise: bundle all emitted `IntegrationStrategy` documents into a single PR using `templates/strategy-pr.md`. Apply non-blocking GitHub label `integration-strategy-review`. Notify reviewer; do NOT wait.
  3. Update `COVERAGE_STATE.yaml`: per module, record `integration_strategy_path`, `boundary_classification`, `evaluate_run_id`, `source_hash` (for next-run delta detection).
Don't: Block on reviewer feedback; commit any test-tree files; modify source.
Exit: → [END]

### [END]
Do: Print PR URL (or strategy bundle path with `--no-pr`), per-module result table (classified / skipped-internal / skipped-already-real / over-mock-warnings), top-5 highest replacement-value candidates across the batch. Suggest `/test-integrate` as the next stage.
Don't: Auto-route or invoke `/test-integrate` directly — handoff is the user's call.
