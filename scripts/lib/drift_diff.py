"""Compute per-file diffs between an artifact source tree and a git ref.

Used by `cortex drift show` and `cortex drift adopt`. Walks the working-tree
source path and the same path inside `git show <sha>:<path>`; for each file
present in either, classifies as modified/added/removed and produces a
unified text diff (or marks binary).

Exclusion rules mirror `hashing.py` so the diff matches what `hash_directory`
sees — drift detected by doctor maps directly to a file diff here.

Stdlib only.
"""
from __future__ import annotations

import difflib
import pathlib
import subprocess
import sys
from dataclasses import dataclass
from typing import Literal

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import hashing  # noqa: E402


@dataclass
class FileDiff:
    relpath: str
    status: Literal["modified", "added", "removed"]
    diff_text: str | None
    binary: bool


def _looks_binary(data: bytes) -> bool:
    """Null byte in the first 8KB → treat as binary."""
    return b"\x00" in data[:8192]


def _git_ls_tree(repo_root: pathlib.Path, git_sha: str, source_rel: str) -> set[str]:
    """List blob paths under source_rel at <git_sha>, posix-relative to source_rel.

    Returns paths surviving the same exclusion rules as hashing.py.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "ls-tree", "-r", "--name-only",
             git_sha, "--", source_rel],
            check=True, capture_output=True, text=True,
        ).stdout
    except subprocess.CalledProcessError:
        return set()
    survivors: set[str] = set()
    prefix = source_rel.rstrip("/") + "/"
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if line == source_rel or not line.startswith(prefix):
            # Single-file source_rel: the entry IS source_rel itself.
            if line == source_rel:
                survivors.add(pathlib.Path(line).name)
            continue
        rel = line[len(prefix):]
        parts = tuple(rel.split("/"))
        if hashing._should_skip(parts):
            continue
        survivors.add(rel)
    return survivors


def _git_blob(repo_root: pathlib.Path, git_sha: str, path: str) -> bytes | None:
    """Read file bytes at <git_sha>:<path>. None if missing."""
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "show", f"{git_sha}:{path}"],
            check=True, capture_output=True,
        )
    except subprocess.CalledProcessError:
        return None
    return out.stdout


def diff_artifact_against_git(
    source_path: pathlib.Path,
    repo_root: pathlib.Path,
    git_sha: str = "HEAD",
) -> list[FileDiff]:
    """Compare working-tree source_path against the same path at <git_sha>.

    Returns one FileDiff per changed file (sorted by relpath).
    """
    repo_root = pathlib.Path(repo_root).resolve()
    source_path = pathlib.Path(source_path).resolve()
    try:
        source_rel = source_path.relative_to(repo_root).as_posix()
    except ValueError:
        raise ValueError(
            f"source_path {source_path} is not inside repo_root {repo_root}"
        )

    working = hashing.file_hashes(source_path)
    git_paths = _git_ls_tree(repo_root, git_sha, source_rel)

    out: list[FileDiff] = []
    all_paths = set(working.keys()) | git_paths
    for rel in sorted(all_paths):
        full_local = source_path / rel
        full_git_path = f"{source_rel}/{rel}" if rel else source_rel

        local_bytes: bytes | None = None
        if rel in working:
            local_bytes = full_local.read_bytes()
        git_bytes = _git_blob(repo_root, git_sha, full_git_path) if rel in git_paths else None

        if local_bytes is not None and git_bytes is None:
            status: Literal["modified", "added", "removed"] = "added"
        elif local_bytes is None and git_bytes is not None:
            status = "removed"
        elif local_bytes == git_bytes:
            continue  # identical — skip
        else:
            status = "modified"

        binary = (
            (local_bytes is not None and _looks_binary(local_bytes))
            or (git_bytes is not None and _looks_binary(git_bytes))
        )
        if binary:
            out.append(FileDiff(relpath=rel, status=status, diff_text=None, binary=True))
            continue

        a_lines = (git_bytes.decode("utf-8", errors="replace").splitlines(keepends=True)
                   if git_bytes is not None else [])
        b_lines = (local_bytes.decode("utf-8", errors="replace").splitlines(keepends=True)
                   if local_bytes is not None else [])
        diff = "".join(difflib.unified_diff(
            a_lines, b_lines,
            fromfile=f"a/{rel}", tofile=f"b/{rel}",
            n=3,
        ))
        out.append(FileDiff(relpath=rel, status=status, diff_text=diff, binary=False))

    return out
