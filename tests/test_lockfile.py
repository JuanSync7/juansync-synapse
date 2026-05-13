"""Tests for scripts/lib/lockfile.py and scripts/lib/lockfile_update.py."""
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
def lockfile_mod():
    sys.path.insert(0, str(LIB_DIR))
    for name in ("lockfile", "lockfile_update", "hashing", "synapse_paths"):
        if name in sys.modules:
            del sys.modules[name]
    mod = importlib.import_module("lockfile")
    yield mod
    sys.path.remove(str(LIB_DIR))


@pytest.fixture
def update_mod(lockfile_mod):
    sys.path.insert(0, str(LIB_DIR))
    if "lockfile_update" in sys.modules:
        del sys.modules["lockfile_update"]
    mod = importlib.import_module("lockfile_update")
    yield mod
    sys.path.remove(str(LIB_DIR))


def test_empty_round_trip(lockfile_mod, tmp_path):
    lf = lockfile_mod.empty()
    p = tmp_path / "installed.lock"
    lockfile_mod.save(lf, p)
    assert p.exists()
    lf2 = lockfile_mod.load(p)
    assert lf2.schema_version == 1
    assert lf2.artifacts == {}
    assert lf2.externals == {}


def test_artifact_round_trip(lockfile_mod, tmp_path):
    lf = lockfile_mod.empty()
    lf.synapse_repo = "/tmp/repo"
    lf.synapse_tag = "v2026.05.0"
    lf.synapse_sha = "abc123"
    lf.installed_at = "2026-05-06T14:32:11Z"
    lf.machine_id = "host-laptop-abc"
    lf.artifacts["skill/foo"] = lockfile_mod.Artifact(
        key="skill/foo",
        source_path="synapse/skills/foo",
        install_path="~/.claude/skills/foo",
        content_hash="sha256:deadbeef",
        type="skill",
        status="installed",
    )
    p = tmp_path / "installed.lock"
    lockfile_mod.save(lf, p)
    parsed = tomllib.loads(p.read_text())
    assert parsed["synapse_tag"] == "v2026.05.0"
    assert parsed["artifact"]["skill/foo"]["content_hash"] == "sha256:deadbeef"

    lf2 = lockfile_mod.load(p)
    assert lf2.artifacts["skill/foo"].content_hash == "sha256:deadbeef"
    assert lf2.synapse_tag == "v2026.05.0"
    assert lf2.machine_id == "host-laptop-abc"


def test_external_round_trip(lockfile_mod, tmp_path):
    lf = lockfile_mod.empty()
    lf.externals["suite-x"] = lockfile_mod.External(
        key="suite-x",
        submodule_path="external/suite-x",
        submodule_sha="fedcba",
        content_hash="sha256:cafe",
        status="installed",
    )
    p = tmp_path / "installed.lock"
    lockfile_mod.save(lf, p)
    lf2 = lockfile_mod.load(p)
    assert lf2.externals["suite-x"].submodule_sha == "fedcba"


def test_atomic_write_preserves_old_on_crash(lockfile_mod, tmp_path, monkeypatch):
    p = tmp_path / "installed.lock"
    p.write_text('schema_version = 1\nsynapse_repo = "original"\n')
    original = p.read_text()

    lf = lockfile_mod.empty()
    lf.synapse_repo = "new-but-will-fail"

    def boom(*args, **kwargs):
        raise RuntimeError("simulated crash")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(RuntimeError):
        lockfile_mod.save(lf, p)
    assert p.read_text() == original


# --- update layer ---


def _make_artifact_dir(root: pathlib.Path, files: dict[str, str]) -> pathlib.Path:
    root.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content)
    return root


def test_upsert_artifact_idempotent(update_mod, lockfile_mod, tmp_path):
    repo = tmp_path / "repo"
    art = _make_artifact_dir(repo / "synapse" / "skills" / "foo", {"SKILL.md": "x"})
    lf = lockfile_mod.empty()
    update_mod.upsert_artifact(
        lf, key="skill/foo", type="skill",
        source_path="synapse/skills/foo",
        install_path="~/.claude/skills/foo",
        repo_root=repo,
    )
    h1 = lf.artifacts["skill/foo"].content_hash
    update_mod.upsert_artifact(
        lf, key="skill/foo", type="skill",
        source_path="synapse/skills/foo",
        install_path="~/.claude/skills/foo",
        repo_root=repo,
    )
    assert len(lf.artifacts) == 1
    assert lf.artifacts["skill/foo"].content_hash == h1
    assert lf.artifacts["skill/foo"].status == "installed"


def test_remove_artifact(update_mod, lockfile_mod, tmp_path):
    repo = tmp_path / "repo"
    _make_artifact_dir(repo / "synapse" / "skills" / "foo", {"SKILL.md": "x"})
    lf = lockfile_mod.empty()
    update_mod.upsert_artifact(
        lf, key="skill/foo", type="skill",
        source_path="synapse/skills/foo",
        install_path="~/.claude/skills/foo",
        repo_root=repo,
    )
    update_mod.remove_artifact(lf, "skill/foo")
    assert "skill/foo" not in lf.artifacts
    # removing missing key is a no-op
    update_mod.remove_artifact(lf, "nope")


def _git(args: list[str], cwd: pathlib.Path):
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "t"
    env["GIT_AUTHOR_EMAIL"] = "t@t"
    env["GIT_COMMITTER_NAME"] = "t"
    env["GIT_COMMITTER_EMAIL"] = "t@t"
    subprocess.run(["git", *args], cwd=cwd, check=True, env=env, capture_output=True)


def test_upsert_external_reads_submodule_sha(update_mod, lockfile_mod, tmp_path):
    repo = tmp_path / "repo"
    sub = repo / "external" / "suite-x"
    sub.mkdir(parents=True)
    _git(["init", "-q", "-b", "main"], sub)
    (sub / "f.txt").write_text("hello")
    _git(["add", "."], sub)
    _git(["commit", "-q", "-m", "init"], sub)
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=sub, check=True,
        capture_output=True, text=True,
    ).stdout.strip()

    lf = lockfile_mod.empty()
    update_mod.upsert_external(
        lf, key="suite-x", submodule_path="external/suite-x", repo_root=repo,
    )
    assert lf.externals["suite-x"].submodule_sha == sha
    assert lf.externals["suite-x"].content_hash.startswith("sha256:")
    assert lf.externals["suite-x"].status == "installed"


def test_stamp_metadata_fills_fields(update_mod, lockfile_mod, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init", "-q", "-b", "main"], repo)
    (repo / "x").write_text("x")
    _git(["add", "."], repo)
    _git(["commit", "-q", "-m", "init"], repo)

    lf = lockfile_mod.empty()
    update_mod.stamp_metadata(lf, repo_root=repo)
    assert lf.synapse_repo == str(repo)
    assert len(lf.synapse_sha) == 40
    assert lf.installed_at.endswith("Z")
    assert lf.machine_id != ""
    # synapse_tag may be "" if no tags — that's fine
    assert isinstance(lf.synapse_tag, str)
