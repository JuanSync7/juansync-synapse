# Lens: Robustness

Evaluates what happens when things go wrong. Third lens — applied after scope and precision are settled.

---

## Core Question

**What happens when things go wrong?**

---

## Diagnostic Questions

1. **Creator sufficiency:** Can the `*-creator` skill build this artifact from the memo alone? What information would be missing? If the memo requires implicit knowledge to execute, the handoff is fragile.
2. **Dependency failure:** What if a consumed artifact (file, sibling, registry entry) doesn't exist? Does the artifact fail loudly with a clear message, or proceed silently with bad data?
3. **Structural preservation:** Are `<!-- VERBATIM -->` blocks identified for content that must survive transfer between phases? Prose compression destroys structural content.
4. **Edge cases:** What happens with ambiguous, incomplete, or adversarial input?
5. **Missing preconditions:** Does the artifact check its inputs before proceeding? Silent acceptance of bad input is the most common robustness failure.

### Artifact-Type-Specific

- **Skills:** What if the user provides wrong or incomplete arguments? Does the skill detect this and fail with guidance, or produce garbage?
- **Agents:** What if the dispatching skill sends incomplete context? Does the agent validate its input contract or assume everything is present?
- **Protocols:** What if an agent doesn't comply? Is non-compliance detectable, or does it pass silently?
- **Tools:** What if input is malformed or outside expected ranges? Does the tool validate and report, or crash?

---

## Anti-Patterns

- **Silent failures** — artifact proceeds with bad data instead of stopping
- **Missing precondition checks** — no validation of inputs before execution
- **Structural loss** — content that must be verbatim gets paraphrased during transfer
- **Creator gap** — memo lacks information the creator skill needs, requiring the builder to guess
- **Assumed dependencies** — artifact relies on something existing without checking
