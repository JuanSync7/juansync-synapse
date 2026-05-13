"""Finding dataclass + severity aggregation for `cortex doctor`.

Stdlib only. Categories use Python identifiers (`pin_rot`, `submodule_stale`)
for ergonomic dataclass usage; the human-readable / JSON form uses hyphens
(`pin-rot`, `submodule-stale`). Use `to_display()` to convert.

Severity rules:
- error → exit code 2
- warn  → exit code 1
- info  → exit code 0 (informational only)

`aggregate_exit_code` honors a `severity_floor`: any finding strictly below the
floor is treated as if absent. Default floor is "info" (include everything).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal

Severity = Literal["info", "warn", "error"]
Category = Literal[
    "drift",
    "stale",
    "missing",
    "orphaned",
    "corrupt",
    "pin_rot",
    "submodule_stale",
]


@dataclass
class Finding:
    category: str          # one of Category (Literal); kept as str for forward-compat
    severity: str          # one of Severity
    artifact: str          # e.g. "skill/foo" or "" for global findings
    message: str           # human-readable one-liner
    details: dict = field(default_factory=dict)  # category-specific data

    def to_dict(self) -> dict:
        return asdict(self)


CATEGORY_SEVERITY: dict[str, str] = {
    "drift": "warn",
    "stale": "warn",
    "missing": "error",
    "orphaned": "warn",
    "corrupt": "error",
    "pin_rot": "warn",
    "submodule_stale": "info",
}


_SEVERITY_RANK = {"info": 0, "warn": 1, "error": 2}


def to_display(cat: str) -> str:
    """Underscore-form Python id → hyphenated display form for messages/JSON."""
    return cat.replace("_", "-")


def aggregate_exit_code(findings: list[Finding], severity_floor: str = "info") -> int:
    """Compute exit code from a list of findings.

    - 0 = clean (no findings, only info, or all below floor)
    - 1 = warn highest
    - 2 = error highest

    `severity_floor` drops any finding whose severity rank is strictly below the
    floor's rank. Default "info" keeps everything.
    """
    floor_rank = _SEVERITY_RANK.get(severity_floor, 0)
    highest = 0
    for f in findings:
        rank = _SEVERITY_RANK.get(f.severity, 0)
        if rank < floor_rank:
            continue
        if rank > highest:
            highest = rank
    # info → 0, warn → 1, error → 2
    return highest
