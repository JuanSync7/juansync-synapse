"""Tests for scripts/lib/drift_diff.py."""
from __future__ import annotations

import importlib
import pathlib
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"


@pytest.fixture
def drift_diff():
    sys.path.insert(0, str(LIB_DIR))
    for n in ("hashing", "drift_diff"):
        if n in sys.modules:
            del sys.modules[n]
    mod = importlib.import_module("drift_diff")
    yield mod
    sys.path.remove(str(LIB_DIR))


def _git(args, cwd):
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True, capture_output=True, text=True,
    )


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(["init", "-q", "-b", "main"], root)
    _git(["config", "user.email", "t@t"], root)
    _git(["config", "user.name", "t"], root)
    art = root / "synapse" / "skills" / "foo"
    art.mkdir(parents=True)
    (art / "SKILL.md").write_text("hello\nworld\n")
    (art / "refs").mkdir()
    (art / "refs" / "a.md").write_text("alpha\n")
    _git(["add", "."], root)
    _git(["commit", "-q", "-m", "init"], root)
    return root


def test_no_drift_clean(drift_diff, repo):
    src = repo / "synapse" / "skills" / "foo"
    diffs = drift_diff.diff_artifact_against_git(src, repo)
    assert diffs == []


def test_modified_file_produces_unified_diff(drift_diff, repo):
    src = repo / "synapse" / "skills" / "foo"
    (src / "SKILL.md").write_text("hello\nuniverse\n")
    diffs = drift_diff.diff_artifact_against_git(src, repo)
    assert len(diffs) == 1
    fd = diffs[0]
    assert fd.relpath == "SKILL.md"
    assert fd.status == "modified"
    assert fd.binary is False
    assert "-world" in fd.diff_text
    assert "+universe" in fd.diff_text


def test_added_file_detected(drift_diff, repo):
    src = repo / "synapse" / "skills" / "foo"
    (src / "NEW.md").write_text("brand new\n")
    diffs = drift_diff.diff_artifact_against_git(src, repo)
    assert len(diffs) == 1
    assert diffs[0].relpath == "NEW.md"
    assert diffs[0].status == "added"


def test_removed_file_detected(drift_diff, repo):
    src = repo / "synapse" / "skills" / "foo"
    (src / "refs" / "a.md").unlink()
    diffs = drift_diff.diff_artifact_against_git(src, repo)
    assert len(diffs) == 1
    assert diffs[0].relpath == "refs/a.md"
    assert diffs[0].status == "removed"


def test_multi_file_diff(drift_diff, repo):
    src = repo / "synapse" / "skills" / "foo"
    (src / "SKILL.md").write_text("changed\n")
    (src / "refs" / "a.md").write_text("changed\n")
    (src / "NEW.md").write_text("new\n")
    diffs = drift_diff.diff_artifact_against_git(src, repo)
    assert {d.relpath for d in diffs} == {"SKILL.md", "refs/a.md", "NEW.md"}
    # sorted
    assert [d.relpath for d in diffs] == sorted(d.relpath for d in diffs)


def test_binary_file_marked(drift_diff, repo):
    src = repo / "synapse" / "skills" / "foo"
    (src / "blob.bin").write_bytes(b"\x00\x01\x02hello")
    diffs = drift_diff.diff_artifact_against_git(src, repo)
    bins = [d for d in diffs if d.relpath == "blob.bin"]
    assert len(bins) == 1
    assert bins[0].binary is True
    assert bins[0].diff_text is None


def test_excluded_change_requests_ignored(drift_diff, repo):
    src = repo / "synapse" / "skills" / "foo"
    (src / "change_requests").mkdir()
    (src / "change_requests" / "cr.md").write_text("cr body\n")
    diffs = drift_diff.diff_artifact_against_git(src, repo)
    # change_requests/ excluded — no drift
    assert diffs == []


def test_eval_md_excluded(drift_diff, repo):
    src = repo / "synapse" / "skills" / "foo"
    (src / "EVAL.md").write_text("generated\n")
    diffs = drift_diff.diff_artifact_against_git(src, repo)
    assert diffs == []


def test_source_path_outside_repo_raises(drift_diff, tmp_path, repo):
    with pytest.raises(ValueError):
        drift_diff.diff_artifact_against_git(tmp_path / "elsewhere", repo)
