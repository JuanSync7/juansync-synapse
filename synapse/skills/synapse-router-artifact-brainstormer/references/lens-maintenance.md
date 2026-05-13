# Lens: Maintenance

Evaluates whether the artifact will survive evolution. Fourth lens — applied after scope, precision, and robustness are settled.

---

## Core Question

**Will this survive evolution?**

---

## Diagnostic Questions

1. **Registry as truth:** Is this artifact discoverable via the appropriate registry? Missing registry entries make artifacts invisible to routing and discovery.
2. **Evolution resilience:** If a sibling is renamed or removed, does this artifact break? Count the hard references.
3. **Coupling assessment:** Is this artifact coupled to frequently-changing things (specific file paths, API versions, tool names, implementation details)?
4. **Taxonomy drift:** Are `domain` and terminal values from the controlled vocabulary in the appropriate taxonomy file? Ad hoc values create drift.
5. **Temporal test:** Does this artifact still make sense in 6 months? Content that encodes current-state assumptions ages poorly.

### Artifact-Type-Specific

- **Skills:** Are companion file paths stable? If a companion is restructured, does the SKILL.md's Load directive break?
- **Agents:** If the dispatching skill changes its interface, does this agent break? How tightly coupled is the input contract?
- **Protocols:** If the enforced behavior changes, how do consuming agents update? Is there a migration path or does it break silently?
- **Tools:** If input/output schema changes, how do consuming skills or scripts adapt? Is the contract versioned?

---

## Anti-Patterns

- **Hard-coded paths/versions** — referencing specific file locations or version strings that will drift
- **Brittle coupling** — depending on implementation details rather than interfaces
- **Stale references** — pointing to artifacts that have been renamed, moved, or removed
- **Missing registry entries** — artifact exists but isn't discoverable through standard channels
- **Taxonomy orphans** — using domain or terminal values that don't exist in the taxonomy file
