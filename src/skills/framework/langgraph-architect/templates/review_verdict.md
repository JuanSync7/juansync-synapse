# Review Verdict — Output Template

The review artifact produced by review mode. The reviewer subagent evaluates
the graph spec against rules.md and produces this structured verdict.

```yaml
verdict: APPROVE | REVISE | REJECT

summary: <1-2 sentence overall assessment>

rule_checks:
  - rule: <rule name from rules.md — e.g., "State Design: reducer required">
    status: pass | fail | warn
    detail: <specific finding — what was checked, what was found>
    fix: <optional — concrete suggestion if fail/warn>

topology_analysis:
  dead_ends: [<nodes with no outgoing edge and not terminal>]
  unbounded_cycles: [<cycles without visible exit condition>]
  orphan_nodes: [<nodes not reachable from entry>]
  missing_fan_in: [<fan-out branches without merge point>]

hitl_analysis:
  checkpoints_without_provisional: [<checkpoint nodes missing safe default>]
  checkpointer_missing: <true if HITL exists but checkpointer is none>

risk_flags:
  - <any design concern not covered by rules — e.g., "node X does 3 things">

recommendations:
  - priority: high | medium | low
    description: <what to change and why>
```

## Reviewer Instructions

When operating in review mode:
- Evaluate ONLY against rules.md. Do not invent new rules.
- Be specific: cite the exact node, field, or edge that violates.
- APPROVE if no failures and no high-priority recommendations.
- REVISE if there are failures or high-priority recommendations.
- REJECT only if the design has fundamental structural problems (wrong graph shape for the problem).
