# Contract vs Pattern Distinction

Part B of the design document has two entry types. Getting the distinction wrong breaks the downstream chain.

## Why the distinction matters

| Entry type | Consumer | What happens if misclassified |
|------------|----------|-------------------------------|
| **CONTRACT** | write-implementation-docs Phase 0 → all agents | If a pattern is labelled as contract, implement-code agents receive implementation hints in their Phase 0 — biasing them toward one approach and compromising test agents who should derive tests from contracts alone |
| **PATTERN** | implement-code task agents directly | If a contract is labelled as pattern, write-implementation-docs Phase 0 is missing types/stubs — agents can't build against incomplete interfaces |

## How to classify

| If the code... | It's a... | Because... |
|----------------|-----------|------------|
| Defines a TypedDict, dataclass, or schema | CONTRACT | Interface surface — all agents need it |
| Defines an exception class | CONTRACT | Error contracts — callers need to know what to catch |
| Has a function signature with `raise NotImplementedError` | CONTRACT | Function interface — agents implement against it |
| Is a pure utility (deterministic, fully implemented) | CONTRACT | Shared helper — safe for all agents, no bias risk |
| Shows an algorithm or data flow approach | PATTERN | Implementation hint — only for the implementing agent |
| Shows a workflow/pipeline graph definition | PATTERN | Architecture sketch — guides but doesn't constrain |
| Shows integration between components | PATTERN | Illustrative — implementing agent decides the exact integration |

## The "bias test"

When unsure, ask: **"Would showing this to a test-writing agent compromise the test?"**

- If yes → it's a PATTERN (implementation detail that tests shouldn't assume)
- If no → it's a CONTRACT (interface definition that tests should verify against)

## Format checklist

**Contract entries must have:**
- `**Type:** Contract (exact — copied to implementation docs Phase 0)`
- Every field with type annotation and FR-tagged comment
- Complete docstrings (args, returns, raises) on all stubs
- `raise NotImplementedError("Task X.Y")` as sole stub body
- Imports at top of each entry
- No line limit — completeness wins

**Pattern entries must have:**
- `**Type:** Pattern (illustrative — for implement-code only, never test agents)`
- `# Illustrative pattern — not the final implementation` comment
- 50-120 lines, self-contained
- "Key design decisions" section with rationale
- No exact type definitions (those belong in contracts)
