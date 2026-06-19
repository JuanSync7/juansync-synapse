# cortex install

Install skill symlinks to Claude Code.

## Usage

```
./cortex install [--force] <targets...>
```

## Description

Creates symlinks from `~/.claude/skills/` to skill directories in the repo. Each target is a path relative to the repo root (e.g., `src/skills/docs`) or the keyword `all` to install every skill found in `src/` and `external/`. Existing symlinks pointing to the same target are skipped. Broken symlinks are automatically repaired. Name collisions with skills from other sources are warned about but not overwritten.

`--force` discards any local edits to the matching source paths via `git checkout -- <source_path> && git clean -fd -- <source_path>` before re-symlinking. With no target (or `all`), `--force` restores every artifact path recorded in the lockfile. With an explicit target, only that path is restored. `--force` is a source-tree concept and is not passed through to harness-specific install paths (Codex, Gemini).

The target directory defaults to `~/.claude/skills/` and can be overridden via the `CLAUDE_SKILLS_DIR` environment variable.

## Examples

```bash
./cortex install all                                        # install every skill
./cortex install src/skills/docs                            # install all skills in the docs domain
./cortex install src/skills/docs src/skills/code/code-build-planner # install specific domains/skills
./cortex install external/jira-suite                        # install skills from an external suite
```

## Options

| Argument | Description |
|----------|-------------|
| `all` | Install all skills from both `src/` and `external/` |
| `<path>` | One or more paths relative to the repo root to search for `SKILL.md` files |
| `--force` | Discard local edits in matching source paths before reinstall |

## Related

- [`cortex codex`](codex.md)
- [`cortex gemini`](gemini.md)
- [`cortex pathway`](pathway.md)
- [`cortex list`](list.md)
- [`cortex available`](available.md)
