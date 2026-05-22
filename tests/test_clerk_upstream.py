"""Tests for scripts/lib/clerk_upstream.py."""
from __future__ import annotations

import importlib
import pathlib
import subprocess
import sys
import textwrap
from unittest.mock import MagicMock

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"


@pytest.fixture
def cu():
    sys.path.insert(0, str(LIB_DIR))
    for name in ("clerk_upstream", "clerk_state"):
        if name in sys.modules:
            del sys.modules[name]
    mod = importlib.import_module("clerk_upstream")
    yield mod
    sys.path.remove(str(LIB_DIR))


@pytest.fixture
def cs():
    sys.path.insert(0, str(LIB_DIR))
    if "clerk_state" in sys.modules:
        del sys.modules["clerk_state"]
    mod = importlib.import_module("clerk_state")
    yield mod
    sys.path.remove(str(LIB_DIR))


# ---------------------------------------------------------------------------
# parse_gitmodules
# ---------------------------------------------------------------------------

def test_parse_gitmodules_missing(cu, tmp_path):
    assert cu.parse_gitmodules(tmp_path) == {}


def test_parse_gitmodules_filters_to_external(cu, tmp_path):
    (tmp_path / ".gitmodules").write_text(textwrap.dedent("""
        [submodule "foo"]
            path = external/foo
            url = https://github.com/x/foo.git
        [submodule "bar"]
            path = external/bar-suite
            url = git@github.com:x/bar.git
        [submodule "qux"]
            path = src/qux
            url = https://github.com/x/qux.git
    """).strip())
    out = cu.parse_gitmodules(tmp_path)
    assert out == {
        "external/foo": "https://github.com/x/foo.git",
        "external/bar-suite": "git@github.com:x/bar.git",
    }


def test_parse_gitmodules_skips_incomplete(cu, tmp_path):
    (tmp_path / ".gitmodules").write_text(textwrap.dedent("""
        [submodule "foo"]
            path = external/foo
        [submodule "bar"]
            url = https://github.com/x/bar.git
    """).strip())
    assert cu.parse_gitmodules(tmp_path) == {}


# ---------------------------------------------------------------------------
# list_upstream_stable_tags
# ---------------------------------------------------------------------------

def _fake_proc(stdout: str, returncode: int = 0):
    p = MagicMock()
    p.stdout = stdout
    p.stderr = ""
    p.returncode = returncode
    return p


def test_list_stable_filters_prereleases(cu):
    out = textwrap.dedent("""
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\trefs/tags/v1.0.0
        bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\trefs/tags/v1.1.0-pre.1
        cccccccccccccccccccccccccccccccccccccccc\trefs/tags/v2.0.0
        dddddddddddddddddddddddddddddddddddddddd\trefs/tags/random-branch-tag
    """).strip() + "\n"
    runner = MagicMock(return_value=_fake_proc(out))
    tags = cu.list_upstream_stable_tags("u", runner=runner)
    assert [t.tag for t in tags] == ["v2.0.0", "v1.0.0"]


def test_list_stable_prefers_dereferenced(cu):
    # Annotated tag: tag-object SHA + dereferenced commit SHA
    out = textwrap.dedent("""
        1111111111111111111111111111111111111111\trefs/tags/v1.0.0
        2222222222222222222222222222222222222222\trefs/tags/v1.0.0^{}
    """).strip() + "\n"
    runner = MagicMock(return_value=_fake_proc(out))
    tags = cu.list_upstream_stable_tags("u", runner=runner)
    assert len(tags) == 1
    assert tags[0].tag == "v1.0.0"
    assert tags[0].sha == "2" * 40   # dereferenced wins


