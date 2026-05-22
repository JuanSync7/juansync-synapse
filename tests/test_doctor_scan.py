"""Tests for scripts/lib/doctor_scan.py.

Uses tmp_path fixtures simulating an artifact source tree + an install_path
target. Creates a real lockfile via lockfile.save() then runs scanners.
"""
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
def lib():
    sys.path.insert(0, str(LIB_DIR))
    for name in (
        "doctor_findings",
        "doctor_scan",
        "lockfile",
        "hashing",
        "pins",
        "pins_resolver",
        "synapse_paths",
    ):
        if name in sys.modules:
            del sys.modules[name]
    mods = {
        "scan": importlib.import_module("doctor_scan"),
        "findings": importlib.import_module("doctor_findings"),
        "lockfile": importlib.import_module("lockfile"),
        "hashing": importlib.import_module("hashing"),
        "pins": importlib.import_module("pins"),
        "resolver": importlib.import_module("pins_resolver"),
    }
    yield mods
    sys.path.remove(str(LIB_DIR))


def _git(args, cwd):
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True, capture_output=True, text=True,
    )


@pytest.fixture
def repo(tmp_path):
    """Tiny git repo with one artifact + git config so commits/tags work."""
    root = tmp_path / "repo"
    root.mkdir()
    _git(["init", "-q", "-b", "main"], root)
    _git(["config", "user.email", "t@t"], root)
    _git(["config", "user.name", "t"], root)
    art = root / "synapse" / "skills" / "foo"
    art.mkdir(parents=True)
    (art / "SKILL.md").write_text("---\nname: foo\n---\nbody\n")
    _git(["add", "."], root)
    _git(["commit", "-q", "-m", "init"], root)
    return root


def _build_lockfile(lib, repo, install_root, *, with_artifact=True):
    """Build an in-memory lockfile pointing at synapse/skills/foo."""
    lf_mod = lib["lockfile"]
    hashing = lib["hashing"]
    lf = lf_mod.empty()
    lf.synapse_repo = str(repo)
    lf.synapse_tag = ""
    lf.synapse_sha = _git(["rev-parse", "HEAD"], repo).stdout.strip()
    if with_artifact:
        src = repo / "synapse" / "skills" / "foo"
        install_path = install_root / "foo"
        install_path.mkdir(parents=True)
        # Copy minimal contents so install_path "exists"
        (install_path / "SKILL.md").write_text((src / "SKILL.md").read_text())
        h = hashing.hash_directory(src)
        lf.artifacts["skill/foo"] = lf_mod.Artifact(
            key="skill/foo",
            source_path="synapse/skills/foo",
            install_path=str(install_path),
            content_hash=h,
            type="skill",
            status="installed",
        )
    return lf


# ---------- drift ----------

def test_scan_drift_clean(lib, repo, tmp_path):
    install_root = tmp_path / "install"
    lf = _build_lockfile(lib, repo, install_root)
    findings = lib["scan"].scan_drift(lf, repo)
    assert findings == []


def test_scan_drift_detects_modification(lib, repo, tmp_path):
    install_root = tmp_path / "install"
    lf = _build_lockfile(lib, repo, install_root)
    # Modify source content
    (repo / "synapse" / "skills" / "foo" / "SKILL.md").write_text("modified\n")
    findings = lib["scan"].scan_drift(lf, repo)
    assert len(findings) == 1
    assert findings[0].category == "drift"
    assert findings[0].severity == "warn"
    assert findings[0].artifact == "skill/foo"
    # Details surface enough for T4 drift adopt
    assert "expected" in findings[0].details
    assert "actual" in findings[0].details


# ---------- missing ----------

def test_scan_missing_clean(lib, repo, tmp_path):
    install_root = tmp_path / "install"
    lf = _build_lockfile(lib, repo, install_root)
    findings = lib["scan"].scan_missing(lf, repo)
    assert findings == []


def test_scan_missing_when_install_path_gone(lib, repo, tmp_path):
    install_root = tmp_path / "install"
    lf = _build_lockfile(lib, repo, install_root)
    # Nuke the install_path
    install_path = pathlib.Path(lf.artifacts["skill/foo"].install_path)
    import shutil
    shutil.rmtree(install_path)
    findings = lib["scan"].scan_missing(lf, repo)
    assert len(findings) == 1
    assert findings[0].category == "missing"
    assert findings[0].severity == "error"


