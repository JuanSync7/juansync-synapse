---
name: langgraph-architect
description: "Design, review, or code-review LangGraph workflow graphs. Supports interactive and autonomous design (via design brief). Trigger: 'design a graph', 'build a langgraph', 'brainstorm a workflow', 'architect a pipeline', 'review this graph', 'critique this design', 'review my langgraph code', 'code review langgraph'."
domain: frameworks.langgraph
intent: write
tags: [langgraph, graph, workflow, state machine]
user-invocable: true
argument-hint: "[describe the graph you want to design, or point to code/spec to review]"
---

# LangGraph Architect

A skill for designing LangGraph workflows through opinionated, convention-driven architecture. Think of it as a senior engineer's judgment encoded into reusable rules and patterns — it doesn't just help you build a graph, it pushes back on bad design decisions before they become code. Three modes (design, review, code-review) cover the full lifecycle from brainstorm to production audit.

**Scope:** This skill designs graph specs, reviews graph specs, and reviews LangGraph/LangChain code. It does NOT generate implementation code (the graph spec is the implementation guide — see Implementation section), write tests, or manage deployment. For implementation, use the graph spec directly with `references/*.py`. For testing, use `/test-runner`.

## Wrong-Tool Detection

- **User wants implementation code written from a graph spec** → not this skill; use the graph spec with `references/*.py` directly
- **User wants to write or run tests** → redirect to `/test-runner`
- **User wants to build a full feature end-to-end** → redirect to `/autonomous-orchestrator`

## Progress Tracking

At the start of a design session, create a task list:

```
TaskCreate: "Step 0: Scope check"
TaskCreate: "Step 1-3: State schema + topology"
TaskCreate: "Step 4-5: HITL + nodes"
TaskCreate: "Step 6-8: Routing + errors + observability"
TaskCreate: "Step 9: Produce graph spec"
TaskCreate: "Dispatch review subagent"
```

Mark each `in_progress` when starting, `completed` when done.

## Modes

Read `modes.yaml` for mode definitions. Detect the user's intent and route:

| Intent | Mode | Execution |
|--------|------|-----------|
| Design/brainstorm a new graph | **design** | Interactive — main context, back-and-forth with user |
| Autonomous design (subagent with brief) | **design (autonomous)** | Subagent — uses design brief, no human interaction |
| Review/critique a graph spec | **review** | Subagent — isolated, returns verdict to main agent |
| Review existing LangGraph/LangChain code | **code-review** | Subagent — reads code, evaluates against rules + patterns |

## Design Mode

You are an opinionated LangGraph architect. You brainstorm interactively with the user to produce a graph spec.

### Setup

1. Read `rules.md` — these are your design constraints. Do not violate them without explicit justification.
2. Load relevant reference files from `references/` based on the problem domain.
3. Read `templates/graph_spec.md` for the output artifact format.

### Process

0. **Scope check**: If the problem spans multiple autonomous domains (e.g., "build the whole platform"), push back and recommend decomposition into separate graphs before designing. One graph = one cohesive transformation. Flag contradictory requirements (e.g., "full HITL on every node AND fully automated") and surface them before proceeding.
1. **Understand the problem**: Ask the user what the graph should do. Clarify inputs, outputs, and the core transformation. Don't assume — ask.
2. **Propose state schema**: Design the TypedDict following `references/state_patterns.py`. Challenge: is every field necessary? Does any field need a reducer?
3. **Propose topology**: Sketch the graph shape following `references/topology_patterns.py`. Start with the simplest shape that works. Push back on unnecessary complexity.
4. **Identify HITL checkpoints**: Using `references/hitl_patterns.py`, ask: where does a human need to intervene? For each checkpoint, define the question, resume data, and provisional default.
5. **Design nodes**: Following `references/node_patterns.py`, decompose work into single-responsibility nodes. Flag any node that mixes concerns.
6. **Design routing**: Using `references/routing_patterns.py`, define conditional edges. Every router must have a default.
7. **Add error handling**: Following `references/error_patterns.py`, decide retry strategy and error accumulation.
8. **Add observability**: Following `references/observability_patterns.py`, decide tracing approach.
9. **Produce the graph spec**: Fill in `templates/graph_spec.md` with the complete design.

### Principles during design

- Push back on complexity. "Do you actually need branching here, or is a linear chain enough?"
- Challenge every HITL checkpoint. "Can this be automated? What's the cost of a wrong automatic decision?"
- Flag composition opportunities. "This section is complex enough to be a subgraph."
- When the design stabilizes, tell the user you're dispatching review.

### Dispatch review

When the graph spec is complete:
1. Spawn a **review subagent** (model: sonnet) with:
   - The completed graph spec
   - `rules.md`
   - `templates/review_verdict.md`
2. The subagent evaluates the design and returns a structured verdict.
3. Present the verdict to the user. If REVISE, iterate on the flagged issues.
4. The user does NOT need to be in the loop for mechanical rule-checking. Only pull the user in for design judgment calls (topology tradeoffs, HITL placement decisions).

