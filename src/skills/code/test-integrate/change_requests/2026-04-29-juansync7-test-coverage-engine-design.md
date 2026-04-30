# Design Document — Autonomous Test Coverage Engine

> Brainstorm slug: `2026-04-28-test-strategy-improvements`
> Status: **complete** | Artifact: skill (creation) | Target: `juansync-synapse/src/skills/code/test-<verb>/`

---

## 1. Problem Statement

Existing test suites suffer from four compounding failures that leave production code under-protected:

1. **Coverage metrics lie.** Line coverage alone reports high percentages while missing weak assertions, untested module-to-module integration paths, and cross-boundary wiring. There is no off-the-shelf metric for call-graph edge coverage.
2. **Test generation is unreviewed.** LLMs can write syntactically correct tests that assert the wrong thing, cover only happy paths, or game coverage tools with `assert True`. Without a structured review gate, bad tests accumulate silently.
3. **Boundary detection is manual.** "What counts as a public boundary" is left to developer intuition — leading to over-testing of private internals and under-testing of HTTP handlers, Temporal activities, and CLI commands.
4. **Real integration is fragile.** No single lifecycle pattern per dependency category means teams pick ad hoc approaches that produce flaky tests, shared-state collisions, and slow CI.

What changes: a six-skill autonomous pipeline replaces manual test authoring with a structured generate → review → integrate loop, backed by deterministic tooling and explicit HITL gates at every point where LLM output reaches production.

---

## 2. Design Principles

### P1 — Four-layer architecture separation

Tools are deterministic, pydantic-typed, cross-project reusable equipment. Skills are stateful workflow recipes that define what and why. Agents are the runtime cooks that decide how. Data is project-local persistent state. Mixing these layers (e.g., putting routing logic in a tool, or project state in a skill) degrades reusability and makes auditing impossible.

**Implication:** Every new capability must be placed in exactly one layer; a capability that appears in two layers is a bug in the architecture, not a feature.

### P2 — Tools deterministic and reusable; skills stateful and project-scoped

Tools in `ai-synapse/tools/testing/` take typed inputs and return typed outputs with no side effects beyond their explicit contract. Skills in `juansync-synapse/src/skills/code/test-<verb>/` hold workflow state, gate semantics, and project-specific policy. Shared schemas (`ai-synapse/tools/testing/schemas.py`) are the single source of truth for all handoff contracts.

**Implication:** A tool can be called by any skill in any project without modification; a skill cannot be called by another skill's agent — only through the handoff chain.

### P3 — Two-tier HITL gates (soft / hard)

Not all human review is equal. Soft gates (for `fix` and `evaluate`) queue work for async review — the engine continues and the reviewer triages at their own pace. Hard gates (for `generate` and `integrate`) stop the engine entirely and require explicit approval before any code or test is committed. This distinction prevents the engine from accumulating unreviewed artifacts while keeping throughput high on low-risk stages.

**Implication:** Any skill that produces artifacts that reach production (tests, integration wrappers) must use a hard gate. Diagnostic or classification outputs use soft gates.

### P4 — Descriptive-test contract enables review-by-intent

Reviewers at the `generate` hard gate approve a list of human-readable intentions extracted from test docstrings — not the test code itself. This decouples the review signal from implementation detail. The descriptive-test contract (`@tests`, `@scenario`, `@asserts`, `@layer`, `@generation_id`) is enforced by `lint` as a pre-condition, so malformed tests never reach a human reviewer.

**Implication:** Any generated test missing a conforming docstring is a lint error, not a style warning — it blocks the pipeline before the hard gate fires.

### P5 — Three orthogonal coverage metrics

Line coverage, mutation kill rate, and edge coverage measure different failure modes and cannot substitute for each other. Line coverage catches unexecuted code. Mutation kill rate catches weak assertions. Edge coverage (a novel metric computed from the call graph) catches untested module-to-module integration paths. All three are required; a green line-coverage report with poor mutation kill rate or zero edge coverage is a false signal.

**Implication:** The `audit` skill must compute and report all three metrics; a gap in any one metric is a valid reason to trigger `generate`.

### P6 — Two-tier boundary definition

