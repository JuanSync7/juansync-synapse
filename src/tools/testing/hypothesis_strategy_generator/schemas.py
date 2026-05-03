# @summary
# Pydantic v2 contracts for the hypothesis-strategy-generator tool:
# per-parameter strategy, per-function decorator bundle, and the aggregated
# StrategyReport returned by the CLI.
# Exports: ParameterStrategy, FunctionStrategy, StrategyReport
# Deps: pydantic
# @end-summary

"""Typed contracts for the ``hypothesis-strategy-generator`` tool.

The generator inspects function type hints via :mod:`ast` and emits ready-to-use
Hypothesis ``@given`` decorators for each parameter. These models form the
public schema consumed by the ``test-generate`` skill and any downstream
property-based test scaffolding.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ParameterStrategy(BaseModel):
    """A single parameter mapped to a Hypothesis strategy expression."""

    parameter_name: str = Field(..., description="Name of the function parameter.")
    type_hint_source: str = Field(
        ...,
        description="Raw source of the annotation, as produced by ``ast.unparse``.",
    )
    strategy_code: str = Field(
        ...,
        description=(
            "Hypothesis strategy expression for this parameter, "
            "e.g. ``st.integers(min_value=0, max_value=100)``."
        ),
    )
    is_supported: bool = Field(
        ...,
        description=(
            "False when the annotation could not be mapped to a known strategy. "
            "When False, ``strategy_code`` is set to ``st.nothing()`` with a TODO."
        ),
    )
    fallback_reason: str | None = Field(
        default=None,
        description="Why mapping fell back to ``st.nothing()`` (only set when ``is_supported`` is False).",
    )


class FunctionStrategy(BaseModel):
    """The full ``@given(...)`` decorator bundle for a single function."""

    module: str = Field(..., description="Dotted module path for the function's source file.")
    function_name: str = Field(..., description="Name of the function.")
    line_start: int = Field(..., description="1-based line number where the function is defined.")
    parameters: list[ParameterStrategy] = Field(
        default_factory=list,
        description="One entry per annotated parameter (self/cls excluded).",
    )
    given_decorator: str = Field(
        ...,
        description="Full ``@given(name=strategy, ...)`` decorator source ready to paste above the function.",
    )
    required_imports: list[str] = Field(
        default_factory=list,
        description=(
            "Import statements required by ``given_decorator`` and the strategies it references, "
            "e.g. ``from hypothesis import given, strategies as st``."
        ),
    )
    all_supported: bool = Field(
        ...,
        description="True when every parameter mapped to a real strategy (no ``st.nothing()`` fallbacks).",
    )


class StrategyReport(BaseModel):
    """Top-level CLI payload for the hypothesis-strategy-generator."""

    source_root: str = Field(..., description="Source root that was scanned.")
    functions: list[FunctionStrategy] = Field(
        default_factory=list,
        description="One entry per discovered function with at least one annotated parameter.",
    )
    total_functions: int = Field(..., description="Number of functions in ``functions``.")
    fully_supported: int = Field(
        ...,
        description="Count of functions whose every parameter mapped successfully (``all_supported`` True).",
    )
    partially_supported: int = Field(
        ...,
        description="Count of functions with at least one unsupported parameter.",
    )
    timestamp: datetime = Field(..., description="UTC timestamp at which the report was assembled.")
