# cortex doctor symlinks

Legacy broken-symlink check across all harnesses. Preserved verbatim from the pre-T2 `cortex doctor` behavior.

## Usage

```
./cortex doctor symlinks
```

## Description

Scans all supported harness install paths and reports any broken symlinks (links whose targets no longer exist):

- Claude Code skills — `~/.claude/skills/`
- Claude Code agents — `~/.claude/agents/`
- Codex CLI skills   — `~/.codex/skills/`
- Gemini CLI skills  — `~/.gemini/extensions/ai-synapse/skills/`

Also surfaces uninitialized `external/` git submodules.

## Exit code

Always `0` (informational). The summary line reports the count of broken symlinks. To repair, run `cortex install all`; to remove all symlinks, run `cortex clean`.

## Relationship to `cortex doctor`

This is a strict subset of what `cortex doctor` (no subcommand) checks: the new behavior covers symlink missingness via the `missing` finding category against the lockfile, and untracked symlinks via the `orphaned` category. The `symlinks` subcommand is kept because:

- It works without a lockfile.
- It surfaces uninitialized submodules, which the lockfile-based scan does not (it checks pinned externals against upstream, not initialization state).

If you want both, use `./cortex doctor all`.

## Related

- [`cortex doctor`](doctor.md)
- [`cortex clean`](clean.md)
- [`cortex install`](install.md)
