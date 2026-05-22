# Protocol Design Principles

These principles determine whether a protocol changes agent behavior or just adds token noise. Each traces to a specific failure mode observed in hand-written protocols.

---

## Mental Model: Protocols Are AXI4 for LLMs

In AMBA AXI4, a master and slave communicate through behavioral contracts: "AWREADY MUST be asserted only after AWVALID." The rule is imperative, point-of-action, and unambiguous. No explanation needed. No example needed. The instruction IS the specification.

Our protocols are the same thing for LLM agents. A consuming skill or agent loads the protocol at a specific interaction point. The protocol defines what the agent MUST or MUST NOT do at that moment. If the rule is clear enough, the agent follows it. If it's vague, the agent rationalizes past it.

**Key difference from skills:** Skills are long-running workflows with phases, progressive disclosure, and companion files. Protocols are short imperative contracts — 30 to 120 lines. A protocol that needs progressive disclosure is probably a skill.

---

## Three Failure Modes (and Their Solutions)

Hand-written protocols fail for three reasons. Protocol-creator must solve all three.

### 1. Competing Priority

The protocol instruction conflicts with the agent's primary task and loses.

**Why it happens:** The agent weighs "finish the user's task" against "follow this protocol rule" and decides the task is more important. Weak wording gives the agent permission to skip.

**Solution:** Commitment language. MUST, NEVER, STOP, DO NOT. Not "should", "try to", "prefer", "consider." Commitment language removes the escape hatch.

**Bad:** "You should consider updating the README when modifying files."
**Good:** "BEFORE returning any response that modifies a file, you MUST verify the README reflects the change. If it does not, update the README BEFORE responding."

### 2. Vague Trigger

The agent doesn't know WHEN the protocol applies, so it never fires.

**Why it happens:** The trigger condition is a fuzzy concept ("when appropriate", "for important files") instead of a named moment. The agent can always argue "this situation isn't important enough."

**Solution:** Named trigger moments. Every instruction specifies the exact moment it fires: "BEFORE returning", "AFTER modifying", "WHEN dispatching a subagent." If you can't name the moment, the protocol isn't ready.

**Bad:** "When working with significant code changes, verify tests pass."
**Good:** "AFTER modifying any file in src/, run the test suite BEFORE returning. If tests fail, STOP and output: `PROTOCOL FAILURE: test-gate — [N] tests failed.`"

### 3. Distance Decay

The protocol is loaded at session start but forgotten by the time it matters.

**Why it happens:** Context window mechanics. Instructions loaded early get diluted by subsequent content. By the time the agent reaches the relevant moment, the protocol is far away in context.

**Solution:** Point-of-action injection. The consuming skill or agent embeds the protocol via `> Read` at the specific phase or decision point where it matters — not at the top of the session. The protocol fires when it's fresh in context.

**Not protocol-creator's job:** The injection point is chosen by the consuming skill's author, not by the protocol itself. Protocol-creator writes the protocol content; the consumer decides where to inject it.

---

## Single-Concern Principle

One protocol, one behavioral contract. This is a hard rule, not a guideline.

**Why:** Protocols scale to thousands — they are thin, cheap, and composable. A protocol that packs two concerns (e.g., "update README AND run tests") creates coupling: a consumer that only needs one concern must load both. Splitting is always cheaper than packing.

**How to detect multi-concern:** If the protocol has two independent trigger moments (one for file modification, one for subagent dispatch), it's two protocols. If removing one contract section wouldn't affect the other, they're independent.

**When to split:** During Phase 1 (Elicit Precision Anchors). If the user's intent spans multiple concerns, split into multiple protocols before drafting.

---

## Failure Assertion Requirement

Every protocol MUST contain a Failure Assertion section. This is non-negotiable.

When a protocol's trigger fires but the precondition isn't met (e.g., README-first protocol fires but no README.md exists), the protocol instructs the agent to output:

```
PROTOCOL FAILURE: [protocol-name] — [specific reason]
```

This follows the tag format defined in `synapse/protocols/observability/synapse-observability-failure-reporting-schema.md`. The agent follows this like any other imperative instruction — the failure becomes part of the agent's output naturally. No separate parsing needed. This is the equivalent of an assertion failure in hardware.

**Why not skip silently?** Silent failures propagate through multi-agent workflows. The consuming skill or orchestrator never knows the protocol didn't apply. The user gets output that looks correct but wasn't validated.

---

## Protocol vs. Config

Not every behavioral rule needs a protocol. The test:

| Signal | It's config (CLAUDE.md rule) | It's a protocol |
|--------|------------------------------|-----------------|
| One line is enough | Yes | — |
| LLM follows it reliably as a single line | Yes | — |
| Needs enforcement mechanism (failure assertion, structured trigger) | — | Yes |
| Needs to be injected at a specific moment, not always-on | — | Yes |
| Multiple skills need the same behavioral contract | — | Yes |
| A single CLAUDE.md line didn't stick | — | Yes |

A protocol is a CLAUDE.md rule that didn't stick, extracted and made injectable with enforcement mechanisms.

---

## Good/Bad Wording Contrasts

### Contract Instructions

**Bad:** "Consider checking if the cache is stale before serving a response."
**Good:** "BEFORE serving any cached response, verify the cache entry is younger than the TTL. If stale, MUST refetch. DO NOT serve stale data."

**Bad:** "It's generally a good idea to validate input parameters."
**Good:** "BEFORE processing any input, validate all required parameters are present. If any are missing, STOP and output: `PROTOCOL FAILURE: input-validation — missing parameter: [name]`."

**Bad:** "When appropriate, log the decision rationale."
**Good:** "AFTER every branching decision in the Contract section, APPEND a one-line rationale to the execution trace: `decision: [what], chose: [option], reason: [why]`."

### Mental Model Paragraphs

**Bad (too long, restates rules):**
"This protocol ensures agents validate input parameters by checking that all required fields are present before processing. It also requires agents to log validation failures using the PROTOCOL FAILURE format. When parameters are missing, agents must stop processing."

**Good (one paragraph, explains WHY):**
"Prevents silent failures from propagating through multi-agent workflows when required input is missing. Without explicit validation, agents produce confident-looking output from incomplete data — errors surface during review or production, when they're expensive to fix."

---

## Line Budget

Protocols should be **30–120 lines** including frontmatter. This is a guideline, not a hard cap, but violations signal problems:

- **Under 30 lines:** The protocol may be config — a single CLAUDE.md rule might suffice.
- **Over 120 lines:** The protocol likely packs multiple concerns or includes explanatory prose that belongs in the mental model, not the contract. Split or trim.
- **Execution-trace is 119 lines:** This includes a YAML schema block and field definitions. Schema-type protocols trend longer; behavioral protocols trend shorter (30–60 lines).
