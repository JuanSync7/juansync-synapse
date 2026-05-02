# @summary
# Pydantic v2 schemas for the coverage-analyzer tool.
# Exports: CoverageGap, Edge, EdgeCoverageReport, CoverageReport
# Deps: pydantic, datetime
# @end-summary

"""Pydantic v2 data contracts for the coverage-analyzer tool."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CoverageGap(BaseModel):
    """Coverage gap for a single function in a source module."""

    module: str = Field(
        ...,
        description="Dotted module path, e.g. 'ragweave.ingest.queue'.",
    )
    function_name: str = Field(
        ...,
        description="Name of the function or method that has insufficient coverage.",
    )
    line_start: int = Field(..., description="First line of the function definition.")
    line_end: int = Field(..., description="Last line of the function definition.")
    coverage_pct: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of lines in this function that are covered (0.0–100.0).",
    )
    missing_lines: list[int] = Field(
        ...,
        description="Sorted list of line numbers within the function that were not executed.",
    )
    is_boundary: bool = Field(
        ...,
        description=(
            "True if the function is a public boundary entry-point: decorated with "
            "@app.route, @activity.defn, @click.command, @router.get/post/put/delete, "
            "or its body reads from request / os.environ / sys.stdin."
        ),
    )


class Edge(BaseModel):
    """A single cross-package call-graph edge observed in a test suite."""

    caller_module: str = Field(
        ...,
        description="Dotted module path of the calling module.",
    )
    callee_module: str = Field(
        ...,
        description="Dotted module path of the called module.",
    )
    call_site_line: int | None = Field(
        default=None,
        description="Line number in the caller's source file where the call appears, if known.",
    )


class EdgeCoverageReport(BaseModel):
    """Cross-package call-graph edge report produced by --edges mode."""

    commit_sha: str | None = Field(
        default=None,
        description="Git commit SHA associated with the analysed test suite, if provided.",
    )
    test_suite_path: str = Field(
        ...,
        description="File-system path to the test suite directory or file that was analysed.",
    )
    edges: list[Edge] = Field(
        ...,
        description="All cross-package edges exercised by the test suite.",
    )
    new_edges: list[Edge] = Field(
        ...,
        description=(
            "Edges not present in the baseline snapshot. "
            "Empty list when no baseline was provided."
        ),
    )
    snapshot_timestamp: datetime = Field(
        ...,
        description="UTC timestamp at which this report was generated.",
    )


class CoverageReport(BaseModel):
    """Per-function coverage gap report produced by default mode."""

    source_root: str = Field(
        ...,
        description="Absolute file-system path to the source root that was analysed.",
    )
    gaps: list[CoverageGap] = Field(
        ...,
        description="All functions with insufficient coverage, ordered by module then line_start.",
    )
    total_functions: int = Field(
        ...,
        description="Total number of functions discovered in source_root.",
    )
    functions_with_gaps: int = Field(
        ...,
        description="Number of functions that have at least one missing line.",
    )
    report_timestamp: datetime = Field(
        ...,
        description="UTC timestamp at which this report was generated.",
    )
