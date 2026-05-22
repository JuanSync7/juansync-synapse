"""Higher-level lockfile mutation operations called by install.sh.

These compose `lockfile` (data shape) with `hashing` (content digest) and
shell-out helpers (git rev-parse for SHAs/tags). They mutate a `Lockfile`
in-place; the caller is responsible for persisting via `lockfile.save()`.
"""
from __future__ import annotations

import datetime
import pathlib
import socket
import subprocess
import sys

from hashing import hash_directory
from lockfile import Artifact, External, Lockfile

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import telemetry as _telemetry  # noqa: E402


def upsert_artifact(
    lockfile: Lockfile,
    *,
    key: str,
    type: str,
    source_path: str,
    install_path: str,
    repo_root: pathlib.Path,
) -> None:
    """Insert or refresh an artifact entry. Hash is computed from
    ``repo_root/source_path``. Status is forced to "installed"."""
    src = pathlib.Path(repo_root) / source_path
    content_hash = hash_directory(src)
    lockfile.artifacts[key] = Artifact(
        key=key,
        source_path=source_path,
        install_path=install_path,
        content_hash=content_hash,
        type=type,
        status="installed",
    )
    _telemetry.emit(
        "install",
        artifact=key,
        metadata={"type": type, "install_path": install_path},
    )


def upsert_external(
    lockfile: Lockfile,
    *,
    key: str,
    submodule_path: str,
    repo_root: pathlib.Path,
) -> None:
    """Read submodule HEAD via git, compute content hash, record entry."""
    sub = pathlib.Path(repo_root) / submodule_path
    sha = ""
    try:
        sha = subprocess.run(
            ["git", "-C", str(sub), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        sha = ""
    content_hash = hash_directory(sub)
    lockfile.externals[key] = External(
        key=key,
        submodule_path=submodule_path,
        submodule_sha=sha,
        content_hash=content_hash,
        status="installed",
    )


def remove_artifact(lockfile: Lockfile, key: str) -> None:
    """Drop an artifact entry. No-op if absent."""
    existed = key in lockfile.artifacts
    lockfile.artifacts.pop(key, None)
    if existed:
        _telemetry.emit("uninstall", artifact=key)


def remove_external(lockfile: Lockfile, key: str) -> None:
    existed = key in lockfile.externals
    lockfile.externals.pop(key, None)
    if existed:
        _telemetry.emit("uninstall", artifact=key, metadata={"kind": "external"})


def _git_head(repo_root: pathlib.Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""


def _latest_stable_tag(repo_root: pathlib.Path) -> str:
    """Latest tag in the form ``vYYYY.MM.N`` (no -pre suffix). Empty if none."""
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "tag", "--list", "v*"],
            check=True, capture_output=True, text=True,
        ).stdout.strip().splitlines()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""
    stable = [t for t in out if "-" not in t]
    if not stable:
        return ""
    # Best-effort sort by version components.
    def _key(t: str):
        parts = t.lstrip("v").split(".")
        try:
            return tuple(int(p) for p in parts)
        except ValueError:
            return (0,)
    stable.sort(key=_key)
    return stable[-1]


def stamp_metadata(lockfile: Lockfile, repo_root: pathlib.Path) -> None:
    """Refresh top-level metadata (repo, sha, tag, time, machine)."""
    lockfile.synapse_repo = str(pathlib.Path(repo_root).resolve())
    lockfile.synapse_sha = _git_head(repo_root)
    lockfile.synapse_tag = _latest_stable_tag(repo_root)
    lockfile.installed_at = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    lockfile.machine_id = socket.gethostname() or "unknown"
