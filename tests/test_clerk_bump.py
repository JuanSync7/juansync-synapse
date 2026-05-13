"""Tests for scripts/lib/clerk_bump.py.

Heavy use of subprocess injection (`runner=`) — no real network or git
operations. The `apply_bump` test mocks every shell call; we don't spin up
a real upstream remote here (the dry-run path is tested instead).
"""
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
def mods():
    sys.path.insert(0, str(LIB_DIR))
    for n in ("clerk_bump", "clerk_state", "clerk_upstream", "clerk_auth",
              "clerk_auth_config"):
        if n in sys.modules:
            del sys.modules[n]
    cb = importlib.import_module("clerk_bump")
    cs = importlib.import_module("clerk_state")
    cu = importlib.import_module("clerk_upstream")
    yield cb, cs, cu
    sys.path.remove(str(LIB_DIR))


class _FakeAuthAdapter:
    """Minimal stand-in for clerk_auth.PatAuthAdapter / AppAuthAdapter."""
    def __init__(self, *, authenticated: bool = True, env: dict | None = None):
        self._auth = authenticated
        self._env = env or {}

    def get_token(self):
        if not self._auth:
            from clerk_auth import AuthError
            raise AuthError("test: not authenticated")
        from clerk_auth import AuthResult
        return AuthResult(mode="pat", token="test-token", auth_user="test")

    def is_authenticated(self):
        return self._auth

    def env_for_subprocess(self):
        return dict(self._env)


def _proc(stdout: str = "", returncode: int = 0, stderr: str = ""):
    p = MagicMock()
    p.stdout = stdout
    p.stderr = stderr
    p.returncode = returncode
    return p


