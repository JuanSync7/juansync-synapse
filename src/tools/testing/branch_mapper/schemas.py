# @summary
# Pydantic v2 schemas for the branch-mapper tool.
# Defines the contract for per-function branch enumeration consumed by the
# test-generate skill to produce branch-coverage-aware tests.
# Exports: Branch, FunctionBranchMap, BranchMap
# Deps: pydantic
# @end-summary

"""Schemas for the branch-mapper tool.

A ``BranchMap`` is the top-level artifact emitted by :mod:`branch_mapper`.
For each public function in a source tree it lists every executable branch
reachable from that function (including branches in private helpers it
transitively calls within the same module).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


BranchType = Literal[
    "if",
    "elif",
    "else",
    "try",
    "except",
    "finally",
    "for",
    "while",
    "ternary",
    "and",
    "or",
]


class Branch(BaseModel):
    """A single executable branch within a function body.

    Attributes:
        branch_type: The kind of branch construct this represents.
        line: 1-indexed line where the branch construct starts.
        end_line: 1-indexed last line of the branch body.
        condition: Source text of the test/condition. ``None`` for ``else``
            and ``finally`` branches which have no condition.
        in_function: Qualified name (``module.func`` or
            ``module.func.helper``) identifying which function body this
            branch was lifted from. Helpers reached transitively are
            inlined under the calling public function.
    """

    branch_type: BranchType
    line: int
    end_line: int
    condition: str | None = None
    in_function: str


class FunctionBranchMap(BaseModel):
    """Branch enumeration for a single function.

    ``branches`` includes branches from private helpers that this function
    transitively calls (only same-module helpers are followed). The
    ``transitive_helpers`` field lists the qualified names of those helpers
    so consumers can attribute branches back to their source.
    """

    module: str
    function_name: str
    line_start: int
    line_end: int
    is_public: bool
    branches: list[Branch] = Field(default_factory=list)
    transitive_helpers: list[str] = Field(default_factory=list)
    total_branch_count: int


class BranchMap(BaseModel):
    """Top-level branch map for a source tree."""

    source_root: str
    functions: list[FunctionBranchMap] = Field(default_factory=list)
    timestamp: datetime
