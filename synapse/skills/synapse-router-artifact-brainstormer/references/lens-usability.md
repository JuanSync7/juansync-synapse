# Lens: Usability

Evaluates whether the consumer knows how to use this artifact. Last lens — applied after scope, precision, robustness, and maintenance are settled.

---

## Core Question

**Will the consumer know how to use this?**

---

## Diagnostic Questions

1. **Invocation clarity:** Will the user or consumer know when and how to invoke this artifact? Is the trigger obvious or buried?
2. **Artifact count awareness:** Are we creating too many artifacts for this problem? More artifacts means more discovery burden and more maintenance.
3. **Discovery:** Can someone find this in the appropriate registry? Is the name self-explanatory to someone who hasn't read the body?
4. **Naming communicates purpose:** Does the name tell you what this does without reading the description? A good name is a routing signal.
5. **Output format expected:** Does the consumer know what shape to expect from this artifact's output? Surprise formats cause friction.

### Artifact-Type-Specific

- **Skills:** Is the description a routing contract — trigger conditions, not a workflow summary? A description that could replace reading the body is too broad.
- **Agents:** Is the input contract documented? Is the output shape clear to the dispatching skill? Undocumented contracts force trial-and-error.
- **Protocols:** Is the compliance signal clear — what does "following this protocol" look like in practice? Vague protocols get ignored.
- **Tools:** Is the CLI interface intuitive? Can someone use it from the help text alone without reading source?

---

## Anti-Patterns

- **Unclear invocation** — consumer can't tell when to use this vs. something else
- **Non-discoverable artifacts** — exists but isn't in the registry or has a cryptic name
- **Names that don't communicate purpose** — requires reading the body to understand what it does
- **Surprise output formats** — consumer expects markdown, gets YAML (or vice versa)
- **Excessive artifact count** — problem could be solved with fewer artifacts at lower maintenance cost
