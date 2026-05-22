# cortex drift list-stashes

List all stashes under `~/.synapse/stash/`.

## Usage

```
./cortex drift list-stashes [--json]
```

## Description

Reads each stash's `STASH_META.toml` and prints the artifact key, timestamp, and reason. Use `--json` for machine-readable output.

## Options

| Flag | Description |
|------|-------------|
| `--json` | Emit a JSON array of stash records |

## Related

- [`cortex drift stash`](drift-stash.md)
- [`cortex drift restore`](drift-restore.md)
