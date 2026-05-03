# Decision Memo — synapse-readme-maintainer

> Artifact type: agent | Memo type: creation | Design doc: `.brainstorms/2026-04-24-readme-update-agent/design.md`

---

## What I want

An agent that maintains the README-index invariant across the synapse tree. When a synapse (skill, agent, or protocol) is created, updated, or deleted, this agent walks the synapse's ancestor path — from the leaf domain README up through parent class READMEs to the repo root — and applies surgical edits: adding, updating, or removing rows, and rewriting top-of-file one-liners only when the existing prose makes a factually false claim about the directory contents.

The agent is shared (tier 3) — a single agent covers all synapse types (skills, agents, protocols). It is dispatched by four consuming skills as a final convenience step, not a precondition. If it fails, the dispatcher logs a warning but does not abort; the pre-commit hook remains the authoritative gate for the README-row invariant.

---

## Why Claude needs it

Without this agent, `*-creator` skills consistently forget to write domain README rows. The pre-commit hook then blocks the commit. The contributor must manually figure out the correct table format, row placement, and description phrasing — which they get wrong often enough that it becomes a repeated friction point. The description column is especially error-prone because frontmatter `description:` is a routing contract ("Use when..."), not a directory-index blurb — humans copying it verbatim produce the wrong register.

A deterministic script cannot solve this because the description column requires LLM judgment to rephrase routing-contract language into a directory-index blurb that matches sibling rows' tone and length.

---

## Injection shape

- **Policy:** Judgment rules for when to add/update/remove/no-op on each README; description-rewrite policy (routing contract → directory-index blurb anchored to sibling rows); top-of-file one-liner policy (factually false claim only — never stylistic preference); cross-domain move detection; failure-first / no-partial-writes discipline; idempotency check.

---

## What it produces

| Output | Count | Mutable? | Purpose |
|--------|-------|----------|---------|
| Domain leaf README (e.g., `synapse/skills/skill/README.md`) | 1 per invocation (most likely) | yes | Adds/updates/removes the artifact's row in its domain index |
| Class README (e.g., `synapse/skills/README.md`) | 0–1 | yes | Adds domain row only when a new domain directory is introduced |
| Top-level READMEs (`synapse/README.md`, repo `README.md`) | 0–1 each | yes | Checked but rarely changed for individual artifacts |
| Structured output report | 1 | no | `affected_readmes` list with per-README action + diff summary; consumed by dispatcher |

On cross-domain moves: up to 2 ancestor paths walked — removal from old domain README + addition in new domain README.

---

## Naming conventions

Name: `synapse-readme-maintainer`

Segment breakdown: `synapse` (domain) + `readme` (sub-scope) + `maintainer` (role). Role value `maintainer` is a taxonomy addition — see Taxonomy CR below. Convention: `domain-subdomain-role`. This pattern is forward-compatible with future agents such as `synapse-registry-maintainer`.

---

## Edge cases considered

| Edge case | Handling |
|-----------|----------|
| Row already exists with correct name + description | Return `no_change` for that README; issue no write. Hard idempotency requirement. |
| Synapse `domain:` value absent from relevant taxonomy file | Halt immediately, return `taxonomy-update-required` with offending value and taxonomy file path. No partial writes. |
| Required frontmatter field missing (`name`, `description`, `domain`) | Fail with `missing_frontmatter`; caller fills frontmatter and re-dispatches. No write. |
| Domain README table unparseable | Fail with `unparseable_table`; manual fix required — agent does not auto-repair. |
| Ancestor-path directory has no `README.md` | Fail with `readme_missing` including the path. Agent does NOT auto-stub — directory purpose needs human judgment. |
| Two rows with the same name in target README | Fail with `multiple_matching_rows`; no auto-resolve. |
| Cross-domain move (synapse moved between domains) | `previous_path` is non-null; agent walks BOTH ancestor paths — removes row from old domain README, adds to new. |
| Dispatcher invokes agent after soft failure | Pre-commit hook remains the source of truth; dispatcher logs warning and continues — does not abort creator skill. |

---

## Dependencies

| Artifact | Direction | Contract |
|----------|-----------|----------|
| `synapse/skills/skill/skill-creator` | consumes this agent | Dispatches at final step; passes `synapse_path`, `action=created`, `previous_path=null` |
| `synapse/skills/skill/agent-creator` | consumes this agent | Dispatches at final step; passes `synapse_path`, `action=created`, `previous_path=null` |
| `synapse/skills/skill/protocol-creator` | consumes this agent | Dispatches at final step; passes `synapse_path`, `action=created`, `previous_path=null` |
| `synapse/skills/skill/improve-skill` | consumes this agent | Dispatches when frontmatter (description, intent, domain) changes; passes `synapse_path`, `action=updated`, `previous_path` if domain changed |
| `taxonomy/AGENT_TAXONOMY.md` | consumes | Must contain `maintainer` role before this agent can be validated by pre-commit hook |
| `registry/AGENTS_REGISTRY.md` | produces for | Must have a row added for this agent during bootstrap |

---

## Frontmatter sample

<!-- VERBATIM -->

```yaml
---
name: synapse-readme-maintainer
description: "Maintains README-index invariant for the ancestor path of a changed synapse — adds/updates/removes rows; rewrites top-of-file one-liner only on factual drift. Dispatched by *-creator skills and improve-skill at end of flow."
domain: synapse
role: maintainer
tags: [readme, index-maintenance, post-creation, post-update]
---
```

---

## Directory layout

<!-- VERBATIM -->

```
synapse/agents/synapse/
├── README.md                              # NEW — created during agent bootstrap
└── synapse-readme-maintainer.md           # this agent
```

