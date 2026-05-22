"""Tests for scripts/lib/drift_resolve.py."""
from __future__ import annotations

import importlib
import os
import pathlib
import subprocess
import sys
import tomllib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"


@pytest.fixture
def lib(monkeypatch, tmp_path):
    # Redirect HOME so ~/.synapse/stash/ lives in tmp_path for these tests
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    sys.path.insert(0, str(LIB_DIR))
    for n in ("hashing", "lockfile", "pins", "drift_diff", "drift_resolve"):
        if n in sys.modules:
            del sys.modules[n]
    mods = {
        "drift_resolve": importlib.import_module("drift_resolve"),
        "lockfile": importlib.import_module("lockfile"),
        "hashing": importlib.import_module("hashing"),
        "pins": importlib.import_module("pins"),
    }
    yield mods
    sys.path.remove(str(LIB_DIR))


def _git(args, cwd):
    return subprocess.run(["git", "-C", str(cwd), *args],
                          check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(["init", "-q", "-b", "main"], root)
    _git(["config", "user.email", "t@t"], root)
    _git(["config", "user.name", "Test User"], root)
    art = root / "synapse" / "skills" / "foo"
    art.mkdir(parents=True)
    (art / "SKILL.md").write_text("hello\nworld\n")
    art2 = root / "synapse" / "agents" / "foo"
    art2.mkdir(parents=True)
    (art2 / "AGENT.md").write_text("agent body\n")
    _git(["add", "."], root)
    _git(["commit", "-q", "-m", "init"], root)
    return root


def _build_lf(lib, repo):
    lf_mod = lib["lockfile"]
    hashing = lib["hashing"]
    lf = lf_mod.empty()
    lf.synapse_repo = str(repo)
    lf.synapse_sha = _git(["rev-parse", "HEAD"], repo).stdout.strip()
    skill_src = repo / "synapse" / "skills" / "foo"
    agent_src = repo / "synapse" / "agents" / "foo"
    lf.artifacts["skill/foo"] = lf_mod.Artifact(
        key="skill/foo",
        source_path="synapse/skills/foo",
        install_path=str(repo / "install" / "foo"),
        content_hash=hashing.hash_directory(skill_src),
        type="skill",
        status="installed",
    )
    lf.artifacts["agent/foo"] = lf_mod.Artifact(
        key="agent/foo",
        source_path="synapse/agents/foo",
        install_path=str(repo / "install_agent" / "foo"),
        content_hash=hashing.hash_directory(agent_src),
        type="agent",
        status="installed",
    )
    return lf


# ---------- resolve_key ----------

def test_resolve_exact_key(lib, repo):
    lf = _build_lf(lib, repo)
    assert lib["drift_resolve"].resolve_key("skill/foo", lf) == "skill/foo"


def test_resolve_bare_name_ambiguous(lib, repo):
    lf = _build_lf(lib, repo)
    with pytest.raises(ValueError, match="ambiguous"):
        lib["drift_resolve"].resolve_key("foo", lf)


def test_resolve_bare_name_unique(lib, repo):
    lf = _build_lf(lib, repo)
    del lf.artifacts["agent/foo"]
    assert lib["drift_resolve"].resolve_key("foo", lf) == "skill/foo"


def test_resolve_unknown_raises(lib, repo):
    lf = _build_lf(lib, repo)
    with pytest.raises(ValueError, match="no such artifact"):
        lib["drift_resolve"].resolve_key("nope", lf)


# ---------- ignore ----------

def test_ignore_writes_pins(lib, repo, tmp_path):
    lf = _build_lf(lib, repo)
    # Drift the source
    (repo / "synapse" / "skills" / "foo" / "SKILL.md").write_text("drifted\n")
    pins_path = tmp_path / "pins.toml"
    res = lib["drift_resolve"].ignore_drift(
        "skill/foo", lf, repo, pins_path,
        reason="local debug", expires="2026-12-31",
    )
    assert pins_path.exists()
    raw = tomllib.loads(pins_path.read_text())
    de = raw["drift_exceptions"]["skill/foo"]
    assert de["reason"] == "local debug"
    assert de["expires"] == "2026-12-31"
    assert de["hash"].startswith("sha256:")
    assert res.expires_warning is False


def test_ignore_no_expires_returns_warning(lib, repo, tmp_path):
    lf = _build_lf(lib, repo)
    pins_path = tmp_path / "pins.toml"
    res = lib["drift_resolve"].ignore_drift(
        "skill/foo", lf, repo, pins_path, reason="r",
    )
    assert res.expires_warning is True


def test_ignore_invalid_expires_raises(lib, repo, tmp_path):
    lf = _build_lf(lib, repo)
    with pytest.raises(ValueError, match="invalid --expires"):
        lib["drift_resolve"].ignore_drift(
            "skill/foo", lf, repo, tmp_path / "pins.toml",
            expires="not-a-date",
        )


# ---------- adopt ----------

def test_adopt_creates_change_request(lib, repo):
    lf = _build_lf(lib, repo)
    src = repo / "synapse" / "skills" / "foo"
    (src / "SKILL.md").write_text("hello\nuniverse\n")
    cr_path = lib["drift_resolve"].adopt_drift(
        "skill/foo", lf, repo, slug="my fix", reason="experimentation",
    )
    assert cr_path.exists()
    body = cr_path.read_text()
    assert "title: my-fix" in body
    assert "author: test-user" in body  # from git config
    assert "artifact: skill/foo" in body
    assert "status: draft" in body
    assert "experimentation" in body
    assert "```diff" in body
    assert "+universe" in body
    # Source NOT restored — local state preserved
    assert (src / "SKILL.md").read_text() == "hello\nuniverse\n"


def test_adopt_default_slug_uses_short_hash(lib, repo):
    lf = _build_lf(lib, repo)
    src = repo / "synapse" / "skills" / "foo"
    (src / "SKILL.md").write_text("hello\nuniverse\n")
    cr_path = lib["drift_resolve"].adopt_drift("skill/foo", lf, repo)
    assert "local-drift-" in cr_path.name


def test_adopt_unknown_key(lib, repo):
    lf = _build_lf(lib, repo)
    with pytest.raises(ValueError):
        lib["drift_resolve"].adopt_drift("skill/nope", lf, repo)


# ---------- stash / list / restore ----------

def test_stash_copies_and_restores(lib, repo):
    lf = _build_lf(lib, repo)
    src = repo / "synapse" / "skills" / "foo"
    (src / "SKILL.md").write_text("dirty\n")
    (src / "EXTRA.md").write_text("added\n")
    stash_dir = lib["drift_resolve"].stash_artifact(
        "skill/foo", lf, repo, reason="trying-something",
    )
    assert stash_dir.is_dir()
    payload = stash_dir / "payload"
    assert (payload / "SKILL.md").read_text() == "dirty\n"
    assert (payload / "EXTRA.md").read_text() == "added\n"
    meta = tomllib.loads((stash_dir / "STASH_META.toml").read_text())
    assert meta["artifact"] == "skill/foo"
    assert meta["reason"] == "trying-something"
    # Source restored to canonical
    assert (src / "SKILL.md").read_text() == "hello\nworld\n"
    assert not (src / "EXTRA.md").exists()


def test_list_stashes_returns_metadata(lib, repo):
    lf = _build_lf(lib, repo)
    src = repo / "synapse" / "skills" / "foo"
    (src / "SKILL.md").write_text("dirty\n")
    lib["drift_resolve"].stash_artifact("skill/foo", lf, repo, reason="r")
    listing = lib["drift_resolve"].list_stashes()
    assert len(listing) == 1
    assert listing[0]["artifact"] == "skill/foo"
    assert listing[0]["reason"] == "r"


def test_restore_stash_force(lib, repo):
    lf = _build_lf(lib, repo)
    src = repo / "synapse" / "skills" / "foo"
    (src / "SKILL.md").write_text("dirty\n")
    stash_dir = lib["drift_resolve"].stash_artifact("skill/foo", lf, repo)
    assert (src / "SKILL.md").read_text() == "hello\nworld\n"  # restored
    lib["drift_resolve"].restore_stash(stash_dir.name, repo, force=True)
    assert (src / "SKILL.md").read_text() == "dirty\n"


def test_restore_unknown_stash_raises(lib, repo):
    with pytest.raises(ValueError, match="no such stash"):
        lib["drift_resolve"].restore_stash("nope", repo, force=True)


def test_restore_no_tty_no_force_raises(lib, repo, monkeypatch):
    lf = _build_lf(lib, repo)
    src = repo / "synapse" / "skills" / "foo"
    (src / "SKILL.md").write_text("dirty\n")
    stash_dir = lib["drift_resolve"].stash_artifact("skill/foo", lf, repo)
    # stdin is non-TTY in pytest
    with pytest.raises(RuntimeError, match="--yes"):
        lib["drift_resolve"].restore_stash(stash_dir.name, repo, force=False)
