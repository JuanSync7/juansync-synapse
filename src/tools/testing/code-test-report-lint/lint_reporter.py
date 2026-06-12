# @summary
# CLI entry point for the lint-reporter tool. Runs ruff, mypy, bandit, and
# vulture as subprocesses against a source root, normalizes their output
# into LintIssue records, and emits a single LintReport JSON document.
# Exports: main, run_lint_report, ALL_TOOLS
# Deps: schemas (sibling), stdlib (subprocess, json, argparse, shutil, re)
# @end-summary

"""``lint-reporter`` CLI.

Aggregates the output of four Python linters into one structured
:class:`~schemas.LintReport`. Each linter runs in its native JSON mode
where possible; ``vulture`` is parsed from its line-oriented text output.

Usage::

    python -m src.tools.testing.lint_reporter <source_root> \\
        [--tools ruff,mypy,bandit,vulture] [--exclude PATTERN]

Exit codes:
    0 — no error-severity issues found
    1 — one or more error-severity issues detected
    2 — internal tool failure (e.g. malformed args, schema error)

Linter unavailability (binary not on ``PATH``) is *not* an error: the
affected tool is recorded with ``available=False`` and an empty issue
list. This tool never modifies source files — it is a pure reporter.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

# Support both `python -m src.tools.testing.lint_reporter` (package mode)
# and direct execution (script mode).
try:
    from .schemas import LintIssue, LintReport, LintToolSummary, Severity, ToolName
except ImportError:  # pragma: no cover — script-mode fallback
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from schemas import (  # type: ignore[no-redef]
        LintIssue,
        LintReport,
        LintToolSummary,
        Severity,
        ToolName,
    )


ALL_TOOLS: tuple[ToolName, ...] = ("ruff", "mypy", "bandit", "vulture")


# ---------------------------------------------------------------------------
# Severity mapping
# ---------------------------------------------------------------------------

def _map_ruff_severity(_rule_id: str) -> Severity:
    """All ruff diagnostics surface as errors in JSON mode."""
    return "error"


def _map_mypy_severity(raw: str) -> Severity:
    if raw == "error":
        return "error"
    if raw == "warning":
        return "warning"
    return "info"


def _map_bandit_severity(raw: str) -> Severity:
    raw_lower = (raw or "").lower()
    if raw_lower == "high":
        return "error"
    if raw_lower == "medium":
        return "warning"
    return "info"


def _map_vulture_severity(_rule_id: str) -> Severity:
    """Vulture reports dead code — surfaced as warnings."""
    return "warning"


# ---------------------------------------------------------------------------
# Subprocess plumbing
# ---------------------------------------------------------------------------

def _run(cmd: list[str]) -> tuple[int, str, str]:
    """Run a subprocess, returning (returncode, stdout, stderr).

    Never raises on non-zero exit — many linters use exit codes to signal
    "issues found" rather than tool failure.
    """
    proc = subprocess.run(  # noqa: S603 — caller controls argv
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _summarize(tool: ToolName, issues: list[LintIssue]) -> LintToolSummary:
    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")
    return LintToolSummary(
        tool=tool,
        issue_count=len(issues),
        error_count=errors,
        warning_count=warnings,
        available=True,
    )


def _unavailable(tool: ToolName) -> LintToolSummary:
    return LintToolSummary(
        tool=tool,
        available=False,
        error_message=f"{tool} not found on PATH",
    )


def _tool_error(tool: ToolName, msg: str) -> LintToolSummary:
    return LintToolSummary(
        tool=tool,
        available=True,
        error_message=msg,
    )


# ---------------------------------------------------------------------------
# Per-linter runners — each returns (issues, summary)
# ---------------------------------------------------------------------------

def _run_ruff(
    source_root: str, excludes: list[str]
) -> tuple[list[LintIssue], LintToolSummary]:
    if shutil.which("ruff") is None:
        return [], _unavailable("ruff")

    cmd = ["ruff", "check", "--output-format=json"]
    for pattern in excludes:
        cmd.extend(["--exclude", pattern])
    cmd.append(source_root)

    _rc, stdout, stderr = _run(cmd)
    if not stdout.strip():
        # Ruff prints nothing on a clean run with --output-format=json? It
        # actually prints "[]" — but be defensive.
        return [], _summarize("ruff", [])

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return [], _tool_error(
            "ruff", f"failed to parse ruff JSON output: {exc}; stderr={stderr!r}"
        )

    issues: list[LintIssue] = []
    for item in payload:
        location = item.get("location") or {}
        rule_id = item.get("code") or "ruff"
        issues.append(
            LintIssue(
                file_path=item.get("filename", ""),
                line=int(location.get("row", 0) or 0),
                column=int(location.get("column", 0) or 0) or None,
                rule_id=rule_id,
                message=item.get("message", ""),
                severity=_map_ruff_severity(rule_id),
                tool="ruff",
            )
        )
    return issues, _summarize("ruff", issues)


_MYPY_TEXT_RE = re.compile(
    r"^(?P<file>[^:]+):(?P<line>\d+)(?::(?P<col>\d+))?:\s*"
    r"(?P<sev>error|warning|note):\s*(?P<msg>.*?)(?:\s*\[(?P<code>[\w\-]+)\])?$"
)


def _parse_mypy_text(stdout: str) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for line in stdout.splitlines():
        match = _MYPY_TEXT_RE.match(line.strip())
        if not match:
            continue
        sev_raw = match.group("sev")
        if sev_raw == "note":
            sev: Severity = "info"
        else:
            sev = _map_mypy_severity(sev_raw)
        col_raw = match.group("col")
        issues.append(
            LintIssue(
                file_path=match.group("file"),
                line=int(match.group("line")),
                column=int(col_raw) if col_raw else None,
                rule_id=match.group("code") or "mypy",
                message=match.group("msg").strip(),
                severity=sev,
                tool="mypy",
            )
        )
    return issues


def _run_mypy(
    source_root: str, excludes: list[str]
) -> tuple[list[LintIssue], LintToolSummary]:
    if shutil.which("mypy") is None:
        return [], _unavailable("mypy")

    base_cmd = [
        "mypy",
        "--no-error-summary",
        "--no-color-output",
        "--show-error-codes",
        "--no-pretty",
    ]
    for pattern in excludes:
        base_cmd.extend(["--exclude", pattern])
    base_cmd.append(source_root)

    _rc, stdout, stderr = _run(base_cmd)
    issues = _parse_mypy_text(stdout)

    if not issues and stderr.strip() and "error" in stderr.lower():
        # Distinguish "mypy ran fine, no issues" from "mypy crashed".
        # Heuristic: stderr without any parseable lines and exit code != 0/1.
        # Keep this conservative — only escalate on clear crash signals.
        if "Traceback" in stderr or "ImportError" in stderr:
            return [], _tool_error("mypy", stderr.strip().splitlines()[-1])

    return issues, _summarize("mypy", issues)


def _run_bandit(
    source_root: str, excludes: list[str]
) -> tuple[list[LintIssue], LintToolSummary]:
    if shutil.which("bandit") is None:
        return [], _unavailable("bandit")

    cmd = ["bandit", "-r", source_root, "-f", "json"]
    if excludes:
        cmd.extend(["-x", ",".join(excludes)])

    _rc, stdout, stderr = _run(cmd)
    if not stdout.strip():
        return [], _tool_error(
            "bandit", f"bandit produced no output; stderr={stderr!r}"
        )

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        return [], _tool_error("bandit", f"failed to parse bandit JSON: {exc}")

    issues: list[LintIssue] = []
    for item in payload.get("results", []):
        rule_id = item.get("test_id") or item.get("test_name") or "bandit"
        issues.append(
            LintIssue(
                file_path=item.get("filename", ""),
                line=int(item.get("line_number", 0) or 0),
                column=item.get("col_offset") or None,
                rule_id=rule_id,
                message=item.get("issue_text", ""),
                severity=_map_bandit_severity(item.get("issue_severity", "")),
                tool="bandit",
            )
        )
    return issues, _summarize("bandit", issues)


_VULTURE_RE = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+):\s*(?P<msg>.*?)\s*\((?P<conf>\d+)% confidence\)\s*$"
)


def _parse_vulture(stdout: str) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for line in stdout.splitlines():
        match = _VULTURE_RE.match(line.rstrip())
        if not match:
            continue
        msg = match.group("msg")
        # Derive a rule_id from the leading category (e.g. "unused import").
        rule_id = "vulture"
        head = msg.split(" ", 2)
        if len(head) >= 2 and head[0] == "unused":
            rule_id = f"unused-{head[1]}"
        issues.append(
            LintIssue(
                file_path=match.group("file"),
                line=int(match.group("line")),
                column=None,
                rule_id=rule_id,
                message=msg,
                severity=_map_vulture_severity(rule_id),
                tool="vulture",
            )
        )
    return issues


def _run_vulture(
    source_root: str, excludes: list[str]
) -> tuple[list[LintIssue], LintToolSummary]:
    if shutil.which("vulture") is None:
        return [], _unavailable("vulture")

    cmd = ["vulture", source_root, "--min-confidence", "60"]
    if excludes:
        cmd.extend(["--exclude", ",".join(excludes)])

    _rc, stdout, _stderr = _run(cmd)
    issues = _parse_vulture(stdout)
    return issues, _summarize("vulture", issues)


_RUNNERS = {
    "ruff": _run_ruff,
    "mypy": _run_mypy,
    "bandit": _run_bandit,
    "vulture": _run_vulture,
}


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_lint_report(
    source_root: str,
    tools: Iterable[ToolName] = ALL_TOOLS,
    excludes: list[str] | None = None,
) -> LintReport:
    """Run the requested linters and return an aggregated :class:`LintReport`."""
    excludes = excludes or []
    all_issues: list[LintIssue] = []
    summaries: list[LintToolSummary] = []

    for tool in tools:
        runner = _RUNNERS[tool]
        issues, summary = runner(source_root, excludes)
        all_issues.extend(issues)
        summaries.append(summary)

    total_errors = sum(1 for i in all_issues if i.severity == "error")
    return LintReport(
        source_root=source_root,
        issues=all_issues,
        summaries=summaries,
        total_issues=len(all_issues),
        total_errors=total_errors,
        report_timestamp=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_tools(raw: str) -> list[ToolName]:
    requested = [t.strip() for t in raw.split(",") if t.strip()]
    invalid = [t for t in requested if t not in ALL_TOOLS]
    if invalid:
        raise argparse.ArgumentTypeError(
            f"unknown tool(s): {', '.join(invalid)}; valid: {', '.join(ALL_TOOLS)}"
        )
    return requested  # type: ignore[return-value]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lint-reporter",
        description=(
            "Aggregate ruff, mypy, bandit, and vulture output into a single "
            "structured LintReport JSON document."
        ),
    )
    parser.add_argument("source_root", help="Path to the source root to lint.")
    parser.add_argument(
        "--tools",
        type=_parse_tools,
        default=list(ALL_TOOLS),
        help="Comma-separated subset of tools to run (default: all four).",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="PATTERN",
        help="Glob/path pattern to exclude. May be passed multiple times.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    source_root = args.source_root
    if not Path(source_root).exists():
        print(
            json.dumps({"error": f"source_root does not exist: {source_root}"}),
            file=sys.stderr,
        )
        return 2

    try:
        report = run_lint_report(
            source_root=source_root,
            tools=args.tools,
            excludes=list(args.exclude),
        )
    except Exception as exc:  # noqa: BLE001 — top-level CLI guard
        print(json.dumps({"error": f"lint-reporter failed: {exc}"}), file=sys.stderr)
        return 2

    print(report.model_dump_json(indent=2))
    return 1 if report.total_errors > 0 else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
