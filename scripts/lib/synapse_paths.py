"""Resolve where the synapse `installed.lock` lockfile should live.

Resolution order:
1. `SYNAPSE_PROJECT` env var → `$SYNAPSE_PROJECT/.synapse/installed.lock`.
2. Walk up from cwd looking for a `.synapse/` directory.
3. Fall back to `~/.synapse/installed.lock`, creating `~/.synapse/` if missing.

Pure stdlib. No side effects in cases (1) or (2); case (3) creates `~/.synapse/`.
"""
from __future__ import annotations

import os
import pathlib

LOCKFILE_NAME = "installed.lock"
SYNAPSE_DIR_NAME = ".synapse"


def _resolve() -> tuple[pathlib.Path, bool]:
    """Return (synapse_dir, is_project_scoped)."""
    env = os.environ.get("SYNAPSE_PROJECT")
    if env:
        return pathlib.Path(env).expanduser().resolve() / SYNAPSE_DIR_NAME, True

    cwd = pathlib.Path(os.getcwd()).resolve()
    for candidate in [cwd, *cwd.parents]:
        synapse_dir = candidate / SYNAPSE_DIR_NAME
        if synapse_dir.is_dir():
            return synapse_dir, True

    # Fallback: ~/.synapse/
    home = pathlib.Path(os.path.expanduser("~")).resolve()
    fallback = home / SYNAPSE_DIR_NAME
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback, False


def lockfile_dir() -> pathlib.Path:
    """The `.synapse/` directory containing the lockfile."""
    return _resolve()[0]


def lockfile_path() -> pathlib.Path:
    """Absolute path to `installed.lock`."""
    return lockfile_dir() / LOCKFILE_NAME


def is_project_scoped() -> bool:
    """True if the lockfile is project-local (env or walked-up `.synapse/`)."""
    return _resolve()[1]
