# Artifact Criteria: Agent

Loaded at [A] when an agent-type artifact is discovered. This is a diagnostic for brainstorming — it answers "is this agent-worthy?" Agents exist for one reason: context isolation. If no isolation is needed, the instructions belong in SKILL.md.

---

## Context Isolation

The defining question: **Does this work need to run in a separate context window?**

Agents are dispatched by a main agent into a fresh context. This matters when:
- The work would pollute the main agent's context (large file reads, exhaustive searches, verbose analysis)
- The work can run in parallel with other tasks
- The work produces a focused artifact that the main agent consumes as a summary

If the instructions can live as a section in SKILL.md and execute in the main conversation flow, they're not an agent — they're a prompt section.

---

## Offloading vs. Shared

Two kinds of agents serve different purposes:

| Type | Lives in | Purpose | Example |
|------|----------|---------|---------|
| **Offloading** (tier 1) | Skill's `agents/` dir | Parallelizes part of one skill's work | `memo-producer` dispatched by brainstorm skill |
| **Shared** (tier 3) | `src/agents/<domain>/` | Reusable capability across multiple skills | `protocol-review-agent` used by protocol-creator and synapse-router-artifact-gatekeeper |

Start as tier 1. Promote to tier 3 only when a second consumer appears. Premature sharing creates coupling without benefit.

---

## Prompt Section Test

Could this agent's instructions fit as a section in SKILL.md?

Apply these checks:
- **Length:** If the instructions are under ~30 lines, they're a SKILL.md section.
- **Interaction:** If the work requires user interaction (questions, approvals, clarification), it must happen in the main conversation flow — not in an agent.
- **Isolation benefit:** If the agent's output is consumed raw (no summarization needed), there's no isolation benefit — inline it.
- **Parallel opportunity:** If this work blocks subsequent steps and nothing else can run alongside it, parallelization isn't a factor.

An agent that's just "read this file and return the contents" is a tool call, not an agent.

---

## Input/Output Contract

Every agent needs a clear contract:
- **Input:** What does the dispatching skill pass to the agent? (Files, notepad content, specific parameters)
- **Output:** What does the agent return? (A memo, a score, a verdict, a list of issues)
- **Failure:** How does the agent signal failure? (Structured error, protocol failure assertion)

If you can't define the input and output, the agent's scope is too vague to be useful.

---

## Signs It's an Agent

- Needs fresh context — the work would pollute the main agent's context window
- Can run in parallel with other work
- Has a clear input contract and output contract
- Multiple skills could dispatch the same agent (for shared agents)
- The work is substantial enough to justify dispatch overhead (~30+ lines of instructions)

---

## Signs It's NOT an Agent

- Instructions are short enough for a SKILL.md section (under ~30 lines)
- The work must happen in the main conversation flow (user interaction needed)
- No context isolation benefit — output consumed raw without summarization
- Only called from one place with one set of instructions and could be inlined
- It's really a tool call (deterministic computation, not judgment)

---

## Naming

Agents follow `{domain}-{subdomain?}-{purpose?}-{role}` where:
- `domain` comes from `taxonomy/AGENT_TAXONOMY.md`: skill-eval, docs, protocol-eval
- `role` comes from `taxonomy/AGENT_TAXONOMY.md`: judge, prompter, auditor, writer, reviewer

Validate the chosen `domain` and `role` against the taxonomy before proceeding. If nothing fits, propose a taxonomy addition — don't invent ad hoc values.

Examples:
- `synapse-skill-eval-judge` — synapse domain, judge role
- `docs-spec-coherence-reviewer` — docs domain, spec subdomain, coherence purpose, reviewer role
- `protocol-review-agent` — protocol-eval domain, reviewer role
