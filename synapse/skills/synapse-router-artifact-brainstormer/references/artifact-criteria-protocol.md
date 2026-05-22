# Artifact Criteria: Protocol

Loaded at [A] when a protocol-type artifact is discovered. This is a diagnostic for brainstorming — it answers "is this protocol-worthy?" Protocols are shared behavioral contracts enforced across multiple agents or skills. If only one consumer exists, it's a rule, not a protocol.

---

## Cross-Cutting Enforcement

The defining question: **Does this enforce behavior across multiple agents or skills?**

Protocols exist because multiple artifacts need the same behavioral convention applied consistently. A single artifact needing a constraint is a rules/ companion file. Two or more artifacts needing the same constraint is a protocol.

Test: If you removed the skill this rule currently lives in, would other artifacts still need this convention? If yes, it's a protocol.

---

## Rule vs. Protocol

| | Rule | Protocol |
|---|------|----------|
| **Lives in** | `rules/` dir of one skill | `src/protocols/<domain>/` |
| **Consumers** | One skill | Multiple skills/agents |
| **Scope** | Local constraint | Cross-cutting convention |
| **Example** | "This skill MUST reject input without a version field" | "All agents that modify indexed files MUST update the index before returning" |

A rule that two skills copy-paste is a protocol waiting to be extracted.

---

## Precision Anchors

Four questions that must be answered for every protocol candidate. Ambiguity in any answer means the protocol isn't ready:

1. **What behavior are you enforcing?** Name the specific behavior, not a category. "Consistent error reporting" is a category. "Every agent failure outputs a structured block with agent name, input hash, and error message" is a behavior.

2. **When exactly must it fire?** Name the trigger moment. Not "when appropriate" or "during execution" but "BEFORE returning any response that modifies a file listed in README.md" or "AFTER every subagent dispatch completes." Vague triggers produce inconsistent enforcement.

3. **What does compliance look like?** Describe the observable output when the protocol is followed correctly. This is how you verify enforcement without reading the agent's reasoning.

4. **What does violation look like?** Describe how to detect the agent skipped it. If you can't detect violation, you can't enforce the protocol.

---

## Trigger Clarity

Does the protocol name the exact moment it fires?

- **Clear trigger:** "BEFORE returning any response that creates a new file in `src/agents/`"
- **Vague trigger:** "When creating agents" (when during creation? before writing? after writing? during review?)
- **Missing trigger:** "Agents should follow this convention" (no trigger at all — the agent loads it and forgets)

Protocols with vague triggers degrade to suggestions. The LLM follows them when they're top-of-mind and ignores them under task pressure.

---

## Signal Strength

Does every instruction use commitment language?

| Commitment level | Language | Effect on LLM |
|-----------------|----------|---------------|
| **Strong** | MUST, NEVER, STOP, BEFORE, AFTER | Treated as hard constraint |
| **Weak** | should, consider, may want to, ideally, when possible | Rationalized away under pressure |

A protocol with weak signals is a suggestion document. Suggestions lose to task pressure every time. Every instruction in the contract section must use strong commitment language.

---

## Signs It's a Protocol

- Multiple consumers need the same behavioral convention
- The convention enforces structural consistency across artifacts
- Removing it would cause divergent behavior across the system
- It has a clear trigger moment and commitment-level language
- Compliance and violation are both observable

---

## Signs It's NOT a Protocol

- **Only one consumer** — make it a `rules/` file in that skill's directory
- **Describes output format** rather than behavioral convention — make it a template in `templates/`
- **Contains domain knowledge** rather than enforcement — make it a `references/` file
- **Uses weak language** throughout — it's advice, not a contract; reconsider whether enforcement is needed at all
- **Trigger is vague or absent** — if you can't name the exact moment, you can't enforce it

---

## Naming

Protocols follow `{domain}-{subdomain}-{subject}-{kind}` (all four slots required) where:
- `domain` comes from `taxonomy/PROTOCOL_TAXONOMY.md` (e.g., synapse)
- `subdomain` comes from `taxonomy/PROTOCOL_TAXONOMY.md` (e.g., observability, memory)
- `subject` is the noun naming what the protocol describes (e.g., execution, failure-reporting, external-memory)
- `kind` is the structural type (trace, schema, contract, format, spec, standard)

Validate the chosen `domain`, `subdomain`, and `kind` against the taxonomy before proceeding. If nothing fits, propose a taxonomy addition — don't invent ad hoc values.

Examples:
- `synapse-observability-execution-trace` — synapse/observability, subject=execution, kind=trace
- `synapse-memory-external-memory-contract` — synapse/memory, subject=external-memory, kind=contract
- `synapse-observability-failure-reporting-schema` — synapse/observability, subject=failure-reporting, kind=schema
