# cortex validate

Run structural checks on artifacts without committing.

## Usage

```
./cortex validate [<path>]
```

## Description

Validates ai-synapse artifacts against structural rules: required frontmatter fields, taxonomy compliance, registry presence, EVAL.md existence, and domain README rows. Can target a specific file, directory, or run against the entire repo. Also detects stale registry entries whose link targets no longer exist on disk. Exits with code 1 if any errors are found.

## Checks Performed

**Skills** (`src/skills/**/SKILL.md`):
- Frontmatter has required fields: `name`, `description`, `domain`, `intent`
- `domain` and `intent` values exist in `taxonomy/SKILL_TAXONOMY.md`
- `EVAL.md` exists alongside `SKILL.md`
- Listed in `registry/SKILL_REGISTRY.md`
- Domain `README.md` has a matching row

**Agents** (`src/agents/**/*.md`):
- Frontmatter has required fields: `name`, `description`, `domain`, `role`
- `domain` and `role` values exist in `taxonomy/AGENT_TAXONOMY.md`
- Listed in `registry/AGENTS_REGISTRY.md`
- Domain `README.md` has a matching row

**Protocols** (`src/protocols/**/*.md`):
- Frontmatter has required fields: `name`, `description`, `domain`, `type`
- `domain` and `type` values exist in `taxonomy/PROTOCOL_TAXONOMY.md`
- Domain `README.md` has a matching row

**Tools** (`src/tools/**/TOOL.md`):
- Frontmatter has required fields: `name`, `description`, `domain`, `action`, `type`
- `domain`, `action`, and `type` values exist in `taxonomy/TOOL_TAXONOMY.md`
- Listed in `registry/TOOL_REGISTRY.md`
- Domain `README.md` has a matching row

**Scripts** (`scripts/*.sh`):
- Comment frontmatter with required fields: `@name`, `@description`, `@audience`, `@action`, `@scope`
- `audience`, `action`, and `scope` values exist in `taxonomy/SCRIPT_TAXONOMY.md`
- Listed in `registry/SCRIPT_REGISTRY.md`

**Stale registry entries**:
- Each registry link points to a file that exists on disk

## Examples

```bash
./cortex validate                                                # validate all artifacts
./cortex validate synapse/skills/skill/skill-creator             # validate one skill (by directory)
./cortex validate synapse/skills/skill/skill-creator/SKILL.md    # validate one skill (by file)
./cortex validate synapse/agents/                                # validate all agents
./cortex validate scripts/install.sh                             # validate one script
```

## Options

| Argument | Description |
|----------|-------------|
| `<path>` | File or directory to validate (optional; defaults to everything) |
| `--help` | Show help message |

## Related

- [`cortex sync`](sync.md)
- [`cortex scaffold`](scaffold.md)
