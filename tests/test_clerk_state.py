"""Tests for scripts/lib/clerk_state.py."""
from __future__ import annotations

import importlib
import pathlib
import sys
import tomllib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"


@pytest.fixture
def cs():
    sys.path.insert(0, str(LIB_DIR))
    if "clerk_state" in sys.modules:
        del sys.modules["clerk_state"]
    mod = importlib.import_module("clerk_state")
    yield mod
    sys.path.remove(str(LIB_DIR))


def test_empty_round_trip(cs, tmp_path):
    p = tmp_path / "clerk_state.toml"
    cs.save(cs.empty(), p)
    assert p.exists()
    s2 = cs.load(p)
    assert s2.schema_version == 1
    assert s2.seen_tags == {}
    assert s2.bumps == {}


def test_missing_file_returns_empty(cs, tmp_path):
    p = tmp_path / "does-not-exist.toml"
    s = cs.load(p)
    assert s.schema_version == 1
    assert s.seen_tags == {}
    assert s.bumps == {}


def test_seen_tags_round_trip(cs, tmp_path):
    state = cs.empty()
    state.seen_tags["external/foo"] = {
        "v1.4.6": cs.SeenTag(sha="a" * 40, first_seen="2026-04-01T12:00:00Z"),
        "v1.4.7": cs.SeenTag(sha="b" * 40, first_seen="2026-05-06T08:00:00Z"),
    }
    state.bumps["external/foo"] = cs.BumpRecord(
        last_bumped_at="2026-05-06T08:00:00Z",
        last_pr_url="https://github.com/o/r/pull/1",
        last_bumped_to="v1.4.7",
    )
    p = tmp_path / "clerk_state.toml"
    cs.save(state, p)

    # Round trip
    s2 = cs.load(p)
    assert s2.seen_tags["external/foo"]["v1.4.6"].sha == "a" * 40
    assert s2.seen_tags["external/foo"]["v1.4.7"].first_seen == "2026-05-06T08:00:00Z"
    assert s2.bumps["external/foo"].last_pr_url == "https://github.com/o/r/pull/1"
    assert s2.bumps["external/foo"].last_bumped_to == "v1.4.7"

    # Generated TOML must parse cleanly
    raw = tomllib.loads(p.read_text())
    assert raw["schema_version"] == 1
    assert raw["seen_tags"]["external/foo"]["v1.4.6"]["sha"] == "a" * 40


def test_atomic_write_no_tmp_left(cs, tmp_path):
    p = tmp_path / "clerk_state.toml"
    cs.save(cs.empty(), p)
    assert p.exists()
    leftover = list(tmp_path.glob("*.tmp"))
    assert leftover == [], f"tmp files left behind: {leftover}"


def test_malformed_toml_raises(cs, tmp_path):
    p = tmp_path / "bad.toml"
    p.write_text("schema_version = 1\n[unclosed\n")
    with pytest.raises(ValueError, match="malformed TOML"):
        cs.load(p)


def test_unsupported_schema_version_raises(cs, tmp_path):
    p = tmp_path / "future.toml"
    p.write_text("schema_version = 99\n")
    with pytest.raises(ValueError, match="schema_version"):
        cs.load(p)


def test_state_path_under_home(cs, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    sp = cs.state_path()
    assert str(sp).startswith(str(tmp_path))
    assert sp.name == "clerk_state.toml"
