"""
@summary
Canonical pydantic v2 contracts for the `code-test-evaluator` skill.

This module is the source-of-truth for two cross-stage shapes used by the
6-skill test coverage engine:

- ``CoverageState`` — produced by ``/code-test-generator``, consumed by
  ``/code-test-evaluator`` (and downstream stages). Captures per-module test
  coverage status, including whether mocked-integration tests exist and
  the priority ranking used to drive evaluation order.
- ``IntegrationStrategy`` — produced by ``/code-test-evaluator`` per module.
  Mirrors the structure of ``templates/integration-strategy.md``: boundary
  classification summary, ranked replacement candidates, considered-but-
  excluded list, over-mocking warnings, and out-of-scope notes.

Per-tool output schemas (boundary classifier, mock inventory, coverage
analyzer, log contract validator, etc.) live alongside their tool under
``src/tools/testing/<tool>/schemas.py`` — not here.

Exports: BoundaryTier, BoundaryCategory, LifecyclePattern, ExclusionReason,
    BoundarySummary, ReplacementCandidate, ExcludedCandidate,
    OverMockingWarning, IntegrationStrategy, ModuleCoverage,
    AuditGapReport, CoverageState
Deps: pydantic
@end-summary
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums (fixed vocabularies referenced by SKILL.md / EVAL.md)
# ---------------------------------------------------------------------------


class BoundaryTier(str, Enum):
    """Two-tier boundary classification plus the excluded `internal` bucket."""

    runtime = "runtime"
    logical = "logical"
    internal = "internal"


class BoundaryCategory(str, Enum):
    """Module category drives risk weight and lifecycle pattern selection."""

    db = "db"
    api = "api"
    queue = "queue"
    file = "file"
    cli = "cli"


class LifecyclePattern(str, Enum):
    """Lifecycle patterns enumerated in references/lifecycle-patterns.md."""

    transaction_rollback = "transaction-rollback"
    schema_per_test = "schema-per-test"
    vcrpy = "vcrpy"
    ephemeral_container = "ephemeral-container"
    workflow_environment = "workflow-environment"  # Temporal harness
    celery_test_harness = "celery-test-harness"
    tmp_path = "tmp_path"
    real_fs = "real-fs"
    subprocess_capture = "subprocess-capture"


class ExclusionReason(str, Enum):
    """Fixed exclusion-reason vocabulary (see EVAL-O13)."""

    low_marginal_gain = "low-marginal-gain"
    low_failure_mode_risk = "low-failure-mode-risk"
    cost_exceeds_budget = "cost-exceeds-budget"
    over_mocking_warning = "over_mocking_warning"
    wrapper_coupling = "wrapper-coupling"
    already_covered = "already-covered"
    unsupported_category = "unsupported-category"


# ---------------------------------------------------------------------------
# IntegrationStrategy and supporting models
# ---------------------------------------------------------------------------


class BoundarySummary(BaseModel):
    """Counts + function lists per boundary tier for one module."""

    model_config = ConfigDict(extra="forbid")

    runtime_count: int = Field(ge=0)
    logical_count: int = Field(ge=0)
    internal_count: int = Field(ge=0)
    runtime_list: list[str] = Field(default_factory=list)
    logical_list: list[str] = Field(default_factory=list)
    internal_list: list[str] = Field(default_factory=list)


class ReplacementCandidate(BaseModel):
    """One ranked mock-replacement candidate inside an IntegrationStrategy."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(ge=1)
    mock_target: str
    boundary_fn: str
    tier: BoundaryTier
    category: BoundaryCategory
    risk: int = Field(ge=1, le=5)
    tier_weight: int = Field(ge=0, le=3)
    risk_weight: int = Field(ge=1, le=5)
    gap: float = Field(ge=0.0, le=1.0)
    score: float = Field(ge=0.0)
    pattern: LifecyclePattern
    pattern_rationale: str
    lifecycle_notes: Optional[str] = None


class ExcludedCandidate(BaseModel):
    """A mock that was considered for replacement but excluded."""

    model_config = ConfigDict(extra="forbid")

    candidate: str
    exclusion_reason: ExclusionReason


class OverMockingWarning(BaseModel):
    """Mock that targets an internal (non-boundary) function."""

    model_config = ConfigDict(extra="forbid")

    mock_target: str
    test_file: str
    internal_fn: str


class IntegrationStrategy(BaseModel):
    """Per-module integration strategy emitted by `/code-test-evaluator`.

    Mirrors `templates/integration-strategy.md`. One instance corresponds to
    one rendered markdown document at
    ``project/coverage/state/integration-strategies/<module-slug>.md``.
    """

    model_config = ConfigDict(extra="forbid")

    module_path: str
    module_category: BoundaryCategory
    evaluate_run_id: str
    source_hash: str
    timestamp: datetime
    boundary_summary: BoundarySummary
    candidates_recommended: list[ReplacementCandidate] = Field(default_factory=list)
    candidates_excluded: list[ExcludedCandidate] = Field(default_factory=list)
    over_mocking_warnings: list[OverMockingWarning] = Field(default_factory=list)
    out_of_scope_libs: list[str] = Field(default_factory=list)
    already_real_modules: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# CoverageState (shared cross-stage state)
# ---------------------------------------------------------------------------


class ModuleCoverage(BaseModel):
    """Per-module coverage record persisted in CoverageState."""

    model_config = ConfigDict(extra="forbid")

    module_path: str
    has_mocked_integration_tests: bool = False
    has_real_integration_tests: bool = False
    criticality_score: float = Field(default=0.0, ge=0.0)
    source_hash: Optional[str] = None
    # Populated by `/code-test-evaluator` after a run.
    integration_strategy_path: Optional[str] = None
    boundary_classification: Optional[BoundarySummary] = None
    evaluate_run_id: Optional[str] = None


class AuditGapReport(BaseModel):
    """Gap report emitted by `/code-test-auditor`; consumed by `/code-test-evaluator`."""

    model_config = ConfigDict(extra="forbid")

    priority_ranking: list[str] = Field(
        default_factory=list,
        description="Module paths in descending priority (critical first).",
    )
    critical_modules: list[str] = Field(default_factory=list)


class CoverageState(BaseModel):
    """Engine-wide coverage state persisted at COVERAGE_STATE.yaml.

    Produced by `/code-test-generator`, mutated by `/code-test-evaluator` (per-module
    strategy paths + boundary classification + run id + source hash), and
    consumed by downstream stages (`/code-test-integrator`, `/code-test-linter`, etc.).
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1"
    generated_at: datetime
    project_root: str
    modules: dict[str, ModuleCoverage] = Field(default_factory=dict)
    audit_gap_report: Optional[AuditGapReport] = None
    last_evaluate_run_id: Optional[str] = None


__all__ = [
    "BoundaryTier",
    "BoundaryCategory",
    "LifecyclePattern",
    "ExclusionReason",
    "BoundarySummary",
    "ReplacementCandidate",
    "ExcludedCandidate",
    "OverMockingWarning",
    "IntegrationStrategy",
    "ModuleCoverage",
    "AuditGapReport",
    "CoverageState",
]
