# Phased Delivery — Engineering Guide Layer

The engineering guide is a **cumulative** document — one living file updated each phase, not split per phase.

## When This Applies

Phased delivery applies when:
- The subsystem has phase-specific documents (e.g., `_SPEC_P1.md`, `_DESIGN_P1.md`)
- The README dashboard exists and shows multiple phases
- The doc-authoring router passes phase context

## Output Naming

```
{SUBSYSTEM}_ENGINEERING_GUIDE.md
```

No phase suffix. The same file is updated for every phase.

## P1: Write Full Guide

For the first phase, write the full engineering guide as normal — all 9 sections plus appendix. No special phasing rules apply.

Add a "Phase History" sub-section to Section 1 (System Overview):

```markdown
### Phase History

| Phase | Delivered | Date |
|-------|-----------|------|
| P1 | {summary of what P1 built} | {date} |
```

## P2+: Cumulative Update

Do NOT rewrite the guide from scratch. Apply surgical updates:

### What to add
- **New Module Reference sections** (Section 3) for modules introduced in this phase — follow the same 5-sub-section format
- **Phase History row** — add a row for this phase to the Section 1 table
- **New Architecture Decisions** (Section 2) if this phase introduced cross-cutting decisions
- **New Data Flow scenarios** (Section 4) for flows introduced in this phase
- **New Configuration parameters** (Section 5)
- **New Integration Contracts** (Section 6) if this phase added system boundary interfaces

### What to update
- **Existing Module sections** that this phase modified — update the affected sub-sections (How it works, Configuration, Error behavior, etc.)
- **System Overview** (Section 1) — update the architecture description if the system shape changed
- **Known Limitations** (Section 8) — remove any that this phase resolved, add any new ones

### What to leave alone
- Module sections for modules this phase did not touch
- Architecture Decisions that did not change
- Data Flow scenarios that are unchanged

### Marking phase provenance
In new module sections, note which phase introduced the module:

```markdown
### `src/auth/roles.py` — Role Management

**Introduced in:** P2
**Module purpose:** ...
```

In updated module sections, note what changed:

```markdown
**Updated in P2:** Added role field to AuthToken, new permission validation logic.
```

## README Dashboard Update

After updating the guide, update the subsystem README dashboard. Read [`references/readme-update-contract.md`](readme-update-contract.md) for the update procedure.
