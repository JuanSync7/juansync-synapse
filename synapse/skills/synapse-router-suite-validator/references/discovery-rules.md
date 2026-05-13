# Discovery Rules

Loaded by `synapse-router-suite-validator` Phase 1. The classifier walks the suite root and assigns every candidate path to exactly one of five artifact types — or marks it `UNRECOGNIZED` and skips it. Without precise rules, a stray `.md` file masquerades as an agent and pollutes the rollup with false failures.

---

## Five artifact types and their signatures

| Type | Signature on disk | Path shape inside suite |
|------|-------------------|-------------------------|
| **skill** | Directory containing a `SKILL.md` file at its root | `skills/<domain>/<skill-name>/SKILL.md` |
| **agent** | `.md` file directly under an `agents/<domain>/` directory (NOT in a subdirectory) | `agents/<domain>/<agent-name>.md` |
| **protocol** | `.md` file directly under a `protocols/<domain>/` directory | `protocols/<domain>/<protocol-name>.md` |
| **tool** | Directory containing a `TOOL.md` file at its root | `tools/<domain>/<tool-name>/TOOL.md` |
| **pathway** | `.yaml` file directly under a `pathways/` directory | `pathways/<pathway-name>.yaml` |

A suite may contain any subset of these; absence is not a failure.

---

## Walk algorithm

1. Start at `<suite-root>`.
2. For each top-level directory whose name is `skills`, `agents`, `protocols`, `tools`, or `pathways`, descend into it.
3. Apply the per-type matcher below. Every match yields one artifact record.
4. Files outside these top-level directories (e.g., suite-level `README.md`, `LICENSE`, `.github/`) are ignored.
5. Files inside these directories that DO NOT match the type signature are recorded as `UNRECOGNIZED` and listed in the rollup's cross-suite section as a hygiene flag — they do not block the verdict.

---

## Per-type matcher rules

### skill

- A directory `D` is a skill iff `D/SKILL.md` exists.
- Nested directories below a skill (e.g., `references/`, `templates/`, `agents/`, `examples/`) are NOT recursed into for further skill discovery — a skill cannot contain another skill.
- A `SKILL.md` file outside a `skills/` subtree is recorded as `UNRECOGNIZED` (misplaced).

### agent

- A file `F.md` is an agent iff its parent directory is exactly `agents/<domain>/` (one level under `agents/`).
- A `.md` file deeper than that (e.g., `agents/<domain>/sub/<file>.md`) is `UNRECOGNIZED`.
- Files named `README.md` are NEVER agents — they are domain READMEs.

### protocol

- A file `F.md` is a protocol iff its parent directory is exactly `protocols/<domain>/`.
- Same nested-depth and `README.md` rules as agents.

### tool

- A directory `D` is a tool iff `D/TOOL.md` exists.
- Script files (`.sh`, `.py`) inside a tool directory are part of the tool, not separate artifacts.

### pathway

- A file `F.yaml` (or `F.yml`) is a pathway iff its parent directory is exactly `pathways/`.
- `pathways/<subdir>/<file>.yaml` is `UNRECOGNIZED` (pathways are flat).

---

## Naming extraction

For each artifact, extract `name`:

- **skill / tool:** parse `name:` from the YAML frontmatter of `SKILL.md` / `TOOL.md`. If frontmatter is unparseable, fall back to the directory name and mark the artifact `UNREADABLE`.
- **agent / protocol:** parse `name:` from the YAML frontmatter of the `.md` file. If unparseable, fall back to the filename without extension and mark `UNREADABLE`.
- **pathway:** parse `name:` from the top of the YAML document. If the file is not valid YAML, mark `UNREADABLE`.

`UNREADABLE` artifacts are still listed in the rollup so the maintainer sees them — they just bypass per-type structural checks.

---

## Empty-suite handling

If the walk completes with zero artifacts of any type, emit:

```
SUITE: REJECT (path: <suite-path>)
No recognizable artifacts found. A suite must contain at least one of: skills/, agents/, protocols/, tools/, pathways/.
```

Stop immediately. Do not run cross-suite checks on an empty suite — they would have nothing to act on.
