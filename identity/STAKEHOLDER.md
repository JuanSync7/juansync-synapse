# Stakeholder Persona

## Priorities

Correctness > Configurability > Structural Clarity > Agent-Parallelizability > Performance

- Correctness has the edge: if the system is correct, I can configure it properly;
  if it's wrong, configurability is meaningless
- Configurability: swappable components, config-driven behavior — I control the system
  from high-level dials, not by touching internals
- Structural clarity: linear flow, clean module boundaries (SystemVerilog-style —
  ports/logic/state are separate concerns), README signposts, PEP/Google-style docstrings,
  block-diagram-able code
- Agent-parallelizability: tasks must decompose independently with clear handoff docs —
  poor context distribution multiplies token cost exponentially
- Performance: not a design driver, but open to targeted improvements when suggested
- Features are welcome — software is an endless cycle of improvement — but they must be
  well-structured and follow the same standards as existing code

## Expertise Map

- Software architecture / system design: confident
- Python (reading, reviewing, config): familiar
- Python (deep internals, metaprogramming): familiar
- LLM / RAG / AI pipelines: confident
- SQL / databases: unfamiliar
- Infrastructure / Docker / networking: familiar
- CI/CD / DevOps: unfamiliar
- Testing strategies (structure, not implementation): familiar
- Frontend / JavaScript / TypeScript: no-opinion
- Security / auth / crypto: no-opinion

## Decision Heuristics

- Prefer proven libraries over custom solutions
- When uncertain between two approaches, pick the one easier to draw as a block diagram
- Configuration over hardcoding — behavior adjustable without touching code
- Every new feature should be addable without modifying the core pipeline — if it
  requires touching the spine, redesign the integration point first
- Schemas first — define the contract before writing the implementation
- Code and directory structure should be navigable like a block diagram — a reader
  should know where to look without grep
- If agents can't execute a task independently with just the handoff doc, the doc
  is insufficient
- When in doubt about security, be strict — agents must explain the why and provide
  a concrete use case before proceeding

## Red Flags

No half-built ghosts, no mystery dependencies, no invisible failures, no untraceable work.

- Scope growth or "we'll need this later" reasoning that results in stubs or partial
  implementations — every feature shipped must be end-to-end functional
- Introducing a new dependency or technology without explaining why existing ones
  don't suffice
- A feature that can't be explained in a few sentences
- Code that creates circular or non-obvious dependencies between modules
- Missing or incomplete handoff documentation for a task meant for parallel agent execution
- Hardcoded values where configuration should exist
- A module or file doing two unrelated things — signals a missing boundary split
- Error handling that silently swallows failures instead of surfacing them clearly
- Tests that mock so heavily they're not testing real behavior
- A PR or task that touches many files across unrelated modules — should have been
  split into independent tasks
- Removing or weakening existing configuration options without explicit justification
- Agent output that doesn't cite which spec/doc/requirement it's working from

## Escalation Triggers

Agents are the technical experts. Make the call, implement it, explain your reasoning,
show alternatives. The architecture is swappable — if a choice is wrong, we replace the
module, not rewrite the system. Escalate only when swappability can't save you:

- Truly irreversible actions that swappability can't undo — permanent data deletion,
  public API contracts consumed by external parties, production credentials or secrets
- Agent genuinely cannot determine the best option — trade-offs are roughly equal
  and no heuristic resolves the tie
- Changes to how agents receive or hand off context (directly affects token cost
  and parallel execution)
- Any action that would compromise the system's ability to remain configurable and
  swappable — introducing tight coupling that can't be undone by config
- Actions visible to external users or systems — publishing packages, sending
  notifications, deploying to production, posting to third-party APIs
