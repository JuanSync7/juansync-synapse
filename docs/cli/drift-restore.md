# cortex drift restore

Restore a stashed source tree back over its `source_path`.

## Usage

```
./cortex drift restore <stash-id> [--yes]
```

## Description

Reads `STASH_META.toml` to find the original `source_path`, then overwrites the current source tree with the stash payload. Confirmation is required: prompts `[y/N]` on a TTY, or fails if stdin is non-interactive (use `--yes`).

`<stash-id>` is either the timestamp folder name printed by `stash`/`list-stashes`, or an absolute path to a stash directory.

The stash is **not** deleted after restore — re-restorable until the user removes it.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Restored |
| 1 | User declined or non-TTY without `--yes` |
| 2 | Error (no such stash, missing meta) |

## Related

- [`cortex drift stash`](drift-stash.md)
- [`cortex drift list-stashes`](drift-list-stashes.md)
