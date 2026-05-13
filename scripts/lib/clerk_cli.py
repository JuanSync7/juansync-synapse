"""CLI entry point for `cortex clerk`.

Subcommands:
  bump-externals [--apply] [--only PATH] [--state PATH] [--json]
      Default mode is dry-run (prints plan; doesn't push).
  status [--state PATH] [--json]
      Compact summary of clerk state (seen tags + last bumps).
  doctor [--state PATH]
      Clerk-specific self checks: state file parses, gh auth status,
      .gitmodules present, every external/<suite> has at least a
      seen-tag record (or warns "never bumped").

Hard rule: only `--apply` mutates remote state.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
from dataclasses import asdict

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import clerk_auth as ca  # noqa: E402
import clerk_auth_config as cac  # noqa: E402
import clerk_bump as cb  # noqa: E402
import clerk_state as cs  # noqa: E402
import clerk_upstream as cu  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _repo_root() -> pathlib.Path:
    env = os.environ.get("SYNAPSE_REPO_ROOT")
    if env:
        return pathlib.Path(env).expanduser().resolve()
    try:
        out = subprocess.run(
            ["git", "-C", str(_HERE), "rev-parse", "--show-toplevel"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return pathlib.Path.cwd()
    return pathlib.Path(out)


def _state_path(arg: str | None) -> pathlib.Path:
    if arg:
        return pathlib.Path(arg).expanduser().resolve()
    return cs.state_path()


def _action_label(action: str) -> str:
    table = {
        "bump":               "BUMP            ",
        "skip-up-to-date":    "up-to-date      ",
        "skip-no-stable-tag": "no-stable-tag   ",
        "abort-force-push":   "ABORT force-push",
        "abort-dirty":        "ABORT dirty     ",
        "abort-branch-exists":"ABORT branch    ",
        "abort-no-auth":      "ABORT no-auth   ",
        "error-network":      "ERROR network   ",
    }
    return table.get(action, action)


# ---------------------------------------------------------------------------
# bump-externals
# ---------------------------------------------------------------------------

def cmd_bump_externals(args: argparse.Namespace) -> int:
    repo = _repo_root()
    sp = _state_path(args.state)
    state = cs.load(sp)

    plans = cb.plan_bumps(repo, state, only=args.only)

    # Persist any newly-observed seen_tags (planner records these in-place).
    cs.save(state, sp)

    if args.json:
        out = {
            "repo": str(repo),
            "state_path": str(sp),
            "apply": bool(args.apply),
            "plans": [asdict(p) for p in plans],
        }
        # When applying, run each bump and append result.
        if args.apply:
            results = []
            for p in plans:
                if p.action != "bump":
                    results.append({"submodule": p.submodule_path,
                                    "skipped": p.action,
                                    "reason": p.reason})
                    continue
                try:
                    pr = cb.apply_bump(p, repo, state, state_path=sp)
                    results.append({"submodule": p.submodule_path,
                                    "applied": True, "pr_url": pr})
                except RuntimeError as e:
                    results.append({"submodule": p.submodule_path,
                                    "applied": False, "error": str(e)})
            out["results"] = results
        print(json.dumps(out, indent=2, default=str))
        return 0

    # Human output
    print(f"clerk bump-externals  (mode={'APPLY' if args.apply else 'dry-run'})")
    print(f"  repo:  {repo}")
    print(f"  state: {sp}")
    print()
    if not plans:
        print("No external/ submodules found in .gitmodules.")
        return 0

    for p in plans:
        line = (
            f"  [{_action_label(p.action)}] {p.submodule_path:<32s} "
            f"target={p.target_tag or '-':<10s} "
        )
        if p.reason:
            line += f"  ({p.reason})"
        print(line)

    if not args.apply:
        print()
        print("Dry-run only. Re-run with --apply to push branches and open PRs.")
        return 0

    # Apply mode
    print()
    failures = 0
    for p in plans:
        if p.action != "bump":
            continue
        print(f"==> applying {p.submodule_path} → {p.target_tag}")
        try:
            pr = cb.apply_bump(p, repo, state, state_path=sp)
            print(f"   PR opened: {pr}")
        except RuntimeError as e:
            print(f"   FAILED: {e}")
            failures += 1
    return 0 if failures == 0 else 1


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> int:
    sp = _state_path(args.state)
    state = cs.load(sp)

    if args.json:
        out = {
            "state_path": str(sp),
            "schema_version": state.schema_version,
            "submodules": {},
        }
        keys = set(state.seen_tags.keys()) | set(state.bumps.keys())
        for k in sorted(keys):
            out["submodules"][k] = {
                "seen_tags": sorted(state.seen_tags.get(k, {}).keys()),
                "last_bumped_at": getattr(state.bumps.get(k), "last_bumped_at", ""),
                "last_bumped_to": getattr(state.bumps.get(k), "last_bumped_to", ""),
                "last_pr_url": getattr(state.bumps.get(k), "last_pr_url", ""),
            }
        print(json.dumps(out, indent=2))
        return 0

    print(f"clerk state: {sp}")
    if not state.seen_tags and not state.bumps:
        print("  no clerk activity yet")
        return 0

    keys = sorted(set(state.seen_tags.keys()) | set(state.bumps.keys()))
    for k in keys:
        seen = state.seen_tags.get(k, {})
        b = state.bumps.get(k)
        print(f"  {k}")
        print(f"    seen tags: {len(seen)}"
              + (f"  (latest: {sorted(seen.keys())[-1]})" if seen else ""))
        if b:
            print(f"    last bump: {b.last_bumped_to} at {b.last_bumped_at}")
            if b.last_pr_url:
                print(f"    last PR:   {b.last_pr_url}")
        else:
            print("    last bump: (never)")
    return 0


# ---------------------------------------------------------------------------
# doctor (clerk-specific; NOT a full T2 doctor scan)
# ---------------------------------------------------------------------------

def cmd_doctor(args: argparse.Namespace) -> int:
    repo = _repo_root()
    sp = _state_path(args.state)
    issues = 0

    print(f"clerk doctor  (repo={repo}, state={sp})")
    print()

    # 1. State file parses
    try:
        state = cs.load(sp)
        if sp.exists():
            print(f"  [ok]   state file parses (schema_version={state.schema_version})")
        else:
            print(f"  [info] state file does not exist yet (will be created on first run)")
            state = cs.empty()
    except ValueError as e:
        print(f"  [ERROR] state file invalid: {e}")
        issues += 1
        state = cs.empty()

    # 2. Auth (PAT or App)
    _doctor_report_auth(probe=getattr(args, "probe_auth", False))

    # 3. .gitmodules
    submodules = cu.parse_gitmodules(repo)
    if not submodules:
        print("  [info] no external/ submodules registered in .gitmodules")
    else:
        print(f"  [ok]   {len(submodules)} external/ submodule(s) in .gitmodules")
        for path in sorted(submodules.keys()):
            seen = state.seen_tags.get(path, {})
            bump = state.bumps.get(path)
            if not seen and not bump:
                print(f"    [warn] {path}: never observed by clerk (run bump-externals)")
            else:
                last_tag = bump.last_bumped_to if bump else "(seen only, never bumped)"
                print(f"    [ok]   {path}: last_bumped_to={last_tag}")

    return 0 if issues == 0 else 1


# ---------------------------------------------------------------------------
# auth subcommands (T6)
# ---------------------------------------------------------------------------

def _doctor_report_auth(*, probe: bool = False) -> None:
    """Print clerk's auth status. Never prints token values.

    Without `probe`, App mode only validates that config + key file are
    present — does NOT mint a token (would consume GitHub rate limit).
    """
    try:
        cfg = cac.load()
    except ValueError as e:
        print(f"  [ERROR] auth config invalid: {e}")
        return

    if cfg.auth == "pat":
        token_env = cfg.pat.token_env
        if os.environ.get(token_env, "").strip():
            print(f"  [ok]   auth: PAT — token from ${token_env}")
            return
        # Check ambient gh
        ok, user = ca._gh_auth_status_user()
        if ok:
            label = f"({user})" if user else ""
            print(f"  [ok]   auth: PAT — gh CLI ambient {label}".rstrip())
        else:
            print(f"  [warn] auth: PAT — NOT AUTHENTICATED "
                  f"(set ${token_env} or run `gh auth login`)")
        return

    # App mode
    if cfg.app is None:
        print("  [ERROR] auth: App mode but [clerk.app] not configured")
        return
    key_present = cfg.app.private_key_path.exists()
    if not key_present:
        print(f"  [warn] auth: App — private key missing at "
              f"{cfg.app.private_key_path}")
        return
    if not probe:
        print(f"  [ok]   auth: App — app_id={cfg.app.app_id} "
              f"installation_id={cfg.app.installation_id} (config valid; "
              f"--probe-auth to mint a real token)")
        return
    # Probe: actually mint a token
    try:
        adapter = ca.AppAuthAdapter(cfg.app)
        result = adapter.get_token()
        print(f"  [ok]   auth: App — app_id={cfg.app.app_id} "
              f"(token expires {result.expires_at})")
    except ca.AuthError as e:
        print(f"  [ERROR] auth: App — NOT AUTHENTICATED — {e}")


def cmd_auth_show(args: argparse.Namespace) -> int:
    cfg = cac.load()
    if args.json:
        out = {
            "auth": cfg.auth,
            "config_path": str(cac.config_path()),
            "pat": {"token_env": cfg.pat.token_env},
            "app": (
                {
                    "app_id": cfg.app.app_id,
                    "installation_id": cfg.app.installation_id,
                    "private_key_path": str(cfg.app.private_key_path),
                }
                if cfg.app else None
            ),
        }
        print(json.dumps(out, indent=2))
        return 0
    print(f"clerk auth config: {cac.config_path()}")
    print(f"  auth     = {cfg.auth!r}")
    print(f"  pat.token_env = {cfg.pat.token_env!r}  "
          f"(value NOT shown for security)")
    if cfg.app is not None:
        print(f"  app.app_id          = {cfg.app.app_id!r}")
        print(f"  app.installation_id = {cfg.app.installation_id!r}")
        print(f"  app.private_key_path = {cfg.app.private_key_path}")
    else:
        print("  app: (not configured)")
    return 0


def cmd_auth_set_mode(args: argparse.Namespace) -> int:
    if args.mode not in ("pat", "app"):
        print(f"error: mode must be 'pat' or 'app', got {args.mode!r}",
              file=sys.stderr)
        return 2

    cfg = cac.load()
    cfg.auth = args.mode
    if args.token_env:
        cfg.pat.token_env = args.token_env
    if args.mode == "app":
        # Build/update app config
        existing = cfg.app
        app_id = args.app_id or (existing.app_id if existing else None)
        iid = args.installation_id or (existing.installation_id if existing else None)
        keyp = (
            pathlib.Path(os.path.expanduser(args.private_key_path))
            if args.private_key_path
            else (existing.private_key_path if existing else None)
        )
        missing = []
        if not app_id: missing.append("--app-id")
        if not iid: missing.append("--installation-id")
        if not keyp: missing.append("--private-key-path")
        if missing:
            print(
                "error: app mode requires " + ", ".join(missing)
                + " (or pre-existing [clerk.app] in the config file)",
                file=sys.stderr,
            )
            return 2
        cfg.app = cac.AppConfig(
            app_id=str(app_id),
            installation_id=str(iid),
            private_key_path=keyp,
        )

    cac.save(cfg, cac.config_path())
    print(f"clerk auth mode set to {cfg.auth!r}; config: {cac.config_path()}")
    return 0


def cmd_auth_probe(args: argparse.Namespace) -> int:
    try:
        cfg = cac.load()
    except ValueError as e:
        print(f"error: invalid config: {e}", file=sys.stderr)
        return 1
    try:
        adapter = ca.get_adapter(cfg)
    except ca.AuthError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        result = adapter.get_token()
    except ca.AuthError as e:
        print(f"error: probe failed — {e}", file=sys.stderr)
        return 1

    # NEVER print the token itself.
    print(f"clerk auth probe: OK")
    print(f"  mode      = {result.mode}")
    print(f"  auth_user = {result.auth_user}")
    if result.expires_at:
        print(f"  expires_at = {result.expires_at}")
    return 0


# ---------------------------------------------------------------------------
# Argparse wiring
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cortex clerk")
    sub = p.add_subparsers(dest="cmd", required=True)

    bp = sub.add_parser("bump-externals",
                        help="Detect and (optionally) apply submodule bumps")
    bp.add_argument("--apply", action="store_true",
                    help="Actually push branches and open PRs (default: dry-run)")
    bp.add_argument("--only", default=None,
                    help="Limit to a single submodule path (e.g. external/foo)")
    bp.add_argument("--state", default=None,
                    help=f"State file path (default: {cs.state_path()})")
    bp.add_argument("--json", action="store_true",
                    help="Emit machine-readable JSON")
    bp.set_defaults(func=cmd_bump_externals)

    sp = sub.add_parser("status",
                        help="Summarize clerk state (per submodule)")
    sp.add_argument("--state", default=None)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_status)

    dp = sub.add_parser("doctor",
                        help="Clerk-self checks (state file, gh auth, .gitmodules)")
    dp.add_argument("--state", default=None)
    dp.add_argument("--probe-auth", action="store_true",
                    help="Actually mint an App-mode token (consumes GitHub rate limit)")
    dp.set_defaults(func=cmd_doctor)

    # auth ----------------------------------------------------------------
    ap = sub.add_parser("auth", help="Manage clerk auth config (PAT / App)")
    asub = ap.add_subparsers(dest="auth_cmd", required=True)

    ash = asub.add_parser("show", help="Print clerk auth config (no token values)")
    ash.add_argument("--json", action="store_true")
    ash.set_defaults(func=cmd_auth_show)

    asm = asub.add_parser("set-mode",
                          help="Set auth mode to 'pat' or 'app' (writes config file)")
    asm.add_argument("mode", choices=["pat", "app"])
    asm.add_argument("--token-env", default=None,
                     help="Env var name for PAT token (default: SYNAPSE_CLERK_TOKEN)")
    asm.add_argument("--app-id", default=None,
                     help="GitHub App ID (required for first-time set-mode app)")
    asm.add_argument("--installation-id", default=None,
                     help="Installation ID (required for first-time set-mode app)")
    asm.add_argument("--private-key-path", default=None,
                     help="Path to RSA private key (required for first-time set-mode app)")
    asm.set_defaults(func=cmd_auth_set_mode)

    apr = asub.add_parser("probe",
                          help="Probe current auth (PAT: env/ambient; App: mint a token)")
    apr.set_defaults(func=cmd_auth_probe)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
