# Lens: Preciseness

Evaluates whether every token in the artifact earns its place. Second lens — applied after boundaries are clear.

---

## Core Question

**Is every token earning its place?**

---

## Diagnostic Questions

1. Could you remove this instruction and get the same output? If yes, it's bloat.
2. Is this something Claude already knows from training? Training-covered knowledge injected as instructions wastes tokens and can even degrade output by over-constraining.
3. Could you say this in half the words without losing the judgment?
4. Is this a decision or an options list? Artifacts state decisions — they don't present menus for the consumer to choose from.
5. Who is the audience/consumer? Does the level of detail match their needs, or is it over-specified for experts / under-specified for novices?

### Artifact-Type-Specific

- **Skills:** Would a user understand when to invoke from the description alone? If the description is a workflow summary instead of trigger conditions, it's imprecise.
- **Agents:** Does the input contract include unnecessary fields that the agent never uses?
- **Protocols:** Are there instructions that don't change observable behavior? Protocol instructions must have enforcement consequences.
- **Tools:** Does the interface have unnecessary parameters? Every parameter should change the output.

---

## Anti-Patterns

- **Token bloat** — verbose instructions that could be compressed without information loss
- **Redundancy** — same instruction repeated in different words across sections
- **Training echo** — teaching what Claude already knows ("use clear variable names," "handle errors gracefully")
- **Options lists** — presenting choices instead of making decisions ("you could do A or B" instead of "do A when X, B when Y")
- **Documentation disguised as context** — explaining why something works instead of injecting what changes behavior