A function is a boundary if it is either logically exported (listed in `__init__.py` `__all__` or imported by tests or other packages) or runtime-exposed (decorated `@app.route`, `@activity.defn`, `@click.command`, or reads `request`/`os.environ`/`sys.stdin`). Internal functions (same-module only, not exported) receive mypy strict coverage and no boundary-style tests. Reclassification is grep-detectable and audited quarterly.

**Implication:** Boundary-style tests (Hypothesis, defensive-code coverage) apply only to boundary functions. Writing Hypothesis tests for private helpers is waste; missing them on HTTP handlers is a bug.

### P7 — Mock-by-default with explicit reclassification

`generate` mocks all external dependencies. `evaluate` later classifies which mocks should be replaced with real integration tests based on boundary tier, external dependency risk, and current mock coverage gap. This separation prevents `generate` from needing knowledge of real infrastructure and keeps the mock integration test suite fast and reproducible. `integrate` then executes only what `evaluate` has explicitly classified.

**Implication:** No real service is ever touched by `generate`. Any test that directly calls a real endpoint without going through the `evaluate` → `integrate` path is out-of-policy.

### P8 — Simplified 2-factor critical scoring

The priority heuristic is `recently_changed AND (public_api OR bug_history > 0)`. Four-factor formulas (complexity × change_freq × fan_in × boundary) give false precision and require continuous calibration. The 2-factor formula is grep-detectable, stable across projects, and easy to explain to reviewers. Additional factors are added only when data justifies — not by default.

**Implication:** `audit` and `generate` target critical-tier functions first; no scoring parameter tuning is needed at project onboarding.

---

## 3. Architecture

### 3.1 Flow Graph

<!-- VERBATIM -->
```
lint → LintReport → fix
fix → clean codebase → audit
audit → AuditGapReport + PriorityRanking → generate
generate → CoverageState + tests → evaluate
evaluate → IntegrationStrategy → integrate
integrate → real integration tests → human validates
```

Shared pydantic schemas live in `ai-synapse/tools/testing/schemas.py`. Both producing and consuming skills import from there.

### 3.2 Node Specifications

#### 3.2.1 — `test-lint`

**Load:**
- `rules/lint-constraints.md` (always-loaded): never auto-fix; report only; never suppress with `# noqa` without flagging; descriptive-test docstring rules.
- `references/ruff-config.md`, `references/mypy-strict.md`, `references/bandit-rules.md`, `references/vulture-thresholds.md`, `references/descriptive-test-rules.md`
- `templates/lint-report.md`

**Do:**
1. Scan repo root with `lint_reporter` (ruff + mypy + bandit + vulture JSON aggregator).
2. Run `secret_scanner`.
3. Validate test files against the descriptive-test contract; flag missing `@tests`, `@scenario`, `@asserts`, `@layer` tags as lint errors.
4. Aggregate all issues into a `LintReport` pydantic model.
5. Serialize report and hand off to `fix`.

**Don't:**
- Never auto-fix any source file.
- Never suppress issues with `# noqa` without flagging.
- Never modify test files.

**Exit:**
- All configured linters run to completion; `LintReport` serialized → hand off to `fix`.

**Output schema:**
```python
class LintIssue(BaseModel):
    tool: Literal["ruff", "mypy", "bandit", "vulture", "detect-secrets"]
    file: str
    line: int
    code: str
    message: str
    severity: Literal["error", "warning", "info"]

class LintReport(BaseModel):
    issues: list[LintIssue]
    files_scanned: int
    duration_ms: int
    descriptive_test_violations: list[LintIssue]  # subset, surfaced separately
```

**Deferred (creator decides):**
- Behavior on linter exit-code 2 (configuration error vs lint failure).
- Whether to bundle pre-commit-hook integration in the skill or leave to project setup.

---

#### 3.2.2 — `test-fix`

**Load:**
- `rules/fix-constraints.md` (always-loaded): never `type: ignore`, never remove security check, never delete code without high confidence, secret rotation out-of-scope.
- `references/mypy-fix-patterns.md`, `references/bandit-remediation.md`, `references/vulture-cleanup.md`, `references/secret-remediation.md`
- `templates/fix-report.md`

