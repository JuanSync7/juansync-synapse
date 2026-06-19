# Pipeline Routing (Point-of-Emit at [SHAPE])

Loaded at `[SHAPE]`. Deterministic decision table — no LLM heuristics beyond the rule order below. Routes the captured customer input into one of five next-node outcomes.

## Decision order

Apply checks **top-down**; halt at first match. Recording which rule fired into PROGRAM.md frontmatter (`routing_rule: <rule-id>`) is mandatory — without it, future audit cannot explain why a program took the path it did.

| Rule | Check | Next node | Sets |
|---|---|---|---|
| R1 | `STORIES.md` exists at `.delivery/stories/STORIES.md` | wrong-tool exit → redirect to `/delivery-orchestration-plan-executor` | — |
| R2 | `SPEC.md` + `architecture.md` + `scope.md` all exist (no STORIES.md) | `[PLAN-GATE]` (skip writers) | `entry_stage: plan` |
| R3 | `SPEC.md` + `architecture.md` exist (no `scope.md`) | `[SCOPE-GATE]` | `entry_stage: scope` |
| R4 | `SPEC.md` exists (no `architecture.md`) | `[ARCH-GATE]` | `entry_stage: arch` |
| R5 | Customer input names `refactor`, `migration`, `port`, `modernize`, `single-module`, or `library extraction` AND no SPEC.md | `[HORIZONTAL]` | `pipeline_shape: horizontal` |
| R6 | Customer input ≥3 sentences AND mentions `problem` + `users/customers` + a noun for the build target | `[SPEC-GATE]` | `pipeline_shape: vertical`, `entry_stage: spec` |
| R7 | Customer input <3 sentences OR missing 2+ of {problem, in-scope, constraints} | `[Q]` | `pipeline_shape: vertical`, `entry_stage: discovery` |
| R8 | Catch-all (none of the above fire) | `[Q]` | `pipeline_shape: vertical`, `entry_stage: discovery` |

R1 is a wrong-tool short-circuit — the orchestrator should never run a program when one is already mid-execution. R7/R8 default to discovery, not to spec — the cost of an extra interview turn is far below the cost of dropping a fuzzy goal into the spec writer, which will produce an under-specified SPEC.md.

## Keyword sets (R5, R6)

**R5 horizontal keywords** (exact substring match, case-insensitive):
`refactor`, `migration`, `migrate`, `port to`, `modernize`, `modernise`, `single module`, `library extraction`, `extract library`, `cleanup pass`, `dead-code removal`.

**R6 problem-shape signals** (any one suffices; combine for confidence):
- contains "problem" or "issue" or "users can't" or "we need to support"
- names a target noun (a feature, page, system, service, API)
- contains an in-scope or out-of-scope phrase ("we want X, not Y", "should do A, not B")

If R5 keywords appear alongside R6 problem-shape (e.g., "refactor auth so users can SSO"), R6 wins — the program-level intent is forward-looking even if the implementation route is partly horizontal. Note the conflict in PROGRAM.md as a routing-note.

## Filesystem probes

| Path | Used by |
|---|---|
| `SPEC.md` (project root or `docs/`) | R2, R3, R4, R6 precedence |
| `architecture.md` (project root or `docs/`) | R2, R3 |
| `scope.md` (project root or `docs/`) | R2 |
| `.delivery/stories/STORIES.md` | R1 short-circuit |
| `.delivery/program/PROGRAM.md` | (separate — handled at [NEW]/[RESUME], not here) |

Search order for each upstream doc: project root → `docs/` → first match wins. If a doc exists in BOTH locations with different content, that's a structural error — halt and surface to customer ("two SPEC.md found at <pathA> and <pathB> — which is authoritative?").

## What this rule table does NOT do

- It does not validate the content of upstream docs. Validation belongs to the consuming writer (architecture-writer checks SPEC.md fields; plan-writer checks architecture.md `foundations:` field).
- It does not infer the TAG at routing time. TAG selection happens at [SCOPE-GATE], by the customer.
- It does not decide whether to skip a gate. Skip decisions are bound by `references/skip-detection.md` and require explicit artifact presence — never derived from routing.

Deviating from this table (adding ad-hoc keyword detection, "smart" content peeking inside SPEC.md, etc.) is a routing leak — the rules surface to PROGRAM.md and become auditable. Heuristic detours don't.
