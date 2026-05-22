# cortex clerk

Automated `external/` submodule bump loop. The clerk runs (typically on a per-machine cron) to detect when an upstream `external/<suite>` repo has shipped a new stable tag, then opens a PR bumping the submodule SHA.

## Subcommands

| Subcommand | Doc |
|------------|-----|
| [`clerk bump-externals`](clerk-bump-externals.md) | Detect upstream tags; dry-run by default |
| [`clerk status`](clerk-status.md) | Summarize `~/.synapse/clerk_state.toml` |
| [`clerk doctor`](clerk-doctor.md) | Clerk-specific self checks |
| [`clerk auth`](clerk-auth.md) | Manage clerk auth (PAT / GitHub App) |

## Safety model

The clerk runs without human supervision, so the safety surface is conservative:

1. **Dry-run by default.** `bump-externals` prints a plan and exits. Only `--apply` mutates remote state (push, open PR). A buggy clerk on a cron should not be able to spam PRs.
2. **Force-push abort.** Clerk records every `(submodule, tag) → SHA` it has seen. If an upstream tag's SHA changes while keeping its name (force-push or tag move), clerk **aborts** that submodule with `abort-force-push`. It does not bump and does not open a PR — the operator must investigate manually.
3. **Auth gate.** `--apply` refuses to run unless the active [auth adapter](clerk-auth.md) can produce credentials. PAT mode looks for a token in `$SYNAPSE_CLERK_TOKEN` (or whatever env var is configured), then falls back to ambient `gh auth status`. App mode mints an installation token from a configured GitHub App + private key.
4. **Dirty-tree refuse.** If a submodule has uncommitted changes, clerk refuses to bump it. The operator's in-flight work is never silently overwritten.
5. **Idempotency.** If the bump branch already exists on `origin`, clerk skips that submodule (it assumes a previous run already opened the PR).
6. **No history rewriting.** Clerk never calls `git push --force` and never skips commit hooks.

## Stable tag definition

A "stable" upstream tag is `vX.Y.Z` with no `-` suffix. Pre-release tags (`v1.0.0-pre.1`) are ignored. Annotated tags are dereferenced to their commit SHA via the `^{}` suffix in `git ls-remote` output.

## State file

`~/.synapse/clerk_state.toml` (per-machine, not project-scoped). Records:

- `seen_tags.<submodule>.<tag>` — first-time SHA observed for each upstream tag (basis for force-push detection).
- `bumps.<submodule>` — last bump timestamp, target tag, and PR URL.

Only the running clerk should modify this file.

## Telemetry

Clerk dispatches events to the configured telemetry sinks via `clerk_bump._emit_event`. Event types: `clerk_bump_planned`, `clerk_bumped`, `clerk_force_push_aborted`, `clerk_dirty_abort`, `clerk_no_auth`, `clerk_branch_exists`, `clerk_network_error`. See [`telemetry`](telemetry.md) for sink configuration.