**Do:**
1. For each issue category (ruff → mypy → bandit → vulture → secrets): apply fix → re-run `lint_reporter` to verify → commit.
2. Open soft-gated PR with per-category change summary.
3. Continue (engine does not wait for review).

**Don't:**
- Never use `# type: ignore` to silence mypy without explicit reason in commit message.
- Never remove a security check from bandit findings — refactor instead.
- Never auto-delete code flagged by vulture unless confidence ≥ 90%.
- Never handle secret remediation autonomously — surface to human (rotation out-of-scope).

**Exit:**
- `LintReport.issues` empty OR all remaining issues flagged `requires-human-review` → soft-gated PR opened → hand off to `audit`.

**Deferred (creator decides):**
- Conflict resolution when fixes overlap (e.g., ruff autofix + mypy fix touch same line) — ordering rules.
- Commit granularity: per-issue, per-category, or per-file.

---

#### 3.2.3 — `test-audit`

**Load:**
- `rules/audit-constraints.md` (always-loaded): never modifies code or tests; read-only; emits report only.
- `references/coverage-analysis.md`, `references/critical-scoring.md`, `references/gaming-patterns.md`, `references/flakiness-detection.md`, `references/edge-coverage-analysis.md`, `references/dep-vulnerability.md`, `references/coverage-pyramid.md`
- `templates/audit-report.md`, `templates/coverage-state-schema.md`

**Do:**
1. Snapshot existing coverage (line + mutation + edge).
2. Score all functions by 2-factor heuristic → critical / standard / cold tiers.
3. Run `gaming_detector` (7+ AST-deterministic patterns).
4. Run `flakiness_checker` against `FLAKE_HISTORY.csv`.
5. Run `dep_vulnerability` scan.
6. Run `edge_coverage_analyzer` (static AST walk + runtime instrumentation).
7. Run `log_contract_validator` against `LOG_POLICY.yaml`.
8. Emit consolidated `AuditGapReport` + `PriorityRanking`.
9. Write timestamped entry to `AUDIT_HISTORY/`.

**Don't:**
- Never modify source code or test files.
- Never make priority decisions — report only; `generate` acts on the ranking.

**Exit:**
- All tools run to completion; report serialized → hand off to `generate`.

**Output schema (high-level):**
```python
class AuditGapReport(BaseModel):
    gaps: list[CoverageGap]            # per function
    priority_ranking: PriorityRanking  # critical/standard/cold tiers
    gaming_alerts: list[GamingAlert]
    flakiness_scores: dict[str, float] # test_id → fail_rate
    dep_vulnerabilities: list[DependencyVulnerability]
    edge_coverage_gaps: EdgeCoverageGaps
    log_contract_violations: list[LogContractViolation]
    audit_timestamp: datetime
    project_sha: str
```

**Deferred (creator decides):**
- Audit cadence: per-PR, nightly, on-demand — CLI flags expose all three.
- Whether report shows delta from last `AUDIT_HISTORY` entry or absolute snapshot.

---

#### 3.2.4 — `test-generate`

**Load:**
- `rules/generation-constraints.md` (always-loaded): never per-line, never `assert True`, ≥2 assertions, must include descriptive docstring, mock-by-default.
- `references/assertion-policy.md` (always-loaded): equality, raises, mock.assert_*, parametrize, approx, etc.
- `references/layer-unit.md`, `references/layer-config.md`, `references/layer-contract.md`, `references/layer-idempotency.md`, `references/layer-mock-integration.md`
- `references/hypothesis-strategies.md`, `references/descriptive-test-schema.md`
- `templates/test-file.md`, `templates/generation-pr.md`

**Do:**
1. For each gap in priority order (critical first):
   a. `branch_mapper` builds public-func → branches map.
   b. LLM crafts inputs to reach each leaf branch through public function.
   c. Apply Hypothesis when invariant exists (target ≥30% of unit tests).
   d. Generate test file with descriptive-test docstring (`@tests`, `@scenario`, `@asserts`, `@layer`, `@generation_id`).
   e. Run test → must pass green.
   f. `mutation_runner` per-gap (≤20 lines): all mutants must be killed.
   g. `assertion_quality` ≥ threshold; ≥2 assertions per test.
