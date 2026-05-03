# README Dashboard Update Contract — Spec Layer

After producing a spec document, update the subsystem's `README.md` dashboard.

## Location

The README lives at the same directory level as the spec: `docs/{subsystem}/README.md`.

## If README Does Not Exist (first phase document)

Create it from this template:

```markdown
# {Subsystem Name}

**Current phase:** P1 — {phase name}
**Last updated:** {today's date}

## Phase Map

| Phase | Name | Objective | FR Range | Status |
|-------|------|-----------|----------|--------|
| P1 | {name} | {one-line objective} | FR-100–199 | In Progress |

## Status Matrix

| Layer | P1 |
|-------|----|
| Scope | — |
| Architecture | — |
| Spec | [Done]({filename}) |
| Spec Summary | — |
| Design | — |
| Impl Docs | — |
| Code | — |
| Eng Guide | — |
| Test Docs | — |

## Cross-Phase Dependencies

_None yet._

## Carry-Forward Contracts

_None yet._
```

Populate the Phase Map from the spec's scope and phasing information. If the spec mentions future phases, add placeholder rows with Status `Planned`.

## If README Already Exists

1. **Status Matrix** — Set the Spec cell for this phase to `[Done]({filename})`
2. **Phase Map** — If this is a new phase not yet in the table, add a row
3. **Cross-Phase Dependencies** — If the spec's "Cross-Phase Dependencies" appendix has entries, add them to the README table (avoid duplicates)
4. **Carry-Forward Contracts** — If the spec's "Prior Phase Contracts" section introduces interfaces that downstream phases will need, add them
5. **Current phase** — Update if this advances the current phase
6. **Last updated** — Set to today's date

## Status Values

- `—` = not started
- `In Progress` = document being written
- `[Done]({filename})` = completed, with link to document
- `[Current]({filename})` = cumulative document (scope, architecture, engineering guide)
