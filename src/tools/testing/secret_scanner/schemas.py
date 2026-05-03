# @summary
# Pydantic v2 schemas for the secret-scanner tool.
# Exports: SecretFinding, SecretScanResult
# Deps: pydantic, datetime
# @end-summary

"""Pydantic v2 data contracts for the secret-scanner tool."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SecretFinding(BaseModel):
    """A single secret detected in a scanned file."""

    line_number: int = Field(
        ...,
        description="1-based line number in the file where the pattern was matched.",
    )
    pattern_name: str = Field(
        ...,
        description=(
            "Identifier for the pattern that fired, e.g. 'authorization_header', "
            "'stripe_live_key', 'aws_access_key'."
        ),
    )
    matched_text: str = Field(
        ...,
        description=(
            "Redacted representation of the matched text: first 4 characters followed "
            "by '***'.  Raw secret values are never stored or emitted."
        ),
    )
    severity: Literal["critical", "high", "medium"] = Field(
        ...,
        description=(
            "Severity rating: 'critical' for live service credentials, "
            "'high' for auth tokens / API keys, 'medium' for generic high-entropy strings."
        ),
    )


class SecretScanResult(BaseModel):
    """Full result of scanning a single file for leaked secrets."""

    file_path: str = Field(
        ...,
        description="Absolute or relative path to the file that was scanned.",
    )
    has_secrets: bool = Field(
        ...,
        description="True if at least one SecretFinding was detected.",
    )
    findings: list[SecretFinding] = Field(
        ...,
        description="All findings detected in the file, ordered by line_number.",
    )
    scan_timestamp: datetime = Field(
        ...,
        description="UTC timestamp at which the scan was performed.",
    )
