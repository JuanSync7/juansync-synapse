"""Clerk bump orchestration: plan and apply external/ submodule bumps.

`plan_bumps` is read-only: it inspects each submodule under external/, queries
upstream for the latest stable tag, and emits a `BumpPlan` per submodule
describing the action (bump / skip-* / abort-*).

`apply_bump` executes a single plan: branch → submodule SHA bump → commit →
push → `gh pr create`. State is updated after a successful bump. Hooks are
NEVER skipped; force-push is NEVER used.

T8 telemetry hook: `_emit_event(...)` is currently a no-op stub. T8 will
plug in a sink (file/HTTP/OTLP) at that single call site without touching
the orchestration flow.
"""
from __future__ import annotations

import datetime
import os
import pathlib
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Literal

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import clerk_auth as _ca
import clerk_state as cs
import clerk_upstream as cu
import telemetry as _telemetry

Action = Literal[
    "bump",
    "skip-up-to-date",
    "skip-no-stable-tag",
    "abort-force-push",
    "abort-dirty",
    "abort-branch-exists",
    "abort-no-auth",
    "error-network",
]


@dataclass
class BumpPlan:
    submodule_path: str
    upstream_url: str
    current_sha: str
    target_tag: str = ""
    target_sha: str = ""
    action: Action = "skip-up-to-date"
    reason: str = ""
    pr_url: str = ""   # filled by apply_bump on success


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------

def _utcnow_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _record_seen(state: cs.ClerkState, submodule_path: str, tag: str, sha: str) -> None:
    """Update state.seen_tags with this (submodule, tag, sha) — only on first sight."""
    by_tag = state.seen_tags.setdefault(submodule_path, {})
    if tag not in by_tag:
        by_tag[tag] = cs.SeenTag(sha=sha, first_seen=_utcnow_iso())


def plan_bumps(
    repo_root: pathlib.Path,
    state: cs.ClerkState,
    *,
    only: str | None = None,
    runner=subprocess.run,
) -> list[BumpPlan]:
    """Build one BumpPlan per submodule under external/ (or just `only`).

    Read-only with one exception: state.seen_tags grows when we observe a
    new (submodule, tag) pairing. This is necessary so the *next* clerk run
    can detect a force-push on this tag. Caller is responsible for saving.
    """
    repo_root = pathlib.Path(repo_root)
    submodules = cu.parse_gitmodules(repo_root)
    if only:
        submodules = {k: v for k, v in submodules.items() if k == only}

    plans: list[BumpPlan] = []
    for sub_path, url in sorted(submodules.items()):
        current_sha = cu.current_submodule_sha(repo_root, sub_path, runner=runner)

        # Discover upstream latest stable tag.
        try:
            top = cu.latest_stable_upstream(url, runner=runner)
        except RuntimeError as e:
            plans.append(BumpPlan(
                submodule_path=sub_path,
                upstream_url=url,
                current_sha=current_sha,
                action="error-network",
                reason=str(e),
            ))
            continue

        if top is None:
            plans.append(BumpPlan(
                submodule_path=sub_path,
                upstream_url=url,
                current_sha=current_sha,
                action="skip-no-stable-tag",
                reason="upstream has no vX.Y.Z stable tags",
            ))
            continue

        # Force-push check BEFORE recording: if state has this tag with a
        # different sha, abort loudly.
        if cu.detect_force_push(state, sub_path, top.tag, top.sha):
            prev = state.seen_tags[sub_path][top.tag].sha
            plans.append(BumpPlan(
                submodule_path=sub_path,
                upstream_url=url,
                current_sha=current_sha,
                target_tag=top.tag,
                target_sha=top.sha,
                action="abort-force-push",
                reason=(
                    f"upstream tag {top.tag!r} sha changed: "
                    f"previously seen {prev}, now {top.sha}"
                ),
            ))
            continue

        # Record observation (first-seen only).
        _record_seen(state, sub_path, top.tag, top.sha)

        if current_sha == top.sha:
            plans.append(BumpPlan(
                submodule_path=sub_path,
                upstream_url=url,
                current_sha=current_sha,
                target_tag=top.tag,
                target_sha=top.sha,
                action="skip-up-to-date",
                reason=f"already at {top.tag}",
            ))
            continue

        plans.append(BumpPlan(
            submodule_path=sub_path,
            upstream_url=url,
            current_sha=current_sha,
            target_tag=top.tag,
            target_sha=top.sha,
            action="bump",
            reason=f"{current_sha[:7]} → {top.sha[:7]} ({top.tag})",
        ))

    return plans


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------

