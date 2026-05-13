"""Scanners that produce `doctor_findings.Finding` lists.

One scanner per category. `scan_all` orchestrates them, tolerating a missing
lockfile by emitting a single `corrupt` finding and bailing.

Stdlib only. Network access only attempted in `scan_submodule_stale`, which
degrades gracefully on failure (single info finding, never raises).
"""
from __future__ import annotations

import datetime
import os
import pathlib
import re
import subprocess
import sys
from typing import Iterable

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import doctor_findings as df  # noqa: E402
import hashing  # noqa: E402
import lockfile as lf_mod  # noqa: E402
import pins as pins_mod  # noqa: E402
import pins_resolver as resolver  # noqa: E402
import telemetry as _telemetry  # noqa: E402

_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

# Default install paths to scan for orphaned (a) findings.
_DEFAULT_INSTALL_ROOTS = (
    "~/.claude/skills",
    "~/.claude/agents",
    "~/.codex/skills",
    "~/.gemini/extensions/ai-synapse/skills",
)


def _expand(p: str) -> pathlib.Path:
    return pathlib.Path(os.path.expanduser(p))


# ---------------------------------------------------------------------------
# drift
# ---------------------------------------------------------------------------

def scan_drift(
    lockfile: lf_mod.Lockfile,
    repo_root: pathlib.Path,
    pins: pins_mod.Pins | None = None,
) -> list[df.Finding]:
    """Compare recomputed source-path hash to lockfile content_hash.

    If `pins` is provided and contains a non-expired `[drift_exceptions]`
    entry whose hash matches the current actual hash, the artifact is
    skipped (drift acknowledged). Expired exceptions are ignored — drift
    re-fires normally.
    """
    out: list[df.Finding] = []
    repo_root = pathlib.Path(repo_root)
    today = datetime.date.today().isoformat()
    exceptions = pins.drift_exceptions if pins is not None else {}
    for key, art in lockfile.artifacts.items():
        src = repo_root / art.source_path
        if not src.exists():
            # Source gone — that's `orphaned`, not drift.
            continue
        actual = hashing.hash_directory(src)
        if actual != art.content_hash:
            ex = exceptions.get(key)
            if ex is not None and ex.hash == actual:
                # Expired? expires == "" means never expires.
                if not ex.expires or ex.expires >= today:
                    continue
            out.append(df.Finding(
                category="drift",
                severity="warn",
                artifact=key,
                message=f"hash mismatch (expected {art.content_hash[:19]}..., got {actual[:19]}...)",
                details={
                    "expected": art.content_hash,
                    "actual": actual,
                    "source_path": str(src),
                    "install_path": art.install_path,
                },
            ))
            _telemetry.emit(
                "drift_detected",
                artifact=key,
                metadata={"expected": art.content_hash, "actual": actual},
            )
    return out


# ---------------------------------------------------------------------------
# stale
# ---------------------------------------------------------------------------

def scan_stale(
    lockfile: lf_mod.Lockfile,
    pins: pins_mod.Pins,
    repo_root: pathlib.Path,
) -> list[df.Finding]:
    """If pin is floating (latest/main), see if its resolved SHA has moved past
    the lockfile's synapse_sha."""
    if pins is None or pins.pin not in ("latest", "main"):
        return []
    try:
        res = resolver.resolve_pin(pins.pin, repo_root)
    except (ValueError, subprocess.CalledProcessError):
        return []
    if not lockfile.synapse_sha:
        return []
    if res.resolved_sha == lockfile.synapse_sha:
        return []
    return [df.Finding(
        category="stale",
        severity="warn",
        artifact="",
        message=(
            f"pin '{pins.pin}' resolves to {res.resolved_sha[:12]}..., "
            f"lockfile is at {lockfile.synapse_sha[:12]}..."
        ),
        details={
            "pin": pins.pin,
            "resolved_sha": res.resolved_sha,
            "lockfile_sha": lockfile.synapse_sha,
        },
    )]


# ---------------------------------------------------------------------------
# missing
# ---------------------------------------------------------------------------

def scan_missing(lockfile: lf_mod.Lockfile, repo_root: pathlib.Path) -> list[df.Finding]:
    """install_path doesn't exist or is a broken symlink."""
    out: list[df.Finding] = []
    for key, art in lockfile.artifacts.items():
        ip = _expand(art.install_path)
        # Path.exists() returns False for broken symlinks, which is what we want.
        if ip.is_symlink() and not ip.exists():
            out.append(df.Finding(
                category="missing",
                severity="error",
                artifact=key,
                message=f"install_path {ip} is a broken symlink",
                details={"install_path": str(ip)},
            ))
        elif not ip.exists():
            out.append(df.Finding(
                category="missing",
                severity="error",
                artifact=key,
                message=f"install_path {ip} does not exist",
                details={"install_path": str(ip)},
            ))
    return out


