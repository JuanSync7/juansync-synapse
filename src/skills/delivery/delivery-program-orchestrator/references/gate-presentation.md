# Gate Presentation Format (Point-of-Emit at every *-GATE)

Loaded at `[SPEC-GATE]`, `[ARCH-GATE]`, `[SCOPE-GATE]`, `[PLAN-GATE]`, `[HANDOFF]`. Implements the customer-facing half of `delivery-orchestration-gate-contract`. The protocol defines WHAT a gate is; this reference defines HOW to render it.

## The block (verbatim shape)

```markdown
## GATE — <stage-id> — <ISO-date>

**Artifact produced:** `<path>` (by <writer-skill-name>)

### Diff summary
- <field 1 from writer output — e.g., "FR-NNN count: 12">
- <field 2 — e.g., "NFR coverage: latency, availability, security">
- <field 3 — e.g., "Glossary: 8 terms">

### Risks / conflicts surfaced
- <verbatim from writer's output — do not paraphrase>
- (or: "none surfaced")

### Decision options
- `approve` — advance to next stage
- `revise <comments>` — re-invoke writer with comments
- `pause` — suspend program; resume later via /delivery-program-orchestrator
- `abort` — close program with exit_reason=abort

> Reply with exactly one token.
```

Token recognition is **strict-prefix** — accept `approve`, `revise`, `pause`, `abort` as the first whitespace-separated token of the customer's reply. Synonyms (`yes`, `lgtm`, `looks good`) trigger a clarification request: "Read as approve? Reply `approve` to confirm." This prevents the silent-approval failure mode where an ambiguous "👍" advances past a half-baked artifact.

## Per-stage field overrides

Diff summary fields differ per stage. Use the table below — do not invent fields.

| Stage | Diff summary fields | Risk source |
|---|---|---|
| `[SPEC-GATE]` | FR count, NFR categories covered, glossary term count, actor count | writer's `risks:` frontmatter if present, else "none surfaced" |
| `[ARCH-GATE]` | Component count, tech stack list, `foundations:` list (MUST be present), data-flow shape (linear/branched/event-driven) | conflicts vs SPEC.md (NFRs unmet, etc.) |
| `[SCOPE-GATE]` | Phase count, each phase's TAG + one-line description, in-scope and out-of-scope summary, deferred list | phasing conflicts vs SPEC priorities |
| `[PLAN-GATE]` | Story count, `foundation_source`, dependency graph shape, file_cap_override count | verbatim CONFLICT blocks from STORIES.md, none-with-risk warnings |
| `[HANDOFF]` | Exit reason, slice rollup counts (green/blocked/superseded/undispatched), lessons tail count | escalation reason if any |

## Special-case decision tokens

Two stages require extended decision syntax:

**[SCOPE-GATE]** — customer must specify TAG with approve:
- `approve --tag <TAG>` — advance with selected TAG
- Bare `approve` → reject with "TAG required. Reply `approve --tag <TAG>`."

**[HANDOFF]** — decision options depend on executor's exit reason:
- `all_slices_green` → `merge` | `next-tag` | `done`
- `escalated_blocked` / `escalated_replan_cap` → `re-shape <comments>` | `pause` | `abort`
- `user_interrupt` → `resume` | `pause` | `abort`

The `next-tag` decision loops the program back to `[SCOPE-GATE]` for the next phase. The `resume` decision returns to `[EXEC]` without re-invoking plan-executor's pre-flight (executor handles its own resume).

## Revise comment format

When customer replies `revise <comments>`, capture the comments verbatim into PROGRAM.md and pass them as the args to the writer on re-invoke:

```
Skill(skill: "<writer-skill>", args: "<comments verbatim> — revising prior output at <path>")
```

Writer is responsible for interpreting the comments and re-emitting. Do not paraphrase or pre-process the comments — they are the customer's words to the writer.

## Audit row appended to PROGRAM.md gate-history table

For every gate emission AND every customer decision, append one row to the gate-history table in PROGRAM.md:

```
| <ISO-date> | <stage-id> | <event: emit \| approve \| revise \| pause \| abort> | <writer-skill> | <one-line note> |
```

Two rows per gate cycle: one `emit` row when the block is presented, one `approve|revise|pause|abort` row when the customer decides. Missing rows break the resumability invariant — [RESUME] reconstructs state by walking this table.

## What this format does NOT include

- No customer-facing rendering of upstream-doc internals (raw frontmatter, raw markdown sections). The writer's output is the source of truth — the gate summary is a navigation aid, not a substitute for reading it.
- No orchestrator-side judgment on artifact quality. "This SPEC.md looks thin to me" is not the orchestrator's call — the gate is for the customer to make that call. The orchestrator surfaces facts (field counts, presence checks) and lets the customer decide.
- No silent re-summarization of writer output. If the writer surfaces a risk verbatim, quote it verbatim in the Risks block — paraphrasing drops nuance the customer needed to see.
