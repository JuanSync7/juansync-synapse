# cortex codex

Install skill symlinks to Codex CLI (global).

## Usage

```
./cortex codex <targets...>
```

## Description

Creates symlinks from `~/.codex/skills/` to skill directories in the repo. Works identically to `cortex install` but targets the Codex CLI global skills directory. Use `cortex codex-project` instead if you want to install to the current project's `.agents/skills/` directory. The target directory can be overridden via the `CODEX_SKILLS_DIR` environment variable.

## Examples

```bash
./cortex codex all                        # install all skills to Codex global
./cortex codex synapse/skills/skill       # install skill-domain skills
```

## Options

| Argument | Description |
|----------|-------------|
| `all` | Install all skills from both `src/` and `external/` |
| `<path>` | One or more paths relative to the repo root |

## Related

- [`cortex install`](install.md)
- [`cortex gemini`](gemini.md)
