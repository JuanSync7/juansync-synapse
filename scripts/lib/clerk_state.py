"""Clerk persistent state — `~/.synapse/clerk_state.toml`.

Stdlib only. Tracks which (submodule, tag) → SHA we've previously seen so we
can detect upstream tag force-pushes (T7 force-push abort path), and records
the most recent bump per submodule for telemetry/status display.

Schema:

    schema_version = 1

    [seen_tags."external/some-suite"]
    "v1.4.6" = { sha = "abc...", first_seen = "2026-04-01T12:00:00Z" }
    "v1.4.7" = { sha = "def...", first_seen = "2026-05-06T..." }

    [bumps."external/some-suite"]
    last_bumped_at = "2026-05-06T..."
    last_pr_url    = "https://github.com/.../pull/123"
    last_bumped_to = "v1.4.7"

State is per-machine (one running clerk modifies it); we don't try to merge
concurrent writers. Writes are atomic via os.replace().
"""
from __future__ import annotations

import os
import pathlib
import tomllib
from dataclasses import dataclass, field


@dataclass
class SeenTag:
    sha: str
    first_seen: str   # UTC ISO8601


@dataclass
class BumpRecord:
    last_bumped_at: str
    last_pr_url: str
    last_bumped_to: str


@dataclass
class ClerkState:
    schema_version: int = 1
    # submodule_path -> tag_name -> SeenTag
    seen_tags: dict[str, dict[str, SeenTag]] = field(default_factory=dict)
    bumps: dict[str, BumpRecord] = field(default_factory=dict)


def state_path() -> pathlib.Path:
    """Always `~/.synapse/clerk_state.toml`. Honors $HOME override."""
    return pathlib.Path(os.path.expanduser("~/.synapse/clerk_state.toml"))


def empty() -> ClerkState:
    return ClerkState()


# ---------------------------------------------------------------------------
# TOML serialization (hand-formatted, mirroring lockfile.py style)
# ---------------------------------------------------------------------------

def _quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _inline_table(d: dict) -> str:
    parts = []
    for k in sorted(d.keys()):
        v = d[k]
        parts.append(f"{k} = {_quote(str(v))}")
    return "{ " + ", ".join(parts) + " }"


def _format(state: ClerkState) -> str:
    lines: list[str] = [f"schema_version = {int(state.schema_version)}"]

    if state.seen_tags:
        for sub_path in sorted(state.seen_tags.keys()):
            tags = state.seen_tags[sub_path]
            if not tags:
                continue
            lines.append("")
            lines.append(f"[seen_tags.{_quote(sub_path)}]")
            for tag in sorted(tags.keys()):
                st = tags[tag]
                inline = _inline_table({"sha": st.sha, "first_seen": st.first_seen})
                lines.append(f"{_quote(tag)} = {inline}")

    if state.bumps:
        for sub_path in sorted(state.bumps.keys()):
            br = state.bumps[sub_path]
            lines.append("")
            lines.append(f"[bumps.{_quote(sub_path)}]")
            lines.append(f"last_bumped_at = {_quote(br.last_bumped_at)}")
            lines.append(f"last_pr_url = {_quote(br.last_pr_url)}")
            lines.append(f"last_bumped_to = {_quote(br.last_bumped_to)}")

    return "\n".join(lines) + "\n"


def save(state: ClerkState, path: pathlib.Path) -> None:
    """Atomic write."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    body = _format(state)
    tmp.write_text(body)
    try:
        os.replace(tmp, path)
    except Exception:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        raise


def load(path: pathlib.Path) -> ClerkState:
    """Parse state from disk. Missing file → empty defaults.

    Raises ValueError on malformed TOML or schema mismatch."""
    path = pathlib.Path(path)
    if not path.exists():
        return empty()
    try:
        raw = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"clerk state file is malformed TOML: {path}: {e}") from e

    schema_version = int(raw.get("schema_version", 1))
    if schema_version != 1:
        raise ValueError(
            f"clerk state schema_version={schema_version} not supported; "
            f"expected 1 (path: {path})"
        )

    state = ClerkState(schema_version=schema_version)

    seen = raw.get("seen_tags") or {}
    if not isinstance(seen, dict):
        raise ValueError(f"clerk state seen_tags must be a table, got {type(seen).__name__}")
    for sub_path, tags in seen.items():
        if not isinstance(tags, dict):
            raise ValueError(f"clerk state seen_tags.{sub_path!r} must be a table")
        state.seen_tags[sub_path] = {}
        for tag_name, body in tags.items():
            if not isinstance(body, dict):
                raise ValueError(
                    f"clerk state seen_tags.{sub_path!r}.{tag_name!r} must be a table"
                )
            state.seen_tags[sub_path][tag_name] = SeenTag(
                sha=str(body.get("sha", "")),
                first_seen=str(body.get("first_seen", "")),
            )

    bumps = raw.get("bumps") or {}
    if not isinstance(bumps, dict):
        raise ValueError(f"clerk state bumps must be a table, got {type(bumps).__name__}")
    for sub_path, body in bumps.items():
        if not isinstance(body, dict):
            raise ValueError(f"clerk state bumps.{sub_path!r} must be a table")
        state.bumps[sub_path] = BumpRecord(
            last_bumped_at=str(body.get("last_bumped_at", "")),
            last_pr_url=str(body.get("last_pr_url", "")),
            last_bumped_to=str(body.get("last_bumped_to", "")),
        )

    return state