2. Open PR; extract descriptive-intent list from docstrings; present to reviewer.
3. **Hard gate:** stop and wait for approval.
4. On approval: commit tests, update `COVERAGE_STATE.yaml`.

**Hard gate workflow:**
```
generate produces tests
  ↓
extract descriptive-intent list from docstrings
  ↓
open PR with intent list as PR body
  ↓
notify reviewer (Slack/email — blocking)
  ↓
WAIT
  ↓ (approve)         ↓ (reject)
commit + update     mark gaps as
COVERAGE_STATE      "human-rejected", iterate
```

**Don't:**
- Never write per-line tests; per-function/branch only.
- Never `assert True` / `assert 1`.
- Never commit fewer than 2 assertions per test (structural + value required).
- Never create a new test file if an existing file covers the same module — append.
- Never test `_private` functions directly — cover through public callers.
- Never commit a failing test.
- Never contact real external services — mock all external dependencies.

**Exit:**
- All critical-tier gaps closed OR mutation kill rate ≥ project threshold OR human rejects intent list → hand off to `evaluate`.

**Deferred (creator decides):**
- Mutation kill-rate threshold for full project (starts at "all mutants killed for new gaps").
- Token budget per generation cycle — measure during first build.

---

#### 3.2.5 — `test-evaluate`

**Load:**
- `rules/evaluate-constraints.md` (always-loaded): analysis only, no code/test modification.
- `references/boundary-db.md`, `references/boundary-api.md`, `references/boundary-queue.md`, `references/boundary-file.md`, `references/boundary-cli.md`, `references/external-lib-policy.md`, `references/real-integration-checklist.md`
- `templates/integration-strategy.md`

**Do:**
1. For each module: detect boundary tier (logical / runtime / internal) using grep for `__init__.py` `__all__` and decorator patterns.
2. Identify mocked dependencies in existing tests.
3. Score replacement value: `boundary_tier × external_dependency_risk × current_mock_coverage_gap`.
4. Pick lifecycle pattern per category from the Real Integration Lifecycle table.
5. Emit `IntegrationStrategy` per module: which mocks to replace, with which pattern, why.
6. Open soft-gated PR with classification doc; continue (engine does not wait).

**Boundary classification rule:** logical (in `__init__.py` `__all__`) OR runtime (decorated `@app.route`/`@activity.defn`/`@click.command`, or reads `request`/`os.environ`/`sys.stdin`) → boundary. Else internal.

**Don't:**
- Never modify source code or test files.
- Never make the replace/keep decision for `integrate` — produce a classification doc only.

**Exit:**
- All top-N modules (by criticality) classified → `IntegrationStrategy` produced → soft-gated PR opened → hand off to `integrate`.

**Deferred (creator decides):**
- "Top-N" cutoff for evaluation — depends on project size.
- Whether to revisit prior `IntegrationStrategy` docs on each run or only score newly-changed modules.

---

#### 3.2.6 — `test-integrate`

**Load:**
- `rules/integration-constraints.md` (always-loaded): never auto-run against production, always ephemeral testcontainers, secret scrubbing for cassettes.
- `references/testcontainers-patterns.md`, `references/vcrpy-patterns.md`, `references/real-api-testing.md`, `references/docker-ci.md`, `references/lifecycle-patterns.md`
- `templates/integration-test.md`, `templates/recorded-response.md`

**Do:**
1. For each item in `IntegrationStrategy`:
   a. Pick pattern: transaction rollback / schema-per-test / vcrpy / ephemeral container.
   b. Spin up real service via testcontainers or record cassette via vcrpy.
   c. Convert mock-integration test to real-integration test (or write new).
   d. Run with `flakiness_checker` (≥10 reruns at this stage).
2. Open PR; **hard gate**: stop and wait for human review.
3. On approval: merge; tests run in tiered CI (slow tier).
4. After each integration test lands: recompute `EDGE_COVERAGE.yaml`; warn if no new edge exercised.

**Staged rollout:** Day 1 lifecycle pattern + tests. After 20 tests OR first flaky incident → flake tracking. After 5min CI runtime → tiered CI (unit+mock on push, real integration on merge to main, nightly full).

