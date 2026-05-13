# cortex clerk bump-externals

Inspect every `external/<suite>` submodule, query the upstream remote for the latest stable tag, and (with `--apply`) open a PR bumping the submodule SHA.

## Usage

```
cortex clerk bump-externals [--apply] [--only <path>] [--state <path>] [--json]
```

| Flag | Meaning |
|------|---------|
| `--apply` | Actually push branches and open PRs. Without this flag, clerk only prints a plan. |
| `--only <path>` | Limit to a single submodule (e.g. `external/foo`). |
| `--state <path>` | Override state-file location (default: `~/.synapse/clerk_state.toml`). |
| `--json` | Emit machine-readable JSON instead of human-readable plan. |

## Plan actions

| Action | Meaning |
|--------|---------|
| `bump` | Submodule is behind upstream's latest stable tag. With `--apply`, clerk creates a branch and opens a PR. |
| `skip-up-to-date` | Submodule already at upstream's latest stable tag. |
| `skip-no-stable-tag` | Upstream has no `vX.Y.Z` tags. Nothing to bump to. |
| `abort-force-push` | Upstream tag SHA changed since clerk last saw it. Manual investigation required. |
| `abort-dirty` | Submodule working tree has uncommitted changes. |
| `abort-branch-exists` | Bump branch already exists on `origin`. A previous run probably opened the PR. |
| `abort-no-auth` | `gh auth status` failed. Run `gh auth login`. |
| `error-network` | `git ls-remote` against the upstream URL failed. |

## Examples

```bash
# Dry-run all external/ submodules:
cortex clerk bump-externals

# JSON output for cron / dashboard:
cortex clerk bump-externals --json | jq '.plans[] | select(.action == "bump")'

# Apply only a specific suite:
cortex clerk bump-externals --apply --only external/foo
```

## Behavior under `--apply`

For each `bump` plan:

1. Verify `gh auth status` exit 0.
2. Verify submodule working tree clean.
3. Verify branch `clerk/bump-<slug>-<tag>` does not already exist on `origin`.
4. `git fetch origin main`; checkout new branch from `origin/main`.
5. Inside the submodule: fetch the target tag, checkout target SHA.
6. Stage submodule path, commit (hooks run; never `--no-verify`), push `-u origin`.
7. `gh pr create --base main --head <branch>`.
8. Record bump in `~/.synapse/clerk_state.toml` and return to `main`.

On any failure, clerk attempts a best-effort `git checkout main` and reports the error.

## Safety

See [clerk.md](clerk.md) for the full safety model.