def _make_repo(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a fake repo root with .gitmodules referencing one external/ submodule."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".gitmodules").write_text(textwrap.dedent("""
        [submodule "foo"]
            path = external/foo
            url = https://example.invalid/x/foo.git
    """).strip())
    (repo / "external" / "foo").mkdir(parents=True)
    return repo


# ---------------------------------------------------------------------------
# plan_bumps
# ---------------------------------------------------------------------------

def _make_runner(submodule_sha: str, ls_remote_lines: list[str]):
    """Build a runner that returns canned ls-remote and submodule-status outputs."""
    def runner(args, **kw):
        if args[0:2] == ["git", "ls-remote"]:
            return _proc("\n".join(ls_remote_lines) + "\n")
        # git -C <path> submodule status -- <path>
        if "submodule" in args and "status" in args:
            return _proc(f" {submodule_sha} external/foo (heads/main)\n")
        # diff --stat (used by render_pr_body, harmless here)
        if "diff" in args and "--stat" in args:
            return _proc(" 1 file changed\n")
        # default OK
        return _proc("")
    return runner


def test_plan_no_op_when_up_to_date(mods, tmp_path):
    cb, cs, _cu = mods
    repo = _make_repo(tmp_path)
    sha = "1" * 40
    runner = _make_runner(
        submodule_sha=sha,
        ls_remote_lines=[f"{sha}\trefs/tags/v1.0.0"],
    )
    state = cs.empty()
    plans = cb.plan_bumps(repo, state, runner=runner)
    assert len(plans) == 1
    assert plans[0].action == "skip-up-to-date"
    assert plans[0].target_tag == "v1.0.0"
    # Observed tag recorded in state
    assert state.seen_tags["external/foo"]["v1.0.0"].sha == sha


def test_plan_bump_when_behind(mods, tmp_path):
    cb, cs, _ = mods
    repo = _make_repo(tmp_path)
    runner = _make_runner(
        submodule_sha="0" * 40,
        ls_remote_lines=[
            f"{'1'*40}\trefs/tags/v1.0.0",
            f"{'2'*40}\trefs/tags/v2.0.0",
        ],
    )
    state = cs.empty()
    plans = cb.plan_bumps(repo, state, runner=runner)
    assert len(plans) == 1
    p = plans[0]
    assert p.action == "bump"
    assert p.target_tag == "v2.0.0"
    assert p.target_sha == "2" * 40
    assert p.current_sha == "0" * 40


def test_plan_force_push_abort(mods, tmp_path):
    cb, cs, _ = mods
    repo = _make_repo(tmp_path)
    # State already records v1.0.0 = aaaa..., but upstream now reports bbbb...
    state = cs.empty()
    state.seen_tags["external/foo"] = {
        "v1.0.0": cs.SeenTag(sha="a" * 40, first_seen="t"),
    }
    runner = _make_runner(
        submodule_sha="a" * 40,
        ls_remote_lines=[f"{'b'*40}\trefs/tags/v1.0.0"],
    )
    plans = cb.plan_bumps(repo, state, runner=runner)
    assert len(plans) == 1
    assert plans[0].action == "abort-force-push"
    assert "force" in plans[0].reason.lower() or "sha changed" in plans[0].reason.lower()
    # We must NOT overwrite the prior seen-record on a force-push.
    assert state.seen_tags["external/foo"]["v1.0.0"].sha == "a" * 40


def test_plan_no_stable_tag(mods, tmp_path):
    cb, cs, _ = mods
    repo = _make_repo(tmp_path)
    runner = _make_runner(
        submodule_sha="0" * 40,
        ls_remote_lines=[f"{'1'*40}\trefs/tags/v1.0.0-pre.1"],
    )
    state = cs.empty()
    plans = cb.plan_bumps(repo, state, runner=runner)
    assert plans[0].action == "skip-no-stable-tag"


def test_plan_network_error(mods, tmp_path):
    cb, cs, _ = mods
    repo = _make_repo(tmp_path)

    def runner(args, **kw):
        if args[0:2] == ["git", "ls-remote"]:
            raise subprocess.CalledProcessError(128, args, stderr="no network")
        if "submodule" in args and "status" in args:
            return _proc(f" {'0'*40} external/foo\n")
        return _proc("")

    state = cs.empty()
    plans = cb.plan_bumps(repo, state, runner=runner)
    assert plans[0].action == "error-network"
    assert "ls-remote failed" in plans[0].reason


def test_plan_only_filter(mods, tmp_path):
    cb, cs, _ = mods
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".gitmodules").write_text(textwrap.dedent("""
        [submodule "foo"]
            path = external/foo
            url = https://example.invalid/foo.git
        [submodule "bar"]
            path = external/bar
            url = https://example.invalid/bar.git
    """).strip())
    runner = _make_runner(
        submodule_sha="0" * 40,
        ls_remote_lines=[f"{'1'*40}\trefs/tags/v1.0.0"],
    )
    plans = cb.plan_bumps(repo, cs.empty(), only="external/foo", runner=runner)
    assert [p.submodule_path for p in plans] == ["external/foo"]


# ---------------------------------------------------------------------------
# Slug + branch + commit-message helpers
# ---------------------------------------------------------------------------

def test_branch_name_strips_leading_v(mods):
    cb, _, _ = mods
    plan = cb.BumpPlan(
        submodule_path="external/Some-Suite",
        upstream_url="u", current_sha="0"*40,
        target_tag="v1.4.7", target_sha="1"*40, action="bump",
    )
    assert cb._branch_name(plan) == "clerk/bump-some-suite-1.4.7"


def test_commit_message_shape(mods):
    cb, _, _ = mods
    plan = cb.BumpPlan(
        submodule_path="external/foo",
        upstream_url="https://example/foo.git",
        current_sha="a"*40, target_tag="v1.0.0", target_sha="b"*40,
        action="bump",
    )
    msg = cb._commit_message(plan)
    assert msg.startswith("chore(external): bump foo to v1.0.0")
    assert "was: " + "a"*40 in msg
    assert "now: " + "b"*40 in msg
    assert "Generated by cortex clerk." in msg


def test_render_pr_body(mods, tmp_path):
    cb, _, _ = mods
    plan = cb.BumpPlan(
        submodule_path="external/foo",
        upstream_url="https://example/foo.git",
        current_sha="a"*40, target_tag="v1.0.0", target_sha="b"*40,
        action="bump",
    )
    body = cb.render_pr_body(plan, tmp_path,
                             runner=lambda *a, **kw: _proc(" 2 files changed\n"))
    assert "external/foo" in body
    assert "v1.0.0" in body
    assert "Gatekeeper certification" in body
    assert "2 files changed" in body


# ---------------------------------------------------------------------------
# apply_bump preconditions
# ---------------------------------------------------------------------------

def test_apply_bump_refuses_when_not_bump(mods, tmp_path):
    cb, cs, _ = mods
    plan = cb.BumpPlan(
        submodule_path="external/foo", upstream_url="u",
        current_sha="0"*40, action="skip-up-to-date",
    )
    with pytest.raises(RuntimeError, match="non-bump"):
        cb.apply_bump(plan, tmp_path, cs.empty(), runner=lambda *a, **kw: _proc(""))


def test_apply_bump_aborts_no_auth(mods, tmp_path):
    cb, cs, _ = mods
    repo = _make_repo(tmp_path)
    plan = cb.BumpPlan(
        submodule_path="external/foo", upstream_url="u",
        current_sha="0"*40, target_tag="v1.0.0", target_sha="1"*40,
        action="bump",
    )

    def runner(args, **kw):
        return _proc("")

    auth = _FakeAuthAdapter(authenticated=False)
    with pytest.raises(RuntimeError, match="not authenticated"):
        cb.apply_bump(plan, repo, cs.empty(), runner=runner, auth_adapter=auth)
    assert plan.action == "abort-no-auth"


def test_apply_bump_aborts_dirty(mods, tmp_path):
    cb, cs, _ = mods
    repo = _make_repo(tmp_path)
    plan = cb.BumpPlan(
        submodule_path="external/foo", upstream_url="u",
        current_sha="0"*40, target_tag="v1.0.0", target_sha="1"*40,
        action="bump",
    )

    def runner(args, **kw):
        if args[0] == "git" and "status" in args and "--porcelain" in args:
            return _proc(" M somefile\n", returncode=0)
        return _proc("")

    with pytest.raises(RuntimeError, match="uncommitted"):
        cb.apply_bump(plan, repo, cs.empty(), runner=runner,
                      auth_adapter=_FakeAuthAdapter())
    assert plan.action == "abort-dirty"


def test_apply_bump_aborts_branch_exists(mods, tmp_path):
    cb, cs, _ = mods
    repo = _make_repo(tmp_path)
    plan = cb.BumpPlan(
        submodule_path="external/foo", upstream_url="u",
        current_sha="0"*40, target_tag="v1.0.0", target_sha="1"*40,
        action="bump",
    )

    def runner(args, **kw):
        if "status" in args and "--porcelain" in args:
            return _proc("", returncode=0)
        if "ls-remote" in args and "--exit-code" in args:
            return _proc(f"{'1'*40}\trefs/heads/clerk/bump-foo-1.0.0\n", returncode=0)
        return _proc("")

    with pytest.raises(RuntimeError, match="already exists"):
        cb.apply_bump(plan, repo, cs.empty(), runner=runner,
                      auth_adapter=_FakeAuthAdapter())
    assert plan.action == "abort-branch-exists"


def test_apply_bump_happy_path_records_state(mods, tmp_path):
    cb, cs, _ = mods
    repo = _make_repo(tmp_path)
    plan = cb.BumpPlan(
        submodule_path="external/foo", upstream_url="u",
        current_sha="0"*40, target_tag="v1.0.0", target_sha="1"*40,
        action="bump",
    )

    def runner(args, **kw):
        if args[:2] == ["gh", "pr"]:
            return _proc("https://github.com/o/r/pull/42\n", returncode=0)
        if "status" in args and "--porcelain" in args:
            return _proc("", returncode=0)
        if "ls-remote" in args and "--exit-code" in args:
            return _proc("", returncode=2)   # not found
        return _proc("")

    state = cs.empty()
    state_path = tmp_path / "clerk_state.toml"
    pr_url = cb.apply_bump(plan, repo, state, runner=runner, state_path=state_path,
                           auth_adapter=_FakeAuthAdapter())
    assert pr_url == "https://github.com/o/r/pull/42"
    assert state.bumps["external/foo"].last_pr_url == pr_url
    assert state.bumps["external/foo"].last_bumped_to == "v1.0.0"
    assert state.seen_tags["external/foo"]["v1.0.0"].sha == "1" * 40
    assert state_path.exists()
    # Reload to confirm persistence
    s2 = cs.load(state_path)
    assert s2.bumps["external/foo"].last_bumped_to == "v1.0.0"
