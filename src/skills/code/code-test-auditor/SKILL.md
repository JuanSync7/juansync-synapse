---
name: code-test-auditor
aliases: [test-audit]
description: "audit test coverage gaps, check for gaming patterns, flakiness, dependency vulnerabilities, edge coverage; produce diagnostic report before writing tests"
domain: code
scope: test
role: auditor
tags: [coverage, audit, gap-analysis, edge-coverage, gaming-detection]
user-invocable: true
argument-hint: "[--delta|--absolute] [--max-edges N] [--cadence pr|nightly|on-demand]"
---

Read-only first stage of the 6-skill test coverage engine. Orchestrates 9 testing tools sequentially to snapshot coverage, score criticality, detect gaming, and produce `AuditGapReport` — the canonical input that `code-test-generator`, `code-test-evaluator`, and `code-test-integrator` all consume.

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

## MUST (every turn)
- Load `rules/audit-constraints.md` — read-only invariants apply at every node
- Record position: `Position: [node-id] — <context>`
- Run all 9 nodes in declared order; no early exit unless precondition fails

## MUST NOT (global)
- Modify any source file, test file, coverage config, or project state file other than the audit history target
- Skip a node — emit empty/sentinel output and note absence in report instead
- Run mutation testing inline (that is `code-test-generator`'s per-gap responsibility)
- Quarantine, delete, or auto-fix any flagged test

## Wrong-Tool Detection
- **User wants tests written from gaps** → `/code-test-generator` (consumes this skill's output)
- **User wants to fix lint issues** → `/code-test-fixer` (audit's precondition)
- **User wants to evaluate test boundary correctness** → `/code-test-evaluator`

## Entry

### [NEW] Fresh session
Do:
  1. Verify precondition: lint passes (or all `LintReport.issues` flagged `requires-human-review`). If not, abort with directive to run `/code-test-linter` first.
  2. Detect mode: `--delta` (default if `AUDIT_HISTORY/` non-empty), `--absolute` (default on first run, or explicit flag).
  3. Confirm tool inventory available under `src/tools/testing/<tool>/` (one directory per tool) — abort with clear error if any of the 9 tools missing.
Don't: Proceed without lint-clean precondition. Re-run lint inline.
Exit: → [SNAPSHOT]

## Flow

### [SNAPSHOT] Coverage analyzer
Load: references/coverage-analysis.md
Do: Run `code-test-analyze-coverage` against repo root; collect `CoverageGap[]` per function (line %, uncovered branches, layer).
Exit: → [SCORE]

### [SCORE] Critical scoring
Load: references/critical-scoring.md
Do: Run `critical_scorer`; apply 2-factor heuristic — `recently_changed AND (public_api OR bug_history > 0)` — to assign tier (critical/standard/cold) and target (95/85/70%).
Don't: Use the deprecated 4-factor formula.
Exit: → [IMPACT]

### [IMPACT] Diff impact
Do: Run `impact_analyzer` with `git diff` + coverage map; classify each gap as unaffected / valid / weak.
Exit: → [GAMING]

### [GAMING] Gaming detection
Load: references/gaming-patterns.md
Do: Run `gaming_detector` over all test files; flag the 7 AST-deterministic anti-patterns.
Exit: → [FLAKINESS]

### [FLAKINESS] Flake measurement
Load: references/flakiness-detection.md
Do: Run `code-test-check-flakiness` over `FLAKE_HISTORY.csv`; compute `fail_rate = distinct_outcomes / total_runs` per `(test_id, sha)`; flag fail_rate > 2%. If `FLAKE_HISTORY.csv` missing, emit `flakiness_scores: {}` and note absence in report.
Exit: → [DEP-VULN]

### [DEP-VULN] Dependency vulnerabilities
Load: references/dep-vulnerability.md
Do: Run `dep_vulnerability` over project dependency manifests; collect `DependencyVulnerability[]`.
Exit: → [EDGE-COV]

### [EDGE-COV] Edge coverage
Load: references/edge-coverage-analysis.md
Do: Run `edge_coverage_analyzer`; static AST walk for cross-package `(caller_module, callee_module)` edges; cross-reference runtime instrumentation for fraction exercised by integration-marked tests. Update `EDGE_COVERAGE.yaml`. Honor `--max-edges` cap; report uncapped edges as `unanalyzed`.
Don't: Execute tests inline.
Exit: → [LOG-CONTRACT]

### [LOG-CONTRACT] Log conformance
Load: LOG_POLICY.yaml (project state)
Do: Run `code-test-validate-logs`; AST-compare every `logger.error/exception/warning` and audit call against the archetype contract; compute log-path coverage. If `LOG_POLICY.yaml` missing, emit warning and skip cleanly with empty `log_contract_violations: []`.
Exit: → [ASSERTION-QUALITY]

### [ASSERTION-QUALITY] Assertion strength
Do: Run `code-test-score-assertions` on all tests; score raises checks, mock assertion methods, value assertions, parametrize coverage.
Exit: → [CONSOLIDATE]

### [CONSOLIDATE] Merge
Load: templates/audit-report.md, references/coverage-pyramid.md
Do: Merge all tool outputs into a single `AuditGapReport` (pydantic; sub-schemas live in each tool's `src/tools/testing/<tool>/schemas.py`, with shared `CoverageState` in `src/skills/code/code-test-evaluator/schemas.py`). Record `audit_timestamp` and `project_sha`. Classify gaps by pyramid layer.
Don't: Omit any tool's output.
Exit: → [WRITE-HISTORY]

### [WRITE-HISTORY] Persist
Load: templates/coverage-state-schema.md
Do: Serialize `AuditGapReport` to `project/coverage/state/AUDIT_HISTORY/<timestamp>.yaml`. If `COVERAGE_STATE.yaml` missing, write initial snapshot.
Don't: Overwrite prior history entries.
Exit: → [END]

### [END]
Do:
  1. Emit `AuditGapReport` for downstream consumers (`code-test-generator` / `code-test-evaluator` / `code-test-integrator`).
  2. Print summary: total gaps, critical-tier count, gaming alerts, flakiness candidates, edge gaps, log violations, dep vulns.
  3. Suggest: "Run `/code-test-generator` to write tests for prioritized gaps."
Don't: Auto-route to `/code-test-generator`.
