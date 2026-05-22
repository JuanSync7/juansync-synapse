---
name: synapse-observability-execution-trace
description: "Structured self-report trace appended by subagents when an observer requests execution observability"
domain: synapse
subdomain: observability
subject: execution
kind: trace
version: 1
tags: [execution-trace, self-reported, subagent-observability]
---

# Execution Trace Protocol

A structured self-report appended by a subagent to its response when an observer requests execution observability. Zero overhead in normal runs — only injected when someone is watching. An **observer** (synapse-skill-skill-improver grading EVAL-E, auto-research optimizing, user debugging) injects this protocol's capture instructions into a subagent's prompt; the subagent executes the skill normally, then appends a trace block describing what it did. The skill itself never references this protocol — it is injected externally.

## Contract

The subagent MUST append this YAML block at the end of its response:

```yaml
## Execution Trace

phases_executed: [0, 1, 2, 3]        # which phases ran (by number or name)
test_file_count: 12                   # relevant input count (if applicable)

agents_dispatched:
  - phase: 1                          # which phase triggered this dispatch
    purpose: scan test file            # what the agent does
    target: tests/test_auth.py         # file or resource targeted
    model: sonnet                      # model explicitly set on Agent()
  - phase: 2
    purpose: cross-match ACs
    model: opus

workflow_decisions:
  - decision: subagent dispatch strategy
    chose: per-file dispatch
    reason: "12 test files >= 10 threshold"
  - decision: intent document source
    chose: spec (docs/auth/SPEC.md)
    reason: "spec exists — higher priority than eng-guide"

precondition_checks:
  - check: intent document exists
    result: pass
    path: docs/auth/SPEC.md
  - check: test directory exists
    result: pass
    path: tests/

context_isolation:
  phase1_prompt_contains_acs: false    # key isolation invariant
  phase1_prompt_contains_spec: false   # another isolation check
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `phases_executed` | list | yes | Phases that ran, in execution order |
| `agents_dispatched` | list of objects | yes (if any) | Each Agent() call with phase, purpose, target, model |
| `workflow_decisions` | list of objects | yes (if any) | Key branching decisions with what was chosen and why |
| `precondition_checks` | list of objects | yes (if any) | Input validations with pass/fail result |
| `context_isolation` | object | no | Boolean flags for what was deliberately excluded from subagent prompts |

Additional fields may be added for skill-specific trace needs. The schema is extensible.

## Failure Assertion

If the skill produces no observable execution phases, STOP and output:

```
PROTOCOL FAILURE: synapse-observability-execution-trace — no phases executed, trace cannot be constructed.
```

## Configuration

### Nesting

| Mode | Behavior | When to use |
|------|----------|-------------|
| `shallow` (default) | Trace only the top-level skill execution. Subagents dispatched by the skill are listed in `agents_dispatched` but do not produce their own traces. | Most evaluation and debugging scenarios |
| `deep` | Each subagent also appends its own execution trace (recursive). The top-level trace contains nested traces. | Diagnosing issues in subagent behavior, not just dispatch |

The observer specifies nesting depth when injecting. Default is `shallow`.