**Don't:**
- Never auto-run against production endpoints.
- Never reuse a shared cluster across tests — always ephemeral testcontainers.
- Never commit vcrpy cassettes without scrubbing secrets.
- Never mark a test `@pytest.mark.integration` without running `flakiness_checker` first.

**Exit:**
- All `IntegrationStrategy` items implemented → hard-gated PR approved → merged → human validates.

**Deferred (creator decides):**
- Quarantine SLA for flaky tests (1 week default, project may override).
- vcrpy recording strategy: record-once vs re-record on dependency upgrade.

---

### 3.3 Entry Gates

| Transition | Gate type | Gate conditions |
|---|---|---|
| `lint` → start | None | No precondition; `lint` accepts any repo root. |
| `lint` → `fix` | None | `lint` runs to completion; `LintReport` serialized. |
| `fix` → `audit` | Soft | Lint-clean codebase; soft-gated PR opened (reviewer may comment async). |
| `audit` → `generate` | None | `AuditGapReport` + `PriorityRanking` produced; read-only, no side effects. |
| `generate` → `evaluate` | **Hard** | Descriptive-intent list approved by human reviewer; tests committed; `COVERAGE_STATE.yaml` updated. |
| `evaluate` → `integrate` | Soft | `IntegrationStrategy` produced; soft-gated PR opened (reviewer may comment async). |
| `integrate` → done | **Hard** | Real integration tests reviewed and approved by human; no production endpoints auto-contacted. |

---

## 4. Coverage Metrics

Three orthogonal metrics are required. No single metric is sufficient; a passing score on two with a gap on the third is a reportable finding.

<!-- VERBATIM -->
| Metric | Catches | Tool |
|---|---|---|
| Line coverage | Unexecuted code | coverage.py |
| Mutation kill rate | Weak assertions | mutmut, per-gap + nightly |
| **Edge coverage** | Untested module-to-module integration | custom pytest plugin |

**Edge coverage** (novel):
- Treat call graph as `(caller_module, callee_module)` edges across top-level package boundaries.
- Coverage = fraction exercised by ≥1 integration-marked test.
- Compute via static AST walk (record cross-package edges) + runtime instrumentation (pytest plugin via sys.settrace or coverage.py extension).
- Edge weight = `call_count_in_static_graph × is_cross_boundary`.
- Engineering cost: real (no off-the-shelf tool); `pytest-trace` may serve as base.

**Coverage ratchet:** coverage never decreases; aim for 100% eventually.

---

## 5. Boundary Definition

<!-- VERBATIM -->
| Tier | Detection | Examples |
|---|---|---|
| Logical | listed in `__init__.py` `__all__` or imported by tests/other packages | module public API |
| Runtime | decorated `@app.route`, `@activity.defn`, `@click.command`; reads `request`/`os.environ`/`sys.stdin` | HTTP handlers, workers, CLI |

- Both tiers get boundary-style tests (Hypothesis, defensive-code coverage).
- Internal funcs (called only same-module, not exported) → mypy strict, no boundary tests.
- Re-classification = grep-detectable: function added to `__all__` or got a decorator.
- Quarterly audit: re-grep boundary callers; if a non-boundary function is now called from a boundary, re-classify.

---

## 6. HITL Gate Semantics

<!-- VERBATIM -->
| Type | Behavior | Where |
|---|---|---|
| **Soft** | PR opens, review queued, work continues. Reviewer comments async; engine moves on. | `fix`, `evaluate` |
| **Hard** | Engine stops. Waits for human approve/reject before proceeding. | `generate`, `integrate` |

- Soft gates → review backlog (Jira-like queue), reviewer triages async.
- Hard gates → blocking notification (Slack/email).

**Descriptive-test contract** (key for `generate` hard gate; validated by `lint`):

<!-- VERBATIM -->
```python
def test_chunker_handles_unicode_grapheme_clusters():
    """
    @tests: chunker.split_text
    @scenario: input contains emoji and combining characters
    @asserts: chunk boundaries don't split graphemes
    @layer: unit
    @generation_id: 2026-04-28-abc123
    """
```

Reviewers approve a list of intentions, not test code:
```
[ ] chunker.split_text — unicode graphemes → chunk boundaries don't split graphemes
[ ] chunker.split_text — empty string → returns []
[ ] retriever.search — query exceeds max length → raises QueryTooLong
```

