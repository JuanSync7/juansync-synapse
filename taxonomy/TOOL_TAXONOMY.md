# Tool Taxonomy

Naming and metadata rules for tools. The controlled vocabulary for each slug slot (and the frontmatter-only `kind` field) lives in [`registry/TOOL_VOCABULARY.md`](../registry/TOOL_VOCABULARY.md). The inventory of tools currently in the repo lives in [`registry/TOOL_REGISTRY.md`](../registry/TOOL_REGISTRY.md). This file defines the *shape*; vocabulary holds the *values*; registry holds the *inventory*.

## Naming convention

`{domain}-{subdomain}-{action}-{target}` — lowercase-hyphenated. All four slots required.

- **`domain`** — ecosystem (e.g., `synapse`, `architecture`).
- **`subdomain`** — category within the domain (e.g., `git`, `registry`).
- **`action`** — imperative verb naming what the tool does (e.g., `dispatch`, `validate`, `sync`).
- **`target`** — noun naming what the action operates on (e.g. `frontmatter`, `skills`).

## Examples

| Slug | Description |
|------|-------------|
| `synapse-git-dispatch-cr` | Dispatches change requests onto worktree branches |
| `synapse-taxonomy-lint-frontmatter` | Lints artifact frontmatter against the controlled vocabulary |

**Anti-patterns:**

| Slug | Why it's wrong |
|------|----------------|
| `synapse-git-cr-dispatch` | Slot order reversed — reads "the CR dispatch" (noun phrase). Tools take action-first; should be `dispatch-cr`. |
| `synapse-taxonomy-frontmatter-validator` | `validator` is a role noun, not an action. Tools are mechanical commands, not personas — use `lint-frontmatter` or `validate-frontmatter`. |

## Tool kind (frontmatter, not slug)

Tool implementation kind is metadata — it does NOT appear in the slug. The set of valid `kind` values lives in [`registry/TOOL_VOCABULARY.md`](../registry/TOOL_VOCABULARY.md).

## Frontmatter

Required fields on every `TOOL.md` file:

```yaml
name: <slug>           # must equal directory name AND match {domain}-{subdomain}-{action}-{target}
domain: <value>
subdomain: <value>
action: <verb>         # what the tool does
target: <noun>         # what the action operates on
kind: <value>          # external | internal | wrapper
description: <text>    # one-line routing/usage hint
```

## Tags

Freeform — no controlled list. Use lowercase, hyphenated multi-word tags (e.g., `schema-check`, `score-computation`).
