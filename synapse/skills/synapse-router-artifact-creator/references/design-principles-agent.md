# design-principles-agent

Loaded at `[W]` in `flow-agent.md` before writing any agent file. Apply every principle
before committing content to the agent's `.md`.

**Framing.** Agents are internal dispatched recipes — they are invoked by skills or other agents,
never directly by users. A skill presents a user-facing workflow; an agent executes one well-scoped
step inside that workflow. Because agents are invisible to the user, their failure modes are harder
to debug. Precision of contract matters more here than anywhere else in the framework.

---

## 1. Single-Purpose

An agent does one job, accepts one input contract, and produces one output contract. If you cannot
name the agent's job without using "and", it is two agents.

**Rationale.** A multi-purpose agent creates hidden coupling: the dispatching skill must know which
sub-purpose it needs, and error reporting becomes ambiguous ("the agent failed" — doing what?).
Single-purpose agents have unambiguous failure modes, are independently testable, and can be
composed without collision.

**Failure mode this prevents.** An agent that "validates frontmatter and writes the registry row"
will fail on frontmatter but silently succeed on the registry write (or vice versa), leaving the
repository in a partial state with no clear rollback signal.

---

## 2. Narrow Tool Scope

Declare the tools an agent is allowed to use. More tool access means more ways to produce unintended
side effects. Prefer the minimum set that makes the job possible.

**Rationale.** An agent with broad tool access (e.g., unrestricted file writes, arbitrary shell
execution) requires a reader to trace all possible side effects across the full agent body. A
narrow-scope declaration makes the blast radius legible at a glance and forces the agent author to
justify each tool grant.

**Failure mode this prevents.** An agent with unconstrained write access that is invoked in the
wrong context (wrong artifact path, wrong domain) can silently corrupt registry files, README
indexes, or taxonomy files — with no declarative surface for the caller to inspect before dispatch.

---

## 3. Idempotent

The same inputs must produce the same outputs. An agent invoked twice on the same state must leave
the system in the same final state as invoking it once.

**Rationale.** Agents are dispatched programmatically. Network errors, partial failures, and
re-runs after debugging all trigger re-invocation. An agent that is not idempotent accumulates
state on each call: duplicate registry rows, duplicate README entries, incremented counters.

**Failure mode this prevents.** A `write-registry-row` agent that always appends (never checks for
existing row) will produce a registry with N duplicate entries after N re-runs, breaking any
downstream lookup that assumes unique names.

---

## 4. Explicit Input/Output Contract in Frontmatter

The `description` frontmatter field documents the expected inputs and output shape — not just "what
the agent does" but "what it receives and what it returns". The dispatching skill uses this field
to validate at call site without reading the full body.

**Rationale.** Agents are consumed by other artifacts that were written weeks or months later. If
the contract lives only in prose inside the `## Input Contract` section, a developer reading the
registry cannot tell whether their dispatch matches the expected shape without opening the file.
The `description` field is the registry-visible contract summary — it must carry enough information
to validate a dispatch.

**Failure mode this prevents.** A dispatching skill that passes `artifact_path` (string) to an
agent expecting `artifact_dir` (directory path) produces a silent mismatch. The agent runs, finds
nothing at the path, and returns a spurious success or confusing error. An explicit description
makes the mismatch detectable at code-review time, not runtime.

---

## 5. No Hidden Side Effects

Every file write, network call, and subagent dispatch must be visible from the agent's `## Behavior`
section. No side effects buried in helper functions, template expansion, or implicit tool calls.

**Rationale.** Agents operate inside a larger workflow. The dispatching skill must be able to reason
about what state changes will occur when it dispatches an agent — without executing it. Hidden side
effects break this reasoning: the caller cannot predict what the agent will do, cannot write a
correct pre-condition check, and cannot write a correct cleanup step if the agent fails mid-flight.

**Failure mode this prevents.** An agent that silently dispatches a subagent (e.g., to update a
README) inside a step labeled only "validate frontmatter" makes the README update invisible to
the caller. If the README update fails, the caller has no recovery path because it did not know
the update was happening.
