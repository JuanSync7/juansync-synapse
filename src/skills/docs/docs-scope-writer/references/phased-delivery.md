# Phased Delivery — Scope Layer

The scope document is **cumulative** — one living file updated across all phases, no phase suffix.

## Output Naming

```
{SUBSYSTEM}_SCOPE.md
```

Always the same file. Updated in place as phases evolve.

## How Phasing Works for Scope

The scope doc is where phases are DEFINED, not where they're consumed. It's the authoritative source for:
- What each phase delivers
- Cross-phase dependencies
- What's deferred to later phases

When a new phase begins planning:
1. Move relevant items from Deferred to In Scope
2. Add a new Phase Plan row
3. Update Cross-Phase Dependencies
4. Reset Status to "Draft" and add new Open Questions for the phase

## README Dashboard Coordination

The scope doc's Phase Plan and the README's Phase Map must stay in sync. When phases change in the scope doc:
1. Update the scope doc Phase Plan
2. Update the README Phase Map to match
3. If a new phase column is needed in the Status Matrix, add it
