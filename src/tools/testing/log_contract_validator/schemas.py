# @summary
# Pydantic v2 schemas for the log-contract-validator tool: log-call records,
# violation entries, and the aggregated report structure (including the
# log path coverage metric).
# Exports: LogCall, LogContractViolation, LogContractReport
# Deps: pydantic
# @end-summary
"""Schemas for the log-contract-validator tool.

These models define the contract surface for log archetype validation:

- ``LogCall``: a single logging call discovered in source.
- ``LogContractViolation``: a single rule infraction tied to a source location.
- ``LogContractReport``: the aggregated audit result, including the
  ``log_path_coverage`` metric used by ``code-test-auditor`` and ``code-test-generator``.

The schemas are intentionally project-agnostic — paths, modules, and policy
locations are passed by the caller.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


LogLevel = Literal[
    "debug",
    "info",
    "warning",
    "error",
    "critical",
    "exception",
]

ViolationType = Literal[
    "missing_log_in_except",
    "wrong_level_for_archetype",
    "missing_required_field",
    "f_string_template",
    "bare_logger_no_module",
    "log_in_hot_loop",
]


class LogCall(BaseModel):
    """A single logging call discovered in source code."""

    module: str
    function_name: str | None = None
    line: int
    level: LogLevel
    message_template: str
    has_extra_fields: bool = False
    extra_field_names: list[str] = Field(default_factory=list)


class LogContractViolation(BaseModel):
    """A single archetype-contract violation tied to a source location."""

    module: str
    line: int
    violation_type: ViolationType
    message: str
    expected: str | None = None
    actual: str | None = None


class LogContractReport(BaseModel):
    """Aggregated audit output for a source tree."""

    source_root: str
    policy_path: str | None = None
    log_calls: list[LogCall] = Field(default_factory=list)
    violations: list[LogContractViolation] = Field(default_factory=list)
    total_branches: int = 0
    branches_with_log: int = 0
    log_path_coverage: float = 0.0
    timestamp: datetime
