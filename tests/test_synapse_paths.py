"""Tests for scripts/lib/synapse_paths.py — lockfile location resolution."""
from __future__ import annotations

import importlib
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"


@pytest.fixture
def synapse_paths(monkeypatch):
    """Re-import synapse_paths fresh for each test (it has no module state, but be safe)."""
    sys.path.insert(0, str(LIB_DIR))
    if "synapse_paths" in sys.modules:
        del sys.modules["synapse_paths"]
    mod = importlib.import_module("synapse_paths")
    yield mod
    sys.path.remove(str(LIB_DIR))


def test_env_var_wins(synapse_paths, monkeypatch, tmp_path):
    project = tmp_path / "myproj"
    project.mkdir()
    monkeypatch.setenv("SYNAPSE_PROJECT", str(project))
    monkeypatch.chdir(tmp_path)  # cwd elsewhere shouldn't matter
    assert synapse_paths.lockfile_path() == project / ".synapse" / "installed.lock"
    assert synapse_paths.lockfile_dir() == project / ".synapse"
    assert synapse_paths.is_project_scoped() is True


def test_walk_up_finds_project_local_synapse(synapse_paths, monkeypatch, tmp_path):
    monkeypatch.delenv("SYNAPSE_PROJECT", raising=False)
    project = tmp_path / "proj"
    nested = project / "a" / "b" / "c"
    nested.mkdir(parents=True)
    (project / ".synapse").mkdir()
    monkeypatch.chdir(nested)
    assert synapse_paths.lockfile_path() == project / ".synapse" / "installed.lock"
    assert synapse_paths.is_project_scoped() is True


def test_fallback_to_home_synapse(synapse_paths, monkeypatch, tmp_path):
    monkeypatch.delenv("SYNAPSE_PROJECT", raising=False)
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    # cwd has no .synapse/ ancestor
    far = tmp_path / "far"
    far.mkdir()
    monkeypatch.chdir(far)
    p = synapse_paths.lockfile_path()
    assert p == fake_home / ".synapse" / "installed.lock"
    assert (fake_home / ".synapse").is_dir(), "fallback should create ~/.synapse/"
    assert synapse_paths.is_project_scoped() is False