Plus one row appended to `synapse/agents/README.md` (parent index).

---

## Input contract

<!-- VERBATIM -->

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `synapse_path` | string (absolute path) | yes | Path to the synapse file in its current location (post-change for create/update; last-known for delete) |
| `action` | enum: `created` \| `updated` \| `deleted` | yes | The change type that triggered this dispatch |
| `previous_path` | string (absolute path) \| null | yes for cross-domain moves | Pre-change path; required when the synapse moved between domains, otherwise null |

---

## Output contract

<!-- VERBATIM -->

```json
{
  "status": "success" | "taxonomy-update-required" | "error",
  "affected_readmes": [
    {
      "path": "synapse/skills/skill/README.md",
      "action": "added_row" | "updated_row" | "removed_row" | "updated_one_liner" | "no_change",
      "row_name": "synapse-readme-maintainer",
      "diff_summary": "added new row at line 14"
    }
  ],
  "warnings": [],
  "error": null | {
    "kind": "domain_not_in_taxonomy" | "missing_frontmatter" | "unparseable_table" | "readme_missing" | "multiple_matching_rows",
    "message": "domain 'synaspe' not found in taxonomy/AGENT_TAXONOMY.md (typo?)",
    "file": "synapse/agents/synapse/synapse-readme-maintainer.md"
  }
}
```

---

## Failure modes table

<!-- VERBATIM -->

| Error kind | Trigger | Recovery |
|------------|---------|----------|
| `domain_not_in_taxonomy` | Synapse's `domain:` value missing from the relevant taxonomy file | Caller adds domain to taxonomy, re-dispatches. Agent does not auto-update taxonomy. |
| `missing_frontmatter` | Required field (name, description, domain, terminal) absent from synapse | Caller fills frontmatter, re-dispatches. |
| `unparseable_table` | Domain README table header doesn't match a recognizable schema | Manual fix to README table format; agent does not auto-repair. |
| `readme_missing` | An ancestor-path directory has no `README.md` | Caller (or human) creates README stub with appropriate header for the directory's role; agent does not auto-stub because directory purpose needs human judgment. |
| `multiple_matching_rows` | Two rows in target README share the same name | Manual resolution — agent does not pick one. |

All failures are non-destructive: the agent never writes a partial state. On error, no files are modified.

---

## Canonical dispatch prompt

<!-- VERBATIM -->

```markdown
**Dispatch synapse-readme-maintainer** (final step, model: sonnet):

Pass:
- `synapse_path`: <absolute path to created/updated/deleted synapse>
- `action`: <created | updated | deleted>
- `previous_path`: <pre-change path if synapse moved between domains; otherwise null>

Treat result as advisory:
- `status: success` → log affected_readmes, proceed.
- `status: taxonomy-update-required` → surface to user; this skill should have caught it earlier — investigate.
- `status: error` → log warning, do NOT abort the creator skill; pre-commit hook will catch any remaining issues.
```

---

## Behavior outline

<!-- VERBATIM -->

The body should be structured (not full prose) — judgment moments only. Mechanics (how to parse markdown tables, how to read YAML frontmatter) are not taught — Claude knows. The body teaches:

1. **Decision: add / update / remove / no-op** — match by `name` field; if no match and action=created, add; if match and action=deleted, remove; if match and action=updated, diff the row content.
2. **Description rewrite policy** — frontmatter description is a routing contract; rewrite as a directory-index blurb anchored to sibling rows' tone/length.
3. **Top-of-file one-liner policy** — only update on factually false claim, never on stylistic preference. When in doubt, leave alone.
4. **Cross-domain move detection** — if `previous_path != null`, walk both ancestor paths; remove from old, add to new.
5. **Failure first, no partial writes** — validate frontmatter completeness, taxonomy match, README parseability BEFORE any write. Any failure → halt with structured error, no files modified.
6. **Idempotency check** — for each target README, if the existing state already matches what the agent would write, return `no_change` instead of issuing a redundant write.

---

## Taxonomy CR

<!-- VERBATIM -->

Append to the Roles table in `taxonomy/AGENT_TAXONOMY.md`:

```markdown
| `maintainer` | Enforces invariants across existing artifacts; reads current state, applies surgical edits, writes updated state. |
```

---

## Bootstrap manual steps

<!-- VERBATIM -->

These run once during this agent's own creation (not part of agent's runtime behavior):

1. Create `synapse/agents/synapse/README.md` with leaf-format header and a single row for `synapse-readme-maintainer`.
2. Add a row to `synapse/agents/README.md` linking to the new `synapse/` subdirectory.
3. Add `synapse-readme-maintainer` to `registry/AGENTS_REGISTRY.md`.
4. Append `maintainer` role to `taxonomy/AGENT_TAXONOMY.md`.
5. Update CR `src/skills/skill/skill-creator/change_requests/2026-04-24-readme-update-agent.md` to mark "implementation tracked under <design-doc-path>" — closes the loop.

---

## Migration: 4 SKILL.md updates

<!-- VERBATIM -->

After agent is created, append the canonical dispatch block to:
- `synapse/skills/skill/skill-creator/SKILL.md` (in [O] or equivalent final step)
- `synapse/skills/skill/agent-creator/SKILL.md`
- `synapse/skills/skill/protocol-creator/SKILL.md`
- `synapse/skills/skill/improve-skill/SKILL.md` (in the post-frontmatter-change step)

These edits are tracked in the design doc, not this agent's memo (memo is per-artifact).

---

## Open questions

None — all threads resolved during brainstorm lens rotation.