Tests with malformed/missing description are rejected before review reaches a human.

---

## 7. Test Pyramid

<!-- VERBATIM -->
```
0. Pre-test:    ruff + mypy --strict + bandit + detect-secrets + vulture
1. Unit:        example tests + Hypothesis (≥30% of unit tests)
1.5 Performance: pytest-benchmark with regression budget
1.5 Observability: log archetype contract + log path coverage
2. Config:      pydantic + cross-field constraint table
3. Contract:    DB, API, schema, file format, queue, CLI (6 contract types)
4. Idempotency: process-twice invariant per persisting module
5. Mocked integration: end-to-end with mocks
6. Real integration: testcontainers + vcrpy with explicit lifecycle pattern
```

Mocks get ~92–95%. Remaining 5–8% (serialization quirks, real DB constraints, latency, wiring) requires real integration.

---

## 8. Hypothesis, Performance, and Observability Policies

### Hypothesis Policy

- **Apply when:** pure function with structured inputs; stateable invariant; user-shaped data.
- **Skip when:** one obvious mapping; nothing universal to assert; side-effect-heavy without invariant.
- **Target:** ≥30% of unit tests property-based; higher in parser/data-transform code.
- `from_type` derives strategies from type hints (enforces annotations as runtime contract).
- **CI tiers:** PR runs `max_examples=100`; nightly runs `max_examples=1000`.
- **Cost:** +10–30% wall-clock on a 1000-test suite. Acceptable.
- **Coexistence:** keep example tests for human-readable intent; add property tests for edge-case search.

### Performance Regression Policy

- **Tool:** `pytest-benchmark` with regression budgets (mean cannot grow >10%, p95 >20%).
- **Selection:** deterministic prefilter (call frequency via profiler, `is_in_init_py`, complexity-claim grep, recently-optimized commits) → LLM picks input shapes/sizes/baselines for top 20 → human review of initial benchmark set.
- **Baselines:** per-branch in CI artifact; PR fails on regression; nightly full-suite to dashboard.
- **Beyond pytest-benchmark:** pyinstrument (hot-spot), memray (memory), asv (long-term history).

### Observability / Log-Path Coverage

<!-- VERBATIM -->
```yaml
log_policy:
  ERROR:
    required_fields: [event, request_id, error_type]
    forbidden_fields: [password, raw_token, ssn, pan]
  WARNING:
    required_fields: [event, request_id]
  audit:
    required_fields: [event, actor_id, resource_id, action]
```

Log archetypes (3–5 per project): `error_event`, `audit_event`, `business_metric`, `debug_trace`. Each has a wrapper enforcing required fields.

Two enforcement layers:
1. Runtime adapter validates every log call against contract — raises in tests, warns + emits metric in prod.
2. Log path coverage as a separate metric: AST detect `logger.error(`/`logger.exception(` calls; verify each is exercised by ≥1 test.

Secret-leak tests stay explicit (negative-space): `assert "hunter2" not in caplog.text`.

---

## 9. Real Integration Lifecycle

<!-- VERBATIM -->
| Category | Pattern | Why |
|---|---|---|
| DB tests (most) | Transaction rollback (SQLAlchemy `nested=True`) | Fastest, works for 90% |
| DB tests with DDL/auto-commit | Schema-per-test | When transactions don't isolate |
| External APIs | vcrpy record/replay | Already standard |
| Whole-system | Ephemeral container per class | Cleanest, slowest — sparingly |

**Flake measurement:** test changes outcome with no code change (multiple outcomes within same `commit_sha`). `pytest-rerunfailures` records reruns → CI artifact → aggregate `(test_id, sha) → distinct_outcomes`. Test failing >2% of runs is quarantined within 1 week; quarantined tests excluded from required CI.

**Staged rollout:** Day 1 lifecycle pattern + tests. After 20 tests OR first flaky incident → flake tracking. After 5min CI runtime → cost sampling + tiered CI (unit+mock on push, real integration on merge to main, nightly full).

---

## 10. Mutation Testing, Gaming Detection, and Critical-Area Scoring

### Mutation Testing Tiers

