# @summary
# CLI entry point for the secret-scanner tool.
# Scans a file for leaked secrets: auth headers, API keys, tokens, high-entropy strings.
# Reads the target file, applies all pattern checks, and outputs a SecretScanResult.
# Exports: main
# Deps: re, json, argparse, sys, pathlib, pydantic, schemas
# @end-summary

"""
secret-scanner — leaked-secret detector for vcrpy cassettes and source files.

Usage
-----
    python -m src.tools.testing.secret_scanner <file_path> [--format json|text]

Exit codes
----------
    0   No secrets detected.
    1   One or more secrets detected.
    2   Tool error (unreadable file, bad arguments, import failure).

Output is written to stdout.  Errors go to stderr.
``matched_text`` in all output is always redacted: first 4 chars + ``***``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Pattern catalogue
# ---------------------------------------------------------------------------

class _Pattern(NamedTuple):
    name: str
    regex: re.Pattern[str]
    severity: str  # "critical" | "high" | "medium"


# Header patterns — match lines that look like YAML/HTTP header entries.
# The value portion is captured in group 1.
_HEADER_PATTERNS: list[_Pattern] = [
    _Pattern(
        name="authorization_bearer",
        regex=re.compile(r"Authorization:\s*Bearer\s+(\S+)", re.IGNORECASE),
        severity="critical",
    ),
    _Pattern(
        name="authorization_basic",
        regex=re.compile(r"Authorization:\s*Basic\s+(\S+)", re.IGNORECASE),
        severity="critical",
    ),
    _Pattern(
        name="x_api_key_header",
        regex=re.compile(r"X-API-Key:\s*(\S+)", re.IGNORECASE),
        severity="high",
    ),
    _Pattern(
        name="x_stripe_signature",
        regex=re.compile(r"X-Stripe-Signature:\s*(\S+)", re.IGNORECASE),
        severity="high",
    ),
    _Pattern(
        name="cookie_header",
        # Non-empty Cookie value only.
        regex=re.compile(r"Cookie:\s*(\S[^\r\n]*)", re.IGNORECASE),
        severity="high",
    ),
    _Pattern(
        name="generic_token_header",
        regex=re.compile(r"[\w]+-token:\s*(\S+)", re.IGNORECASE),
        severity="high",
    ),
    _Pattern(
        name="generic_secret_header",
        regex=re.compile(r"[\w]+-secret:\s*(\S+)", re.IGNORECASE),
        severity="high",
    ),
    _Pattern(
        name="generic_key_header",
        regex=re.compile(r"[\w]+-key:\s*(\S+)", re.IGNORECASE),
        severity="high",
    ),
]

# Query-string patterns — match anywhere on the line.
# The parameter value is captured in group 1.
_QUERY_PATTERNS: list[_Pattern] = [
    _Pattern(
        name="query_api_key",
        regex=re.compile(r"[?&]api_key=([^&\s\"']+)", re.IGNORECASE),
        severity="high",
    ),
    _Pattern(
        name="query_token",
        regex=re.compile(r"[?&]token=([^&\s\"']+)", re.IGNORECASE),
        severity="high",
    ),
    _Pattern(
        name="query_key",
        regex=re.compile(r"[?&]key=([^&\s\"']+)", re.IGNORECASE),
        severity="high",
    ),
    _Pattern(
        name="query_secret",
        regex=re.compile(r"[?&]secret=([^&\s\"']+)", re.IGNORECASE),
        severity="high",
    ),
    _Pattern(
        name="query_access_token",
        regex=re.compile(r"[?&]access_token=([^&\s\"']+)", re.IGNORECASE),
        severity="high",
    ),
]

# Body / JSON field patterns — match JSON key: value pairs in the line.
# The value is captured in group 1.
_BODY_PATTERNS: list[_Pattern] = [
    _Pattern(
        name="body_password",
        regex=re.compile(r'"password"\s*:\s*"([^"]+)"', re.IGNORECASE),
        severity="critical",
    ),
    _Pattern(
        name="body_token",
        regex=re.compile(r'"token"\s*:\s*"([^"]+)"', re.IGNORECASE),
        severity="high",
    ),
    _Pattern(
        name="body_secret",
        regex=re.compile(r'"secret"\s*:\s*"([^"]+)"', re.IGNORECASE),
        severity="high",
    ),
    _Pattern(
        name="body_client_secret",
        regex=re.compile(r'"client_secret"\s*:\s*"([^"]+)"', re.IGNORECASE),
        severity="critical",
    ),
    _Pattern(
        name="body_api_key",
        regex=re.compile(r'"api_key"\s*:\s*"([^"]+)"', re.IGNORECASE),
        severity="high",
    ),
    _Pattern(
        name="body_access_token",
        regex=re.compile(r'"access_token"\s*:\s*"([^"]+)"', re.IGNORECASE),
        severity="high",
    ),
    _Pattern(
        name="body_refresh_token",
        regex=re.compile(r'"refresh_token"\s*:\s*"([^"]+)"', re.IGNORECASE),
        severity="high",
    ),
]

# Generic high-entropy / known-format patterns.
# These patterns match the full token directly (no separate capture group for value).
_GENERIC_PATTERNS: list[_Pattern] = [
    _Pattern(
        name="stripe_live_key",
        regex=re.compile(r"((?:sk|pk|rk)_live_[A-Za-z0-9]{10,})", re.IGNORECASE),
        severity="critical",
    ),
    _Pattern(
        name="aws_access_key",
        regex=re.compile(r"(AKIA[A-Z0-9]{16})"),
        severity="critical",
    ),
    _Pattern(
        name="high_entropy_base64",
        regex=re.compile(r"([A-Za-z0-9+/]{40,}={0,2})"),
        severity="medium",
    ),
]

# All patterns in one flat list for uniform iteration.
_ALL_PATTERNS: list[_Pattern] = (
    _HEADER_PATTERNS + _QUERY_PATTERNS + _BODY_PATTERNS + _GENERIC_PATTERNS
)


# ---------------------------------------------------------------------------
# Redaction helper
# ---------------------------------------------------------------------------

def _redact(value: str) -> str:
    """Return the first 4 characters of *value* followed by ``***``."""
    if len(value) <= 4:
        return value[:len(value)] + "***"
    return value[:4] + "***"


# ---------------------------------------------------------------------------
# Core scanner
# ---------------------------------------------------------------------------

def _scan_lines(lines: list[str]) -> list[dict]:
    """
    Scan *lines* against all patterns and return a list of raw finding dicts.

    Each dict contains: line_number (int, 1-based), pattern_name (str),
    matched_text (str, redacted), severity (str).
    """
    findings: list[dict] = []

    for lineno, line in enumerate(lines, start=1):
        for pattern in _ALL_PATTERNS:
            for match in pattern.regex.finditer(line):
                # Use group 1 (the captured value) when available; otherwise the full match.
                try:
                    raw_value = match.group(1)
                except IndexError:
                    raw_value = match.group(0)

                # Skip empty captures (e.g. Cookie with truly empty value).
                if not raw_value or not raw_value.strip():
                    continue

                findings.append(
                    {
                        "line_number": lineno,
                        "pattern_name": pattern.name,
                        "matched_text": _redact(raw_value),
                        "severity": pattern.severity,
                    }
                )

    # Sort by line number for deterministic output.
    findings.sort(key=lambda f: f["line_number"])
    return findings


def scan_file(file_path: str | Path) -> dict:
    """
    Scan *file_path* for secrets and return a SecretScanResult-shaped dict.

    Raises ``OSError`` if the file cannot be read.
    """
    path = Path(file_path)

    # Ensure schemas module is importable from this tool's directory.
    tool_dir = Path(__file__).parent
    if str(tool_dir) not in sys.path:
        sys.path.insert(0, str(tool_dir))

    from schemas import SecretFinding, SecretScanResult  # noqa: PLC0415

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    raw_findings = _scan_lines(lines)

    findings = [SecretFinding(**f) for f in raw_findings]
    result = SecretScanResult(
        file_path=str(path),
        has_secrets=bool(findings),
        findings=findings,
        scan_timestamp=datetime.now(tz=timezone.utc),
    )
    return result.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def _format_json(result: dict) -> str:
    return json.dumps(result, indent=2, default=str)


def _format_text(result: dict) -> str:
    lines: list[str] = []
    lines.append(f"File     : {result['file_path']}")
    lines.append(f"Secrets  : {'YES' if result['has_secrets'] else 'none'}")
    lines.append(f"Scanned  : {result['scan_timestamp']}")

    if result["findings"]:
        lines.append("")
        lines.append(f"{'Line':<8} {'Severity':<10} {'Pattern':<30} {'Matched'}")
        lines.append("-" * 72)
        for f in result["findings"]:
            lines.append(
                f"{f['line_number']:<8} {f['severity']:<10} {f['pattern_name']:<30} {f['matched_text']}"
            )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _fatal(message: str, code: int = 2) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(code)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="secret-scanner",
        description=(
            "Scan a file for leaked secrets — auth headers, API keys, tokens, "
            "and high-entropy strings.  Exit 0 = clean; exit 1 = secrets found; "
            "exit 2 = tool error."
        ),
    )
    parser.add_argument(
        "file_path",
        help="Path to the file to scan (e.g. a vcrpy cassette YAML or source file).",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format: 'json' (default) or human-readable 'text'.",
    )
    return parser


def main() -> None:
    """Entry point for the secret-scanner tool."""
    parser = _build_parser()
    args = parser.parse_args()

    target = Path(args.file_path)
    if not target.is_file():
        _fatal(f"'{target}' is not a file or does not exist.", code=2)

    try:
        result = scan_file(target)
    except OSError as exc:
        _fatal(f"Could not read '{target}': {exc}", code=2)

    if args.format == "text":
        print(_format_text(result))
    else:
        print(_format_json(result))

    sys.exit(1 if result["has_secrets"] else 0)


if __name__ == "__main__":
    main()
