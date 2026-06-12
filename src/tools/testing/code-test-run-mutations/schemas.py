# @summary
# Pydantic v2 contracts for the mutation-runner tool: Mutant descriptors,
# per-mutant test results, and the aggregated MutationReport returned by
# the CLI.
# Exports: Mutant, MutationResult, MutationReport, MutationType
# Deps: pydantic
# @end-summary

"""Typed contracts for the ``mutation-runner`` tool.

The mutation-runner generates AST mutants of a target function and runs
the project's test suite against each mutant. A mutant is "killed" when
at least one test fails under it; surviving mutants indicate weak
assertions in the test suite.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

MutationType = Literal[
    "arithmetic_op",   # + → -, * → /
    "comparison_op",   # < → >, == → !=
    "boolean_op",      # and → or
    "constant_swap",   # 0 → 1, True → False
    "boundary_flip",   # < → <=, > → >=
    "return_value",    # return x → return None
    "negate_condition",  # if x → if not x
]


class Mutant(BaseModel):
    """A single AST-level mutation applied to one source location."""

    mutant_id: str = Field(
        ...,
        description=(
            'Stable identifier of the form "<module>.<func>:<line>:'
            '<mutation_type>:<ordinal>".'
        ),
    )
    module: str
    function_name: str
    line: int
    mutation_type: MutationType
    original_code: str
    mutated_code: str


class MutationResult(BaseModel):
    """Outcome of running the test suite against one Mutant."""

    mutant: Mutant
    killed: bool = Field(
        ...,
        description="True if at least one test failed under the mutant.",
    )
    killing_test: str | None = Field(
        default=None,
        description="Pytest node id of the first failing test, if parseable.",
    )
    runtime_seconds: float
    error_output: str | None = Field(
        default=None,
        description="Subprocess error output (timeout, traceback, etc).",
    )


class MutationReport(BaseModel):
    """Aggregated mutation-testing report — the CLI's stdout payload."""

    source_root: str
    target_module: str
    target_function: str | None = None
    total_mutants: int = 0
    killed: int = 0
    survived: int = 0
    timeout: int = 0
    kill_rate: float = Field(
        default=0.0,
        description="killed / total_mutants; 1.0 means perfect mutation kill.",
    )
    results: list[MutationResult] = Field(default_factory=list)
    line_budget: int
    timestamp: datetime
