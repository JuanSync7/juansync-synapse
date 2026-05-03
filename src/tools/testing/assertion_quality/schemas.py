"""Pydantic v2 schemas for the assertion-quality tool.

Defines typed contracts for assertion issues, per-test quality scores, and the
top-level report emitted by ``assertion_quality.py``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

IssueType = Literal[
    "no_assertion",
    "trivial_assertion",
    "tautological_assertion",
    "mock_called_no_args",
    "weak_isinstance",
    "exception_swallowed",
]


class AssertionIssue(BaseModel):
    """A single weak-assertion finding inside a test function."""

    line: int = Field(..., description="1-indexed source line where the issue was detected.")
    issue_type: IssueType = Field(..., description="Category of weak-assertion smell.")
    message: str = Field(..., description="Human-readable explanation of the finding.")
    snippet: str = Field(..., description="Single-line source snippet for context.")


class TestQualityScore(BaseModel):
    """Quality score for a single ``test_*`` function."""

    test_file: str
    test_function: str
    line_start: int
    assertion_count: int = Field(
        ...,
        description=(
            "Total assert / pytest.raises / mock.assert_* calls detected in the body."
        ),
    )
    quality_score: float = Field(..., ge=0.0, le=1.0)
    issues: list[AssertionIssue] = Field(default_factory=list)
    has_meaningful_assertion: bool = Field(
        ...,
        description=(
            "True iff assertion_count >= 1 AND no no_assertion/trivial_assertion issues."
        ),
    )


class AssertionQualityReport(BaseModel):
    """Top-level report aggregated across an entire test root."""

    test_root: str
    scores: list[TestQualityScore] = Field(default_factory=list)
    total_tests: int
    tests_below_threshold: int = Field(
        ..., description="Count of tests whose quality_score is strictly less than threshold."
    )
    tests_with_no_assertion: int
    average_score: float = Field(..., ge=0.0, le=1.0)
    threshold: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime
