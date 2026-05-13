"""Drift resolution primitives: resolve, stash, restore, list, adopt, ignore.

Pure-Python helpers used by `drift_cli.py`. Each helper takes already-loaded
state (lockfile, repo_root) so tests can inject fixtures without touching the
filesystem outside `tmp_path`.

Stdlib only.
"""
from __future__ import annotations

import datetime
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import drift_diff as dd_mod  # noqa: E402
import hashing  # noqa: E402
import lockfile as lf_mod  # noqa: E402
import pins as pins_mod  # noqa: E402


# ---------------------------------------------------------------------------
# stash root resolution
# ---------------------------------------------------------------------------

def _stash_root() -> pathlib.Path:
    """Always under ~/.synapse/stash/ — stashes are user-machine local even when
    the project is project-scoped."""
    root = pathlib.Path(os.path.expanduser("~")) / ".synapse" / "stash"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _utc_timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def _today_iso() -> str:
    return datetime.date.today().isoformat()


_SLUG_NON_ALNUM = re.compile(r"[^a-z0-9-]+")


def _kebab(s: str) -> str:
    s = s.strip().lower().replace(" ", "-")
    s = _SLUG_NON_ALNUM.sub("-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "anon"


def _sanitize_key_for_path(key: str) -> str:
    return key.replace("/", "__")


# ---------------------------------------------------------------------------
# resolve_key
# ---------------------------------------------------------------------------

def resolve_key(raw: str, lockfile: lf_mod.Lockfile) -> str:
    """Accept 'skill/foo' or 'foo'. Returns canonical 'type/name' key.

    - If raw matches an existing lockfile key exactly → return it.
    - Else interpret as bare name and look up across all artifact types.
      If exactly one match → return its key. If 0 → raise. If >1 → raise
      with the candidate list.
    """
    if raw in lockfile.artifacts:
        return raw
    if "/" in raw:
        raise ValueError(f"no such artifact in lockfile: {raw!r}")
    matches = [k for k in lockfile.artifacts if k.split("/", 1)[1] == raw]
    if not matches:
        raise ValueError(f"no such artifact in lockfile: {raw!r}")
    if len(matches) > 1:
        raise ValueError(
            f"ambiguous name {raw!r}: matches {', '.join(sorted(matches))}"
        )
    return matches[0]


# ---------------------------------------------------------------------------
# stash / restore / list
# ---------------------------------------------------------------------------

def _toml_quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _write_stash_meta(meta_path: pathlib.Path, meta: dict) -> None:
    lines: list[str] = []
    for k in ("artifact", "source_path", "stashed_at", "reason",
              "expected_hash", "actual_hash"):
        if k in meta:
            lines.append(f"{k} = {_toml_quote(str(meta[k]))}")
    meta_path.write_text("\n".join(lines) + "\n")


def stash_artifact(
    key: str,
    lockfile: lf_mod.Lockfile,
    repo_root: pathlib.Path,
    reason: str = "",
) -> pathlib.Path:
    """Copy current source_path tree to ~/.synapse/stash/<ts>-<key>/, then
    `git checkout -- <source_path>` to restore canonical state.

    Returns the stash directory path.
    """
    repo_root = pathlib.Path(repo_root).resolve()
    if key not in lockfile.artifacts:
        raise ValueError(f"key not in lockfile: {key!r}")
    art = lockfile.artifacts[key]
    src = repo_root / art.source_path
    if not src.exists():
        raise ValueError(f"source_path does not exist: {src}")

    ts = _utc_timestamp()
    stash_dir = _stash_root() / f"{ts}-{_sanitize_key_for_path(key)}"
    if stash_dir.exists():
        # extremely unlikely collision; suffix with PID
        stash_dir = stash_dir.with_name(stash_dir.name + f"-{os.getpid()}")
    stash_dir.mkdir(parents=True)

    # Copy source tree into stash_dir/payload/
    payload = stash_dir / "payload"
    shutil.copytree(src, payload, symlinks=True)

    actual_hash = hashing.hash_directory(src)
    _write_stash_meta(stash_dir / "STASH_META.toml", {
        "artifact": key,
        "source_path": art.source_path,
        "stashed_at": ts,
        "reason": reason,
        "expected_hash": art.content_hash,
        "actual_hash": actual_hash,
    })

    # Restore canonical via git checkout. If files were added, also remove them.
    subprocess.run(
        ["git", "-C", str(repo_root), "checkout", "--", art.source_path],
        check=True, capture_output=True,
    )
    # Remove any files that were added (untracked) under source_path so the
    # tree matches HEAD exactly.
    subprocess.run(
        ["git", "-C", str(repo_root), "clean", "-fd", "--", art.source_path],
        check=True, capture_output=True,
    )
    return stash_dir


def list_stashes() -> list[dict]:
    """List all stashes under ~/.synapse/stash/ with metadata."""
    root = _stash_root()
    out: list[dict] = []
    for d in sorted(root.iterdir() if root.is_dir() else []):
        if not d.is_dir():
            continue
        meta_path = d / "STASH_META.toml"
        meta: dict = {"stash_id": d.name, "path": str(d)}
        if meta_path.exists():
            try:
                raw = tomllib.loads(meta_path.read_text())
                meta.update({
                    "artifact": raw.get("artifact", ""),
                    "source_path": raw.get("source_path", ""),
                    "stashed_at": raw.get("stashed_at", ""),
                    "reason": raw.get("reason", ""),
                    "expected_hash": raw.get("expected_hash", ""),
                    "actual_hash": raw.get("actual_hash", ""),
                })
            except Exception as e:
                meta["meta_error"] = str(e)
        out.append(meta)
    return out


def restore_stash(stash_id: str, repo_root: pathlib.Path, *, force: bool = False) -> None:
    """Restore a stash payload back over its source_path.

    `force=True` skips the confirmation prompt. `force=False` requires a TTY
    and prints a y/N prompt — non-TTY → raises RuntimeError.
    """
    # Resolve stash dir
    sp = pathlib.Path(stash_id)
    if not sp.is_absolute():
        sp = _stash_root() / stash_id
    if not sp.is_dir():
        raise ValueError(f"no such stash: {stash_id}")

    meta_path = sp / "STASH_META.toml"
    if not meta_path.exists():
        raise ValueError(f"missing STASH_META.toml in {sp}")
    meta = tomllib.loads(meta_path.read_text())
    source_rel = meta.get("source_path", "")
    if not source_rel:
        raise ValueError("stash meta missing source_path")
    repo_root = pathlib.Path(repo_root).resolve()
    target = repo_root / source_rel

    if not force:
        if not sys.stdin.isatty():
            raise RuntimeError(
                "restore requires --yes when stdin is not a TTY"
            )
        sys.stdout.write(
            f"Restore stash {sp.name} over {target}? "
            "This will overwrite current state. [y/N] "
        )
        sys.stdout.flush()
        ans = sys.stdin.readline().strip().lower()
        if ans not in ("y", "yes"):
            raise RuntimeError("user declined restore")

    # Wipe target then copy payload back
    payload = sp / "payload"
    if not payload.is_dir():
        raise ValueError(f"missing payload in {sp}")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(payload, target, symlinks=True)


# ---------------------------------------------------------------------------
# adopt
# ---------------------------------------------------------------------------

_DIFF_LINE_CAP = 500


def _truncate_diff(diff: str) -> str:
    lines = diff.splitlines(keepends=True)
    if len(lines) <= _DIFF_LINE_CAP:
        return diff
    head = "".join(lines[:_DIFF_LINE_CAP])
    return head + "... (truncated)\n"


def _git_user_name(repo_root: pathlib.Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "config", "user.name"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return ""
    return out


def adopt_drift(
    key: str,
    lockfile: lf_mod.Lockfile,
    repo_root: pathlib.Path,
    *,
    slug: str = "",
    reason: str = "",
    author_override: str = "",
) -> pathlib.Path:
    """Write a change_request markdown file capturing the drift.

    Does NOT restore source — adopting promotes the local state.
    Returns the path to the CR file.
    """
    repo_root = pathlib.Path(repo_root).resolve()
    if key not in lockfile.artifacts:
        raise ValueError(f"key not in lockfile: {key!r}")
    art = lockfile.artifacts[key]
    src = repo_root / art.source_path
    if not src.exists():
        raise ValueError(f"source_path does not exist: {src}")

    actual_hash = hashing.hash_directory(src)
    git_sha = lockfile.synapse_sha or "HEAD"
    diffs = dd_mod.diff_artifact_against_git(src, repo_root, git_sha=git_sha)

    today = _today_iso()
    author = _kebab(author_override or _git_user_name(repo_root) or "anon")
    if slug:
        slug_kebab = _kebab(slug)
    else:
        # actual_hash is "sha256:<hex>" — take 7 chars from hex part
        hex_part = actual_hash.split(":", 1)[-1]
        slug_kebab = f"local-drift-{hex_part[:7]}"

    cr_dir = src / "change_requests"
    cr_dir.mkdir(parents=True, exist_ok=True)
    cr_path = cr_dir / f"{today}-{author}-{slug_kebab}.md"

    body_reason = reason if reason else "Drift adopted from local edit."

    lines: list[str] = []
    lines.append("---")
    lines.append(f"title: {slug_kebab}")
    lines.append(f"author: {author}")
    lines.append(f"date: {today}")
    lines.append(f"artifact: {key}")
    lines.append("status: draft")
    lines.append(f"synapse_sha: {git_sha}")
    lines.append(f"expected_hash: {art.content_hash}")
    lines.append(f"actual_hash: {actual_hash}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {slug_kebab}")
    lines.append("")
    lines.append(body_reason)
    lines.append("")
    lines.append("## Diff")
    lines.append("")

    if not diffs:
        lines.append("_No file-level diffs against the lockfile sha._")
        lines.append("")
    else:
        for fd in diffs:
            lines.append(f"### {fd.relpath}  ({fd.status})")
            lines.append("")
            if fd.binary:
                lines.append("_binary differs_")
                lines.append("")
                continue
            lines.append("```diff")
            lines.append(_truncate_diff(fd.diff_text or "").rstrip("\n"))
            lines.append("```")
            lines.append("")

    cr_path.write_text("\n".join(lines))
    return cr_path


# ---------------------------------------------------------------------------
# ignore
# ---------------------------------------------------------------------------

@dataclass
class IgnoreResult:
    pins_path: pathlib.Path
    expires_warning: bool
    actual_hash: str


def ignore_drift(
    key: str,
    lockfile: lf_mod.Lockfile,
    repo_root: pathlib.Path,
    pins_path: pathlib.Path,
    *,
    reason: str = "",
    expires: str = "",
) -> IgnoreResult:
    """Add a `[drift_exceptions]` entry to pins.toml. Returns result with a
    flag if no expires was set (caller should print a warning)."""
    repo_root = pathlib.Path(repo_root).resolve()
    if key not in lockfile.artifacts:
        raise ValueError(f"key not in lockfile: {key!r}")
    art = lockfile.artifacts[key]
    src = repo_root / art.source_path
    if not src.exists():
        raise ValueError(f"source_path does not exist: {src}")

    if expires:
        # Validate YYYY-MM-DD parse
        try:
            datetime.date.fromisoformat(expires)
        except ValueError as e:
            raise ValueError(f"invalid --expires {expires!r}: {e}") from e

    actual_hash = hashing.hash_directory(src)
    pins = pins_mod.load(pins_path)
    pins.drift_exceptions[key] = pins_mod.DriftException(
        artifact_key=key,
        hash=actual_hash,
        reason=reason,
        expires=expires,
    )
    pins_mod.save(pins, pins_path)
    return IgnoreResult(
        pins_path=pins_path,
        expires_warning=(expires == ""),
        actual_hash=actual_hash,
    )
