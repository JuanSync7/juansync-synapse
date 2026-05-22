# cortex drift

Resolve drift — local edits to installed artifact source paths that don't match the lockfile content hash.

## Usage

```
./cortex drift <subcommand> [args...]
```

## Subcommands

| Subcommand | Doc | Description |
|------------|-----|-------------|
| [show](drift-show.md) | Diff a drifted artifact against the lockfile sha |
| [stash](drift-stash.md) | Save local edits and restore canonical state |
| [restore](drift-restore.md) | Restore a previously stashed payload |
| [list-stashes](drift-list-stashes.md) | List entries under `~/.synapse/stash/` |
| [adopt](drift-adopt.md) | Promote drift to a `change_request` markdown file |
| [ignore](drift-ignore.md) | Add a `[drift_exceptions]` entry to `pins.toml` |

## When to use

`cortex doctor` reports a drift finding — pick one of:

- **Throw it away** → `cortex install --force <artifact>`.
- **Save it for later** → `cortex drift stash <artifact>`. Recover with `cortex drift restore <stash-id>`.
- **Promote it** → `cortex drift adopt <artifact>`. Writes a `change_request/<date>-<author>-<slug>.md` next to the artifact for review and commit.
- **Acknowledge it** → `cortex drift ignore <artifact> [--expires DATE]`. Doctor will skip the finding while the exception is valid.

`<artifact>` accepts the canonical lockfile key (`skill/foo`) or the bare name (`foo`); ambiguous bare names error.

## Related

- [`cortex doctor`](doctor.md) — detects drift in the first place
- [`cortex install`](install.md) — `--force` discards drift before reinstall
- [`cortex pin`](pin.md), [`cortex status`](status.md)
