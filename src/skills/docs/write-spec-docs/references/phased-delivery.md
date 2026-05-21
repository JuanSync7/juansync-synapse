# Phased Delivery — Spec Layer

This reference applies when writing a spec for a specific delivery phase (P1, P2, P3...) rather than an unphased monolithic spec.

## When This Applies

Phased delivery is triggered when:
- The user says "write spec for phase N" or "P2 spec"
- The doc-authoring router passes phase context
- Prior phase spec documents exist in the same directory

If none of these apply, write an unphased spec as normal — ignore this reference.

## Output Naming

```
{SUBSYSTEM}_SPEC_P{N}.md
```

Examples: `AUTH_SPEC_P1.md`, `AUTH_SPEC_P2.md`

## FR-ID Ranges Across Phases

Each phase gets its own ID range to keep cross-phase references visually obvious:

| Phase | FR Range | NFR Range |
|-------|----------|-----------|
| P1 | FR-100–FR-199 | NFR-100–NFR-199 |
| P2 | FR-200–FR-299 | NFR-200–NFR-299 |
| P3 | FR-300–FR-399 | NFR-300–NFR-399 |

Within each range, group by section as normal (e.g., P2 Section 3 → FR-210–FR-229, Section 4 → FR-230–FR-249). Leave gaps for future insertions.

State the phase's ID range explicitly in Section 1.5 (Requirement Format) of each phase spec.

## Scope Boundary Per Phase

Section 1.2 (Scope) must explicitly state:

- **"This phase covers:"** — what's in scope for this phase
- **"Deferred to later phases:"** — what's intentionally excluded (with phase target if known)
- **"Delivered in prior phases:"** — what already exists (with references to prior spec documents)

## Prior Phase Contracts (mandatory for P2+)

Every P2+ spec must include a section immediately after Scope & Definitions:

```markdown
## Prior Phase Contracts

Interfaces and requirements from prior phases that this phase depends on or extends.

| Interface / FR | Established In | How This Phase Uses It |
|---------------|---------------|----------------------|
| AuthToken TypedDict (FR-102) | AUTH_SPEC_P1.md | Extended with role field |
| Session validation (FR-105) | AUTH_SPEC_P1.md | Called by new permission checks |
```

Rules:
- List only contracts this phase actually depends on — not the entire prior phase
- If this phase CHANGES a prior-phase interface, note the change explicitly ("Extended with...", "Modified to...")
- If this phase only USES a prior interface without changing it, note "Used as-is"
- Link to the source spec document, not the implementation

## Cross-Phase Dependencies Appendix

Add to Appendix (after Implementation Phasing if present):

```markdown
### Appendix D: Cross-Phase Dependencies

| This Phase FR | Depends On | Phase | Nature |
|--------------|-----------|-------|--------|
| FR-201 | FR-102 | P1 | Extends token model with role field |
| FR-205 | FR-105 | P1 | Calls existing session validation |
```

## Shared Definitions

- Terminology defined in P1 applies across all phases. P2+ specs should reference the P1 terminology section by link rather than restating definitions.
- If P2+ adds NEW terms, define them in that phase's terminology section with a note: "New in P{N}."
- If P2+ CHANGES a P1 definition, restate the updated definition with a note: "Updated from P1 — previously [old definition]."

## README Dashboard Update

After writing the spec, update the subsystem README dashboard. Read [`references/readme-update-contract.md`](readme-update-contract.md) for the update procedure.
