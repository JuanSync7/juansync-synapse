"""Read/write `installed.lock` (TOML) lockfiles.

Stdlib only. Reads via `tomllib`. Writes by hand-formatting strings, since
Python's stdlib has no TOML writer. The schema is fixed and small, so we don't
attempt to be a general TOML serializer — we serialize exactly the shapes
defined by the dataclasses below.

Schema (excerpt):

    schema_version = 1
    synapse_repo   = "/abs/path"
    synapse_tag    = "v2026.05.0"
    synapse_sha    = "abc123..."
    installed_at   = "2026-05-06T14:32:11Z"
    machine_id     = "host"

    [artifact."skill/foo"]
    source_path  = "..."
    install_path = "..."
    content_hash = "sha256:..."
    type         = "skill"
    status       = "installed"

    [external."some-suite"]
    submodule_path = "..."
    submodule_sha  = "..."
    content_hash   = "sha256:..."
    status         = "installed"
"""
from __future__ import annotations

import os
import pathlib
import tomllib
from dataclasses import dataclass, field


@dataclass
class Artifact:
    key: str
    source_path: str
    install_path: str
    content_hash: str
    type: str
    status: str


@dataclass
class External:
    key: str
    submodule_path: str
    submodule_sha: str
    content_hash: str
    status: str


@dataclass
class Lockfile:
    schema_version: int = 1
    synapse_repo: str = ""
    synapse_tag: str = ""
    synapse_sha: str = ""
    installed_at: str = ""
    machine_id: str = ""
    artifacts: dict[str, Artifact] = field(default_factory=dict)
    externals: dict[str, External] = field(default_factory=dict)


def empty() -> Lockfile:
    return Lockfile()


def _quote(s: str) -> str:
    """Quote a string as a basic TOML string. Escape backslash and double quote."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _quote_key(k: str) -> str:
    """Quote a TOML table key (always wrap; our keys contain `/`)."""
    return _quote(k)


def _write_toml(data: dict) -> str:
    """Hand-format the lockfile dict to TOML.

    Expected shape:
      {
        "schema_version": int,
        "synapse_repo" / "synapse_tag" / "synapse_sha" / "installed_at" / "machine_id": str,
        "artifact": {key: {field: str|int, ...}, ...},
        "external": {key: {field: str|int, ...}, ...},
      }
    """
    lines: list[str] = []

    # Top-level scalars in a stable order.
    scalar_order = [
        "schema_version",
        "synapse_repo",
        "synapse_tag",
        "synapse_sha",
        "installed_at",
        "machine_id",
    ]
    for k in scalar_order:
        if k not in data:
            continue
        v = data[k]
        if isinstance(v, bool):
            lines.append(f"{k} = {'true' if v else 'false'}")
        elif isinstance(v, int):
            lines.append(f"{k} = {v}")
        else:
            lines.append(f"{k} = {_quote(str(v))}")

    def _emit_section(section_name: str, sub: dict[str, dict]):
        # Sort keys for deterministic output.
        for key in sorted(sub.keys()):
            entry = sub[key]
            lines.append("")
            lines.append(f"[{section_name}.{_quote_key(key)}]")
            for ek in sorted(entry.keys()):
                ev = entry[ek]
                if isinstance(ev, bool):
                    lines.append(f"{ek} = {'true' if ev else 'false'}")
                elif isinstance(ev, int):
                    lines.append(f"{ek} = {ev}")
                else:
                    lines.append(f"{ek} = {_quote(str(ev))}")

    if data.get("artifact"):
        _emit_section("artifact", data["artifact"])
    if data.get("external"):
        _emit_section("external", data["external"])

    return "\n".join(lines) + "\n"


def _to_dict(lf: Lockfile) -> dict:
    out: dict = {
        "schema_version": lf.schema_version,
        "synapse_repo": lf.synapse_repo,
        "synapse_tag": lf.synapse_tag,
        "synapse_sha": lf.synapse_sha,
        "installed_at": lf.installed_at,
        "machine_id": lf.machine_id,
    }
    if lf.artifacts:
        out["artifact"] = {
            k: {
                "source_path": a.source_path,
                "install_path": a.install_path,
                "content_hash": a.content_hash,
                "type": a.type,
                "status": a.status,
            }
            for k, a in lf.artifacts.items()
        }
    if lf.externals:
        out["external"] = {
            k: {
                "submodule_path": e.submodule_path,
                "submodule_sha": e.submodule_sha,
                "content_hash": e.content_hash,
                "status": e.status,
            }
            for k, e in lf.externals.items()
        }
    return out


def save(lockfile: Lockfile, path: pathlib.Path) -> None:
    """Atomically write the lockfile. Writes to a temp file then os.replace()s."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    body = _write_toml(_to_dict(lockfile))
    tmp.write_text(body)
    try:
        os.replace(tmp, path)
    except Exception:
        # If atomic swap fails, do not leave the temp file lying around.
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise


def load(path: pathlib.Path) -> Lockfile:
    """Parse a lockfile from disk. Returns empty() if the file is missing."""
    path = pathlib.Path(path)
    if not path.exists():
        return empty()
    raw = tomllib.loads(path.read_text())

    lf = Lockfile(
        schema_version=int(raw.get("schema_version", 1)),
        synapse_repo=str(raw.get("synapse_repo", "")),
        synapse_tag=str(raw.get("synapse_tag", "")),
        synapse_sha=str(raw.get("synapse_sha", "")),
        installed_at=str(raw.get("installed_at", "")),
        machine_id=str(raw.get("machine_id", "")),
    )
    for key, body in (raw.get("artifact") or {}).items():
        lf.artifacts[key] = Artifact(
            key=key,
            source_path=str(body.get("source_path", "")),
            install_path=str(body.get("install_path", "")),
            content_hash=str(body.get("content_hash", "")),
            type=str(body.get("type", "")),
            status=str(body.get("status", "installed")),
        )
    for key, body in (raw.get("external") or {}).items():
        lf.externals[key] = External(
            key=key,
            submodule_path=str(body.get("submodule_path", "")),
            submodule_sha=str(body.get("submodule_sha", "")),
            content_hash=str(body.get("content_hash", "")),
            status=str(body.get("status", "installed")),
        )
    return lf
