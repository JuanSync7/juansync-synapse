# Design Brief — Input Template for Autonomous Invocation

Parent agents fill this in before dispatching langgraph-architect as a subagent.
This replaces the interactive Q&A in design mode — every question the architect
would ask the user, the brief answers upfront.

The brief must be specific enough that the design subagent never needs to ask
a clarifying question. If a section is genuinely unknown, say "unknown" —
the architect will make an opinionated default and document the assumption.

```yaml
brief:
  domain: <what domain/system this graph serves>
  purpose: <what the graph does — one sentence: input → transformation → output>

  inputs:
    - name: <field name>
      type: <python type annotation>
      source: <where this data comes from — API, user, upstream graph, etc.>

  outputs:
    - name: <field name>
      type: <python type annotation>
      consumer: <who/what uses this output — downstream graph, API response, storage, etc.>

  constraints:  # hard requirements — non-negotiable, design MUST satisfy these
    - <constraint — e.g., "must complete in under 30s", "no external API calls">

  preferences:  # soft requirements — can be traded off if justified
    - <preference — e.g., "prefer parallel processing where possible">

  known_stages:  # operations the graph should perform (order is a suggestion, not a mandate)
    - name: <stage name>
      does: <what this stage does — one sentence>
      type: pure | io | hitl | unknown  # optional hint
    # The architect may reorder, merge, split, or add stages based on rules.md

  hitl_requirements:
    - stage: <at which stage human intervenes>
      reason: <why human judgment is needed here>
      provisional: <safe default if running headless — or "unknown" to let architect decide>
    # Empty list = fully automated. The architect will still challenge this.

  integration:
    orchestrator: none | temporal | celery  # affects retry strategy
    existing_systems:
      - <system name — e.g., "Weaviate vector DB", "MinIO object store">
    checkpointer: memory | sqlite | postgres | unknown

  quality_criteria:  # what makes this graph spec "done" — the review subagent checks these too
    - <criterion — e.g., "all error paths route to a fallback, never silent failure">

  context: |
    # Optional free-form context the parent agent wants to pass.
    # Architecture decisions, related specs, constraints not captured above.
    # The architect reads this but is not bound by it — rules.md takes precedence.
```

## What the Architect Does With This

1. Validates the brief against rules.md (flags contradictions)
2. Runs design steps 0-9 using the brief as input (no interactive questions)
3. Where the brief says "unknown", makes an opinionated default and documents the assumption in the graph spec
4. Dispatches review subagent
5. Iterates until APPROVE or max cycles reached

## What Makes a Good Brief

- **Specific inputs/outputs** — not "takes documents" but "takes `list[Document]` from the ingestion API"
- **Explicit constraints** — anything the architect can't infer from the domain
- **Honest unknowns** — "unknown" is better than a guess the architect will design around
- **Quality criteria** — tells the review subagent what to prioritize beyond rules.md
