# Code Review Verdict — Output Template

The review artifact produced by code-review mode. Evaluates LangGraph/LangChain
Python code against rules.md. Cites files, functions, and line numbers.

```yaml
verdict: APPROVE | REVISE | REJECT

summary: <1-2 sentence overall assessment>

files_reviewed:
  - <file path>

rule_checks:
  - rule: <rule name from rules.md — e.g., "Node Design: single responsibility">
    status: pass | fail | warn
    location: <file:function_name or file:line_number>
    detail: <specific finding — what was checked, what was found>
    fix: <optional — concrete code change suggestion if fail/warn>

pattern_conformance:
  state_schema:
    uses_typeddict: <true/false>
    flat: <true/false>
    reducers_present: <true/false for multi-writer fields>
    issues: [<specific field/line issues>]

  node_design:
    single_responsibility: <true/false>
    types_correct: <true/false — pure/io/hitl labels match behavior>
    no_cross_imports: <true/false — nodes don't import each other>
    issues: [<specific function/line issues>]

  graph_topology:
    builder_pattern: <true/false — uses fluent builder, not raw StateGraph>
    all_defaults_present: <true/false — conditional edges have fallbacks>
    bounded_cycles: <true/false>
    issues: [<specific edge/routing issues>]

  hitl:
    uses_human_gate: <true/false — not raw interrupt>
    provisionals_defined: <true/false>
    checkpointer_present: <true/false when HITL exists>
    issues: [<specific checkpoint issues>]

  execution:
    uses_wrapper: <true/false — CompiledWorkflow or equivalent, not raw graph>
    stream_format_isolated: <true/false — callers don't parse LangGraph events>
    issues: [<specific execution issues>]

  error_handling:
    retry_in_node: <true/false — not graph-level cycles>
    errors_written_to_state: <true/false>
    no_silent_swallowing: <true/false>
    issues: [<specific error handling issues>]

  observability:
    callbacks_via_config: <true/false — not hardcoded>
    no_tracing_in_nodes: <true/false>
    issues: [<specific observability issues>]

risk_flags:
  - <any concern not covered by rules — e.g., "function X is 200 lines">

recommendations:
  - priority: high | medium | low
    location: <file:function_name or file:line_number>
    description: <what to change and why>
```

## Reviewer Instructions

When operating in code-review mode:
- Evaluate against rules.md. The same rules apply to code as to specs.
- Reference the patterns in references/*.py — code should follow these patterns.
- Be specific: cite file, function name, and line number for every finding.
- APPROVE if no failures and no high-priority recommendations.
- REVISE if there are failures or high-priority recommendations.
- REJECT only if the code has fundamental architectural problems.
