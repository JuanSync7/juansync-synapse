# Change Request: Status lifecycle — gatekeeper promotes, pre-commit demotes

Supersedes `2026-04-21-auto-record-verdict.md` (which proposed writing `status: certified` to `SKILLS_REGISTRY.yaml`; the actual source-of-truth is the `Status` column in `registry/SKILL_REGISTRY.md`, and the chosen vocabulary is `draft`/`stable`/`deprecated`, not `certified`).

## Problem

A gatekeeper APPROVE verdict lives only in PR descriptions per GOVERNANCE.md. Nothing on disk records that a skill has been certified, so:

- Re-running gatekeeper later cannot see prior approval.
- Skills can drift after approval (SKILL.md edits) without anyone noticing certification is now stale.
- The pre-commit hook treats every commit equally — no signal that a stable skill has been touched.

## Decision

Two-state lifecycle in the `Status` column of `registry/SKILL_REGISTRY.md`:

```
draft ←→ stable
```

`deprecated` is a third terminal state; gatekeeper and pre-commit leave it alone.

| Trigger | Effect |
|---------|--------|
| `/synapse-gatekeeper` issues APPROVE on a skill | Status row → `stable` (from `draft` or unset). `deprecated` is never overwritten. |
| Any change to `SKILL.md` of a `stable` skill is staged | Pre-commit auto-demotes the row to `draft` and re-stages the registry. Warns: "re-run /synapse-gatekeeper". |
| REVISE or REJECT verdict | No status change. |

Rationale for auto-demote in pre-commit (instead of WARN-only):
- WARN-only requires human discipline to actually demote — easy to ignore.
- Demotion is mechanical and reversible: re-running gatekeeper restores `stable` with one command.
- Keeps registry truthful at all times: a `stable` row always means "this exact SKILL.md was approved."

## Scope

- `synapse/skills/skill/synapse-gatekeeper/SKILL.md` — Phase 5 gains a write step on APPROVE for skill flow.
- `.githooks/pre-commit` — for each changed skill dir, if registry status is `stable`, rewrite to `draft` and `git add registry/SKILL_REGISTRY.md`.

## Out of scope

- Agent / protocol / tool / pathway lifecycle. Their registries don't have a Status column today; they can adopt the same pattern later.
- Auto-demoting `references/` or `templates/` edits. Only `SKILL.md` triggers demotion — companion-file edits are common and don't always invalidate the eval. (Reconsider if drift becomes a problem.)
