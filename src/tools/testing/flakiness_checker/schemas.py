# @summary
# Pydantic v2 schemas for the flakiness-checker tool.
# Exports: TestOutcome, FlakinessSummary
# Deps: pydantic, datetime, typing
# @end-summary

"""Pydantic v2 data contracts for the flakiness-checker tool."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TestOutcome(BaseModel):
    """Result of a single pytest invocation."""

    run_number: int = Field(..., description="1-based index of this run in the batch.")
    passed: bool = Field(..., description="True if pytest exited with code 0.")
    duration_seconds: float = Field(..., description="Wall-clock time for this run in seconds.")
    error_message: str | None = Field(
        default=None,
        description="Captured stderr/stdout excerpt on failure; None when passed.",
    )


class FlakinessSummary(BaseModel):
    """Aggregated flakiness result for a single pytest test node."""

    test_id: str = Field(
        ...,
        description="Fully-qualified pytest node id, e.g. tests/test_foo.py::test_bar.",
    )
    total_runs: int = Field(..., description="Number of times the test was executed (>= 10).")
    failures: int = Field(..., description="Number of runs that did not exit with code 0.")
    fail_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="failures / total_runs as a fraction between 0.0 and 1.0.",
    )
    status: Literal["stable", "flaky-quarantined"] = Field(
        ...,
        description=(
            "'stable' when fail_rate < 0.02; "
            "'flaky-quarantined' when fail_rate >= 0.02."
        ),
    )
    outcomes: list[TestOutcome] = Field(
        ...,
        description="Per-run pass/fail detail, ordered by run_number.",
    )
    run_timestamp: datetime = Field(
        ...,
        description="UTC timestamp at which the flakiness-checker run began.",
    )
