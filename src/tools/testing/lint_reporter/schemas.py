# @summary
# Pydantic v2 contracts for the lint-reporter tool: per-issue, per-tool
# summary, and the aggregated LintReport returned by the CLI.
# Exports: LintIssue, LintToolSummary, LintReport, ToolName, Severity
# Deps: pydantic
# @end-summary

"""Typed contracts for the ``lint-reporter`` tool.

The lint-reporter aggregates output from four Python linters (``ruff``,
``mypy``, ``bandit``, ``vulture``) into a single :class:`LintReport`.
These models form the public schema consumed by the ``code-test-linter`` skill
and any downstream tooling.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ToolName = Literal["ruff", "mypy", "bandit", "vulture"]
Severity = Literal["error", "warning", "info"]


class LintIssue(BaseModel):
    """A single normalized lint finding from any of the supported tools."""

    file_path: str
    line: int
    column: int | None = None
    rule_id: str = Field(
        ...,
        description='Tool-native rule identifier (e.g. "E501", "B902", "no-untyped-def").',
    )
    message: str
    severity: Severity
    tool: ToolName


class LintToolSummary(BaseModel):
    """Per-tool aggregate including availability + counts.

    A tool that is not installed (not on ``PATH``) is reported with
    ``available=False`` and zero counts; this is *not* an error.
    """

    tool: ToolName
    issue_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    available: bool = True
    error_message: str | None = None


class LintReport(BaseModel):
    """Aggregated linter report — the CLI's stdout payload."""

    source_root: str
    issues: list[LintIssue] = Field(default_factory=list)
    summaries: list[LintToolSummary] = Field(default_factory=list)
    total_issues: int = 0
    total_errors: int = 0
    report_timestamp: datetime
