"""CLI entry point for `cortex doctor` — runs all 7 finding categories.

Usage:
    python3 scripts/lib/doctor_cli.py [--json] [--severity-floor info|warn|error]
                                      [--skip cat1,cat2,...] [--threshold-days N]

Exit codes (after `--severity-floor` filtering):
    0  clean (or only info findings)
    1  warn highest
    2  error highest
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import doctor_findings as df  # noqa: E402
import doctor_scan as scan_mod  # noqa: E402
import pins as pins_mod  # noqa: E402
import synapse_paths  # noqa: E402

PINS_FILENAME = "pins.toml"


def _repo_root() -> pathlib.Path:
    env = os.environ.get("SYNAPSE_REPO_ROOT")
    if env:
        return pathlib.Path(env).expanduser().resolve()
    out = subprocess.run(
        ["git", "-C", str(_HERE), "rev-parse", "--show-toplevel"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return pathlib.Path(out)


def _format_human(findings: list[df.Finding]) -> str:
    if not findings:
        return "No findings.\nFindings: 0 errors, 0 warnings, 0 info\n"
    n_err = sum(1 for f in findings if f.severity == "error")
    n_warn = sum(1 for f in findings if f.severity == "warn")
    n_info = sum(1 for f in findings if f.severity == "info")
    lines = [f"Findings: {n_err} errors, {n_warn} warnings, {n_info} info", ""]
    # Sort: error first, then warn, then info; stable within
    rank = {"error": 0, "warn": 1, "info": 2}
    sorted_f = sorted(findings, key=lambda f: rank.get(f.severity, 99))
    for f in sorted_f:
        cat_disp = df.to_display(f.category)
        lines.append(
            f"{f.severity:5s} {cat_disp:16s} {f.artifact:30s} {f.message}"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cortex doctor")
    p.add_argument("--json", action="store_true",
                   help="Emit JSON instead of human-readable output.")
    p.add_argument("--severity-floor", default="info",
                   choices=["info", "warn", "error"],
                   help="Suppress findings below this severity.")
    p.add_argument("--skip", default="",
                   help="Comma-separated category names to skip (e.g. 'pin_rot,submodule_stale').")
    p.add_argument("--threshold-days", type=int, default=90,
                   help="pin-rot threshold in days (default 90).")
    args = p.parse_args(argv)

    skip = {s.strip() for s in args.skip.split(",") if s.strip()}

    lockfile_path = synapse_paths.lockfile_path()
    pins_path = synapse_paths.lockfile_dir() / PINS_FILENAME
    pins = pins_mod.load(pins_path) if pins_path.exists() else pins_mod.empty()

    try:
        repo_root = _repo_root()
    except subprocess.CalledProcessError:
        repo_root = pathlib.Path.cwd()

    findings = scan_mod.scan_all(
        lockfile_path=lockfile_path,
        repo_root=repo_root,
        pins=pins,
        skip=skip,
        pin_rot_threshold_days=args.threshold_days,
    )

    # Apply severity floor for display + exit code
    rank = {"info": 0, "warn": 1, "error": 2}
    floor = rank[args.severity_floor]
    visible = [f for f in findings if rank.get(f.severity, 0) >= floor]

    exit_code = df.aggregate_exit_code(findings, severity_floor=args.severity_floor)

    if args.json:
        out = {
            "findings": [{
                "category": df.to_display(f.category),
                "severity": f.severity,
                "artifact": f.artifact,
                "message": f.message,
                "details": f.details,
            } for f in visible],
            "summary": {
                "error": sum(1 for f in visible if f.severity == "error"),
                "warn": sum(1 for f in visible if f.severity == "warn"),
                "info": sum(1 for f in visible if f.severity == "info"),
            },
            "exit_code": exit_code,
            "lockfile_path": str(lockfile_path),
            "repo_root": str(repo_root),
        }
        print(json.dumps(out, indent=2))
    else:
        sys.stdout.write(_format_human(visible))

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
