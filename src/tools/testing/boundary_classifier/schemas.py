# @summary
# Pydantic v2 schemas for the boundary-classifier tool. Defines BoundaryFunction,
# InternalFunction, and the BoundaryClassification report envelope.
# Exports: BoundaryFunction, InternalFunction, BoundaryClassification, BoundaryType
# Deps: pydantic
# @end-summary

"""Schemas for boundary-classifier output.

A "boundary" function is one exposed at runtime via an external surface
(HTTP route, Temporal activity/workflow, CLI command, Celery task, env reader,
stdin reader, or a public export consumed across packages). All other functions
are "internal".
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

BoundaryType = Literal[
    "http_route",
    "temporal_activity",
    "temporal_workflow",
    "cli_command",
    "celery_task",
    "env_reader",
    "stdin_reader",
    "exported_public",
]


class BoundaryFunction(BaseModel):
    """A function classified as a runtime-exposed boundary."""

    module: str
    function_name: str
    qualified_name: str = Field(
        ...,
        description="Dotted path, e.g. 'ragweave.api.handlers.ingest_endpoint'.",
    )
    line: int
    boundary_type: BoundaryType
    detection_reason: str = Field(
        ..., description="Human-readable explanation of why this was classified."
    )
    decorator_source: str | None = Field(
        default=None,
        description="`ast.unparse` of the matched decorator, when decorator-based.",
    )


class InternalFunction(BaseModel):
    """A function classified as internal (not boundary-exposed)."""

    module: str
    function_name: str
    qualified_name: str
    line: int
    is_private: bool = Field(..., description="Name starts with an underscore.")
    in_all: bool = Field(..., description="Listed in the module's __all__.")


class BoundaryClassification(BaseModel):
    """Top-level report emitted to stdout."""

    source_root: str
    boundaries: list[BoundaryFunction] = Field(default_factory=list)
    internals: list[InternalFunction] = Field(default_factory=list)
    total_functions: int
    boundary_count: int
    internal_count: int
    timestamp: datetime