<!-- VERBATIM -->
| When | Scope | Cost |
|---|---|---|
| Per-gap (in generate loop) | Only lines just covered (~5–20 lines) | Seconds |
| Per-PR | Skip — per-gap already validated | Free |
| Nightly/weekly | Full-project for pre-existing weak test detection | 1–3 hours, background |

Pure AST + test runner, no LLM. Targeted: only run on critical functions (top N by critical_scorer); rest get assertion_quality check.

### Gaming Detection

Seven or more AST-deterministic patterns detected by `gaming_detector`:
- `pragma: no cover` abuse (count threshold)
- `assert True` / `assert 1` padding
- Tests with no assertions
- Mocking the thing being tested
- Copy-paste tests (AST hash dedup)
- `_private` attribute assertions
- Self-referential test helpers

### Critical-Area Scoring (2-factor)

<!-- VERBATIM -->
```
priority = recently_changed AND (public_api OR bug_history > 0)
```

| Tier | Definition | Coverage target |
|---|---|---|
| Critical | recently_changed AND (public_api OR has_bug_history) | ~95% |
| Standard | most code | ~85% |
| Cold | untouched 6+ months, no bugs, internal | ~70% |

Iterate to add factors only when data justifies. Old `complexity × change_freq × fan_in × boundary` formula gave false precision — discarded.

---

## 11. Tool Inventory

<!-- VERBATIM -->
| Tool | Purpose | Used by |
|---|---|---|
| coverage_analyzer | CoverageGap[] per function | audit |
| branch_mapper | Public func → _private calls → all branches | generate |
| impact_analyzer | Git diff + coverage map → affected tests | audit, generate |
| critical_scorer | Priority tiers (2-factor heuristic) | audit |
| mutation_runner | AST mutants + test runner → MutationResult[] | generate (per-gap), nightly job |
| assertion_quality | Quality score per test | audit |
| lint_reporter | Structured lint issues (ruff/mypy/bandit/vulture JSON) | lint |
| secret_scanner | SecretScanResult[] | lint |
| dep_vulnerability | DependencyVulnerability[] | audit |
| flakiness_checker | Flakiness score (failures/runs over N repeats) | audit, integrate |
| gaming_detector | GamingAlert[] | audit |
| edge_coverage_analyzer | Static + runtime edge coverage on call graph | audit |
| log_contract_validator | Enforces log archetype contract; computes log path coverage | audit, generate |
| hypothesis_strategy_generator | Generates Hypothesis strategies from type hints | generate |
| benchmark_selector | Deterministic prefilter for perf benchmark candidates | audit, generate |
| schemas.py | Pydantic models for all tool I/O and skill handoff contracts | all |

All tools live in `ai-synapse/tools/testing/`. Shared schemas: `ai-synapse/tools/testing/schemas.py`.

---

## 12. Project-Specific State Layout

<!-- VERBATIM -->
```
project/coverage/
├── state/
│   ├── COVERAGE_STATE.yaml      # gaps, auto-generated test tracking, validation status
│   ├── EDGE_COVERAGE.yaml       # call-graph edges + exercised set
│   ├── BENCHMARK_BASELINES.json # per-branch perf baselines
│   ├── FLAKE_HISTORY.csv        # (test_id, sha, outcome) tuples
│   └── AUDIT_HISTORY/           # timestamped audit reports
├── INVENTORY.csv                # fixture inventory (input types × edge cases)
├── CONSTRAINT_TABLE.md          # config cross-field constraint table
└── LOG_POLICY.yaml              # log archetype contract
```

No scripts here — tools are in ai-synapse. State only.

---

## 13. Naming Conventions

**Pattern:** `test-<verb>`

- Domain: `testing`
- Skill domain (frontmatter): `code.test`
- Directory name: `test-<verb>` where verb ∈ `{lint, fix, audit, generate, evaluate, integrate}`

**Validation rule:** all six skills sit under `juansync-synapse/src/skills/code/test-<verb>/` with `domain: code.test` in their `SKILL.md` frontmatter. Terminal verb describes the outcome, not the mechanism.

**File locations:** `juansync-synapse/src/skills/code/test-<verb>/`

---

## 14. Test Suite Health (CI Shape)

