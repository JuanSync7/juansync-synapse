"""CLI entry point for `cortex drift <subcommand>`.

Subcommands:
  show <artifact> [--json]
  stash <artifact> [--reason TEXT]
  restore <stash-id> [--yes]
  list-stashes [--json]
  adopt <artifact> [--slug NAME] [--reason TEXT]
  ignore <artifact> [--reason TEXT] [--expires DATE]

Exit codes:
  0 ok
  1 drift present (`show`) / user declined (`restore`)
  2 error
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import drift_diff as dd_mod  # noqa: E402
import drift_resolve as dr_mod  # noqa: E402
import lockfile as lf_mod  # noqa: E402
import synapse_paths  # noqa: E402
import telemetry as _telemetry  # noqa: E402

PINS_FILENAME = "pins.toml"


def _repo_root() -> pathlib.Path:
    env = os.environ.get("SYNAPSE_REPO_ROOT")
    if env:
        return pathlib.Path(env).expanduser().resolve()
    out = subprocess.run(
        ["git", "-C", str(_HERE), "rev-parse", "--show-toplevel"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return pathlib.Path(out)


def _load_lockfile() -> lf_mod.Lockfile:
    return lf_mod.load(synapse_paths.lockfile_path())


def _resolve(raw: str) -> tuple[str, lf_mod.Lockfile, pathlib.Path]:
    lf = _load_lockfile()
    key = dr_mod.resolve_key(raw, lf)
    return key, lf, _repo_root()


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------

def cmd_show(args) -> int:
    try:
        key, lf, repo_root = _resolve(args.artifact)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    art = lf.artifacts[key]
    src = repo_root / art.source_path
    git_sha = lf.synapse_sha or "HEAD"
    diffs = dd_mod.diff_artifact_against_git(src, repo_root, git_sha=git_sha)

    if args.json:
        out = {
            "key": key,
            "files": [{
                "path": d.relpath,
                "status": d.status,
                "diff": d.diff_text,
                "binary": d.binary,
            } for d in diffs],
        }
        print(json.dumps(out, indent=2))
    else:
        print(f"Drift in {key}: {len(diffs)} files differ")
        for d in diffs:
            print(f"\n--- {d.relpath} ({d.status}) ---")
            if d.binary:
                print("binary differs")
            else:
                sys.stdout.write(d.diff_text or "")

    return 0 if not diffs else 1


# ---------------------------------------------------------------------------
# stash
# ---------------------------------------------------------------------------

def cmd_stash(args) -> int:
    try:
        key, lf, repo_root = _resolve(args.artifact)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    try:
        stash_dir = dr_mod.stash_artifact(key, lf, repo_root, reason=args.reason or "")
    except (ValueError, subprocess.CalledProcessError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    _telemetry.emit("drift_stashed", artifact=key,
                    metadata={"stash_dir": str(stash_dir),
                              "reason": args.reason or ""})
    print(
        f"Stashed {key} to {stash_dir}/  "
        f"(use cortex drift restore {stash_dir.name} to recover)"
    )
    return 0


# ---------------------------------------------------------------------------
# restore
# ---------------------------------------------------------------------------

def cmd_restore(args) -> int:
    repo_root = _repo_root()
    try:
        dr_mod.restore_stash(args.stash_id, repo_root, force=args.yes)
    except RuntimeError as e:
        print(f"declined: {e}", file=sys.stderr)
        return 1
    except (ValueError, subprocess.CalledProcessError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    _telemetry.emit("drift_restored", artifact=args.stash_id,
                    metadata={"stash_id": args.stash_id})
    print(f"Restored stash {args.stash_id}")
    return 0


# ---------------------------------------------------------------------------
# list-stashes
# ---------------------------------------------------------------------------

def cmd_list_stashes(args) -> int:
    listing = dr_mod.list_stashes()
    if args.json:
        print(json.dumps(listing, indent=2))
        return 0
    if not listing:
        print("No stashes.")
        return 0
    for s in listing:
        print(
            f"{s.get('stash_id','')}  "
            f"{s.get('artifact','?'):30s}  "
            f"{s.get('stashed_at','?'):20s}  "
            f"reason={s.get('reason','')!r}"
        )
    return 0


# ---------------------------------------------------------------------------
# adopt
# ---------------------------------------------------------------------------

def cmd_adopt(args) -> int:
    try:
        key, lf, repo_root = _resolve(args.artifact)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    try:
        cr_path = dr_mod.adopt_drift(
            key, lf, repo_root,
            slug=args.slug or "",
            reason=args.reason or "",
        )
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    try:
        rel = cr_path.relative_to(repo_root)
    except ValueError:
        rel = cr_path
    _telemetry.emit("drift_adopted", artifact=key,
                    metadata={"change_request": str(rel),
                              "reason": args.reason or ""})
    print(f"Adopted drift in {key} as change_request: {rel}")
    print(f"  hint: review and `git add {rel}` to commit")
    return 0


# ---------------------------------------------------------------------------
# ignore
# ---------------------------------------------------------------------------

def cmd_ignore(args) -> int:
    try:
        key, lf, repo_root = _resolve(args.artifact)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    pins_path = synapse_paths.lockfile_dir() / PINS_FILENAME
    try:
        res = dr_mod.ignore_drift(
            key, lf, repo_root, pins_path,
            reason=args.reason or "",
            expires=args.expires or "",
        )
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    when = args.expires or "indefinitely"
    _telemetry.emit("drift_ignored", artifact=key,
                    metadata={"expires": args.expires or "",
                              "reason": args.reason or ""})
    print(f"Ignored drift in {key} until {when}")
    if res.expires_warning:
        print("  warn: no --expires set — drift exception never auto-clears.",
              file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cortex drift")
    sub = p.add_subparsers(dest="cmd", required=True)

    sh = sub.add_parser("show")
    sh.add_argument("artifact")
    sh.add_argument("--json", action="store_true")
    sh.set_defaults(func=cmd_show)

    st = sub.add_parser("stash")
    st.add_argument("artifact")
    st.add_argument("--reason", default="")
    st.set_defaults(func=cmd_stash)

    rs = sub.add_parser("restore")
    rs.add_argument("stash_id")
    rs.add_argument("--yes", action="store_true")
    rs.set_defaults(func=cmd_restore)

    ls = sub.add_parser("list-stashes")
    ls.add_argument("--json", action="store_true")
    ls.set_defaults(func=cmd_list_stashes)

    ad = sub.add_parser("adopt")
    ad.add_argument("artifact")
    ad.add_argument("--slug", default="")
    ad.add_argument("--reason", default="")
    ad.set_defaults(func=cmd_adopt)

    ig = sub.add_parser("ignore")
    ig.add_argument("artifact")
    ig.add_argument("--reason", default="")
    ig.add_argument("--expires", default="")
    ig.set_defaults(func=cmd_ignore)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
