"""CLI entry point for lockfile mutations, invoked from install.sh.

Subcommands:
  path                    Print absolute lockfile path and exit.
  upsert-artifact         Insert/update an artifact entry.
  upsert-external         Insert/update an external submodule entry.
  remove                  Remove an artifact entry.
  remove-external         Remove an external entry.
  stamp                   Refresh top-level metadata (sha, tag, time, etc).

Repo root is resolved via `git rev-parse --show-toplevel` from this file's
location so that the CLI works no matter where the user runs it from.

If `SYNAPSE_LOCKFILE_DISABLE` is set in the environment, every subcommand is
a no-op (path still prints), so install.sh can call us unconditionally.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys

# Make sibling modules importable when invoked as a script.
_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import lockfile as lf_mod  # noqa: E402
import lockfile_update as lu  # noqa: E402
import synapse_paths  # noqa: E402


def _repo_root() -> pathlib.Path:
    """Resolve repo root via git, anchored at this file's directory."""
    out = subprocess.run(
        ["git", "-C", str(_HERE), "rev-parse", "--show-toplevel"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return pathlib.Path(out)


def _disabled() -> bool:
    return bool(os.environ.get("SYNAPSE_LOCKFILE_DISABLE"))


def cmd_path(_args) -> int:
    print(synapse_paths.lockfile_path())
    return 0


def cmd_upsert_artifact(args) -> int:
    if _disabled():
        return 0
    path = synapse_paths.lockfile_path()
    lf = lf_mod.load(path)
    lu.upsert_artifact(
        lf,
        key=args.key,
        type=args.type,
        source_path=args.source_path,
        install_path=args.install_path,
        repo_root=_repo_root(),
    )
    lf_mod.save(lf, path)
    return 0


def cmd_upsert_external(args) -> int:
    if _disabled():
        return 0
    path = synapse_paths.lockfile_path()
    lf = lf_mod.load(path)
    lu.upsert_external(
        lf,
        key=args.key,
        submodule_path=args.submodule_path,
        repo_root=_repo_root(),
    )
    lf_mod.save(lf, path)
    return 0


def cmd_remove(args) -> int:
    if _disabled():
        return 0
    path = synapse_paths.lockfile_path()
    lf = lf_mod.load(path)
    lu.remove_artifact(lf, args.key)
    lf_mod.save(lf, path)
    return 0


def cmd_remove_external(args) -> int:
    if _disabled():
        return 0
    path = synapse_paths.lockfile_path()
    lf = lf_mod.load(path)
    lu.remove_external(lf, args.key)
    lf_mod.save(lf, path)
    return 0


def cmd_stamp(_args) -> int:
    if _disabled():
        return 0
    path = synapse_paths.lockfile_path()
    lf = lf_mod.load(path)
    lu.stamp_metadata(lf, _repo_root())
    lf_mod.save(lf, path)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="lockfile_cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("path").set_defaults(func=cmd_path)

    ua = sub.add_parser("upsert-artifact")
    ua.add_argument("--key", required=True)
    ua.add_argument("--type", required=True)
    ua.add_argument("--source-path", required=True)
    ua.add_argument("--install-path", required=True)
    ua.set_defaults(func=cmd_upsert_artifact)

    ue = sub.add_parser("upsert-external")
    ue.add_argument("--key", required=True)
    ue.add_argument("--submodule-path", required=True)
    ue.set_defaults(func=cmd_upsert_external)

    rm = sub.add_parser("remove")
    rm.add_argument("--key", required=True)
    rm.set_defaults(func=cmd_remove)

    rmx = sub.add_parser("remove-external")
    rmx.add_argument("--key", required=True)
    rmx.set_defaults(func=cmd_remove_external)

    sub.add_parser("stamp").set_defaults(func=cmd_stamp)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
