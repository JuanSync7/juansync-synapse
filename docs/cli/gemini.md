# cortex gemini

Install skill symlinks to Gemini CLI.

## Usage

```
./cortex gemini <targets...>
```

## Description

Creates symlinks from `~/.gemini/extensions/ai-synapse/skills/` to skill directories in the repo. On first use, a `gemini-extension.json` manifest is created in the extension directory so Gemini CLI discovers the skills. The extension directory can be overridden via the `GEMINI_EXT_DIR` environment variable.

## Examples

```bash
./cortex gemini all                       # install all skills to Gemini CLI
./cortex gemini synapse/skills/skill      # install skill-domain skills
```

## Options

| Argument | Description |
|----------|-------------|
| `all` | Install all skills from both `src/` and `external/` |
| `<path>` | One or more paths relative to the repo root |

## Related

- [`cortex install`](install.md)
- [`cortex codex`](codex.md)
