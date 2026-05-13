# Done Signal Checklist

Loaded at [D]. All items must pass before output production. No exceptions, no shortcuts.

---

## Pre-Done Checklist

- [ ] All artifacts in the Artifacts Discovered table are marked lens-complete
- [ ] Final mandatory hygiene check passed (load `references/hygiene-check.md`)
- [ ] Cross-artifact sweep passed (load `references/cross-artifact-sweep.md`):
  - [ ] Contract symmetry verified
  - [ ] No unacknowledged orphans
  - [ ] No circular dependencies (or explicitly acknowledged)
- [ ] All per-artifact Open sections are empty (no unresolved items remaining)
- [ ] Session-level Open/Orphaned section is empty or all items resolved
- [ ] Registry checked for overlaps (`registry/SKILL_REGISTRY.md` if exists) — overlaps surfaced to user
- [ ] Final circle-back: walk the entire notepad, confirm all threads are terminal

---

## If Any Check Fails

Route back to [B] with specific artifacts and items that need attention. Name the artifact, name the failing check, name the unresolved item. Do not produce output with unresolved items — incomplete memos create incomplete handoffs to `*-creator` skills.

---

## If User Pushes to Skip

Push back with the specific failing items named:

> "These items are unresolved: [list]. Producing memos now would create incomplete handoffs to the creator skills. Let's address [specific item] first — it should take [estimated turns]."

The Done Signal is the coach's honest judgment that no major flaws remain. Firing it early undermines the entire brainstorm's value.
