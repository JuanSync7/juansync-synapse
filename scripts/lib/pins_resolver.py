"""Resolve pin specs (`tag`, `"latest"`, `"main"`, `"sha:HEX"`) to concrete SHAs.

Stdlib only. Shells out to `git` for tag and SHA resolution.

Pin grammar:
- `latest`            — floating; resolves to highest stable semver tag.
- `main`              — floating; resolves to current `origin/main` HEAD
                        (falls back to local `main` if no remote).
- `vX.Y.Z[-pre.N]`    — exact tag.
- `sha:HEX`           — exact commit; HEX is 7+ hex chars.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
from dataclasses import dataclass

_TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)(?:-pre\.(\d+))?$")
_SHA_RE = re.compile(r"^sha:([0-9a-fA-F]{7,40})$")


@dataclass
class Resolution:
    pin: str
    kind: str           # "tag" | "latest" | "main" | "sha"
    resolved_sha: str   # 40-char SHA
    resolved_tag: str   # tag name if pin was tag or "latest"; else ""


def _git(args: list[str], repo: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True, capture_output=True, text=True,
    )


def validate_pin_value(pin: str) -> tuple[bool, str]:
    """Returns (ok, reason). Validates grammar only — does not check existence."""
    if not isinstance(pin, str) or not pin:
        return False, "pin must be a non-empty string"
    if pin == "latest":
        return True, ""
    if pin == "main":
        return True, ""
    if _TAG_RE.match(pin):
        return True, ""
    if _SHA_RE.match(pin):
        return True, ""
    return False, (
        f"invalid pin {pin!r} — expected 'latest', 'main', "
        f"'vX.Y.Z[-pre.N]', or 'sha:HEX' (7+ hex chars)"
    )


def _semver_key(tag: str) -> tuple[int, int, int]:
    m = _TAG_RE.match(tag)
    if not m or m.group(4) is not None:
        return (-1, -1, -1)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def latest_stable_tag(repo_root: pathlib.Path) -> str:
    """Highest semver tag without -pre suffix, or '' if none exist."""
    try:
        out = _git(["tag", "-l", "v*"], repo_root).stdout
    except subprocess.CalledProcessError:
        return ""
    tags = [t.strip() for t in out.splitlines() if t.strip()]
    stable = [t for t in tags if _TAG_RE.match(t) and "-" not in t]
    if not stable:
        return ""
    stable.sort(key=_semver_key)
    return stable[-1]


def _rev_parse(repo_root: pathlib.Path, ref: str) -> str:
    try:
        out = _git(["rev-parse", "--verify", ref + "^{commit}"], repo_root).stdout
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        raise ValueError(f"could not resolve ref {ref!r}: {stderr}") from e
    sha = out.strip()
    if len(sha) != 40:
        raise ValueError(f"unexpected rev-parse output for {ref!r}: {sha!r}")
    return sha


def resolve_pin(pin: str, repo_root: pathlib.Path) -> Resolution:
    """Resolve a pin spec to a concrete SHA. Raises ValueError on bad input."""
    ok, reason = validate_pin_value(pin)
    if not ok:
        raise ValueError(reason)

    if pin == "latest":
        tag = latest_stable_tag(repo_root)
        if not tag:
            raise ValueError(
                "pin 'latest' could not be resolved: no stable semver tags found in repo"
            )
        sha = _rev_parse(repo_root, tag)
        return Resolution(pin=pin, kind="latest", resolved_sha=sha, resolved_tag=tag)

    if pin == "main":
        # Try origin/main first, fall back to local main.
        for ref in ("origin/main", "main"):
            try:
                sha = _rev_parse(repo_root, ref)
                return Resolution(pin=pin, kind="main", resolved_sha=sha, resolved_tag="")
            except ValueError:
                continue
        raise ValueError(
            "pin 'main' could not be resolved: neither origin/main nor main exist"
        )

    m = _SHA_RE.match(pin)
    if m:
        hex_part = m.group(1)
        sha = _rev_parse(repo_root, hex_part)
        return Resolution(pin=pin, kind="sha", resolved_sha=sha, resolved_tag="")

    # Tag form (validated above)
    sha = _rev_parse(repo_root, pin)
    return Resolution(pin=pin, kind="tag", resolved_sha=sha, resolved_tag=pin)
