# cortex drift show

Show a unified diff between a drifted artifact's source tree and the lockfile sha.

## Usage

```
./cortex drift show <artifact> [--json]
```

## Description

Walks the artifact's `source_path` and compares each file against the same path in `git show <synapse_sha>:<path>`. Files excluded by `hashing.py` (e.g. `EVAL.md`, `change_requests/`, `*.pyc`) are also excluded here. Binary files are reported as `binary differs` rather than diffed.

`<artifact>` may be the canonical lockfile key (`skill/foo`) or the bare name (`foo`).

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | No drift |
| 1 | Drift present |
| 2 | Error (unknown artifact, ambiguous name, missing lockfile) |

## Options

| Flag | Description |
|------|-------------|
| `--json` | Emit `{key, files: [{path, status, diff, binary}]}` instead of human-readable output |

## Examples

```bash
./cortex drift show skill/foo
./cortex drift show foo --json | jq .files
```

## Related

- [`cortex drift adopt`](drift-adopt.md)
- [`cortex drift stash`](drift-stash.md)
