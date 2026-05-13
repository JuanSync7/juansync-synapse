# Lens: Boundary

Defines where an artifact stops and something else starts. First lens in rotation because all other lenses depend on scope being clear.

---

## Core Question

**Where does this artifact stop and something else start?**

---

## Diagnostic Questions

1. What does this artifact do? What does it explicitly NOT do?
2. Is there an adjacent artifact (sibling, complement, or alternate)? What if someone means the sibling instead?
3. Is the scope creeping? Can you write "[this] does X; [sibling] does Y" as a clean boundary sentence?
4. If the artifact were removed, what breaks? If the answer is "nothing specific," the boundary is unclear or the artifact is redundant.

### Artifact-Type-Specific

- **Skills:** Does the Wrong-Tool Detection section name specific siblings and redirect cleanly?
- **Agents:** Is this agent's responsibility distinct from the dispatching skill's logic? Could the skill do this inline?
- **Protocols:** Is the enforcement boundary clear — what behavior is in scope, what's explicitly out?
- **Tools:** Is the input/output contract distinct from other tools? Could two tools produce overlapping outputs?

### Interface Stability (tier 2+ companions)

- If this artifact is consumed by another skill or workflow, is the interface stable?
- Could extracting or restructuring this artifact break consumers?
- Would renaming this artifact cascade to dependents?

---

## Anti-Patterns

- **Scope creep** — artifact does "one more thing" that belongs to a sibling
- **Overlapping responsibilities** — two artifacts handle the same concern with no clear ownership
- **Missing Wrong-Tool Detection** — skills that don't redirect when mismatched
- **Unstable interfaces** — shared companions whose shape changes frequently, breaking consumers
- **Phantom boundaries** — artifact claims to exclude something but the body still handles it