_SLUG_RE = re.compile(r"[^a-z0-9-]+")


def _slug(suite: str) -> str:
    """Last path segment, lowered, sanitized to [a-z0-9-]."""
    base = pathlib.Path(suite).name.lower()
    return _SLUG_RE.sub("-", base).strip("-") or "suite"


def _branch_name(plan: BumpPlan) -> str:
    return f"clerk/bump-{_slug(plan.submodule_path)}-{plan.target_tag.lstrip('v')}"


def _commit_message(plan: BumpPlan) -> str:
    suite = pathlib.Path(plan.submodule_path).name
    return (
        f"chore(external): bump {suite} to {plan.target_tag}\n\n"
        f"was: {plan.current_sha}\n"
        f"now: {plan.target_sha}\n"
        f"upstream: {plan.upstream_url}\n\n"
        f"Generated by cortex clerk.\n"
    )


def render_pr_body(plan: BumpPlan, repo_root: pathlib.Path, *, runner=subprocess.run) -> str:
    """Compose PR body: SHAs, upstream link, diff stat (best-effort), CI note."""
    sub_abs = pathlib.Path(repo_root) / plan.submodule_path
    diffstat = "(unavailable: submodule diff could not be computed)"
    try:
        proc = runner(
            ["git", "-C", str(sub_abs), "diff", "--stat",
             f"{plan.current_sha}..{plan.target_sha}"],
            check=False, capture_output=True, text=True,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            diffstat = proc.stdout.strip()
    except (FileNotFoundError, subprocess.SubprocessError):
        pass

    return (
        f"## Bump `{plan.submodule_path}` to `{plan.target_tag}`\n\n"
        f"- **was:** `{plan.current_sha}`\n"
        f"- **now:** `{plan.target_sha}`\n"
        f"- **upstream:** {plan.upstream_url}\n"
        f"- **tag:** `{plan.target_tag}`\n\n"
        f"### Diff stat\n\n"
        f"```\n{diffstat}\n```\n\n"
        f"---\n"
        f"Gatekeeper certification will run via existing CI.\n\n"
        f"_Generated by `cortex clerk`._\n"
    )


# ---------------------------------------------------------------------------
# Telemetry hook (T8 plugs in here)
# ---------------------------------------------------------------------------

def _emit_event(event_type: str, plan: BumpPlan, *, exit_status: str = "ok",
                metadata: dict | None = None) -> None:
    """T8 telemetry hook — dispatches to the configured sinks.

    Event schema (v1):
        timestamp     str   - ISO8601 UTC, set by telemetry
        event_type    str   - "clerk_bump_planned" | "clerk_bumped"
                              | "clerk_force_push_aborted" | "clerk_dirty_abort"
                              | "clerk_no_auth" | "clerk_branch_exists"
                              | "clerk_network_error"
        artifact      str   - plan.submodule_path
        version       str   - plan.target_tag
        exit_status   str   - "ok" | "error"
        metadata      dict  - {current_sha, target_sha, upstream_url, pr_url?, ...}

    Non-raising: telemetry.emit swallows all exceptions internally.
    """
    md = {
        "current_sha": plan.current_sha,
        "target_sha": plan.target_sha,
        "upstream_url": plan.upstream_url,
        "action": plan.action,
    }
    if plan.pr_url:
        md["pr_url"] = plan.pr_url
    if metadata:
        md.update(metadata)
    _telemetry.emit(
        event_type,
        artifact=plan.submodule_path,
        version=plan.target_tag,
        exit_status=exit_status,
        metadata=md,
    )


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------

def _run(args: list[str], *, cwd: pathlib.Path | None = None,
         runner=subprocess.run, check: bool = True,
         capture: bool = True,
         env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    env = None
    if env_extra:
        env = dict(os.environ)
        env.update(env_extra)
    return runner(
        args,
        cwd=str(cwd) if cwd else None,
        check=check, capture_output=capture, text=True,
        env=env,
    )


def _get_auth_adapter():
    """Return the active auth adapter (PAT or App) per ~/.synapse/config.toml.

    T6 replaces the T7-era `_gh_authenticated()` boolean check. The adapter
    returned exposes `get_token()` (raises AuthError if no auth available)
    and `env_for_subprocess()` (vars to inject into git/gh subprocess calls).
    """
    return _ca.get_adapter()


def _branch_exists_remote(repo_root: pathlib.Path, branch: str,
                          runner=subprocess.run) -> bool:
    try:
        proc = runner(
            ["git", "-C", str(repo_root), "ls-remote", "--exit-code",
             "origin", f"refs/heads/{branch}"],
            check=False, capture_output=True, text=True,
        )
    except FileNotFoundError:
        return False
    return proc.returncode == 0


def _submodule_dirty(repo_root: pathlib.Path, sub_path: str,
                     runner=subprocess.run) -> bool:
    sub_abs = pathlib.Path(repo_root) / sub_path
    if not sub_abs.exists():
        return False
    try:
        proc = runner(
            ["git", "-C", str(sub_abs), "status", "--porcelain"],
            check=True, capture_output=True, text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return bool(proc.stdout.strip())


@dataclass
class _ApplyContext:
    repo_root: pathlib.Path
    runner: object


def apply_bump(
    plan: BumpPlan,
    repo_root: pathlib.Path,
    state: cs.ClerkState,
    *,
    runner=subprocess.run,
    state_path: pathlib.Path | None = None,
    pr_base: str = "main",
    auth_adapter=None,
) -> str:
    """Execute a 'bump' plan. Returns PR URL.

    Mutates `plan.action` in place if a precondition fails (auth/dirty/branch),
    so the caller can render an updated plan.

    Steps (no force-push, no skipping hooks):
      1. Verify gh authenticated
      2. Verify submodule clean
      3. Verify branch absent on remote
      4. Create branch from origin/main
      5. Fetch + checkout target_sha inside submodule
      6. Stage submodule path
      7. Commit (hooks run; commit message templated)
      8. Push -u origin <branch>
      9. gh pr create
     10. Update state.bumps + persist state if state_path provided
     11. Checkout main (don't leave caller on the bump branch)

    On failure mid-flow: best-effort `git checkout main`, raise RuntimeError.
    """
    if plan.action != "bump":
        raise RuntimeError(f"apply_bump called with non-bump plan: {plan.action}")

    repo_root = pathlib.Path(repo_root)
    sub_abs = repo_root / plan.submodule_path
    branch = _branch_name(plan)

    # 1. Auth — resolve adapter, fetch token (raises AuthError if no auth).
    if auth_adapter is None:
        try:
            auth_adapter = _get_auth_adapter()
        except _ca.AuthError as e:
            plan.action = "abort-no-auth"
            plan.reason = f"auth adapter init failed: {e}"
            _emit_event("clerk_no_auth", plan, exit_status="error",
                        metadata={"auth_error": str(e)})
            raise RuntimeError(plan.reason) from e
    try:
        auth_result = auth_adapter.get_token()
    except _ca.AuthError as e:
        plan.action = "abort-no-auth"
        plan.reason = f"clerk not authenticated: {e}"
        _emit_event("clerk_no_auth", plan, exit_status="error",
                    metadata={"auth_error": str(e), "auth_mode": getattr(auth_adapter, "cfg", None).__class__.__name__ if hasattr(auth_adapter, "cfg") else ""})
        raise RuntimeError(plan.reason) from e
    auth_env = auth_adapter.env_for_subprocess()

    # 2. Submodule clean
    if _submodule_dirty(repo_root, plan.submodule_path, runner=runner):
        plan.action = "abort-dirty"
        plan.reason = f"submodule {plan.submodule_path} has uncommitted changes"
        _emit_event("clerk_dirty_abort", plan, exit_status="error")
        raise RuntimeError(plan.reason)

    # 3. Branch absent
    if _branch_exists_remote(repo_root, branch, runner=runner):
        plan.action = "abort-branch-exists"
        plan.reason = f"branch {branch} already exists on origin"
        _emit_event("clerk_branch_exists", plan, exit_status="error")
        raise RuntimeError(plan.reason)

    # ------------------- mutations begin -------------------
    pushed = False
    on_branch = False
    try:
        # 4. Create branch from origin/main
        _run(["git", "-C", str(repo_root), "fetch", "origin", pr_base],
             runner=runner)
        _run(["git", "-C", str(repo_root), "checkout", "-B", branch,
              f"origin/{pr_base}"], runner=runner)
        on_branch = True

        # 5. Fetch + checkout target_sha inside submodule
        _run(["git", "-C", str(sub_abs), "fetch", "origin",
              f"refs/tags/{plan.target_tag}:refs/tags/{plan.target_tag}"],
             runner=runner, check=False)   # tag may already exist locally
        _run(["git", "-C", str(sub_abs), "checkout", plan.target_sha],
             runner=runner)

        # 6. Stage submodule path (gitlink)
        _run(["git", "-C", str(repo_root), "add", "--", plan.submodule_path],
             runner=runner)

        # 7. Commit
        _run(["git", "-C", str(repo_root), "commit", "-m", _commit_message(plan)],
             runner=runner)

        # 8. Push (no --force, ever) — inject auth env if adapter provides one
        _run(["git", "-C", str(repo_root), "push", "-u", "origin", branch],
             runner=runner, env_extra=auth_env)
        pushed = True

        # 9. gh pr create — inject auth env so installation tokens reach gh
        body = render_pr_body(plan, repo_root, runner=runner)
        title = f"chore(external): bump {pathlib.Path(plan.submodule_path).name} to {plan.target_tag}"
        proc = _run(
            ["gh", "pr", "create",
             "--base", pr_base, "--head", branch,
             "--title", title, "--body", body],
            cwd=repo_root, runner=runner, env_extra=auth_env,
        )
        # gh prints the PR URL on stdout
        pr_url = (proc.stdout or "").strip().splitlines()[-1] if proc.stdout else ""
        plan.pr_url = pr_url

        # 10. Update state
        state.bumps[plan.submodule_path] = cs.BumpRecord(
            last_bumped_at=_utcnow_iso(),
            last_pr_url=pr_url,
            last_bumped_to=plan.target_tag,
        )
        # ensure seen_tags has this entry
        _record_seen(state, plan.submodule_path, plan.target_tag, plan.target_sha)
        if state_path is not None:
            cs.save(state, state_path)

        _emit_event("clerk_bumped", plan, exit_status="ok",
                    metadata={"pr_url": pr_url})
        return pr_url

    except subprocess.CalledProcessError as e:
        _emit_event("clerk_bumped", plan, exit_status="error",
                    metadata={"stderr": (e.stderr or "")[:500]})
        # Best-effort cleanup: drop back to base branch.
        if on_branch and not pushed:
            try:
                _run(["git", "-C", str(repo_root), "checkout", pr_base],
                     runner=runner, check=False)
            except Exception:
                pass
        raise RuntimeError(
            f"apply_bump failed: {' '.join(e.cmd)}: "
            f"exit={e.returncode} stderr={(e.stderr or '').strip()[:300]}"
        ) from e
    finally:
        # 11. Always try to leave the user on the base branch.
        if on_branch:
            try:
                _run(["git", "-C", str(repo_root), "checkout", pr_base],
                     runner=runner, check=False)
            except Exception:
                pass
