# Discovery Interview (Point-of-Emit at [Q])

Loaded at `[Q]` only. Defines the question grammar used to fill the minimum chat-intent schema before routing to `[SPEC-GATE]`. The interview is bounded (≤5 questions total) and concrete (each question maps to exactly one missing field).

## The minimum schema

Four fields must be populated before [Q] exits to [SHAPE]:

| Field | Definition | Failure if missing |
|---|---|---|
| `problem` | One sentence stating what's broken or absent today | Spec writer has no narrative anchor; FRs read as feature list, not problem solution |
| `in-scope` | List of named things the build will deliver | Spec drifts toward gold-plating without an in-scope boundary |
| `out-of-scope` | List of named things the build will NOT deliver | Subagent scope-creep at execution time; closeout violation (d) on most slices |
| `constraints` | Hard limits (time, budget, tech stack, compliance, user) | Architecture-writer makes blind choices; plan-writer can't surface CONFLICT blocks |

## Question grammar

Every question must:
1. Map to exactly one missing field (name the field in PROGRAM.md when capturing the answer)
2. Be concrete and singular ("What's the one user pain you're solving?" — not "Tell me about your users")
3. Cite an example if the field is abstract ("Constraints — for example: must run on AWS, must be HIPAA-compliant, must launch by Q3")
4. Be answerable in one sentence

## Question templates (pick by missing field)

**For `problem`:**
- "What's the user pain or capability gap this build closes? In one sentence."
- "Today, when a user wants <inferred goal from dump>, what happens — and what should happen instead?"

**For `in-scope`:**
- "Name the 2–5 things this build will deliver. (Pages, endpoints, flows, capabilities — concrete nouns.)"
- "When this ships, what specifically will exist that doesn't exist today?"

**For `out-of-scope`:**
- "Name 1–3 things this build will explicitly NOT deliver, even if they seem adjacent. (This prevents scope creep at execution time.)"
- "Anything users might assume is included but isn't?"

**For `constraints`:**
- "Hard constraints — tech stack required, deadlines, compliance, integrations that must work. Even one of each is fine."
- "What can't change? (Existing systems we must integrate with, languages we're locked into, regulations.)"

## Batching rule

Ask all missing-field questions in ONE message — do not drip-feed. Drip-feeding inflates turn count and loses customer patience. Example for 3 missing fields:

```
Three quick questions to frame the spec:

1. **Problem** — what's the user pain or capability gap? (One sentence.)
2. **Out of scope** — 1–3 things this build will NOT deliver, to prevent scope creep.
3. **Constraints** — hard limits (tech, deadlines, compliance, integrations).
```

After the customer responds, update PROGRAM.md and re-check completeness. If still incomplete, batch the still-missing questions in a follow-up message — never re-ask answered ones.

## The 5-question cap

Total questions asked across all [Q] loop iterations: ≤5. Why bounded:
- A customer who can't fill 4 fields in 5 questions has a fuzzy goal, not a missing-words problem. Pushing further wastes both sides.
- The escalation path (route to `/brainstorm` first) is correct for genuine fuzziness.

When cap hit without completion, escalate with this exact message:

```
After 5 questions the intent still has gaps in <named fields>. Vertical-slice planning
needs all four fields filled to produce a quality spec. Recommended next step:
/brainstorm to explore the problem space first, then re-enter /delivery-program-orchestrator
once the framing is clearer. Reply `pause` to suspend this program meanwhile.
```

## What this reference does NOT do

- It does not ask design questions ("should the API be REST or GraphQL?"). Design is `docs-architecture-writer`'s job — discovery interview only fills the intent schema.
- It does not validate answer quality. If the customer answers "constraints: none", record verbatim — that's a valid answer for the orchestrator's purpose. The spec writer may push back later.
- It does not re-ask answered fields. If the customer's first dump named `in-scope`, do not include an `in-scope` question in the batch.
- It does not produce a spec, PRD, or any artifact. Discovery output is captured in PROGRAM.md only; the spec writer is the one who synthesizes a SPEC.md from it.