def test_scan_missing_broken_symlink(lib, repo, tmp_path):
    install_root = tmp_path / "install"
    lf = _build_lockfile(lib, repo, install_root)
    install_path = pathlib.Path(lf.artifacts["skill/foo"].install_path)
    import shutil
    shutil.rmtree(install_path)
    # Replace with broken symlink
    install_path.symlink_to(tmp_path / "nonexistent")
    findings = lib["scan"].scan_missing(lf, repo)
    assert len(findings) == 1
    assert findings[0].category == "missing"


# ---------- corrupt ----------

def test_scan_corrupt_invalid_hash(lib, repo, tmp_path):
    lf_mod = lib["lockfile"]
    lf = lf_mod.empty()
    lf.artifacts["skill/foo"] = lf_mod.Artifact(
        key="skill/foo",
        source_path="x",
        install_path="y",
        content_hash="not-a-sha",  # malformed
        type="skill",
        status="installed",
    )
    findings = lib["scan"].scan_corrupt(tmp_path / "installed.lock", lf)
    assert len(findings) == 1
    assert findings[0].category == "corrupt"
    assert findings[0].severity == "error"


def test_scan_corrupt_no_lockfile(lib, tmp_path):
    findings = lib["scan"].scan_corrupt(tmp_path / "missing.lock", None)
    assert len(findings) == 1
    assert findings[0].category == "corrupt"
    assert findings[0].severity == "error"
    assert findings[0].artifact == ""


def test_scan_corrupt_clean(lib, repo, tmp_path):
    install_root = tmp_path / "install"
    lf = _build_lockfile(lib, repo, install_root)
    findings = lib["scan"].scan_corrupt(tmp_path / "installed.lock", lf)
    assert findings == []


# ---------- orphaned ----------

def test_scan_orphaned_lockfile_entry_source_gone(lib, repo, tmp_path):
    """Lockfile has artifact but source_path no longer exists in registry."""
    install_root = tmp_path / "install"
    lf = _build_lockfile(lib, repo, install_root)
    # Remove the source dir from the registry
    import shutil
    shutil.rmtree(repo / "synapse" / "skills" / "foo")
    findings = lib["scan"].scan_orphaned(lf, repo)
    keys = [f.artifact for f in findings]
    assert "skill/foo" in keys
    f = next(f for f in findings if f.artifact == "skill/foo")
    assert f.category == "orphaned"
    assert f.severity == "warn"


# ---------- stale ----------

def test_scan_stale_when_latest_resolves_ahead(lib, repo, tmp_path):
    install_root = tmp_path / "install"
    lf = _build_lockfile(lib, repo, install_root)
    # Make a tag at HEAD then advance and stamp lockfile sha to old commit
    _git(["tag", "v2026.05.0"], repo)
    old_sha = _git(["rev-parse", "HEAD"], repo).stdout.strip()
    # advance HEAD past tag
    (repo / "more.txt").write_text("x")
    _git(["add", "."], repo)
    _git(["commit", "-q", "-m", "more"], repo)
    # tag now resolves to old_sha; lockfile claims old_sha — but pin=latest →
    # resolver finds tag's sha == old_sha; lockfile says old_sha → not stale
    # Force "stale" by setting lockfile.synapse_sha to a different sha:
    lf.synapse_sha = "0" * 40  # nonexistent placeholder
    pins = lib["pins"].empty()
    pins.pin = "latest"
    findings = lib["scan"].scan_stale(lf, pins, repo)
    assert any(f.category == "stale" for f in findings)


def test_scan_stale_skips_when_pin_is_tag(lib, repo, tmp_path):
    install_root = tmp_path / "install"
    lf = _build_lockfile(lib, repo, install_root)
    pins = lib["pins"].empty()
    pins.pin = "v2026.05.0"
    findings = lib["scan"].scan_stale(lf, pins, repo)
    assert findings == []


# ---------- pin-rot ----------

def test_pin_rot_old_tag(lib, repo, tmp_path):
    # Create an annotated tag with an old date
    env = os.environ.copy()
    env["GIT_COMMITTER_DATE"] = "2020-01-01T00:00:00"
    env["GIT_AUTHOR_DATE"] = "2020-01-01T00:00:00"
    subprocess.run(
        ["git", "-C", str(repo), "tag", "-a", "v2020.01.0", "-m", "old"],
        check=True, env=env,
    )
    pins = lib["pins"].empty()
    pins.pin = "v2020.01.0"
    findings = lib["scan"].scan_pin_rot(pins, repo, threshold_days=90)
    assert any(f.category == "pin_rot" for f in findings)


