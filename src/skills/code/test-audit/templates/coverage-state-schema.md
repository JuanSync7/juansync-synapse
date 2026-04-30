# Coverage State Schema

Loaded by [WRITE-HISTORY]. Defines the two YAML files that node produces:
- `project/coverage/state/AUDIT_HISTORY/<timestamp>.yaml` — append-only audit record
- `project/coverage/state/COVERAGE_STATE.yaml` — living baseline (first-run write only)

Companion files managed by other skills (do NOT write here):
`EDGE_COVERAGE.yaml`, `FLAKE_HISTORY.csv`, `LOG_POLICY.yaml`, `MUTATION_BUDGET.yaml`

---

## Write Rules

- NEVER overwrite an existing `AUDIT_HISTORY/<timestamp>.yaml` — each filename is a unique UTC timestamp.
- NEVER overwrite an existing `COVERAGE_STATE.yaml` — audit writes it once; `test-generate` owns it thereafter.
- Serialize all sub-objects via pydantic `model_dump(mode="json")` so datetimes and enums are JSON-safe strings.
- If `COVERAGE_STATE.yaml` already exists, [WRITE-HISTORY] writes ONLY the `AUDIT_HISTORY` entry and exits.

---

## A) `AUDIT_HISTORY/<timestamp>.yaml`

Filename format: `<YYYYMMDDTHHMMSSZ>.yaml` (UTC ISO-8601 compact, e.g. `20260430T143022Z.yaml`).

```yaml
# Append-only. Never overwrite. Filename = audit_timestamp in compact UTC ISO-8601.
schema_version: 1

audit_timestamp: <ISO8601 UTC>       # matches AuditGapReport.audit_timestamp; also the filename stem
project_sha: <40-char hex>           # matches AuditGapReport.project_sha

mode: <absolute|delta>               # mode flag used for this run

summary:
  total_functions: <int>             # total functions analyzed by coverage_analyzer
  gap_count: <int>                   # len(gaps)
  critical_tier_count: <int>         # gaps where tier == "critical"
  gaming_alert_count: <int>          # len(gaming_alerts)
  flakiness_candidate_count: <int>   # tests with fail_rate > 0.02
  edge_coverage_ratio: <float>       # 0.0–1.0; from edge_coverage_analyzer
  log_contract_violation_count: <int>
  dep_vuln_count_by_severity:
    critical: <int>
    high: <int>
    medium: <int>
    low: <int>

# Full serialized lists — sub-objects via model_dump(mode="json")
gaps: [<CoverageGap>...]             # see audit-report.md surface A for field definitions
priority_ranking: <PriorityRanking>  # ranked gap_ids with rationale
gaming_alerts: [<GamingAlert>...]    # anti-pattern flags from gaming_detector
flakiness_scores:                    # keyed by test_id; empty dict if FLAKE_HISTORY.csv absent
  <test_id>: <float>                 # fail_rate = distinct_outcomes / total_runs
dep_vulnerabilities: [<DependencyVulnerability>...]
edge_coverage_gaps: <EdgeCoverageGaps>
log_contract_violations: [<LogContractViolation>...]
```

---

## B) `COVERAGE_STATE.yaml`

Written ONCE on first run (when file does not yet exist). `test-generate` and `test-integrate`
mutate this file thereafter — audit MUST NOT touch it after initialization.

```yaml
# Living state file. Written once by test-audit; mutated by test-generate / test-integrate.
# AUDIT MUST NOT overwrite this file if it already exists.
schema_version: 1

initialized_at: <ISO8601 UTC>        # timestamp of the first audit run that created this file
project_sha: <40-char hex>           # SHA at initialization time

last_audit_timestamp: <ISO8601 UTC>  # points to the most recent AUDIT_HISTORY entry

# Default coverage targets per tier — sourced from design doc §10 critical-area scoring.
# Override via project config; do not hardcode in tool logic.
coverage_targets:
  critical: 0.95
  standard: 0.85
  cold: 0.70

gap_state:
  open: [<gap_id>...]                # baseline = all gap_ids from the first audit
  closed: []                         # empty at initialization; test-integrate populates

edge_coverage:
  ratio: <float>                     # from edge_coverage_analyzer at init time
  uncovered_edges: [<edge>...]       # list of (caller_module, callee_module) pairs

# Populated by downstream skills — empty at audit initialization
flakiness_quarantine: []             # test-integrate sets quarantine entries here
generation_lineage: []               # test-generate appends generation records here
```

---

## Path Reference

```
project/coverage/
└── state/
    ├── COVERAGE_STATE.yaml               # baseline (written once by test-audit)
    └── AUDIT_HISTORY/
        └── <YYYYMMDDTHHMMSSZ>.yaml       # one file per audit run, never overwritten
```
