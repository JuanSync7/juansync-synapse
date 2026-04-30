# Decision Memo — test-audit

> Artifact type: skill | Memo type: creation | Design doc: `.brainstorms/2026-04-28-test-strategy-improvements/` (design doc TBD — shared contracts sourced from notepad cross-cutting sections)

---

## What I want

A fully autonomous, read-only skill that runs **first in the pipeline** and produces a complete diagnostic snapshot of the project's test coverage health. It orchestrates 9 tools sequentially, then emits a consolidated `AuditGapReport` that all downstream skills depend on.

This skill is **the first to build** across the entire 6-skill test coverage engine. It informs every other skill's behavior: `generate` uses `AuditGapReport` to pick what tests to write; `evaluate` uses it to identify integration boundaries; `integrate` uses flakiness data to classify quarantine candidates. Building `audit` first means all other skills can be built with a clear, stable input contract.

Key capabilities it must deliver:
- Snapshot existing line coverage per function via `coverage_analyzer`
- Score every function by the **2-factor criticality heuristic** (see cross-cutting Critical-Area Scoring)
- Detect **gaming patterns** (7+ AST-deterministic anti-patterns) via `gaming_detector`
- Compute **edge coverage** — fraction of cross-package `(caller_module, callee_module)` call-graph edges exercised by integration-marked tests — a metric no existing off-the-shelf tool produces
- Record flakiness scores per test via `flakiness_checker`
- Identify dependency vulnerabilities via `dep_vulnerability`
- Validate log contract conformance via `log_contract_validator`
- Score assertion quality per test via `assertion_quality`
- Compute test-impact from git diff via `impact_analyzer`
- Write a timestamped report to `AUDIT_HISTORY/<timestamp>.yaml`

---

## Why Claude needs it

Without this skill, Claude has no systematic way to prioritize coverage work. Given a codebase, Claude currently:

1. **Lacks priority ordering.** It will generate tests for whatever gap it notices first, not for the most critical-and-changed functions. The 2-factor heuristic (`recently_changed AND (public_api OR bug_history > 0)`) is not applied — Claude drifts toward easy-to-cover cold code.

2. **Has no edge-coverage metric.** Line coverage and mutation kill rate are standard, but neither detects untested module-to-module integration seams. Claude cannot reason about call-graph edges without a tool that walks the static AST and cross-references runtime instrumentation. It will miss entire classes of integration risk.

3. **Cannot detect gaming.** If a test suite contains `assert True` padding, copy-paste tests, or tests that mock the system under test, Claude treats them as valid coverage. It has no AST-based signal to flag these patterns before generating more tests on top of a corrupt baseline.

4. **Has no prior-state awareness.** Without `AUDIT_HISTORY`, Claude treats every run as a fresh audit with no delta signal. It cannot tell whether coverage is improving, stagnant, or regressing.

---

## Injection shape

- **Workflow:** Sequential 9-tool orchestration pipeline with a defined node order, stopping conditions, and a write-to-history step at the end.
- **Policy:** Read-only constraint — never modifies source files, test files, or coverage config. Emits reports only. This is always-loaded.

---

## What it produces

| Output | Count | Mutable? | Purpose |
|---|---|---|---|
| `AuditGapReport` (pydantic) | 1 per run | No | Primary handoff to `generate`; includes gaps, priority ranking, gaming alerts, flakiness, dep vulns, edge gaps, log violations |
| `AUDIT_HISTORY/<timestamp>.yaml` | 1 per run | No | Persisted audit record for delta tracking across runs |
| `COVERAGE_STATE.yaml` (initial snapshot) | 1 (first run only) | No | Baseline state; subsequent runs update via `generate` |

---

## Flow graph

```
[START]
   |
   v
[SNAPSHOT] — coverage_analyzer
   |
   v
[SCORE] — critical_scorer (2-factor heuristic)
   |
   v
[IMPACT] — impact_analyzer (git diff → affected tests)
   |
   v
[GAMING] — gaming_detector (7+ AST patterns)
   |
   v
[FLAKINESS] — flakiness_checker (FLAKE_HISTORY.csv)
   |
   v
[DEP-VULN] — dep_vulnerability
   |
   v
[EDGE-COV] — edge_coverage_analyzer (static AST + runtime)
   |
   v
[LOG-CONTRACT] — log_contract_validator
   |
   v
[ASSERTION-QUALITY] — assertion_quality
   |
   v
[CONSOLIDATE] — merge all tool outputs into AuditGapReport
   |
   v
[WRITE-HISTORY] — write AUDIT_HISTORY/<timestamp>.yaml
   |
   v
[DONE] — emit AuditGapReport for generate
```

---

## Node specifications