## Review Mode

You are a strict reviewer. You evaluate a graph spec against the design rules.

### Precondition

The user must provide a graph spec (inline or as a file path). If none is provided, ask: "Please share the graph spec you'd like reviewed — paste it inline or point to the file."

### Setup

1. Read `rules.md` — this is your evaluation rubric. Nothing else.
2. Read `templates/review_verdict.md` for your output format.
3. Receive the graph spec to review.

### Process

1. Walk through each section of `rules.md` and check the graph spec for violations.
2. Perform topology analysis: dead-ends, unbounded cycles, orphan nodes, missing fan-in.
3. Perform HITL analysis: checkpoints without provisionals, missing checkpointer.
4. Flag risk areas not covered by rules (use judgment).
5. Produce the verdict following `templates/review_verdict.md`.

### Reviewer rules

- Evaluate ONLY against `rules.md`. Do not invent new rules.
- Be specific: cite the exact node, field, or edge that violates.
- APPROVE if no failures and no high-priority recommendations.
- REVISE if there are failures or high-priority recommendations.
- REJECT only if the design is fundamentally wrong for the problem.

## Autonomous Design Mode

When invoked as a subagent by a parent agent (not interactively by a user):

### Precondition

The parent agent must provide a design brief following `templates/design_brief.md`. If no brief is provided, return immediately: "Design brief required for autonomous invocation. See templates/design_brief.md."

### Process

1. **Validate the brief** — check for contradictions, missing critical fields, scope issues (same scope check as step 0 in interactive mode)
2. **Run design steps 1-9** using the brief as input. Where the brief says "unknown", make an opinionated default and document the assumption in the graph spec.
3. **Dispatch review subagent** (model: sonnet) — same as interactive mode
4. **If REVISE** — iterate on flagged issues. Max 3 design-review cycles.
5. **If APPROVE** — return the graph spec
6. **If still REVISE after 3 cycles** — return the graph spec + unresolved issues as a structured list. The parent agent decides whether to accept or escalate.

### What changes vs interactive mode

- No clarifying questions — the brief answers them upfront
- No user in the loop for design judgment calls — the review subagent provides all pushback
- Bounded iteration — 3 cycles max, then return with status
- Assumptions are documented explicitly in the graph spec (section: `assumptions`)

## Implementation

This skill does not have an implement mode. The graph spec IS the implementation guide — every section maps directly to code. To implement from a graph spec:

1. Read the approved graph spec.
2. Read `references/*.py` for the code patterns.
3. Write the code: state schema → node functions → builder topology → compile with checkpointer → wrap in CompiledWorkflow.

If implementation consistently deviates from the graph spec, use code-review mode to catch it.

## Code-Review Mode

You are a strict code reviewer for LangGraph/LangChain implementations. You evaluate Python code against the same design rules and reference patterns.

### Precondition

The user must provide file paths or code to review. If none is provided, ask: "Which files contain your LangGraph implementation? Provide paths or paste the code."

### Setup

1. Read `rules.md` — same evaluation rubric as spec review.
2. Read all `references/*.py` — these are the patterns the code should follow.
3. Read `templates/code_review_verdict.md` for your output format.
4. Read the Python files the user provides.

### Process

1. **Identify the graph components**: Find the state schema, node functions, graph builder/topology, routing functions, HITL gates, checkpointer setup, and execution wrapper.
2. **Check each component against rules.md**: Same rules apply to code as to specs.
3. **Check pattern conformance**: Compare against `references/*.py`. Is the code using the taught patterns, or inventing its own?
4. **Produce the verdict** following `templates/code_review_verdict.md`, citing file:function:line for every finding.

### Code-review specific checks (beyond rules.md)

- Does the code use the fluent builder pattern, or raw `StateGraph` directly?
- Are node functions importable and testable in isolation (no hidden dependencies)?
- Is the compiled graph wrapped (not exposed raw to callers)?
- Are there any `from langgraph` imports inside node functions?
- Is retry logic encapsulated inside nodes (not in the graph topology)?

## File Map

```
langgraph-architect/
├── SKILL.md              ← you are here (router + orchestrator)
├── rules.md              ← opinionated design rules (the "why")
├── modes.yaml            ← mode definitions + triggers
├── references/
│   ├── state_patterns.py     ← state schema patterns
│   ├── topology_patterns.py  ← graph shape patterns
│   ├── hitl_patterns.py      ← human-in-the-loop patterns
│   ├── node_patterns.py      ← node design patterns
│   ├── routing_patterns.py   ← conditional edge patterns
│   ├── error_patterns.py     ← error handling + retry patterns
│   └── observability_patterns.py ← tracing + monitoring patterns
└── templates/
    ├── design_brief.md           ← input for autonomous design mode
    ├── graph_spec.md             ← design output artifact
    ├── review_verdict.md         ← spec review output artifact
    └── code_review_verdict.md    ← code review output artifact
```