def test_pin_rot_fresh_tag_no_finding(lib, repo, tmp_path):
    # Tag at current date
    subprocess.run(
        ["git", "-C", str(repo), "tag", "-a", "v2026.05.0", "-m", "fresh"],
        check=True,
    )
    pins = lib["pins"].empty()
    pins.pin = "v2026.05.0"
    findings = lib["scan"].scan_pin_rot(pins, repo, threshold_days=90)
    assert findings == []


def test_pin_rot_skips_floating(lib, repo):
    pins = lib["pins"].empty()
    pins.pin = "latest"
    findings = lib["scan"].scan_pin_rot(pins, repo)
    assert findings == []


# ---------- submodule-stale ----------

def test_submodule_stale_network_failure_degrades(lib, repo, tmp_path, monkeypatch):
    lf_mod = lib["lockfile"]
    lf = lf_mod.empty()
    lf.externals["some-suite"] = lf_mod.External(
        key="some-suite",
        submodule_path="external/some-suite",
        submodule_sha="a" * 40,
        content_hash="sha256:" + "0" * 64,
        status="installed",
    )

    # Force ls-remote subprocess to fail
    real_run = subprocess.run

    def fake_run(cmd, *args, **kwargs):
        if isinstance(cmd, list) and "ls-remote" in cmd:
            raise subprocess.CalledProcessError(1, cmd, output="", stderr="no network")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", fake_run)
    findings = lib["scan"].scan_submodule_stale(lf, repo)
    assert len(findings) == 1
    assert findings[0].category == "submodule_stale"
    assert findings[0].severity == "info"
    assert "reason" in findings[0].details


def test_submodule_stale_no_externals(lib, repo):
    lf_mod = lib["lockfile"]
    lf = lf_mod.empty()
    findings = lib["scan"].scan_submodule_stale(lf, repo)
    assert findings == []


# ---------- scan_all ----------

def test_scan_all_no_lockfile(lib, repo, tmp_path):
    findings = lib["scan"].scan_all(
        lockfile_path=tmp_path / "missing.lock",
        repo_root=repo,
        pins=None,
    )
    assert len(findings) == 1
    assert findings[0].category == "corrupt"


def test_scan_drift_respects_ignore_exception(lib, repo, tmp_path):
    install_root = tmp_path / "install"
    lf = _build_lockfile(lib, repo, install_root)
    # Drift the source
    (repo / "synapse" / "skills" / "foo" / "SKILL.md").write_text("local edit\n")
    actual = lib["hashing"].hash_directory(repo / "synapse" / "skills" / "foo")
    pins = lib["pins"].empty()
    pins.drift_exceptions["skill/foo"] = lib["pins"].DriftException(
        artifact_key="skill/foo",
        hash=actual,
        reason="ok",
        expires="2099-01-01",
    )
    findings = lib["scan"].scan_drift(lf, repo, pins=pins)
    assert findings == []


def test_scan_drift_expired_exception_re_fires(lib, repo, tmp_path):
    install_root = tmp_path / "install"
    lf = _build_lockfile(lib, repo, install_root)
    (repo / "synapse" / "skills" / "foo" / "SKILL.md").write_text("local edit\n")
    actual = lib["hashing"].hash_directory(repo / "synapse" / "skills" / "foo")
    pins = lib["pins"].empty()
    pins.drift_exceptions["skill/foo"] = lib["pins"].DriftException(
        artifact_key="skill/foo",
        hash=actual,
        reason="stale",
        expires="2000-01-01",
    )
    findings = lib["scan"].scan_drift(lf, repo, pins=pins)
    assert len(findings) == 1
    assert findings[0].category == "drift"


def test_scan_all_clean_fixture(lib, repo, tmp_path):
    # Build a valid lockfile, save it, scan everything, expect no findings
    install_root = tmp_path / "install"
    lf = _build_lockfile(lib, repo, install_root)
    lock_path = tmp_path / "installed.lock"
    lib["lockfile"].save(lf, lock_path)
    pins = lib["pins"].empty()
    pins.pin = "main"  # avoids needing tags
    findings = lib["scan"].scan_all(
        lockfile_path=lock_path,
        repo_root=repo,
        pins=pins,
        skip={"submodule_stale"},  # no externals
    )
    # The clean fixture might still emit pin_rot? main is floating → skipped.
    # stale: lockfile.synapse_sha == HEAD == main → equal → no finding.
    assert findings == [], f"unexpected findings: {findings}"