# ---------------------------------------------------------------------------
# orphaned
# ---------------------------------------------------------------------------

def scan_orphaned(
    lockfile: lf_mod.Lockfile,
    repo_root: pathlib.Path,
    install_roots: Iterable[str] = _DEFAULT_INSTALL_ROOTS,
) -> list[df.Finding]:
    """Two flavors:
    (a) symlinks under install_roots pointing into repo with no lockfile entry
    (b) lockfile entry whose source_path no longer exists in the registry
    """
    out: list[df.Finding] = []
    repo_root = pathlib.Path(repo_root).resolve()

    # (b) lockfile artifact, source gone
    for key, art in lockfile.artifacts.items():
        src = repo_root / art.source_path
        if not src.exists():
            out.append(df.Finding(
                category="orphaned",
                severity="warn",
                artifact=key,
                message=f"source_path {art.source_path} no longer exists in registry",
                details={
                    "source_path": art.source_path,
                    "install_path": art.install_path,
                    "kind": "source_gone",
                },
            ))

    # (a) symlinks pointing into repo without a matching lockfile entry
    known_install_paths = {
        str(_expand(a.install_path).resolve(strict=False))
        for a in lockfile.artifacts.values()
    }
    for root in install_roots:
        rp = _expand(root)
        if not rp.is_dir():
            continue
        for entry in rp.iterdir():
            if not entry.is_symlink():
                continue
            try:
                target = pathlib.Path(os.readlink(entry))
            except OSError:
                continue
            if not target.is_absolute():
                target = (entry.parent / target)
            try:
                target_resolved = target.resolve(strict=False)
            except (OSError, RuntimeError):
                continue
            try:
                target_resolved.relative_to(repo_root)
            except ValueError:
                continue  # not into our repo
            entry_resolved = str(entry.resolve(strict=False))
            if entry_resolved in known_install_paths:
                continue
            out.append(df.Finding(
                category="orphaned",
                severity="warn",
                artifact="",
                message=f"symlink {entry} points into repo but has no lockfile entry",
                details={
                    "install_path": str(entry),
                    "target": str(target_resolved),
                    "kind": "untracked_symlink",
                },
            ))

    return out


# ---------------------------------------------------------------------------
# corrupt
# ---------------------------------------------------------------------------

def scan_corrupt(
    lockfile_path: pathlib.Path,
    lockfile_or_none: lf_mod.Lockfile | None,
) -> list[df.Finding]:
    """If the lockfile failed to parse → single error finding. Otherwise
    iterate artifacts/externals and check content_hash format."""
    lockfile_path = pathlib.Path(lockfile_path)
    if lockfile_or_none is None:
        return [df.Finding(
            category="corrupt",
            severity="error",
            artifact="",
            message=f"no lockfile at {lockfile_path}; run cortex install",
            details={"lockfile_path": str(lockfile_path)},
        )]
    out: list[df.Finding] = []
    for key, art in lockfile_or_none.artifacts.items():
        if not _HASH_RE.match(art.content_hash):
            out.append(df.Finding(
                category="corrupt",
                severity="error",
                artifact=key,
                message=f"malformed content_hash {art.content_hash!r}",
                details={"content_hash": art.content_hash},
            ))
    for key, ext in lockfile_or_none.externals.items():
        if not _HASH_RE.match(ext.content_hash):
            out.append(df.Finding(
                category="corrupt",
                severity="error",
                artifact=f"external/{key}",
                message=f"malformed content_hash {ext.content_hash!r}",
                details={"content_hash": ext.content_hash},
            ))
    return out


# ---------------------------------------------------------------------------
# pin-rot
# ---------------------------------------------------------------------------

def _tag_date(repo_root: pathlib.Path, tag: str) -> datetime.datetime | None:
    """Return tagger date (annotated) or commit date (lightweight). None if
    tag missing or unparseable."""
    for fmt in ("%(taggerdate:iso8601-strict)", "%(creatordate:iso8601-strict)"):
        try:
            out = subprocess.run(
                ["git", "-C", str(repo_root), "for-each-ref",
                 "--format=" + fmt, f"refs/tags/{tag}"],
                check=True, capture_output=True, text=True,
            ).stdout.strip()
        except subprocess.CalledProcessError:
            return None
        if not out:
            continue
        try:
            return datetime.datetime.fromisoformat(out)
        except ValueError:
            continue
    return None


