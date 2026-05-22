"""Tests for scripts/lib/hashing.py — deterministic directory content hashing."""
from __future__ import annotations

import importlib
import pathlib
import shutil
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"


@pytest.fixture
def hashing():
    sys.path.insert(0, str(LIB_DIR))
    if "hashing" in sys.modules:
        del sys.modules["hashing"]
    mod = importlib.import_module("hashing")
    yield mod
    sys.path.remove(str(LIB_DIR))


def _make_dir(root: pathlib.Path, files: dict[str, str]) -> pathlib.Path:
    root.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return root


def test_identical_dirs_hash_identically(hashing, tmp_path):
    a = _make_dir(tmp_path / "a", {"SKILL.md": "x", "refs/foo.md": "y"})
    b = _make_dir(tmp_path / "b", {"SKILL.md": "x", "refs/foo.md": "y"})
    assert hashing.hash_directory(a) == hashing.hash_directory(b)
    assert hashing.hash_directory(a).startswith("sha256:")


def test_eval_md_excluded(hashing, tmp_path):
    a = _make_dir(tmp_path / "a", {"SKILL.md": "x"})
    h1 = hashing.hash_directory(a)
    (a / "EVAL.md").write_text("eval content")
    assert hashing.hash_directory(a) == h1


def test_change_requests_excluded(hashing, tmp_path):
    a = _make_dir(tmp_path / "a", {"SKILL.md": "x"})
    h1 = hashing.hash_directory(a)
    (a / "change_requests").mkdir()
    (a / "change_requests" / "anything.md").write_text("hi")
    (a / "change_requests" / "nested" / "deep.md").parent.mkdir()
    (a / "change_requests" / "nested" / "deep.md").write_text("deep")
    assert hashing.hash_directory(a) == h1


def test_changing_non_excluded_file_changes_hash(hashing, tmp_path):
    a = _make_dir(tmp_path / "a", {"SKILL.md": "x"})
    h1 = hashing.hash_directory(a)
    (a / "SKILL.md").write_text("y")
    assert hashing.hash_directory(a) != h1


def test_rename_changes_hash(hashing, tmp_path):
    a = _make_dir(tmp_path / "a", {"foo.md": "same"})
    h1 = hashing.hash_directory(a)
    (a / "foo.md").rename(a / "bar.md")
    assert hashing.hash_directory(a) != h1


def test_empty_dir_stable(hashing, tmp_path):
    a = tmp_path / "a"
    a.mkdir()
    b = tmp_path / "b"
    b.mkdir()
    assert hashing.hash_directory(a) == hashing.hash_directory(b)


def test_file_hashes_basic(hashing, tmp_path):
    a = _make_dir(tmp_path / "a", {"SKILL.md": "x", "refs/foo.md": "y"})
    h = hashing.file_hashes(a)
    assert set(h.keys()) == {"SKILL.md", "refs/foo.md"}
    # all hex
    for v in h.values():
        assert len(v) == 64
        int(v, 16)


def test_file_hashes_respects_exclusions(hashing, tmp_path):
    a = _make_dir(tmp_path / "a", {
        "SKILL.md": "x",
        "EVAL.md": "skip",
        "change_requests/cr.md": "skip",
        "x.pyc": "skip",
    })
    h = hashing.file_hashes(a)
    assert set(h.keys()) == {"SKILL.md"}


def test_file_hashes_empty_for_missing_dir(hashing, tmp_path):
    assert hashing.file_hashes(tmp_path / "nope") == {}


def test_file_hashes_extra_exclude(hashing, tmp_path):
    a = _make_dir(tmp_path / "a", {"SKILL.md": "x", "extra.md": "y"})
    h = hashing.file_hashes(a, exclude={"extra.md"})
    assert set(h.keys()) == {"SKILL.md"}


def test_pyc_and_dsstore_excluded(hashing, tmp_path):
    a = _make_dir(tmp_path / "a", {"SKILL.md": "x"})
    h1 = hashing.hash_directory(a)
    (a / ".DS_Store").write_text("junk")
    (a / "x.pyc").write_text("compiled")
    (a / "__pycache__").mkdir()
    (a / "__pycache__" / "y.pyc").write_text("c")
    (a / "draft.swp").write_text("vim")
    assert hashing.hash_directory(a) == h1
