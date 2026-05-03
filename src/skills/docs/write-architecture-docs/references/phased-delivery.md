# Phased Delivery — Architecture Layer

The architecture document is **cumulative** — one living file updated across all phases, no phase suffix.

## Output Naming

```
{SUBSYSTEM}_ARCHITECTURE.md
```

Always the same file. Updated in place as new phases introduce components or technology decisions.

## How Phasing Works for Architecture

When new phases introduce new components or technology decisions:
- Add new rows to existing tables (Component Boundaries, Technology Decisions, Integration Points)
- Add new Data Flow Patterns sections as needed
- Annotate the phase in the Technology Decisions table's Decided column (e.g., "2026-04-09 (P2)")

## Carry-Forward Contracts

The architecture doc owns the Carry-Forward Contracts table in the README. When interfaces are established at the architecture level (e.g., "the API contract between frontend and backend is REST with OpenAPI 3.0"), record them so downstream phases inherit the contract.
