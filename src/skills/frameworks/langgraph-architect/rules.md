# LangGraph Architect — Design Rules

These rules are opinionated. They encode design decisions, not suggestions.
The reviewer subagent evaluates against these rules. Violations require justification.

---

## State Design

- Use `TypedDict` for state schemas. Use `dataclass` only when you need methods or validation logic.
- Every field that multiple nodes write to MUST have a reducer annotation (e.g., `Annotated[list, operator.add]`).
- Fields representing "done/skip" flags must be `Optional` with `None` default. Never use sentinel values.
- State schemas are flat. Every field that nodes read or write is top-level.
- If you need nesting, you need a subgraph with its own schema — not a deeper dict.
- Passthrough metadata (data that travels untouched) may be nested, but nodes must not read into it.

## Node Design

- One responsibility per node. If a node calls an LLM AND transforms data, split it.
- Three node types:
  - `pure` — data transforms only. No side effects, no I/O, no suspension.
  - `io` — external calls (API, database, LLM, storage). Side effects live here.
  - `hitl` — human interaction gates. Calls `human_gate()`, which suspends execution. Not pure (suspension is a side effect), not standard I/O.
- Side effects (I/O, API calls, storage) go in dedicated I/O nodes, clearly named (e.g., `store_results`, `fetch_context`).
- Never import or call another node directly. Nodes communicate only through state.
- Nodes must not import or depend on any framework library (LangGraph, tracing, etc.) directly. The `human_gate()` abstraction is the only permitted point of contact with LangGraph's interrupt mechanism.

## Graph Topology

- Every conditional edge must define an explicit default/fallback path. Silent dead-ends are bugs.
- Cycles must have a bounded exit condition visible in the routing function. Never rely on LLM output alone to break a loop.
- Prefer linear chains unless the problem genuinely requires branching. Complexity must be justified.
- Fan-out (parallel branches) must have a corresponding fan-in (merge point) — no dangling branches.

## Human-in-the-Loop

- Default to `interrupt_before` for approval gates (human decides before node runs).
- Use `interrupt_after` only when the node's output needs human inspection but not pre-approval.
- Every HITL checkpoint must define:
  1. What question the human sees.
  2. What data they provide on resume.
  3. A provisional/safe default for headless execution.
- The provisional default must be explicit and deterministic. Silent auto-approve is not acceptable.
- Use `human_gate()` abstraction — never call `langgraph.types.interrupt` directly.

## Checkpointing

- If the graph has any HITL checkpoint, it MUST compile with a checkpointer.
- Default to memory checkpointer for dev/test, persistent backend (sqlite/postgres) for production.
- Use a checkpointer factory — never instantiate checkpoint savers directly in graph code.

## Execution

- Callers use a compiled workflow wrapper (`run()` / `arun()` / `stream()`). Never expose the raw compiled graph.
- Stream mode yields `(step_name, state)` tuples. Callers must not parse LangGraph's internal event format.

## Error Handling

- Retry transient failures INSIDE the node (use tenacity or similar). Never use graph-level cycles for retry.
- Nodes that can fail must write error info to state. Route conditionally on error presence — not try/except in the graph builder.
- For pipelines that should continue on partial failure, use an error accumulator field with a list reducer.
- Never silently swallow exceptions. Either write to `state["errors"]` or let it propagate.

## Retry

- Default: max 3 attempts, exponential backoff (1s min, 10s max).
- Only retry transient errors (timeout, rate limit, 5xx). Never retry validation or auth errors.
- If the graph runs inside an orchestrator (Temporal, Celery), prefer the orchestrator's retry for infrastructure failures.
- In-node retry handles fast/transient failures. Orchestrator retry handles slow/infra failures.
- Never duplicate retry at both levels for the same failure class.

## Observability

- Pass tracing callbacks through the `config` dict at execution time. Never hardcode tracing inside nodes.
- Nodes must not import or depend on any tracing library directly.
- For node-level timing/metrics, use a framework-agnostic decorator on the node function.
- Decorator contract: log node name, elapsed time, input/output state keys, error if raised.

## Composition

- Build subgraphs as separate `workflow() → compile()` units. Add the compiled subgraph as a node in the parent.
- Subgraphs own their own state schema. Parent and child communicate through explicit input/output mapping at the edge.
- Never share state schemas across graph boundaries.
