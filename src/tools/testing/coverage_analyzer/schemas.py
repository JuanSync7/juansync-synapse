# @summary
# Pydantic v2 schemas for coverage-analyzer tool outputs.
# Exports: CoverageGap, Edge, EdgeCoverageReport, CoverageReport
# Deps: pydantic, datetime
# @end-summary

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CoverageGap(BaseModel):
    module: str = Field(description="Dotted module path, e.g. 'ragweave.ingest.queue'")
    function_name: str = Field(description="Function or method name")
    line_start: int = Field(description="First line of the function definition")
    line_end: int = Field(description="Last line of the function definition")
    coverage_pct: float = Field(ge=0.0, le=100.0, description="Percentage of lines covered")
    missing_lines: list[int] = Field(description="Line numbers not executed during test run")
    is_boundary: bool = Field(
        description="True if function is runtime-exposed via @app.route, @activity.defn, "
        "@click.command, or reads request/os.environ/sys.stdin"
    )


class Edge(BaseModel):
    caller_module: str = Field(description="Dotted module path of the calling module")
    callee_module: str = Field(description="Dotted module path of the called module")
    call_site_line: int | None = Field(
        default=None, description="Line number of the call site in caller_module"
    )


class EdgeCoverageReport(BaseModel):
    commit_sha: str | None = Field(default=None, description="Git SHA of the measured commit")
    test_suite_path: str = Field(description="Path to the test file or directory that was run")
    edges: list[Edge] = Field(description="All cross-package edges found in source_root")
    new_edges: list[Edge] = Field(
        description="Edges not present in the baseline snapshot; empty when no baseline provided"
    )
    snapshot_timestamp: datetime = Field(description="UTC timestamp when the report was produced")


class CoverageReport(BaseModel):
    source_root: str = Field(description="Absolute path to the source root that was analyzed")
    gaps: list[CoverageGap] = Field(description="Functions with less than 100% line coverage")
    total_functions: int = Field(ge=0, description="Total number of functions analyzed")
    functions_with_gaps: int = Field(ge=0, description="Number of functions with at least one missing line")
    report_timestamp: datetime = Field(description="UTC timestamp when the report was produced")
