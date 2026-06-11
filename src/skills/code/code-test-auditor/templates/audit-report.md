# AuditGapReport — In-Memory Shape (Surface A)

> **Scope:** This template defines the pydantic model emitted in-memory by [CONSOLIDATE] and
> handed off to downstream skills (`code-test-generator`, `code-test-evaluator`, `code-test-integrator`).
> For the YAML on-disk serialization written at [WRITE-HISTORY], see
> `templates/coverage-state-schema.md`.

---

## Pydantic Model Definition

All sub-types are imported from each tool's per-tool `schemas.py` module under
`src/tools/testing/<tool>/schemas.py` — those modules are the canonical sources of truth.
Do not redefine them here. The shared `CoverageState` lives in
`src/skills/code/code-test-evaluator/schemas.py`.

```python
from datetime import datetime
from src.tools.testing.coverage_analyzer.schemas import (
    CoverageGap,            # per-function gap with line %, uncovered branches, layer
    EdgeCoverageGaps,       # (caller_module, callee_module) edges: covered vs unanalyzed
)
from src.tools.testing.critical_scorer.schemas import PriorityRanking  # critical/standard/cold tier assignments + coverage targets
from src.tools.testing.gaming_detector.schemas import GamingAlert      # flagged AST anti-pattern with test_id and pattern name
from src.tools.testing.dep_vulnerability.schemas import DependencyVulnerability  # advisory ID, severity, affected package, fixed version
from src.tools.testing.log_contract_validator.schemas import LogContractViolation  # call-site path, violation type, log-path coverage fraction

class AuditGapReport(BaseModel):
    gaps: list[CoverageGap]                         # <list[CoverageGap]> — one entry per function
    priority_ranking: PriorityRanking               # single object covering all tiers
    gaming_alerts: list[GamingAlert]                # empty list [] if none detected
    flakiness_scores: dict[str, float]              # test_id → fail_rate; {} if FLAKE_HISTORY missing
    dep_vulnerabilities: list[DependencyVulnerability]  # empty list [] if none found
    edge_coverage_gaps: EdgeCoverageGaps            # includes unanalyzed edges when --max-edges hit
    log_contract_violations: list[LogContractViolation] # empty list [] if LOG_POLICY.yaml missing
    audit_timestamp: datetime                       # timezone-aware UTC — see invariants
    project_sha: str                                # full 40-char hex — see invariants
```

---

## Field Assembly Recipe

Each field is assembled from a specific node's output. [CONSOLIDATE] merges them all.

| Field | Source node(s) | Notes |
|---|---|---|
| `gaps` | [SNAPSHOT] + [IMPACT] + [ASSERTION-QUALITY] | Gap list with layer classification, impact tag (`unaffected`/`valid`/`weak`), and assertion strength score attached |
| `priority_ranking` | [SCORE] | 2-factor heuristic output; single `PriorityRanking` object with `critical`, `standard`, `cold` tier lists |
| `gaming_alerts` | [GAMING] | `GamingAlert[]`; one entry per flagged test/pattern pair |
| `flakiness_scores` | [FLAKINESS] | `dict[str, float]` keyed by `test_id`; `fail_rate = distinct_outcomes / total_runs` per `(test_id, sha)` |
| `dep_vulnerabilities` | [DEP-VULN] | `DependencyVulnerability[]`; includes severity and fixed version where known |
| `edge_coverage_gaps` | [EDGE-COV] | `EdgeCoverageGaps`; includes `unanalyzed` bucket when `--max-edges` cap was reached |
| `log_contract_violations` | [LOG-CONTRACT] | `LogContractViolation[]`; empty if `LOG_POLICY.yaml` absent (node skipped with warning) |
| `audit_timestamp` | [CONSOLIDATE] — `datetime.now(UTC)` | Captured at merge time, not at tool invocation time |
| `project_sha` | [CONSOLIDATE] — `git rev-parse HEAD` | Captured at merge time to match the working tree state |

---

## Required Invariants

These invariants MUST hold before [CONSOLIDATE] exits. Violating any of them is a node
failure — do not pass a malformed report to [WRITE-HISTORY].

1. **No field may be omitted.** If a tool produced no data (node skipped, file missing,
   timeout), the field MUST still be present with its empty default:
   - `list` fields → `[]`
   - `dict` fields → `{}`
   - Object fields (`PriorityRanking`, `EdgeCoverageGaps`) → sentinel instance with
     empty tier lists / edge lists as defined in each tool's `src/tools/testing/<tool>/schemas.py`

2. **`audit_timestamp` MUST be timezone-aware UTC.**
   Use `datetime.now(timezone.utc)` — never `datetime.utcnow()` (naive, deprecated).

3. **`project_sha` MUST be a full 40-character hex string.**
   Reject short SHAs. If `git rev-parse HEAD` fails, abort [CONSOLIDATE] with a clear
   error — do not emit a partial or empty SHA.

4. **`gaps` carries the composite output of three nodes.**
   Each `CoverageGap` in the list must carry:
   - Layer classification from [SNAPSHOT] (`unit`/`config`/`contract`/`idempotency`/`mock-integration`/`real-integration`)
   - Impact tag from [IMPACT] (`unaffected`/`valid`/`weak`)
   - Assertion strength score from [ASSERTION-QUALITY]
   A gap missing any of these three annotations is incomplete — note the gap ID and the
   missing annotation in the report rather than silently dropping it.

---

## Mode Note

The `AuditGapReport` always contains the **absolute** snapshot for the current run.
Delta computation (new gaps vs prior run) is a consumer responsibility — `code-test-generator`
and `code-test-evaluator` apply delta filtering using `AUDIT_HISTORY/` if needed.
The `--delta` / `--absolute` CLI flag controls which gaps [CONSOLIDATE] includes in
`gaps`, not the report structure itself. <!-- <absolute|delta> mode is resolved before
[CONSOLIDATE] runs; the model shape is identical in both cases -->

---

> **On-disk format:** See `templates/coverage-state-schema.md` for the YAML serialization
> written to `AUDIT_HISTORY/<timestamp>.yaml` at [WRITE-HISTORY].
