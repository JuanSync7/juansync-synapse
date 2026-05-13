# cortex drift stash

Save the current source tree of a drifted artifact to `~/.synapse/stash/` and restore canonical state via `git checkout`.

## Usage

```
./cortex drift stash <artifact> [--reason TEXT]
```

## Description

Copies the entire `source_path` tree (including untracked files added during the drift) to `~/.synapse/stash/<UTC-timestamp>-<sanitized-key>/payload/`. Writes a `STASH_META.toml` capturing artifact key, source path, timestamp, reason, and pre/post hashes.

After staging, `git checkout -- <source_path>` restores tracked files and `git clean -fd -- <source_path>` removes untracked additions, leaving the source tree at the canonical state recorded by the lockfile.

Stashes always live under `~/.synapse/stash/` regardless of project scope — they are user-machine local.

## Options

| Flag | Description |
|------|-------------|
| `--reason TEXT` | Free-form note recorded in `STASH_META.toml` |

## Recovery

Use `cortex drift restore <stash-id> [--yes]` where `<stash-id>` is the timestamp folder name printed by `stash`.

## Related

- [`cortex drift restore`](drift-restore.md)
- [`cortex drift list-stashes`](drift-list-stashes.md)
- [`cortex drift adopt`](drift-adopt.md) — preserve drift instead of throwing it away