def test_list_stable_semver_descending(cu):
    out = textwrap.dedent("""
        1111111111111111111111111111111111111111\trefs/tags/v1.2.3
        2222222222222222222222222222222222222222\trefs/tags/v1.10.0
        3333333333333333333333333333333333333333\trefs/tags/v2.0.1
        4444444444444444444444444444444444444444\trefs/tags/v0.9.9
    """).strip() + "\n"
    runner = MagicMock(return_value=_fake_proc(out))
    tags = cu.list_upstream_stable_tags("u", runner=runner)
    assert [t.tag for t in tags] == ["v2.0.1", "v1.10.0", "v1.2.3", "v0.9.9"]


def test_list_stable_empty(cu):
    runner = MagicMock(return_value=_fake_proc(""))
    assert cu.list_upstream_stable_tags("u", runner=runner) == []


def test_list_stable_only_prereleases_returns_empty(cu):
    out = "1111111111111111111111111111111111111111\trefs/tags/v1.0.0-pre.1\n"
    runner = MagicMock(return_value=_fake_proc(out))
    assert cu.list_upstream_stable_tags("u", runner=runner) == []


def test_list_stable_subprocess_failure(cu):
    def boom(*a, **kw):
        raise subprocess.CalledProcessError(128, a[0], stderr="bad url")
    with pytest.raises(RuntimeError, match="ls-remote failed"):
        cu.list_upstream_stable_tags("u", runner=boom)


def test_list_stable_timeout(cu):
    def slow(*a, **kw):
        raise subprocess.TimeoutExpired(a[0], 1)
    with pytest.raises(RuntimeError, match="timed out"):
        cu.list_upstream_stable_tags("u", runner=slow, timeout=1)


def test_latest_stable_upstream_picks_top(cu):
    out = textwrap.dedent("""
        1111111111111111111111111111111111111111\trefs/tags/v1.0.0
        2222222222222222222222222222222222222222\trefs/tags/v1.5.0
    """).strip() + "\n"
    runner = MagicMock(return_value=_fake_proc(out))
    top = cu.latest_stable_upstream("u", runner=runner)
    assert top.tag == "v1.5.0"


def test_latest_stable_upstream_none_when_empty(cu):
    runner = MagicMock(return_value=_fake_proc(""))
    assert cu.latest_stable_upstream("u", runner=runner) is None


# ---------------------------------------------------------------------------
# current_submodule_sha
# ---------------------------------------------------------------------------

def test_current_submodule_sha_parses_status(cu, tmp_path):
    # ` <sha> <path> (...)` shape
    sha = "a" * 40
    runner = MagicMock(return_value=_fake_proc(f" {sha} external/foo (heads/main)\n"))
    assert cu.current_submodule_sha(tmp_path, "external/foo", runner=runner) == sha


def test_current_submodule_sha_strips_status_char(cu, tmp_path):
    sha = "b" * 40
    runner = MagicMock(return_value=_fake_proc(f"+{sha} external/foo\n"))
    assert cu.current_submodule_sha(tmp_path, "external/foo", runner=runner) == sha


def test_current_submodule_sha_handles_failure(cu, tmp_path):
    def boom(*a, **kw):
        raise subprocess.CalledProcessError(1, a[0])
    assert cu.current_submodule_sha(tmp_path, "external/foo", runner=boom) == ""


# ---------------------------------------------------------------------------
# detect_force_push
# ---------------------------------------------------------------------------

def test_detect_force_push_new_tag_no_record(cu, cs):
    state = cs.empty()
    assert cu.detect_force_push(state, "external/foo", "v1.0.0", "a" * 40) is False


def test_detect_force_push_same_sha(cu, cs):
    state = cs.empty()
    state.seen_tags["external/foo"] = {
        "v1.0.0": cs.SeenTag(sha="a" * 40, first_seen="t"),
    }
    assert cu.detect_force_push(state, "external/foo", "v1.0.0", "a" * 40) is False


def test_detect_force_push_changed_sha(cu, cs):
    state = cs.empty()
    state.seen_tags["external/foo"] = {
        "v1.0.0": cs.SeenTag(sha="a" * 40, first_seen="t"),
    }
    assert cu.detect_force_push(state, "external/foo", "v1.0.0", "b" * 40) is True
