# @summary
# CLI tool that runs a pytest test node ≥10 times and computes a flakiness fail rate.
# Outputs a FlakinessSummary as JSON to stdout.
# Exits 0 (stable), 1 (flaky-quarantined), or 2 (tool error).
# Exports: main (entry point)
# Deps: subprocess, argparse, time, datetime, json, sys, schemas.FlakinessSummary, schemas.TestOutcome
# @end-summary

"""Flakiness-checker: run a pytest test repeatedly and measure its fail rate.

Usage
-----
    python -m src.tools.testing.flakiness_checker <test_node_id> [--runs N] [--timeout SECONDS]

Exit codes
----------
    0  Test is stable (fail_rate < 2 %).
    1  Test is flaky-quarantined (fail_rate >= 2 %).
    2  Tool error (bad arguments, pytest not found, etc.).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone

# Support both package import and ``python flakiness_checker.py``
# (the hyphenated tool directory cannot be imported as a package).
try:  # pragma: no cover - import shim
    from .schemas import FlakinessSummary, TestOutcome
except ImportError:  # pragma: no cover - import shim
    import os

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from schemas import FlakinessSummary, TestOutcome  # type: ignore[no-redef]

_MIN_RUNS = 10
_STABLE_THRESHOLD = 0.02  # fail_rate strictly below this → stable


def _run_once(test_node_id: str, timeout: float, run_number: int) -> TestOutcome:
    """Execute pytest for *test_node_id* once and return a TestOutcome."""
    cmd = ["pytest", test_node_id, "-x", "--tb=short", "-q"]
    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - start
        combined = (exc.stdout or "") + (exc.stderr or "")
        return TestOutcome(
            run_number=run_number,
            passed=False,
            duration_seconds=round(duration, 4),
            error_message=f"Timed out after {timeout}s. {combined[:2000]}".strip(),
        )
    except FileNotFoundError:
        raise RuntimeError(
            "pytest executable not found. Ensure pytest is installed in the active environment."
        )

    duration = time.monotonic() - start
    passed = result.returncode == 0
    error_message: str | None = None
    if not passed:
        combined = (result.stdout + result.stderr).strip()
        error_message = combined[:2000] if combined else f"pytest exited {result.returncode}"

    return TestOutcome(
        run_number=run_number,
        passed=passed,
        duration_seconds=round(duration, 4),
        error_message=error_message,
    )


def run_flakiness_check(
    test_node_id: str,
    runs: int,
    timeout: float,
) -> FlakinessSummary:
    """Run *test_node_id* exactly *runs* times and return a FlakinessSummary."""
    outcomes: list[TestOutcome] = []
    started_at = datetime.now(tz=timezone.utc)

    for i in range(1, runs + 1):
        outcome = _run_once(test_node_id, timeout=timeout, run_number=i)
        outcomes.append(outcome)

    failures = sum(1 for o in outcomes if not o.passed)
    fail_rate = failures / runs
    status = "stable" if fail_rate < _STABLE_THRESHOLD else "flaky-quarantined"

    return FlakinessSummary(
        test_id=test_node_id,
        total_runs=runs,
        failures=failures,
        fail_rate=round(fail_rate, 6),
        status=status,
        outcomes=outcomes,
        run_timestamp=started_at,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flakiness-checker",
        description=(
            "Run a pytest test node ≥10 times and compute a flakiness fail rate. "
            "Outputs FlakinessSummary JSON to stdout."
        ),
    )
    parser.add_argument(
        "test_node_id",
        help="Pytest node id to test, e.g. tests/test_foo.py::test_bar.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=_MIN_RUNS,
        metavar="N",
        help=f"Number of times to run the test (minimum {_MIN_RUNS}, default {_MIN_RUNS}).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        metavar="SECONDS",
        help="Per-run timeout in seconds (default: 120).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.runs < _MIN_RUNS:
        parser.error(
            f"--runs must be at least {_MIN_RUNS}; got {args.runs}. "
            "The minimum is enforced to produce a statistically meaningful fail rate."
        )

    if args.timeout <= 0:
        parser.error(f"--timeout must be a positive number; got {args.timeout}.")

    try:
        summary = run_flakiness_check(
            test_node_id=args.test_node_id,
            runs=args.runs,
            timeout=args.timeout,
        )
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
    except Exception as exc:  # noqa: BLE001
        print(f"Unexpected tool error: {exc}", file=sys.stderr)
        sys.exit(2)

    print(summary.model_dump_json(indent=2))

    if summary.status == "flaky-quarantined":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