**[SNAPSHOT]** — Load: `references/coverage-analysis.md`. Do: Run `coverage_analyzer` against repo root; collect `CoverageGap[]` per function (line coverage %, uncovered branches, layer). Don't: modify any source or test file. Exit: gaps list ready → [SCORE].

**[SCORE]** — Load: `references/critical-scoring.md`. Do: Run `critical_scorer` on all functions; apply 2-factor heuristic (`recently_changed AND (public_api OR bug_history > 0)`) to assign tier (critical / standard / cold) and coverage target (95% / 85% / 70%). Don't: use the deprecated 4-factor formula. Exit: `PriorityRanking` ready → [IMPACT].

**[IMPACT]** — Load: none (deterministic). Do: Run `impact_analyzer` with current `git diff` + coverage map; classify each gap as unaffected (no covering tests), valid (tests cover + mutants killed), or weak (tests cover + mutants survive). Don't: run mutation testing here — that is `generate`'s job per-gap. Exit: impact classification attached to each gap → [GAMING].

**[GAMING]** — Load: `references/gaming-patterns.md`. Do: Run `gaming_detector` on all test files; flag any of the 7 AST-deterministic anti-patterns (`pragma: no cover` abuse, `assert True`/`assert 1` padding, tests with no assertions, mocking the SUT, copy-paste tests via AST hash dedup, `_private` attribute assertions, self-referential test helpers). Don't: auto-delete or auto-fix flagged tests. Exit: `GamingAlert[]` ready → [FLAKINESS].

**[FLAKINESS]** — Load: `references/flakiness-detection.md`. Do: Run `flakiness_checker` against `FLAKE_HISTORY.csv`; compute per-test `fail_rate = distinct_outcomes / total_runs` for each `(test_id, sha)` pair; flag tests with fail_rate > 2% as quarantine candidates. Don't: modify FLAKE_HISTORY or quarantine any test — audit is read-only. Exit: `dict[str, float]` (test_id → fail_rate) ready → [DEP-VULN].

**[DEP-VULN]** — Load: `references/dep-vulnerability.md`. Do: Run `dep_vulnerability` against project dependency manifests; collect `DependencyVulnerability[]`. Don't: modify pyproject.toml or requirements files. Exit: vulnerability list ready → [EDGE-COV].

**[EDGE-COV]** — Load: `references/edge-coverage-analysis.md`. Do: Run `edge_coverage_analyzer`; static AST walk to enumerate all `(caller_module, callee_module)` cross-package boundary edges; cross-reference with runtime instrumentation data (pytest plugin / sys.settrace) to compute fraction exercised by integration-marked tests. Read/write `EDGE_COVERAGE.yaml` (update only). Don't: execute tests inline. Exit: `EdgeCoverageGaps` ready → [LOG-CONTRACT].

**[LOG-CONTRACT]** — Load: `LOG_POLICY.yaml` (project state). Do: Run `log_contract_validator`; compare every `logger.error(` / `logger.exception(` / `logger.warning(` / audit call in AST against the log archetype contract (required fields, forbidden fields); compute log-path coverage (fraction of detected log call sites exercised by ≥1 test). Don't: modify LOG_POLICY.yaml. Exit: `list[LogContractViolation]` ready → [ASSERTION-QUALITY].

**[ASSERTION-QUALITY]** — Load: none (deterministic). Do: Run `assertion_quality` on all existing tests; score each test on assertion strength (presence of raises checks, mock assertion methods, value assertions, parametrize coverage). Don't: rewrite any test. Exit: quality scores attached to coverage gaps → [CONSOLIDATE].

**[CONSOLIDATE]** — Load: `templates/audit-report.md`. Do: Merge all tool outputs into a single `AuditGapReport` pydantic model; record `audit_timestamp` and `project_sha`. Don't: omit any tool's output from the report. Exit: consolidated report → [WRITE-HISTORY].

**[WRITE-HISTORY]** — Load: `templates/coverage-state-schema.md`. Do: Serialize `AuditGapReport` to `project/coverage/state/AUDIT_HISTORY/<timestamp>.yaml`; if `COVERAGE_STATE.yaml` does not exist, write initial snapshot. Don't: overwrite prior history entries. Exit: history written → [DONE].

---

## Entry gates

| Transition | Gate |
|---|---|
| Invoke audit | None — fully autonomous, read-only; no human approval required |
| Precondition | Clean codebase (lint passes); `LintReport.issues` must be empty or all issues flagged `requires-human-review` |

---

## Edge cases considered

