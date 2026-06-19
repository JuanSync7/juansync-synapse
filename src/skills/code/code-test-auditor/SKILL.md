---
name: code-test-auditor
aliases: [test-audit]
description: "Use when asked to audit tests, check coverage gaps, find missing tests, detect gaming or flakiness, or produce a coverage report — before writing new tests. Not for writing tests (use code-test-generator) or fixing lint (use code-test-linter)."
domain: code
scope: test
role: auditor
tags: [coverage, audit, gap-analysis, edge-coverage, gaming-detection]
user-invocable: true
argument-hint: "[--delta|--absolute] [--max-edges N] [--cadence pr|nightly|on-demand]"
---

This skill is a diagnostic instrument, not a fix agent. Its single responsibility is to produce an accurate, structured `AuditGapReport` — the canonical contract that every downstream skill (`code-test-generator`, `code-test-evaluator`, `code-test-integrator`) depends on. The audit's value comes from completeness and honesty: a gap report that skips a tool or silently drops data will cause downstream skills to generate tests against a distorted view of coverage. All 9 tools run in order; missing data produces sentinel values, not aborts. The skill never writes, modifies, quarantines, or deletes any test or source file — doing so would corrupt the state the audit is trying to measure.

> **Execution scope:** Ignore `research/`, `EVAL.md`, `PROGRAM.md`, `SCOPE.md`, and `test-inputs/` during execution — these are used only by improvement and migration workflows.

## MUST (every turn)
- Load `rules/audit-constraints.md` — read-only invariants apply at every node
- Record position: `Position: [node-id] — <context>`
- Run all 9 nodes in declared order; no early exit unless precondition fails

## MUST NOT (global)
- Modify any source file, test file, coverage config, or project state file other than the audit history target — any write corrupts the pre-run hash baseline and invalidates EVAL-O11
- Skip a node — emit empty/sentinel output and note absence in report instead; skipping produces gaps in `AuditGapReport` that downstream generators treat as "no problem found"
- Run mutation testing inline — that is `code-test-generator`'s per-gap responsibility; doing it here conflates read-only audit with generation and triggers the MUST NOT on writes
- Quarantine, delete, or auto-fix any flagged test — the audit's job is to surface problems, not resolve them; auto-fixes silently change the state being measured

## Wrong-Tool Detection
- **User wants tests written from gaps** → `/code-test-generator` (consumes this skill's output)
- **User wants to fix lint issues** → `/code-test-fixer` (audit's precondition)
- **User wants to evaluate test boundary correctness** → `/code-test-evaluator`

## Progress Tracking

For runs spanning multiple turns, use `TaskCreate` to checkpoint each completed node:

```
TaskCreate: title="[SNAPSHOT] Coverage snapshot complete", status="completed"
TaskCreate: title="[GAMING] Gaming detection in progress", status="in_progress"
```

Create one task per node when entering it; mark completed on exit. This lets the user resume a partial run and shows which tool is active.

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
