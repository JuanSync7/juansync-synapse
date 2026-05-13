"""Detect upstream submodule tag changes.

Pure-ish logic: shells out to `git` for ls-remote / submodule status,
parses the result. No filesystem mutation. No network access except via
git subprocess (test patches the runner).

Stable tag definition (matches synapse-wide convention from
`pins_resolver._semver_key`): `vX.Y.Z` with no `-` suffix.
"""
from __future__ import annotations

import configparser
import pathlib
import re
import subprocess
from dataclasses import dataclass

_TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
# ls-remote output: "<sha>\trefs/tags/<tagname>" possibly suffixed with "^{}"
_LS_REMOTE_RE = re.compile(
    r"^(?P<sha>[0-9a-f]{40})\s+refs/tags/(?P<tag>[^\s\^]+)(?P<deref>\^\{\})?\s*$"
)


@dataclass(frozen=True)
class UpstreamTag:
    tag: str
    sha: str


# ---------------------------------------------------------------------------
# .gitmodules parsing
# ---------------------------------------------------------------------------

def parse_gitmodules(repo_root: pathlib.Path) -> dict[str, str]:
    """Return {submodule_path: url}. Empty dict if .gitmodules missing.

    Only entries whose `path` lives under `external/` are considered, since
    clerk only manages externally-owned suites.
    """
    gm = pathlib.Path(repo_root) / ".gitmodules"
    if not gm.exists():
        return {}

    # .gitmodules is INI-shaped: [submodule "name"]\n  path = ...\n  url = ...
    parser = configparser.ConfigParser()
    # Section names contain quotes; configparser handles that fine.
    text = gm.read_text()
    parser.read_string(text)

    out: dict[str, str] = {}
    for section in parser.sections():
        if not section.startswith("submodule "):
            continue
        path = parser.get(section, "path", fallback=None)
        url = parser.get(section, "url", fallback=None)
        if not path or not url:
            continue
        if not path.startswith("external/"):
            continue
        out[path] = url
    return out


# ---------------------------------------------------------------------------
# Upstream tag listing
# ---------------------------------------------------------------------------

def _semver_key(tag: str) -> tuple[int, int, int]:
    m = _TAG_RE.match(tag)
    if not m:
        return (-1, -1, -1)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def list_upstream_stable_tags(
    submodule_url: str,
    *,
    env: dict | None = None,
    timeout: int = 30,
    runner=subprocess.run,
) -> list[UpstreamTag]:
    """`git ls-remote --tags <url>` → stable tags only, semver-sorted descending.

    Annotated tags appear twice in ls-remote output: once for the tag object
    and once for the commit it points to (suffixed with `^{}`). When both are
    present we prefer the dereferenced (commit) SHA, which is what we'd pin to.

    Raises RuntimeError on git failure (e.g., network down, bad URL).
    """
    try:
        proc = runner(
            ["git", "ls-remote", "--tags", submodule_url],
            check=True, capture_output=True, text=True,
            env=env, timeout=timeout,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"git ls-remote failed for {submodule_url!r}: "
            f"exit={e.returncode} stderr={(e.stderr or '').strip()}"
        ) from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(
            f"git ls-remote timed out after {timeout}s for {submodule_url!r}"
        ) from e
    except FileNotFoundError as e:
        raise RuntimeError("git executable not found on PATH") from e

    # Build tag → sha, preferring dereferenced.
    plain: dict[str, str] = {}
    deref: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        m = _LS_REMOTE_RE.match(line)
        if not m:
            continue
        tag = m.group("tag")
        sha = m.group("sha")
        if not _TAG_RE.match(tag):
            continue   # pre-release / non-stable
        if m.group("deref"):
            deref[tag] = sha
        else:
            plain.setdefault(tag, sha)

    merged: dict[str, str] = {}
    for tag in plain.keys() | deref.keys():
        merged[tag] = deref.get(tag, plain[tag])

    tags = [UpstreamTag(tag=t, sha=s) for t, s in merged.items()]
    tags.sort(key=lambda u: _semver_key(u.tag), reverse=True)
    return tags


def latest_stable_upstream(submodule_url: str, **kw) -> UpstreamTag | None:
    tags = list_upstream_stable_tags(submodule_url, **kw)
    return tags[0] if tags else None


# ---------------------------------------------------------------------------
# Local submodule SHA
# ---------------------------------------------------------------------------

def current_submodule_sha(
    repo_root: pathlib.Path,
    submodule_path: str,
    *,
    runner=subprocess.run,
) -> str:
    """Read the submodule's recorded SHA via `git submodule status -- <path>`.

    Output format (per gitmodules(7)):
        " <sha> <path> (<describe>)"     # initialized & up-to-date
        "+<sha> <path> ..."              # checked-out commit differs from index
        "-<sha> <path>"                  # not initialized
        "U<sha> <path>"                  # merge conflict

    We only need the SHA; ignore the leading status character. Returns "" if
    git fails or the submodule isn't present.
    """
    try:
        proc = runner(
            ["git", "-C", str(repo_root), "submodule", "status", "--", submodule_path],
            check=True, capture_output=True, text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""
    line = proc.stdout.strip()
    if not line:
        return ""
    # Strip leading status char if present.
    body = line[1:] if line[0] in " +-U" else line
    parts = body.strip().split()
    if not parts:
        return ""
    sha = parts[0]
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        return ""
    return sha


# ---------------------------------------------------------------------------
# Force-push detection
# ---------------------------------------------------------------------------

def detect_force_push(
    state,                             # ClerkState (avoid cycle: duck-typed)
    submodule_path: str,
    tag: str,
    upstream_sha: str,
) -> bool:
    """True iff state has a previously-recorded SHA for (submodule, tag) that
    differs from `upstream_sha`. New tags (no record) are not force-pushes.
    """
    by_tag = state.seen_tags.get(submodule_path, {})
    prev = by_tag.get(tag)
    if prev is None:
        return False
    return prev.sha != upstream_sha