- **Performance:** `pytest-xdist` (`-n auto`) + layered CI:
  - Fast tier (push): unit + mock integration.
  - Medium tier: + contract + config.
  - Slow tier (merge to main, nightly): everything.
- **Directory mirroring:** `tests/` mirrors `src/`; cross-cutting tests at boundary level.
- **Markers (9):** `unit, mock, integration, slow, idempotency, contract, config, regression, smoke`.
- **Coverage ratchet:** never decrease; aim for 100% eventually.

---

## 15. 4-Layer Architecture Reference

<!-- VERBATIM -->
```
Skills (recipe)     → define WHAT and WHY (workflow, policy, stopping conditions, gate semantics)
Agents (cook)       → decide HOW (execute, interact with tools, adapt)
Tools (equipment)   → provide CAPABILITY (deterministic, pydantic I/O, reusable)
Data (state)        → provide STATE (persistent, queryable, project-specific)
```

- Skills live in: `juansync-synapse/src/skills/code/test-<verb>/` (domain `code.test`)
- Tools live in: `ai-synapse/tools/testing/` (cross-project reusable)
- Data lives in: `project/coverage/` (project-specific state only)
- Shared schemas: `ai-synapse/tools/testing/schemas.py`

---

## 16. Accepted Tensions

| Tension | Decision | Revisit when |
|---|---|---|
| Custom edge-coverage tooling vs off-the-shelf | Custom pytest plugin (no off-the-shelf tool covers cross-package call-graph edges). `pytest-trace` evaluated as base. | An off-the-shelf tool emerges that covers cross-package edge coverage semantics. |
| Mutation testing cost vs coverage completeness | Per-gap only (seconds); nightly for full project. Per-PR skipped because per-gap already validates new lines. | CI runtime grows past acceptable threshold; then reconsider scope of per-gap mutation. |
| LLM benchmark selection vs deterministic prefilter | LLM alone unreliable; deterministic prefilter (call frequency, `is_in_init_py`, complexity-claim grep, recently-optimized commits) narrows candidates; LLM picks shapes/baselines for top 20; human reviews initial set. | LLM judgment on benchmark selection demonstrably improves with better prompting or tooling. |
| Hypothesis coexistence with example tests | Both maintained: example tests for human-readable intent, property tests for edge-case search. Extra wall-clock cost (+10–30%) accepted. | Cost becomes prohibitive (>50% CI wall-clock growth). |
| 6 skills vs merged audit+evaluate | Kept separate. Boundary analysis (evaluate) is distinct from gap generation (audit) and real infrastructure wiring (integrate). Reorganize via outcome-based epics E1–E6 instead of merging. | A strong operational argument for merging emerges (e.g., shared state causes sync bugs). |
| 2-factor scoring vs multi-factor formulas | 2-factor formula (`recently_changed AND (public_api OR bug_history > 0)`) preferred. Multi-factor gave false precision. | Data from ≥3 projects shows the 2-factor formula systematically misses high-risk functions. |
| "Top-N" cutoff for evaluate | Left to creator/project — no universal default. | A sensible default emerges from empirical data across projects. |

---

## 17. Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `test-lint` | produces for `fix` | `LintReport` (pydantic, `ai-synapse/tools/testing/schemas.py`) |
| `test-fix` | consumes from `lint`; produces for `audit` | clean codebase (lint passes) |
| `test-audit` | consumes from `fix`; produces for `generate` | `AuditGapReport` + `PriorityRanking` (pydantic, `schemas.py`) |
| `test-generate` | consumes from `audit`; produces for `evaluate` | `CoverageState` + test files + updated `COVERAGE_STATE.yaml` |
| `test-evaluate` | consumes from `generate`; produces for `integrate` | `IntegrationStrategy` (pydantic, `schemas.py`) |
| `test-integrate` | consumes from `evaluate`; produces for human | real integration tests committed to branch |
| `ai-synapse/tools/testing/schemas.py` | shared by all | single source of truth for all handoff pydantic models |
| `project/coverage/` | state consumed/written by `audit`, `generate`, `integrate` | `COVERAGE_STATE.yaml`, `EDGE_COVERAGE.yaml`, `FLAKE_HISTORY.csv`, `AUDIT_HISTORY/` |
