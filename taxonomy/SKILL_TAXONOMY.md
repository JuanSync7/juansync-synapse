# Skill Taxonomy

Naming and metadata rules for skills. The controlled vocabulary for each slug slot lives in [`registry/SKILL_VOCABULARY.md`](../registry/SKILL_VOCABULARY.md). The inventory of skills currently in the repo lives in [`registry/SKILL_REGISTRY.md`](../registry/SKILL_REGISTRY.md). This file defines the *shape*; vocabulary holds the *values*; registry holds the *inventory*.

## Naming convention

```
{namespace}-{subdomain?}-{scope}-{role}
   required     optional    required required
```

Lowercase-hyphenated. **Fixed tail, variable head** — the last two tokens are always
`scope`-`role`; `subdomain` is optional.

- **`namespace`** (the `domain` field) — required collision-safe prefix. Claude Code discovers
  skills from a flat `~/.claude/skills/` directory, so the namespace is what keeps the name
  globally unique (e.g., `synapse`, `docs`, `code`).
- **`subdomain`** — **optional.** Include it *only* when `{namespace}-{scope}-{role}` would
  collide with another artifact and a category token is needed to disambiguate (e.g.,
  `framework-langgraph-workflow-designer`). Omit it otherwise — do not pad with `general`.
- **`scope`** — noun naming what the skill operates on (e.g., `spec`, `test`, `eval`). This is
  the *document/artifact type* for doc skills (a spec-writer operates on a `spec`).
- **`role`** — agentive noun naming what the skill is (e.g., `writer`, `reviewer`, `gatekeeper`).

**Parse rule:** split the last two hyphen-tokens off — those are `scope`-`role` (the function
signature); everything before is the namespace. `name:` must equal the directory name, and its
last two tokens must equal the `scope` and `role` frontmatter fields.

### `(scope, role)` is the similarity signature

Two skills sharing a `(scope, role)` pair in the same namespace are presumptively redundant.
Because both are controlled-vocabulary values, "does a similar skill already exist?" is a
structured query — *show every skill with `scope=X` AND `role=Y`*. Run it (against
[`registry/SKILL_REGISTRY.md`](../registry/SKILL_REGISTRY.md)) **before** creating a new skill.

### The slug classifies; the description routes

The slug exists for human glance-readability, governance, and global uniqueness. The actual
routing contract is the frontmatter `description` + triggers — that is what an LLM selects on.
Do not over-invest the name with routing detail the description already carries.

## Examples

| Slug | Head | Tail (scope-role) |
|------|------|-------------------|
| `docs-spec-writer` | `docs` (no subdomain needed) | operates on a `spec`, is a `writer` |
| `synapse-router-artifact-gatekeeper` | `synapse-router` | operates on an `artifact`, is a `gatekeeper` |
| `asic-frontend-spec-writer` *(illustrative)* | `asic-frontend` (subdomain disambiguates from `asic-verification-spec-writer`) | operates on a `spec`, is a `writer` |

**Anti-patterns:**

| Slug | Why it's wrong |
|------|----------------|
| `docs-general-doc-writer` | `general` is filler. Drop the subdomain: `docs-doc-writer` (or promote the doc-type to scope: `docs-spec-writer`). |
| `synapse-skill-skill-improver` *(historical)* | `skill` doubled across subdomain+scope. Drop the redundant subdomain: `synapse-skill-improver`. |
| `synapse-skill-design-validate` | `validate` is a verb. Role must be an agentive noun (`validator`). |

## Persona / mode skills

Persona or interaction-mode skills (e.g. a simulated advisory "office-hour") have **no
`scope-role` transformation signature** and do **not** follow this grammar. They live under
`src/skills/persona/`, use the loose rule `persona-{handle}`, and are governed by
[`PERSONA_TAXONOMY.md`](PERSONA_TAXONOMY.md).

## Frontmatter

Required fields on every `SKILL.md`:

```yaml
name: <slug>           # must equal directory name; last two tokens == scope-role
domain: <value>        # required — the namespace prefix
subdomain: <value>     # OPTIONAL — include only if present in the name
scope: <noun>          # required — what the skill operates over (last-but-one name token)
role: <noun>           # required — what the skill IS (last name token)
```

`subdomain` is omitted entirely (field absent) when the name has no subdomain token.

## Aliases

Optional frontmatter field — terse invocation handles layered on top of the structured slug:

```yaml
aliases: [brainstorm]   # OPTIONAL — convenience handles for human invocation
```

Think Twitter identity: the **slug** is the immutable user ID (registries, pipelines, and
`Consumers` columns reference it — *always*), the **alias** is the @handle (what a human types),
and the **description** is the display name (what the LLM routes on). Rules:

- **Aliases never appear in governance surfaces.** Registry rows, pipeline stages,
  `requires_*` chains, and cross-skill references use the slug only. An alias is resolved at
  install time and nowhere else.
- **Aliases share one global uniqueness pool with names.** An alias must not equal any skill's
  name or any other skill's alias, repo-wide. The pre-commit hook and `scripts/validate.sh`
  enforce this; `cortex install` re-checks against whatever is already installed on the machine
  (other packs included) and refuses to overwrite — alias squatting fails loudly, never silently.
- **Aliases are mutable; slugs are not.** Renaming a skill is a breaking change; remapping an
  alias is not. This is the point: terse handles can evolve or be reassigned without touching
  the stable key.
- Keep them scarce. An alias is earned by frequent human typing (`brainstorm`, `build-plan`),
  not granted by default. Most skills need none.

Install behavior: `cortex install` creates one symlink per alias alongside the canonical
symlink, applying the same collision guard, and reconciles missing alias links on reinstall.
Removing an alias from frontmatter stops it being installed; an already-installed alias link
is cleaned up by `cortex clean` (it removes broken/stale symlinks), not by reinstall.

## Tags

Freeform — no controlled list. Use lowercase, hyphenated multi-word tags (e.g., `test-planning`, `source-of-truth`).