def scan_pin_rot(
    pins: pins_mod.Pins,
    repo_root: pathlib.Path,
    threshold_days: int = 90,
) -> list[df.Finding]:
    if pins is None:
        return []
    pin = pins.pin
    if pin in ("latest", "main") or pin.startswith("sha:"):
        return []
    # Tag form
    if not resolver._TAG_RE.match(pin):
        return []
    dt = _tag_date(repo_root, pin)
    if dt is None:
        return []
    now = datetime.datetime.now(dt.tzinfo) if dt.tzinfo else datetime.datetime.now()
    age = now - dt
    if age.days <= threshold_days:
        return []
    return [df.Finding(
        category="pin_rot",
        severity="warn",
        artifact="",
        message=f"pin {pin!r} is {age.days} days old (threshold {threshold_days})",
        details={
            "pin": pin,
            "age_days": age.days,
            "threshold_days": threshold_days,
            "tag_date": dt.isoformat(),
        },
    )]


# ---------------------------------------------------------------------------
# submodule-stale
# ---------------------------------------------------------------------------

def _submodule_upstream_url(repo_root: pathlib.Path, submodule_path: str) -> str:
    """Best-effort look up `git config submodule.<path>.url` in repo."""
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "config", "--file", ".gitmodules",
             "--get", f"submodule.{submodule_path}.url"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        return out
    except subprocess.CalledProcessError:
        return ""


def scan_submodule_stale(
    lockfile: lf_mod.Lockfile,
    repo_root: pathlib.Path,
) -> list[df.Finding]:
    out: list[df.Finding] = []
    if not lockfile.externals:
        return out
    for key, ext in lockfile.externals.items():
        url = _submodule_upstream_url(repo_root, ext.submodule_path) or ext.submodule_path
        try:
            ls = subprocess.run(
                ["git", "ls-remote", "--tags", url],
                check=True, capture_output=True, text=True, timeout=15,
            ).stdout
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
            out.append(df.Finding(
                category="submodule_stale",
                severity="info",
                artifact=f"external/{key}",
                message=f"could not reach upstream for {key}",
                details={"reason": "could not reach upstream", "error": str(e)[:200]},
            ))
            continue
        # Parse ls-remote output: "<sha>\trefs/tags/<tag>[^{}]"
        latest_sha = ""
        latest_tag = ""
        best_key: tuple = (-1, -1, -1)
        for line in ls.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                sha, ref = line.split(maxsplit=1)
            except ValueError:
                continue
            if not ref.startswith("refs/tags/"):
                continue
            tag = ref[len("refs/tags/"):].rstrip("^{}")
            m = resolver._TAG_RE.match(tag)
            if not m or m.group(4) is not None:
                continue
            sk = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
            if sk > best_key:
                best_key = sk
                latest_sha = sha
                latest_tag = tag
        if latest_sha and latest_sha != ext.submodule_sha:
            out.append(df.Finding(
                category="submodule_stale",
                severity="info",
                artifact=f"external/{key}",
                message=f"upstream tag {latest_tag} ahead of pinned {ext.submodule_sha[:12]}...",
                details={
                    "upstream_tag": latest_tag,
                    "upstream_sha": latest_sha,
                    "submodule_sha": ext.submodule_sha,
                },
            ))
    return out


# ---------------------------------------------------------------------------
# scan_all
# ---------------------------------------------------------------------------

def scan_all(
    lockfile_path: pathlib.Path,
    repo_root: pathlib.Path,
    pins: pins_mod.Pins | None = None,
    skip: set[str] | None = None,
    pin_rot_threshold_days: int = 90,
) -> list[df.Finding]:
    """Run all scanners. If lockfile is missing or fails to parse, emit a
    single corrupt finding and stop."""
    skip = skip or set()
    lockfile_path = pathlib.Path(lockfile_path)
    repo_root = pathlib.Path(repo_root)

    # Try to load lockfile
    if not lockfile_path.exists():
        return scan_corrupt(lockfile_path, None)
    try:
        lockfile = lf_mod.load(lockfile_path)
    except Exception as e:
        return [df.Finding(
            category="corrupt",
            severity="error",
            artifact="",
            message=f"failed to parse lockfile: {e}",
            details={"lockfile_path": str(lockfile_path), "error": str(e)},
        )]

    findings: list[df.Finding] = []
    if "corrupt" not in skip:
        findings += scan_corrupt(lockfile_path, lockfile)
    if "drift" not in skip:
        findings += scan_drift(lockfile, repo_root, pins=pins)
    if "missing" not in skip:
        findings += scan_missing(lockfile, repo_root)
    if "orphaned" not in skip:
        findings += scan_orphaned(lockfile, repo_root)
    if "stale" not in skip and pins is not None:
        findings += scan_stale(lockfile, pins, repo_root)
    if "pin_rot" not in skip and pins is not None:
        findings += scan_pin_rot(pins, repo_root, threshold_days=pin_rot_threshold_days)
    if "submodule_stale" not in skip:
        findings += scan_submodule_stale(lockfile, repo_root)
    return findings