| Edge case | Handling |
|---|---|
| No prior `AUDIT_HISTORY` entry | Run as absolute audit (no delta); skip delta computation; note in report that baseline is being established |
| `COVERAGE_STATE.yaml` missing | Write initial snapshot at [WRITE-HISTORY]; downstream `generate` will treat all gaps as new |
| `FLAKE_HISTORY.csv` missing | Skip flakiness node output gracefully; emit empty `flakiness_scores: {}` in report; note absence in report |
| `EDGE_COVERAGE.yaml` missing | `edge_coverage_analyzer` initializes it from scratch; first run computes baseline with no prior edge data |
| Delta vs absolute audit | CLI flag `--delta` / `--absolute`; default is delta when `AUDIT_HISTORY` exists, absolute on first run |
| Audit cadence (per-PR, nightly, on-demand) | Exposed via CLI flags; default cadence is on-demand; creator decides CI integration defaults |
| `LOG_POLICY.yaml` missing | `log_contract_validator` emits a warning and skips log-contract node; does not fail the audit |
| Large repo — edge analysis timeout | `edge_coverage_analyzer` supports `--max-edges` cap; uncapped edges reported as `unanalyzed` in `EdgeCoverageGaps` |

---

## Companion files anticipated

**Always-loaded (rules):**
- `rules/audit-constraints.md` — loaded at every node: never modifies code or tests; read-only; emits report only.

**References (loaded at relevant nodes):**
- `references/coverage-analysis.md` — loaded at [SNAPSHOT]: line coverage interpretation, gap classification.
- `references/critical-scoring.md` — loaded at [SCORE]: 2-factor heuristic definition, tier thresholds, rationale for discarding 4-factor formula.
- `references/gaming-patterns.md` — loaded at [GAMING]: all 7 AST-deterministic anti-patterns with detection logic.
- `references/flakiness-detection.md` — loaded at [FLAKINESS]: `(test_id, sha) → distinct_outcomes` measurement, quarantine threshold (>2%).
- `references/dep-vulnerability.md` — loaded at [DEP-VULN]: vulnerability severity classification, advisory source.
- `references/edge-coverage-analysis.md` — loaded at [EDGE-COV]: call-graph edge definition, static AST walk + runtime instrumentation method, edge weight formula, `pytest-trace` base reference.
- `references/coverage-pyramid.md` — loaded at [CONSOLIDATE]: layer definitions (unit → config → contract → idempotency → mock-integration → real-integration) for gap classification.

**Templates:**
- `templates/audit-report.md` — loaded at [CONSOLIDATE]: output report structure.
- `templates/coverage-state-schema.md` — loaded at [WRITE-HISTORY]: `COVERAGE_STATE.yaml` schema.

---

## Output schema

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

All types (`CoverageGap`, `PriorityRanking`, `GamingAlert`, `DependencyVulnerability`, `EdgeCoverageGaps`, `LogContractViolation`) are defined in `ai-synapse/tools/testing/schemas.py`. Both this skill and its consumers import from that canonical location.

---

## Dependencies

| Artifact | Direction | Contract |
|---|---|---|
| `test-fix` | consumes from | Precondition: clean codebase (lint-clean). `audit` does not receive a `LintReport` directly — it simply requires lint passes before invocation. |
| `test-generate` | produces for | `AuditGapReport` (pydantic): `gaps`, `priority_ranking`, `gaming_alerts`, `flakiness_scores`, `dep_vulnerabilities`, `edge_coverage_gaps`, `log_contract_violations`, `audit_timestamp`, `project_sha` |
| `test-evaluate` | produces for | `AuditGapReport` (boundary classification uses `gaps` + `priority_ranking` + `edge_coverage_gaps`) |
| `test-integrate` | produces for | `flakiness_scores` (quarantine candidates), `edge_coverage_gaps` (integration test feedback loop baseline) |
| `ai-synapse/tools/testing/schemas.py` | consumes from | Shared pydantic I/O contracts for all 9 tools |
| `project/coverage/state/AUDIT_HISTORY/` | produces for | Persisted timestamped audit record |
| `project/coverage/state/COVERAGE_STATE.yaml` | produces for | Initial snapshot on first run |

---

## Open questions

1. **Audit cadence default.** Which cadence should be the default when invoked from CI — per-PR, nightly, or on-demand? The notepad defers this to the creator. Recommendation: on-demand as default, with `--cadence=pr|nightly|on-demand` flag exposing all three.

2. **Delta vs absolute report format.** When `AUDIT_HISTORY` exists, should the `AuditGapReport` surface only new/changed gaps (delta mode) or always emit the full absolute snapshot? Creator decides whether to include both representations or make it flag-driven.

3. **Edge analyzer timeout/cap.** The notepad flags that edge coverage analysis has real engineering cost. Creator needs to decide the default `--max-edges` value and whether timeout-exceeded edges are reported as `unanalyzed` or cause the node to fail.

4. **`FLAKE_HISTORY.csv` bootstrap.** On a project with no prior flake history, the flakiness node produces an empty result. Creator should decide whether `audit` triggers an initial flakiness measurement run (N reruns of the test suite) or whether that responsibility belongs to `integrate`.
