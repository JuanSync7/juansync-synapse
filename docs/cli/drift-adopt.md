# cortex drift adopt

Promote drift to a `change_request/<date>-<author>-<slug>.md` next to the artifact.

## Usage

```
./cortex drift adopt <artifact> [--slug NAME] [--reason TEXT]
```

## Description

Computes a unified text diff between the current source tree and `git show <synapse_sha>:<path>`, then writes it to `<source_path>/change_requests/<YYYY-MM-DD>-<author>-<slug>.md`. The CR includes frontmatter (artifact, status, expected/actual hashes) and per-file diff blocks (capped at 500 lines per file).

`<author>` comes from `git config user.name`, kebab-cased. `<slug>` defaults to `local-drift-<short-hash>` when `--slug` is omitted.

Unlike `stash`, **adopt does not restore canonical state**. The local edits remain in place — adoption promotes them to a tracked CR for review. The next gatekeeper-approved merge or `cortex install` will refresh the lockfile content hash to match.

## Options

| Flag | Description |
|------|-------------|
| `--slug NAME` | CR slug (kebab-cased) |
| `--reason TEXT` | Body paragraph; defaults to `"Drift adopted from local edit."` |

## Output

Prints the CR path and a hint to `git add` and commit it.

## Related

- [`cortex drift show`](drift-show.md)
- [`cortex drift ignore`](drift-ignore.md)
