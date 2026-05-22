# Cross-Artifact Sweep

Session-level verification across ALL discovered artifacts. Loaded at [D] Done Signal — not during [B] lens rotation. This is a different concern: lenses evaluate individual artifacts, the sweep evaluates relationships between them.

---

## 1. Contract Symmetry

Every output has a consumer. Every input has a producer. Walk each artifact's dependency list:

- "Artifact X produces Y — who consumes Y?"
- "Artifact X consumes Z — who produces Z?"

**Flag:**
- **Orphan outputs** — an artifact produces something that no other artifact consumes. Is the output for the user directly, or is it dangling?
- **Dangling inputs** — an artifact expects an input that no other artifact in the session produces. Is it supplied by the user, by an existing artifact outside this session, or is it genuinely missing?

For each flagged item, determine: is this a real gap, or an expected external boundary (user-supplied input, existing infrastructure)?

---

## 2. Orphan Detection

Flag artifacts that nothing depends on AND that depend on nothing. These are fully disconnected from the artifact graph.

Possible interpretations:
- **Genuinely standalone** — a leaf artifact that serves users directly with no inter-artifact dependencies. Valid, but confirm intentional.
- **Missing connections** — should depend on or be depended on by something, but the relationship wasn't articulated. Needs investigation.

Ask: "If this artifact were removed, would anything break? Would anyone notice?"

---

## 3. Circular Dependency Check

Walk dependency chains across all artifacts. Flag any A -> B -> C -> A loops.

Circular dependencies aren't always wrong, but they must be:
- **Acknowledged** — the participants know about the cycle
- **Justified** — there's a reason the cycle exists (mutual enrichment, co-evolution)
- **Bounded** — there's a termination condition so the cycle doesn't loop infinitely during execution

Unjustified or unacknowledged cycles are design smells that indicate unclear boundaries.

---

## Procedure

1. List all artifacts from the Artifacts Discovered table
2. For each artifact, list what it produces and what it consumes
3. Run contract symmetry check — flag orphan outputs and dangling inputs
4. Run orphan detection — flag fully disconnected artifacts
5. Run circular dependency check — flag any cycles
6. Summarize findings

**If any check fails:** Route back to [B] to address specific artifacts. Name the artifacts and the specific issue.

**If all checks pass:** Proceed with Done Signal completion.
