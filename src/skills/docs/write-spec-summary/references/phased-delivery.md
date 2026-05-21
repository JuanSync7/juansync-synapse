# Phased Delivery — Spec Summary Layer

This reference applies when writing a spec summary for a phase-specific spec (`_SPEC_P{N}.md`).

## When This Applies

Phased delivery is triggered when:
- The companion spec has a phase suffix (e.g., `AUTH_SPEC_P2.md`)
- The doc-authoring router passes phase context
- Prior phase summaries exist in the same directory

If none apply, write an unphased summary as normal — ignore this reference.

## Output Naming

```
{SUBSYSTEM}_SPEC_SUMMARY_P{N}.md
```

The phase number mirrors the companion spec: `AUTH_SPEC_P2.md` → `AUTH_SPEC_SUMMARY_P2.md`.

## §1 Generic System Overview — Phase Evolution

§1 is the most important section and handles phasing differently from all other sections:

- **§1 describes the FULL system as it will exist after this phase** — not just the delta from the prior phase.
- For P1: §1 describes the system as P1 delivers it.
- For P2+: §1 describes the system including both prior-phase capabilities and this phase's additions. It should read as a coherent whole, not a changelog.
- Read prior phase summaries' §1 sections to ensure continuity — P2's §1 should build on P1's framing, not contradict it.
- §1 grows richer each phase as the system gains capabilities.

All §1 hard constraints still apply: no FR-IDs, no technology names, no file names, no threshold values.

## §2+ Sections — Phase Scoping

Sections §2 onward scope to THIS phase's spec only:
- §3 Scope: reflects this phase's scope boundary
- §5 Requirement Framework: covers this phase's FR-ID range
- §6 Functional Domains: covers domains introduced or extended in this phase
- §7+ sections: cover this phase's content only

## Phase Context Section (new for phased delivery)

Add a "Phase Context" section between §1 (Generic System Overview) and §2 (Header):

```markdown
## Phase Context

**Phase:** P{N} of {total if known}
**Prior phases:**
- P1 — {one-sentence summary of what P1 delivered}
- P2 — {one-sentence summary of what P2 delivered}

**This phase adds:** {one-sentence summary of this phase's contribution}
```

Keep each prior-phase summary to one sentence. The goal is orientation, not detail.

## Sync Status

The sync status section should reference the phase-specific spec:

```markdown
## Sync Status

Aligned to: `AUTH_SPEC_P2.md` v1.0
Date: 2026-04-09
```

## README Dashboard Update

After writing the summary, update the subsystem README dashboard. Read [`references/readme-update-contract.md`](readme-update-contract.md) for the update procedure.
