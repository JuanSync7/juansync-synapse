"""Read/write `pins.toml` (user-intent layer for synapse versioning).

Stdlib only. Reads via `tomllib`. Writes by hand-formatting strings, mirroring
the approach in `lockfile.py`.

Schema:

    schema_version = 1

    [synapse]
    pin = "v2026.05.0"   # tag | "latest" | "main" | "sha:HEX"

    [drift_exceptions."skill/foo"]
    hash    = "sha256:def..."
    reason  = "local debug logging"
    expires = "2026-06-01"   # or "" for never
"""
from __future__ import annotations

import os
import pathlib
import tomllib
from dataclasses import dataclass, field


@dataclass
class DriftException:
    artifact_key: str
    hash: str
    reason: str
    expires: str  # ISO date "YYYY-MM-DD" or "" for never


@dataclass
class Pins:
    schema_version: int = 1
    pin: str = "latest"
    drift_exceptions: dict[str, DriftException] = field(default_factory=dict)


def empty() -> Pins:
    return Pins()


def _quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _quote_key(k: str) -> str:
    return _quote(k)


def _to_toml(pins: Pins) -> str:
    lines: list[str] = []
    lines.append(f"schema_version = {pins.schema_version}")
    lines.append("")
    lines.append("[synapse]")
    lines.append(f"pin = {_quote(pins.pin)}")

    if pins.drift_exceptions:
        for key in sorted(pins.drift_exceptions.keys()):
            d = pins.drift_exceptions[key]
            lines.append("")
            lines.append(f"[drift_exceptions.{_quote_key(key)}]")
            lines.append(f"hash = {_quote(d.hash)}")
            lines.append(f"reason = {_quote(d.reason)}")
            lines.append(f"expires = {_quote(d.expires)}")

    return "\n".join(lines) + "\n"


def save(pins: Pins, path: pathlib.Path) -> None:
    """Atomically write pins.toml. Writes to a .tmp then os.replace()s."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    body = _to_toml(pins)
    tmp.write_text(body)
    try:
        os.replace(tmp, path)
    except Exception:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise


def load(path: pathlib.Path) -> Pins:
    """Parse pins.toml. Returns defaults if file missing.

    Raises tomllib.TOMLDecodeError if file exists but is malformed.
    """
    path = pathlib.Path(path)
    if not path.exists():
        return empty()
    raw = tomllib.loads(path.read_text())

    pins = Pins(
        schema_version=int(raw.get("schema_version", 1)),
    )
    syn = raw.get("synapse") or {}
    pins.pin = str(syn.get("pin", "latest")) or "latest"

    for key, body in (raw.get("drift_exceptions") or {}).items():
        pins.drift_exceptions[key] = DriftException(
            artifact_key=key,
            hash=str(body.get("hash", "")),
            reason=str(body.get("reason", "")),
            expires=str(body.get("expires", "")),
        )
    return pins
