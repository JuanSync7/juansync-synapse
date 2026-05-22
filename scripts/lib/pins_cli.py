"""CLI entry point for pins.toml mutations and inspection.

Subcommands:
  path                     Print absolute pins.toml path and exit.
  current                  Print current pin value (default 'latest' if no file).
  pin <value>              Validate, resolve, and write pin = <value>.
  unpin                    Equivalent to `pin latest`.
  bump                     Freeze a floating pin to its current resolved tag/sha.
  status [--json]          Print pin status + drift summary.

Repo root for resolution is taken from `SYNAPSE_REPO_ROOT` env var (used by
tests + future externals), else `git rev-parse --show-toplevel` from this file.
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

import lockfile as lf_mod  # noqa: E402
import pins as pins_mod  # noqa: E402
import pins_resolver as resolver  # noqa: E402
import synapse_paths  # noqa: E402
import telemetry as _telemetry  # noqa: E402

PINS_FILENAME = "pins.toml"


def _pins_path() -> pathlib.Path:
    return synapse_paths.lockfile_dir() / PINS_FILENAME


def _repo_root() -> pathlib.Path:
    env = os.environ.get("SYNAPSE_REPO_ROOT")
    if env:
        return pathlib.Path(env).expanduser().resolve()
    out = subprocess.run(
        ["git", "-C", str(_HERE), "rev-parse", "--show-toplevel"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return pathlib.Path(out)


def cmd_path(_args) -> int:
    print(_pins_path())
    return 0


def cmd_current(_args) -> int:
    pins = pins_mod.load(_pins_path())
    print(pins.pin)
    return 0


def cmd_pin(args) -> int:
    value = args.value
    ok, reason = resolver.validate_pin_value(value)
    if not ok:
        print(f"error: {reason}", file=sys.stderr)
        return 2
    # Resolve eagerly so we fail loudly if the tag/sha doesn't exist.
    try:
        resolver.resolve_pin(value, _repo_root())
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    p = _pins_path()
    pins = pins_mod.load(p)
    before = pins.pin
    pins.pin = value
    pins_mod.save(pins, p)
    _telemetry.emit("pin_changed", metadata={"old": before, "new": value})
    print(f"pin: {before} -> {value}")
    return 0


def cmd_unpin(_args) -> int:
    p = _pins_path()
    pins = pins_mod.load(p)
    before = pins.pin
    pins.pin = "latest"
    pins_mod.save(pins, p)
    _telemetry.emit("pin_unpinned", metadata={"old": before, "new": "latest"})
    print(f"pin: {before} -> latest")
    return 0


def cmd_bump(_args) -> int:
    p = _pins_path()
    pins = pins_mod.load(p)
    before = pins.pin

    try:
        res = resolver.resolve_pin(before, _repo_root())
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if res.kind in ("tag", "sha"):
        # already frozen — write back same value, idempotent.
        pins_mod.save(pins, p)
        print(f"pin already frozen at {before} ({res.resolved_sha[:12]}...)")
        return 0

    if res.kind == "latest":
        # If a stable tag exists, write the tag.
        if res.resolved_tag:
            new_pin = res.resolved_tag
        else:
            new_pin = f"sha:{res.resolved_sha}"
    elif res.kind == "main":
        new_pin = f"sha:{res.resolved_sha}"
    else:
        print(f"error: unknown pin kind {res.kind!r}", file=sys.stderr)
        return 2

    pins.pin = new_pin
    pins_mod.save(pins, p)
    _telemetry.emit("pin_bumped", metadata={"old": before, "new": new_pin})
    print(f"pin: {before} -> {new_pin}")
    return 0


def _drift_counts(lf: lf_mod.Lockfile) -> tuple[int, int]:
    """(non_installed_artifacts, externals_total) from lockfile."""
    drifted = sum(1 for a in lf.artifacts.values() if a.status != "installed")
    return drifted, len(lf.externals)


def _expired(pins: pins_mod.Pins, today: str) -> int:
    n = 0
    for d in pins.drift_exceptions.values():
        if d.expires and d.expires < today:
            n += 1
    return n


def _today_iso() -> str:
    import datetime
    return datetime.date.today().isoformat()


def cmd_status(args) -> int:
    p = _pins_path()
    pins = pins_mod.load(p)
    lock_path = synapse_paths.lockfile_path()
    lf = lf_mod.load(lock_path)

    # Resolve pin (best-effort — if it fails we still want to show the spec).
    resolved_sha = ""
    kind = ""
    resolve_error = ""
    try:
        res = resolver.resolve_pin(pins.pin, _repo_root())
        resolved_sha = res.resolved_sha
        kind = res.kind
    except (ValueError, subprocess.CalledProcessError) as e:
        resolve_error = str(e)

    today = _today_iso()
    n_exceptions = len(pins.drift_exceptions)
    n_expired = _expired(pins, today)
    n_drifted, n_externals = _drift_counts(lf)
    lockfile_present = lock_path.exists()
    n_artifacts = len(lf.artifacts)

    if args.json:
        out = {
            "pin": pins.pin,
            "kind": kind,
            "resolved_sha": resolved_sha,
            "resolve_error": resolve_error,
            "drift_exceptions": n_exceptions,
            "drift_exceptions_expired": n_expired,
            "lockfile_path": str(lock_path),
            "lockfile_present": lockfile_present,
            "lockfile_artifacts": n_artifacts,
            "lockfile_externals": n_externals,
            "lockfile_drifted_artifacts": n_drifted,
            "pins_path": str(p),
        }
        print(json.dumps(out, indent=2))
        return 0

    print(f"Pin:           {pins.pin}")
    if resolved_sha:
        print(f"Resolved SHA:  {resolved_sha}")
    else:
        print(f"Resolved SHA:  <unresolved: {resolve_error}>")
    print(f"Pin kind:      {kind or '<unknown>'}")
    print(
        f"Drift summary: {n_exceptions} exceptions, {n_expired} expired, "
        f"{n_drifted} drifted artifacts"
    )
    if lockfile_present:
        print(
            f"Lockfile:      {lock_path} "
            f"({n_artifacts} artifacts, {n_externals} externals)"
        )
    else:
        print(f"Lockfile:      {lock_path} (no lockfile)")
    print(f"Pins file:     {p}{'' if p.exists() else ' (defaults — no file)'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="pins_cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("path").set_defaults(func=cmd_path)
    sub.add_parser("current").set_defaults(func=cmd_current)
    sub.add_parser("unpin").set_defaults(func=cmd_unpin)
    sub.add_parser("bump").set_defaults(func=cmd_bump)

    pin_sub = sub.add_parser("pin")
    pin_sub.add_argument("value")
    pin_sub.set_defaults(func=cmd_pin)

    st = sub.add_parser("status")
    st.add_argument("--json", action="store_true")
    st.set_defaults(func=cmd_status)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
