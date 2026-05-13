"""Deterministic content hashing for artifact directories.

The hash is independent of install state, machine, or filesystem ordering.
It deliberately ignores files that change without representing a real
artifact-content change (e.g. EVAL.md is regenerated; change_requests/ are
working notes).

Algorithm:
1. Walk all files under `path` recursively.
2. Drop any file whose relative path matches the exclusion rules.
3. Sort the surviving (POSIX) relative paths lexicographically.
4. For each file emit `f"{relpath}\\0{sha256_of_contents_hex}\\n"` into a
   running sha256.
5. Return `"sha256:" + hex_digest`.
"""
from __future__ import annotations

import fnmatch
import hashlib
import pathlib

# Filenames anywhere in the tree that must be excluded.
_EXCLUDE_BASENAMES: frozenset[str] = frozenset({"EVAL.md", ".DS_Store"})

# Glob patterns matched against the basename.
_EXCLUDE_GLOBS: tuple[str, ...] = ("*.swp", "*.pyc")

# Top-level relative path components whose entire subtree is excluded.
_EXCLUDE_DIR_NAMES: frozenset[str] = frozenset({"change_requests", "__pycache__"})


def _should_skip(rel_parts: tuple[str, ...]) -> bool:
    if not rel_parts:
        return True
    # Any directory component matching an excluded dir name skips the file.
    for part in rel_parts[:-1]:
        if part in _EXCLUDE_DIR_NAMES:
            return True
    name = rel_parts[-1]
    if name in _EXCLUDE_BASENAMES:
        return True
    for pat in _EXCLUDE_GLOBS:
        if fnmatch.fnmatch(name, pat):
            return True
    return False


def hash_directory(
    path: pathlib.Path, exclude: set[str] | None = None
) -> str:
    """Hash the content of `path` recursively.

    `exclude` is an optional set of additional basenames to skip on top of the
    default exclusions.
    """
    root = pathlib.Path(path)
    extra = set(exclude or ())

    survivors: list[tuple[str, pathlib.Path]] = []
    if root.is_dir():
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(root)
            parts = rel.parts
            if _should_skip(parts):
                continue
            if parts[-1] in extra:
                continue
            posix = rel.as_posix()
            survivors.append((posix, p))

    survivors.sort(key=lambda t: t[0])

    outer = hashlib.sha256()
    for rel, full in survivors:
        inner = hashlib.sha256()
        with open(full, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                inner.update(chunk)
        outer.update(rel.encode("utf-8"))
        outer.update(b"\x00")
        outer.update(inner.hexdigest().encode("ascii"))
        outer.update(b"\n")
    return "sha256:" + outer.hexdigest()


def file_hashes(
    path: pathlib.Path, exclude: set[str] | None = None
) -> dict[str, str]:
    """Return {posix_relpath: sha256_hex} for every non-excluded file.

    Exclusion logic mirrors `hash_directory`. The hex digests are bare hex
    (no `sha256:` prefix), so callers can compare individual files without
    re-hashing the entire tree.
    """
    root = pathlib.Path(path)
    extra = set(exclude or ())
    out: dict[str, str] = {}
    if not root.is_dir():
        return out
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        parts = rel.parts
        if _should_skip(parts):
            continue
        if parts[-1] in extra:
            continue
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        out[rel.as_posix()] = h.hexdigest()
    return out
