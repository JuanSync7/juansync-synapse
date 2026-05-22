"""Tests for scripts/lib/pins_resolver.py."""
from __future__ import annotations

import importlib
import os
import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"


@pytest.fixture
def resolver_mod():
    sys.path.insert(0, str(LIB_DIR))
    if "pins_resolver" in sys.modules:
        del sys.modules["pins_resolver"]
    mod = importlib.import_module("pins_resolver")
    yield mod
    sys.path.remove(str(LIB_DIR))


def _git(args: list[str], cwd: pathlib.Path):
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "t"
    env["GIT_AUTHOR_EMAIL"] = "t@t"
    env["GIT_COMMITTER_NAME"] = "t"
    env["GIT_COMMITTER_EMAIL"] = "t@t"
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, env=env,
        capture_output=True, text=True,
    )


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    _git(["init", "-q", "-b", "main"], r)
    (r / "x").write_text("1")
    _git(["add", "."], r)
    _git(["commit", "-q", "-m", "c1"], r)
    _git(["tag", "v1.0.0"], r)
    (r / "x").write_text("2")
    _git(["add", "."], r)
    _git(["commit", "-q", "-m", "c2"], r)
    _git(["tag", "v1.2.3"], r)
    (r / "x").write_text("3")
    _git(["add", "."], r)
    _git(["commit", "-q", "-m", "c3"], r)
    _git(["tag", "v1.10.2"], r)  # ensures semver-aware sort
    (r / "x").write_text("4")
    _git(["add", "."], r)
    _git(["commit", "-q", "-m", "c4"], r)
    _git(["tag", "v2.0.0-pre.1"], r)  # should be ignored by latest_stable
    return r


# --- validate_pin_value ---


def test_validate_valid_forms(resolver_mod):
    for v in ["latest", "main", "v1.0.0", "v10.20.30", "v1.0.0-pre.1",
              "v1.0.0-pre.99", "sha:abcdef0", "sha:" + "a" * 40]:
        ok, reason = resolver_mod.validate_pin_value(v)
        assert ok, f"expected {v!r} to validate, got {reason!r}"


def test_validate_invalid_forms(resolver_mod):
    for v in ["v1", "v1.2", "sha:xy", "sha:", "random-string",
              "1.0.0", "v1.0", "vXYZ", ""]:
        ok, _ = resolver_mod.validate_pin_value(v)
        assert not ok, f"expected {v!r} to fail validation"


# --- latest_stable_tag ---


def test_latest_stable_tag_picks_highest_semver(resolver_mod, repo):
    assert resolver_mod.latest_stable_tag(repo) == "v1.10.2"


def test_latest_stable_tag_empty_repo(resolver_mod, tmp_path):
    r = tmp_path / "empty"
    r.mkdir()
    _git(["init", "-q", "-b", "main"], r)
    (r / "x").write_text("1")
    _git(["add", "."], r)
    _git(["commit", "-q", "-m", "c1"], r)
    assert resolver_mod.latest_stable_tag(r) == ""


# --- resolve_pin ---


def test_resolve_tag(resolver_mod, repo):
    res = resolver_mod.resolve_pin("v1.2.3", repo)
    assert res.kind == "tag"
    assert res.resolved_tag == "v1.2.3"
    assert len(res.resolved_sha) == 40
    assert res.pin == "v1.2.3"


def test_resolve_latest(resolver_mod, repo):
    res = resolver_mod.resolve_pin("latest", repo)
    assert res.kind == "latest"
    assert res.resolved_tag == "v1.10.2"
    assert len(res.resolved_sha) == 40


def test_resolve_main(resolver_mod, repo):
    res = resolver_mod.resolve_pin("main", repo)
    assert res.kind == "main"
    assert res.resolved_tag == ""
    assert len(res.resolved_sha) == 40


def test_resolve_sha(resolver_mod, repo):
    head = _git(["rev-parse", "HEAD"], repo).stdout.strip()
    short = head[:8]
    res = resolver_mod.resolve_pin(f"sha:{short}", repo)
    assert res.kind == "sha"
    assert res.resolved_sha == head
    assert len(res.resolved_sha) == 40


def test_resolve_invalid_pin_raises(resolver_mod, repo):
    with pytest.raises(ValueError):
        resolver_mod.resolve_pin("garbage", repo)


def test_resolve_missing_tag_raises(resolver_mod, repo):
    with pytest.raises(ValueError):
        resolver_mod.resolve_pin("v9.9.9", repo)


def test_resolve_latest_in_empty_repo_raises(resolver_mod, tmp_path):
    r = tmp_path / "norep"
    r.mkdir()
    _git(["init", "-q", "-b", "main"], r)
    (r / "x").write_text("1")
    _git(["add", "."], r)
    _git(["commit", "-q", "-m", "c1"], r)
    with pytest.raises(ValueError) as exc:
        resolver_mod.resolve_pin("latest", r)
    assert "tag" in str(exc.value).lower() or "stable" in str(exc.value).lower()
